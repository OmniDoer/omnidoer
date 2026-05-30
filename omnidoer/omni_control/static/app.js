const main = document.querySelector("main");

const runtimeStatus = document.createElement("section");
runtimeStatus.id = "runtime-status";
runtimeStatus.className = "status-strip";
runtimeStatus.innerHTML = `
  <div>
    <strong id="runtime-mode">Checking runtime...</strong>
    <span id="runtime-detail">Control Client does not call OpenAI APIs or models directly.</span>
  </div>
  <div id="runtime-counts">Requests: 0</div>
`;
main.prepend(runtimeStatus);

const requestsRoot = document.createElement("section");
requestsRoot.id = "requests-panel";
requestsRoot.innerHTML = `
  <div class="panel-heading">
    <div>
      <h2>Requests</h2>
      <p>Handle credentials, verification, approvals, and human takeover from request-scoped controls.</p>
    </div>
    <div class="filter-row" aria-label="Request filters">
      <button data-filter="all" class="active">All</button>
      <button data-filter="credential">Secrets</button>
      <button data-filter="challenge">Challenges</button>
      <button data-filter="approval">Approvals</button>
      <button data-filter="takeover">Takeover</button>
    </div>
  </div>
  <div id="requests-list" class="request-grid">Loading...</div>
`;
main.insertBefore(requestsRoot, document.querySelector("#task-panel"));

const submitTaskButton = document.querySelector("#submit-task");
if (submitTaskButton) {
  submitTaskButton.onclick = () => submitTask();
}

const pairDeviceButton = document.querySelector("#pair-device");
if (pairDeviceButton) {
  pairDeviceButton.onclick = () => pairDevice();
}

const refreshDevicesButton = document.querySelector("#refresh-devices");
if (refreshDevicesButton) {
  refreshDevicesButton.onclick = () => loadDevicesAndSessions();
}

document.querySelectorAll("[data-filter]").forEach((button) => {
  button.onclick = () => {
    document.querySelectorAll("[data-filter]").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    renderRequestList(cachedRequests, button.dataset.filter);
  };
});

const encoder = new TextEncoder();
const decoder = new TextDecoder();
let cachedRequests = [];
let requestStreamActive = false;
let requestStreamRestart = null;
let activeTakeoverFrameRequest = null;
let takeoverFrameTimer = null;

const urlParams = new URLSearchParams(window.location.search);
if (urlParams.get("code")) {
  document.querySelector("#pairing-code").value = urlParams.get("code");
  document.querySelector("#pairing-code-preview").textContent = urlParams.get("code");
}
if (urlParams.get("pairing_id")) {
  loadPairingDetails(urlParams.get("pairing_id"));
} else {
  document.querySelector("#pairing-server-url").textContent = window.location.origin;
}

function csrfHeaders() {
  const token = localStorage.getItem("omnidoer_csrf_token");
  return token ? { "x-omnidoer-csrf": token } : {};
}

function bytesToB64url(bytes) {
  return b64url(bytes);
}

function b64urlToBytes(value) {
  const padded = value + "=".repeat((4 - value.length % 4) % 4);
  const binary = atob(padded.replaceAll("-", "+").replaceAll("_", "/"));
  return Uint8Array.from(binary, (char) => char.charCodeAt(0));
}

function activeFilter() {
  return document.querySelector("[data-filter].active")?.dataset.filter || "all";
}

function formatTimestamp(value) {
  if (!value) return "not set";
  return new Date(value * 1000).toLocaleString();
}

function requestKind(request) {
  if (request.request_type === "credential") return "credential";
  if (request.request_type === "human_takeover" || request.request_type === "account_registration") return "takeover";
  if (["file_upload", "account_delete", "password_change", "two_factor_change", "message_send"].includes(request.request_type)) return "approval";
  if (request.request_type.endsWith("_approval") || request.request_type.includes("approval")) return "approval";
  return "challenge";
}

function setStatus(message, detail = "") {
  document.querySelector("#runtime-mode").textContent = message;
  document.querySelector("#runtime-detail").textContent = detail;
}

