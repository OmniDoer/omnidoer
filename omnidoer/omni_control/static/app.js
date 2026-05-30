const statusEl = document.createElement("p");
statusEl.textContent = "Local trusted mode. Remote mode requires pairing and broker fingerprint pinning.";
document.querySelector("main").prepend(statusEl);

const requestsRoot = document.createElement("section");
requestsRoot.id = "requests-panel";
requestsRoot.innerHTML = "<h2>Requests</h2><div id=\"requests-list\">Loading...</div>";
document.querySelector("main").append(requestsRoot);

const encoder = new TextEncoder();
const decoder = new TextDecoder();

function b64url(bytes) {
  return btoa(String.fromCharCode(...new Uint8Array(bytes))).replaceAll("+", "-").replaceAll("/", "_").replaceAll("=", "");
}

function stableAssociatedData(request) {
  return encoder.encode(`{"origin":"${request.origin}","request_id":"${request.request_id}","request_type":"${request.request_type}"}`);
}

async function deriveAesKey(sharedBits, request) {
  const hkdfBase = await crypto.subtle.importKey("raw", sharedBits, "HKDF", false, ["deriveKey"]);
  const salt = await crypto.subtle.digest("SHA-256", stableAssociatedData(request));
  return crypto.subtle.deriveKey(
    { name: "HKDF", hash: "SHA-256", salt, info: encoder.encode("omnidoer-control-web-v1") },
    hkdfBase,
    { name: "AES-GCM", length: 256 },
    false,
    ["encrypt"]
  );
}

async function encryptForBroker(payload, request) {
  const broker = await fetch("/api/broker-key", { cache: "no-store" }).then((r) => r.json());
  const brokerKey = await crypto.subtle.importKey(
    "jwk",
    broker.web_public_jwk,
    { name: "ECDH", namedCurve: "P-256" },
    false,
    []
  );
  const ephemeral = await crypto.subtle.generateKey({ name: "ECDH", namedCurve: "P-256" }, true, ["deriveBits"]);
  const sharedBits = await crypto.subtle.deriveBits({ name: "ECDH", public: brokerKey }, ephemeral.privateKey, 256);
  const key = await deriveAesKey(sharedBits, request);
  const nonce = crypto.getRandomValues(new Uint8Array(12));
  const aad = stableAssociatedData(request);
  const ciphertext = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv: nonce, additionalData: aad },
    key,
    encoder.encode(JSON.stringify(payload))
  );
  return {
    version: "web-p256-v1",
    ephemeral_public_jwk: await crypto.subtle.exportKey("jwk", ephemeral.publicKey),
    nonce: b64url(nonce),
    ciphertext: b64url(ciphertext),
    request_id: request.request_id,
    origin: request.origin,
    request_type: request.request_type
  };
}

async function submitEncrypted(request, payload) {
  const envelope = await encryptForBroker(payload, request);
  await fetch(`/api/requests/${request.request_id}/submit`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ envelope })
  });
  await loadRequests();
}

async function postAction(request, action) {
  await fetch(`/api/requests/${request.request_id}/${action}`, { method: "POST" });
  await loadRequests();
}

async function sendTakeoverInput(request, eventPayload) {
  await fetch(`/api/requests/${request.request_id}/input`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(eventPayload)
  });
}

function framePoint(event, image) {
  const rect = image.getBoundingClientRect();
  return {
    x: Math.round((event.clientX - rect.left) * (image.naturalWidth / rect.width)),
    y: Math.round((event.clientY - rect.top) * (image.naturalHeight / rect.height))
  };
}