async function loadPairingDetails(pairingId) {
  document.querySelector("#pairing-server-url").textContent = window.location.origin;
  try {
    const response = await fetch(`/api/pairing/${encodeURIComponent(pairingId)}`, { cache: "no-store" });
    if (!response.ok) throw new Error("pairing unavailable");
    const pairing = await response.json();
    document.querySelector("#pairing-server-url").textContent = pairing.public_url || window.location.origin;
    document.querySelector("#pairing-broker-fingerprint").textContent = pairing.broker_fingerprint || "not loaded";
    document.querySelector("#pairing-web-broker-fingerprint").textContent = pairing.web_broker_fingerprint || "not loaded";
    document.querySelector("#pairing-expires-at").textContent = formatTimestamp(pairing.expires_at);
  } catch {
    document.querySelector("#pairing-broker-fingerprint").textContent = "pairing metadata unavailable";
    document.querySelector("#pairing-web-broker-fingerprint").textContent = "pairing metadata unavailable";
  }
}

async function deviceKeyPair() {
  const storedPrivate = localStorage.getItem("omnidoer_device_private_jwk");
  const storedPublic = localStorage.getItem("omnidoer_device_public_jwk");
  if (storedPrivate && storedPublic) {
    const privateJwk = JSON.parse(storedPrivate);
    const privateKey = await crypto.subtle.importKey(
      "jwk",
      privateJwk,
      { name: "ECDSA", namedCurve: "P-256" },
      true,
      ["sign"]
    );
    return { publicJwk: JSON.parse(storedPublic), privateKey };
  }
  const key = await crypto.subtle.generateKey({ name: "ECDSA", namedCurve: "P-256" }, true, ["sign", "verify"]);
  const privateJwk = await crypto.subtle.exportKey("jwk", key.privateKey);
  const publicJwk = await crypto.subtle.exportKey("jwk", key.publicKey);
  localStorage.setItem("omnidoer_device_private_jwk", JSON.stringify(privateJwk));
  localStorage.setItem("omnidoer_device_public_jwk", JSON.stringify(publicJwk));
  return { publicJwk, privateKey: key.privateKey };
}

async function deviceSignatureHeaders(method, path) {
  const deviceId = localStorage.getItem("omnidoer_device_id");
  const sessionId = localStorage.getItem("omnidoer_session_id");
  const storedPrivate = localStorage.getItem("omnidoer_device_private_jwk");
  if (!deviceId || !sessionId || !storedPrivate) return {};
  const { privateKey } = await deviceKeyPair();
  const timestamp = String(Math.floor(Date.now() / 1000));
  const nonce = bytesToB64url(crypto.getRandomValues(new Uint8Array(16)));
  const message = [
    "omnidoer-device-v1",
    deviceId,
    sessionId,
    method.toUpperCase(),
    path,
    timestamp,
    nonce
  ].join("\n");
  const signature = await crypto.subtle.sign(
    { name: "ECDSA", hash: "SHA-256" },
    privateKey,
    encoder.encode(message)
  );
  return {
    "x-omnidoer-device-id": deviceId,
    "x-omnidoer-device-ts": timestamp,
    "x-omnidoer-device-nonce": nonce,
    "x-omnidoer-device-sig": bytesToB64url(signature)
  };
}

async function signedFetch(url, options = {}) {
  const target = new URL(url, window.location.origin);
  const method = (options.method || "GET").toUpperCase();
  const headers = {
    ...(options.headers || {}),
    ...(await deviceSignatureHeaders(method, target.pathname))
  };
  return fetch(url, { ...options, method, headers });
}

async function pairDevice() {
  const code = document.querySelector("#pairing-code").value.trim();
  const deviceName = document.querySelector("#device-name").value.trim() || "PWA Control Client";
  if (!code) return;
  const { publicJwk } = await deviceKeyPair();
  const response = await fetch("/api/pair", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ code, device_name: deviceName, device_public_key: JSON.stringify(publicJwk) })
  });
  const payload = await response.json();
  if (!response.ok) {
    document.querySelector("#pairing-status").textContent = "Pairing failed.";
    return;
  }
  localStorage.setItem("omnidoer_device_id", payload.device.device_id);
  localStorage.setItem("omnidoer_session_id", payload.session.session_id);
  localStorage.setItem("omnidoer_csrf_token", payload.csrf_token);
  document.querySelector("#pairing-status").textContent = `Paired ${payload.device.name}. Device identity created. Device fingerprint: ${payload.device.fingerprint || "not visible"}.`;
  await loadRequests();
  await loadDevicesAndSessions();
}

function b64url(bytes) {
  return btoa(String.fromCharCode(...new Uint8Array(bytes))).replaceAll("+", "-").replaceAll("/", "_").replaceAll("=", "");
}

function stableAssociatedData(request) {
  const data = {
    origin: request.origin,
    request_id: request.request_id,
    request_type: request.request_type
  };
  if (request.device_id) data.device_id = request.device_id;
  if (request.expires_at) data.expires_at = request.expires_at;
  const sorted = Object.keys(data).sort().reduce((acc, key) => {
    acc[key] = data[key];
    return acc;
  }, {});
  return encoder.encode(JSON.stringify(sorted));
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
  const requestForAad = {
    ...request,
    device_id: localStorage.getItem("omnidoer_device_id") || undefined,
    expires_at: request.expires_at
  };
  const broker = await signedFetch("/api/broker-key", { cache: "no-store" }).then((r) => r.json());
  const brokerKey = await crypto.subtle.importKey(
    "jwk",
    broker.web_public_jwk,
    { name: "ECDH", namedCurve: "P-256" },
    false,
    []
  );
  const ephemeral = await crypto.subtle.generateKey({ name: "ECDH", namedCurve: "P-256" }, true, ["deriveBits"]);
  const sharedBits = await crypto.subtle.deriveBits({ name: "ECDH", public: brokerKey }, ephemeral.privateKey, 256);
  const key = await deriveAesKey(sharedBits, requestForAad);
  const nonce = crypto.getRandomValues(new Uint8Array(12));
  const aad = stableAssociatedData(requestForAad);
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
    request_type: request.request_type,
    device_id: requestForAad.device_id,
    expires_at: requestForAad.expires_at
  };
}

async function submitEncrypted(request, payload) {
  const envelope = await encryptForBroker(payload, request);
  const response = await signedFetch(`/api/requests/${request.request_id}/submit`, {
    method: "POST",
    headers: { "content-type": "application/json", ...csrfHeaders() },
    body: JSON.stringify({ envelope })
  });
  if (!response.ok) {
    setStatus("Request submit failed", "Pair again if this is Cloud Direct Mode.");
  }
  await loadRequests();
}

async function postAction(request, action) {
  const response = await signedFetch(`/api/requests/${request.request_id}/${action}`, { method: "POST", headers: csrfHeaders() });
  if (!response.ok) {
    setStatus("Action failed", `${request.request_type} ${action}`);
  }
  await loadRequests();
}

async function submitTask() {
  const input = document.querySelector("#task-text");
  const text = input.value.trim();
  if (!text) return;
  await signedFetch("/api/tasks", {
    method: "POST",
    headers: { "content-type": "application/json", ...csrfHeaders() },
    body: JSON.stringify({ text })
  });
  input.value = "";
  await loadTasks();
}

async function updateTask(task, action) {
  await signedFetch(`/api/tasks/${task.task_id}/${action}`, { method: "POST", headers: csrfHeaders() });
  await loadTasks();
}

async function revokeDevice(device) {
  await signedFetch(`/api/devices/${device.device_id}/revoke`, {
    method: "POST",
    headers: { "content-type": "application/json", ...csrfHeaders() },
    body: "{}"
  });
  await loadDevicesAndSessions();
}

async function revokeSession(session) {
  await signedFetch(`/api/sessions/${session.session_id}/revoke`, {
    method: "POST",
    headers: { "content-type": "application/json", ...csrfHeaders() },
    body: "{}"
  });
  await loadDevicesAndSessions();
}

function appendText(parent, tag, text, className) {
  const node = document.createElement(tag);
  node.textContent = text;
  if (className) node.className = className;
  parent.append(node);
  return node;
}

function renderTask(task) {
  const item = document.createElement("article");
  item.className = "task";
  appendText(item, "h3", task.status);
  appendText(item, "p", `task_id: ${task.task_id}`);
  appendText(item, "p", task.text);
  appendText(item, "p", `source: ${task.source}`);
  appendText(item, "p", "Delivery: local queue -> MCP control.next_user_task -> Codex CLI. The Control Client does not call models directly.", "flow-note");
  if (task.status !== "completed" && task.status !== "cancelled") {
    const actions = document.createElement("div");
    actions.className = "button-row";
    const complete = document.createElement("button");
    complete.textContent = "Mark Complete";
    complete.onclick = () => updateTask(task, "complete");
    const cancel = document.createElement("button");
    cancel.textContent = "Cancel";
    cancel.onclick = () => updateTask(task, "cancel");
    actions.append(cancel, complete);
    item.append(actions);
  }
  return item;
}