function installTakeoverPointerHandlers(request, stream) {
  let start = null;
  let last = null;
  stream.tabIndex = 0;
  stream.onpointerdown = (event) => {
    const img = document.querySelector("#takeover-frame");
    if (!img) return;
    stream.setPointerCapture(event.pointerId);
    start = { ...framePoint(event, img), at: Date.now() };
    last = start;
  };
  stream.onpointermove = (event) => {
    const img = document.querySelector("#takeover-frame");
    if (!img || !start) return;
    last = framePoint(event, img);
  };
  stream.onpointerup = (event) => {
    const img = document.querySelector("#takeover-frame");
    if (!img || !start) return;
    const end = framePoint(event, img);
    const distance = Math.hypot(end.x - start.x, end.y - start.y);
    const duration = Date.now() - start.at;
    if (distance > 12) {
      sendTakeoverInput(request, { event_type: "drag", x: start.x, y: start.y, to_x: end.x, to_y: end.y });
    } else if (duration > 650) {
      sendTakeoverInput(request, { event_type: "long_press", x: start.x, y: start.y });
    } else {
      sendTakeoverInput(request, { event_type: "tap", x: end.x, y: end.y });
    }
    start = null;
    last = null;
  };
  stream.onkeydown = (event) => {
    if (event.key.length === 1 || ["Enter", "Tab", "Backspace", "Escape", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(event.key)) {
      event.preventDefault();
      sendTakeoverInput(request, { event_type: "key", key: event.key });
    }
  };
}

function renderRequest(request) {
  const item = document.createElement("article");
  item.className = "request";
  item.innerHTML = `
    <h3>${request.request_type}</h3>
    <p><strong>request_id:</strong> ${request.request_id}</p>
    <p><strong>origin:</strong> ${request.origin}</p>
    <p><strong>risk:</strong> ${request.risk_level}</p>
    <p><strong>status:</strong> ${request.status}</p>
    <p>Secret destination: Secret Broker. Challenge destination: Challenge Relay / target website. Human Takeover destination: controlled browser.</p>
  `;
  if (request.request_type === "credential") {
    const button = document.createElement("button");
    button.textContent = "Submit Credential";
    button.onclick = () => submitEncrypted(request, {
      username: document.querySelector("#username").value,
      password: document.querySelector("#password").value,
      totp_seed: document.querySelector("#totp-seed").value,
      save_to_vault: true
    }).then(() => {
      document.querySelector("#password").value = "";
      document.querySelector("#totp-seed").value = "";
    });
    item.append(button);
  }
  if (["totp", "sms_code", "email_code", "one_time_code", "payment_3ds", "captcha"].includes(request.request_type)) {
    const button = document.createElement("button");
    button.textContent = "Submit Challenge";
    button.onclick = () => submitEncrypted(request, { code: document.querySelector("#one-time-code").value || "user-completed" })
      .then(() => postAction(request, "complete-challenge"))
      .then(() => { document.querySelector("#one-time-code").value = ""; });
    item.append(button);
  }
  if (request.request_type === "human_takeover") {
    const stream = document.querySelector("#browser-stream");
    stream.textContent = "Loading control-only browser frame...";
    fetch(`/api/requests/${request.request_id}/frame`, { cache: "no-store" })
      .then((r) => r.json())
      .then((frame) => {
        if (frame.data_b64) {
          stream.innerHTML = `<img id="takeover-frame" alt="Controlled browser frame" src="data:${frame.content_type};base64,${frame.data_b64}">`;
          installTakeoverPointerHandlers(request, stream);
        } else {
          stream.textContent = "Browser context is not connected in this process.";
        }
      });
    stream.onwheel = (event) => {
      event.preventDefault();
      sendTakeoverInput(request, { event_type: "scroll", delta_y: Math.round(event.deltaY) });
    };
    const textInput = document.createElement("input");
    textInput.type = "password";
    textInput.placeholder = "Text to controlled browser";
    textInput.autocomplete = "off";
    const sendText = document.createElement("button");
    sendText.textContent = "Send Text";
    sendText.onclick = () => sendTakeoverInput(request, { event_type: "type", text: textInput.value }).then(() => { textInput.value = ""; });
    const enter = document.createElement("button");
    enter.textContent = "Enter";
    enter.onclick = () => sendTakeoverInput(request, { event_type: "key", key: "Enter" });
    const release = document.createElement("button");
    release.textContent = "Release Control";
    release.onclick = () => postAction(request, "release");
    item.append(textInput, sendText, enter, release);
  }
  if (request.request_type.endsWith("_approval") || request.request_type === "payment_approval") {
    const approve = document.createElement("button");
    approve.textContent = "Approve";
    approve.onclick = () => postAction(request, "approve");
    const deny = document.createElement("button");
    deny.textContent = "Deny";
    deny.onclick = () => postAction(request, "deny");
    item.append(deny, approve);
  }
  return item;
}

async function loadRequests() {
  const list = document.querySelector("#requests-list");
  const requests = await fetch("/api/requests", { cache: "no-store" }).then((r) => r.json());
  list.innerHTML = "";
  if (!requests.length) {
    list.textContent = "No pending requests.";
    return;
  }
  requests.forEach((request) => list.append(renderRequest(request)));
}

loadRequests();
setInterval(loadRequests, 3000);