async function loadTasks() {
  const list = document.querySelector("#tasks-list");
  if (!list) return;
  try {
    const tasks = await signedFetch("/api/tasks", { cache: "no-store" }).then((r) => r.json());
    list.innerHTML = "";
    if (!tasks.length) {
      list.textContent = "No queued tasks.";
      return;
    }
    tasks.forEach((task) => list.append(renderTask(task)));
  } catch {
    list.textContent = "Pair this device to view task queue in Cloud Direct Mode.";
  }
}

function renderDevice(device) {
  const item = document.createElement("article");
  item.className = "mini-record";
  appendText(item, "h3", device.name || "Control Client");
  appendText(item, "p", `device_id: ${device.device_id}`);
  appendText(item, "p", `fingerprint: ${device.fingerprint || "not visible"}`);
  appendText(item, "p", `status: ${device.revoked ? "revoked" : "active"}`);
  if (!device.revoked) {
    const actions = document.createElement("div");
    actions.className = "button-row";
    const revoke = document.createElement("button");
    revoke.textContent = "Revoke Device";
    revoke.onclick = () => revokeDevice(device);
    actions.append(revoke);
    item.append(actions);
  }
  return item;
}

function renderSession(session) {
  const item = document.createElement("article");
  item.className = "mini-record";
  appendText(item, "h3", session.revoked ? "revoked" : "active");
  appendText(item, "p", `session_id: ${session.session_id}`);
  appendText(item, "p", `device_id: ${session.device_id}`);
  appendText(item, "p", `expires_at: ${formatTimestamp(session.expires_at)}`);
  if (!session.revoked) {
    const actions = document.createElement("div");
    actions.className = "button-row";
    const revoke = document.createElement("button");
    revoke.textContent = "Revoke Session";
    revoke.onclick = () => revokeSession(session);
    actions.append(revoke);
    item.append(actions);
  }
  return item;
}

async function loadDevicesAndSessions() {
  const devicesRoot = document.querySelector("#devices-list");
  const sessionsRoot = document.querySelector("#sessions-list");
  if (!devicesRoot || !sessionsRoot) return;
  try {
    const [devices, sessions] = await Promise.all([
      signedFetch("/api/devices", { cache: "no-store" }).then((r) => {
        if (!r.ok) throw new Error("devices unauthorized");
        return r.json();
      }),
      signedFetch("/api/sessions", { cache: "no-store" }).then((r) => {
        if (!r.ok) throw new Error("sessions unauthorized");
        return r.json();
      })
    ]);
    devicesRoot.innerHTML = "";
    sessionsRoot.innerHTML = "";
    if (!devices.length) {
      devicesRoot.textContent = "No paired devices.";
    } else {
      devices.forEach((device) => devicesRoot.append(renderDevice(device)));
    }
    if (!sessions.length) {
      sessionsRoot.textContent = "No sessions.";
    } else {
      sessions.forEach((session) => sessionsRoot.append(renderSession(session)));
    }
  } catch {
    devicesRoot.textContent = "Pair this device to view paired devices.";
    sessionsRoot.textContent = "Pair this device to view sessions.";
  }
}

async function sendTakeoverInput(request, eventPayload) {
  await signedFetch(`/api/requests/${request.request_id}/input`, {
    method: "POST",
    headers: { "content-type": "application/json", ...csrfHeaders() },
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
  stream.tabIndex = 0;
  stream.onpointerdown = (event) => {
    const img = document.querySelector("#takeover-frame");
    if (!img) return;
    stream.setPointerCapture(event.pointerId);
    start = { ...framePoint(event, img), at: Date.now() };
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
  };
  stream.onkeydown = (event) => {
    if (event.key.length === 1 || ["Enter", "Tab", "Backspace", "Escape", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(event.key)) {
      event.preventDefault();
      sendTakeoverInput(request, { event_type: "key", key: event.key });
    }
  };
  stream.onwheel = (event) => {
    event.preventDefault();
    sendTakeoverInput(request, { event_type: "scroll", delta_y: Math.round(event.deltaY) });
  };
}

function stopTakeoverFramePolling(requestId = null) {
  if (requestId && activeTakeoverFrameRequest !== requestId) return;
  if (takeoverFrameTimer) clearInterval(takeoverFrameTimer);
  takeoverFrameTimer = null;
  activeTakeoverFrameRequest = null;
}

async function fetchTakeoverFrame(request, stream) {
  if (activeTakeoverFrameRequest !== request.request_id) return;
  try {
    const frame = await signedFetch(`/api/requests/${request.request_id}/frame`, { cache: "no-store" }).then((r) => r.json());
    if (activeTakeoverFrameRequest !== request.request_id) return;
    if (frame.data_b64) {
      stream.innerHTML = `<img id="takeover-frame" alt="Controlled browser frame" src="data:${frame.content_type};base64,${frame.data_b64}">`;
      stream.dataset.frameUrl = frame.url || "";
      stream.dataset.frameOrigin = frame.origin || "";
    } else {
      stream.textContent = "Browser context is not connected in this process.";
    }
  } catch {
    if (activeTakeoverFrameRequest === request.request_id) {
      stream.textContent = "Waiting for the controlled browser frame...";
    }
  }
}

function startTakeoverFramePolling(request, stream) {
  if (request.status !== "user_control") {
    stopTakeoverFramePolling(request.request_id);
    stream.textContent = "Takeover is not active. Agent control can resume after release.";
    return;
  }
  if (activeTakeoverFrameRequest && activeTakeoverFrameRequest !== request.request_id) {
    stopTakeoverFramePolling();
  }
  if (activeTakeoverFrameRequest === request.request_id && takeoverFrameTimer) return;
  activeTakeoverFrameRequest = request.request_id;
  stream.textContent = "Loading control-only browser frame...";
  installTakeoverPointerHandlers(request, stream);
  fetchTakeoverFrame(request, stream);
  takeoverFrameTimer = setInterval(() => fetchTakeoverFrame(request, stream), 1500);
}

function requestHeader(request) {
  const header = document.createElement("div");
  header.className = "request-header";
  const titleBlock = document.createElement("div");
  appendText(titleBlock, "h3", request.request_type.replaceAll("_", " "));
  appendText(titleBlock, "p", request.action_summary || "Waiting for user action", "request-summary");
  const badges = document.createElement("div");
  badges.className = "badge-row";
  appendText(badges, "span", request.status, `badge status-${request.status}`);
  appendText(badges, "span", request.risk_level || "unknown risk", `badge risk-${request.risk_level || "unknown"}`);
  appendText(badges, "span", requestKind(request), "badge");
  header.append(titleBlock, badges);
  return header;
}

function requestMetadata(request) {
  const dl = document.createElement("dl");
  dl.className = "metadata";
  [
    ["request_id", request.request_id],
    ["origin", request.origin],
    ["current_url", request.top_level_url],
    ["expires_at", formatTimestamp(request.expires_at)],
    ["allowed_device", request.allowed_device_id || "any paired device"],
    ["broker_fingerprint", request.broker_public_key_fingerprint || "server pinned"]
  ].forEach(([label, value]) => {
    const dt = document.createElement("dt");
    dt.textContent = label;
    const dd = document.createElement("dd");
    dd.textContent = value || "not visible";
    dl.append(dt, dd);
  });
  return dl;
}

function renderCredentialControls(request, item) {
  const form = document.createElement("form");
  form.className = "secure-form";
  form.innerHTML = `
    <p class="flow-note">Secret will be encrypted to Secret Broker. It will not be sent to Agent/LLM context, MCP return values, logs, or DOM observation.</p>
    <label>Username <input id="username" data-secret-field="username" autocomplete="username"></label>
    <label>Password <input id="password" data-secret-field="password" type="password" autocomplete="current-password"></label>
    <label>TOTP seed <input id="totp-seed" data-secret-field="totp_seed" type="password" autocomplete="off"></label>
    <label class="check-row"><input type="checkbox" data-secret-field="save_to_vault" checked> Save encrypted in Vault</label>
    <div class="button-row"><button type="submit">Submit Credential</button></div>
  `;
  form.onsubmit = (event) => {
    event.preventDefault();
    const payload = {
      username: form.querySelector("[data-secret-field='username']").value,
      password: form.querySelector("[data-secret-field='password']").value,
      totp_seed: form.querySelector("[data-secret-field='totp_seed']").value,
      save_to_vault: form.querySelector("[data-secret-field='save_to_vault']").checked
    };
    submitEncrypted(request, payload).then(() => {
      form.querySelector("[data-secret-field='password']").value = "";
      form.querySelector("[data-secret-field='totp_seed']").value = "";
    });
  };
  item.append(form);
}

function renderChallengeControls(request, item) {
  const form = document.createElement("form");
  form.className = "secure-form";
  const isVisualChallenge = ["captcha", "passkey", "webauthn", "device_confirmation"].includes(request.request_type);
  form.innerHTML = isVisualChallenge ? `
    <p class="flow-note">Challenge will be completed by you, not by the Agent. OmniDoer will not bypass CAPTCHA/MFA/Passkey/WebAuthn/3DS.</p>
    <p class="flow-note">No challenge answer is submitted to OmniDoer. Complete the challenge in the controlled browser or external device, then mark it complete.</p>
    <div class="button-row"><button type="submit">Mark User Completed</button></div>
  ` : `
    <p class="flow-note">Challenge will be completed by you, not by the Agent. OmniDoer will not bypass CAPTCHA/MFA/Passkey/WebAuthn/3DS.</p>
    <label>One-time code <input data-challenge-field="code" inputmode="numeric" autocomplete="one-time-code"></label>
    <div class="button-row"><button type="submit">Submit Challenge</button></div>
  `;
  form.onsubmit = (event) => {
    event.preventDefault();
    if (isVisualChallenge) {
      postAction(request, "complete-challenge");
      return;
    }
    const field = form.querySelector("[data-challenge-field='code']");
    const value = field.value;
    submitEncrypted(request, { code: value }).then(() => postAction(request, "complete-challenge")).then(() => {
      field.value = "";
    });
  };
  item.append(form);
}

function renderTakeoverControls(request, item) {
  const stream = document.querySelector("#browser-stream");
  startTakeoverFramePolling(request, stream);
  if (request.request_type === "account_registration") {
    appendText(
      item,
      "p",
      "Registration Handoff: the registration page is proxied to this Control Client. Agent paused. You complete account creation directly; OmniDoer does not automate fake or bulk registration, and registration secrets or challenge answers are not sent to the LLM.",
      "flow-note"
    );
  }
  appendText(item, "p", "The browser is streamed to this Control Client. Agent paused. User in control. Sensitive input is not recorded.", "flow-note");
  const controls = document.createElement("div");
  controls.className = "takeover-controls";
  controls.innerHTML = `
    <label>Text to controlled browser <input type="password" autocomplete="off" data-takeover-text placeholder="Text to controlled browser"></label>
    <div class="button-row">
      <button data-action="send-text">Send Text</button>
      <button data-action="enter-key">Enter</button>
      <button data-action="release">Release Control</button>
    </div>
  `;
  controls.querySelector("[data-action='send-text']").onclick = () => {
    const input = controls.querySelector("[data-takeover-text]");
    sendTakeoverInput(request, { event_type: "type", text: input.value }).then(() => { input.value = ""; });
  };
  controls.querySelector("[data-action='enter-key']").onclick = () => sendTakeoverInput(request, { event_type: "key", key: "Enter" });
  controls.querySelector("[data-action='release']").onclick = () => postAction(request, "release");
  item.append(controls);
}

function renderApprovalControls(request, item) {
  const details = request.structured_details || {};
  const detailList = document.createElement("dl");
  detailList.className = "metadata approval-details";
  [
    ["Merchant", details.merchant],
    ["Amount", details.amount],
    ["Currency", details.currency],
    ["Recipient", details.recipient || details.payee],
    ["Shipping address", details.shipping_address],
    ["Billing method summary", details.billing_method_summary],
    ["Subscription / renewal", details.subscription || details.renewal],
    ["Refund / cancellation terms", details.refund_terms || details.cancellation_terms],
    ["Origin", details.origin || request.origin],
    ["Final button text", details.final_button],
    ["Agent prepared action", request.action_summary],
    ["After approval", details.after_approval || "Submit only after approval"]
  ].forEach(([label, value]) => {
    const dt = document.createElement("dt");
    dt.textContent = label;
    const dd = document.createElement("dd");
    dd.textContent = value || "not visible";
    detailList.append(dt, dd);
  });
  item.append(detailList);
  const actions = document.createElement("div");
  actions.className = "button-row";
  const approve = document.createElement("button");
  approve.textContent = "Approve";
  approve.onclick = () => postAction(request, "approve");
  const deny = document.createElement("button");
  deny.textContent = "Deny";
  deny.onclick = () => postAction(request, "deny");
  actions.append(deny, approve);
  item.append(actions);
}

function renderRequest(request) {
  const item = document.createElement("article");
  item.className = `request request-${requestKind(request)}`;
  item.append(requestHeader(request));
  item.append(requestMetadata(request));
  if (request.request_type === "credential") {
    renderCredentialControls(request, item);
  } else if (request.request_type === "human_takeover" || request.request_type === "account_registration") {
    renderTakeoverControls(request, item);
  } else if (requestKind(request) === "approval") {
    renderApprovalControls(request, item);
  } else {
    renderChallengeControls(request, item);
  }
  return item;
}

function renderRequestList(requests, filter = activeFilter()) {
  const list = document.querySelector("#requests-list");
  list.innerHTML = "";
  const visible = filter === "all" ? requests : requests.filter((request) => requestKind(request) === filter);
  if (activeTakeoverFrameRequest && !requests.some((request) => request.request_id === activeTakeoverFrameRequest && request.status === "user_control")) {
    stopTakeoverFramePolling();
  }
  document.querySelector("#runtime-counts").textContent = `Requests: ${requests.length}`;
  if (!visible.length) {
    list.textContent = requests.length ? "No requests match this filter." : "No pending requests.";
    return;
  }
  visible.forEach((request) => list.append(renderRequest(request)));
}

async function loadRuntimeStatus() {
  try {
    const status = await fetch("/api/status", { cache: "no-store" }).then((r) => r.json());
    setStatus(`Mode: ${status.mode}`, "Control Client does not call OpenAI APIs or models directly.");
  } catch {
    setStatus("Runtime offline", "Start omnidoer control serve.");
  }
}

async function loadRequests() {
  try {
    const requests = await signedFetch("/api/requests", { cache: "no-store" }).then((r) => {
      if (!r.ok) throw new Error("unauthorized");
      return r.json();
    });
    cachedRequests = requests;
    renderRequestList(requests);
  } catch {
    document.querySelector("#requests-list").textContent = "Pair this device to view requests in Cloud Direct Mode.";
  }
}

function applyRequestEvent(payload) {
  cachedRequests = payload.requests || [];
  renderRequestList(cachedRequests);
}

function handleSseBlock(block) {
  let eventName = "message";
  let data = "";
  block.split("\n").forEach((line) => {
    if (line.startsWith("event:")) eventName = line.slice(6).trim();
    if (line.startsWith("data:")) data += line.slice(5).trim();
  });
  if (eventName === "requests" && data) {
    applyRequestEvent(JSON.parse(data));
  }
}

async function startRequestStream() {
  if (requestStreamActive || !window.ReadableStream) return;
  requestStreamActive = true;
  if (requestStreamRestart) clearTimeout(requestStreamRestart);
  try {
    const response = await signedFetch("/api/events?stream=1&snapshots=30&interval=2", { cache: "no-store" });
    if (!response.ok || !response.body) throw new Error("request stream unavailable");
    const reader = response.body.getReader();
    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const blocks = buffer.split("\n\n");
      buffer = blocks.pop();
      blocks.filter(Boolean).forEach(handleSseBlock);
    }
  } catch {
    if (!cachedRequests.length) {
      document.querySelector("#requests-list").textContent = "Pair this device to receive signed request events in Cloud Direct Mode.";
    }
  } finally {
    requestStreamActive = false;
    requestStreamRestart = setTimeout(startRequestStream, 3000);
  }
}

loadRuntimeStatus();
loadRequests();
loadTasks();
loadDevicesAndSessions();
startRequestStream();
setInterval(loadRuntimeStatus, 10000);
setInterval(loadRequests, 15000);
setInterval(loadTasks, 5000);
setInterval(loadDevicesAndSessions, 15000);
