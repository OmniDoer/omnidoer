const $ = (selector) => document.querySelector(selector);
const encoder = new TextEncoder();
const API_TIMEOUT_MS = 9000;
const CORE_SECRET_TYPES = new Set(["credential", "totp", "one_time_code", "sms_code", "email_code"]);
const HIGH_RISK_TYPES = new Set(["payment_approval", "oauth_approval", "account_delete", "password_change", "two_factor_change", "console_restart"]);
let activeSessionId = localStorage.getItem("omnidoer_lite_active_session") || "default";
let lastFingerprint = "";
let streamAbort = null;
let pendingChatPayload = null;
let chatRenderFrame = 0;
const renderedMessageNodes = new Map();
let renderedTerminalTail = "";

function setStatus(text) {
  $("#status").textContent = text;
}

function b64url(bytes) {
  return btoa(String.fromCharCode(...new Uint8Array(bytes))).replaceAll("+", "-").replaceAll("/", "_").replaceAll("=", "");
}

function csrfHeaders() {
  const token = localStorage.getItem("omnidoer_csrf_token");
  return token ? { "x-omnidoer-csrf": token } : {};
}

async function deviceKeyPair() {
  const storedPrivate = localStorage.getItem("omnidoer_device_private_jwk");
  const storedPublic = localStorage.getItem("omnidoer_device_public_jwk");
  if (storedPrivate && storedPublic) {
    return {
      publicJwk: JSON.parse(storedPublic),
      privateKey: await crypto.subtle.importKey("jwk", JSON.parse(storedPrivate), { name: "ECDSA", namedCurve: "P-256" }, true, ["sign"])
    };
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
  if (!deviceId || !sessionId || !localStorage.getItem("omnidoer_device_private_jwk")) return {};
  const { privateKey } = await deviceKeyPair();
  const timestamp = String(Math.floor(Date.now() / 1000));
  const nonce = b64url(crypto.getRandomValues(new Uint8Array(16)));
  const message = ["omnidoer-device-v1", deviceId, sessionId, method.toUpperCase(), path, timestamp, nonce].join("\n");
  const signature = await crypto.subtle.sign({ name: "ECDSA", hash: "SHA-256" }, privateKey, encoder.encode(message));
  return {
    "x-omnidoer-device-id": deviceId,
    "x-omnidoer-session-id": sessionId,
    "x-omnidoer-device-ts": timestamp,
    "x-omnidoer-device-nonce": nonce,
    "x-omnidoer-device-sig": b64url(signature)
  };
}

async function signedFetch(url, options = {}) {
  const target = new URL(url, location.origin);
  const method = (options.method || "GET").toUpperCase();
  const externalSignal = options.signal;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), options.timeoutMs || API_TIMEOUT_MS);
  if (externalSignal) {
    if (externalSignal.aborted) controller.abort();
    else externalSignal.addEventListener("abort", () => controller.abort(), { once: true });
  }
  const headers = { ...(options.headers || {}), ...(await deviceSignatureHeaders(method, target.pathname)) };
  try {
    const { timeoutMs: _timeoutMs, ...rest } = options;
    return await fetch(url, { ...rest, method, headers, signal: controller.signal });
  } finally {
    clearTimeout(timeout);
  }
}

async function pair() {
  const code = $("#pair-code").value.replace(/\D/g, "").slice(0, 6);
  if (code.length !== 6) {
    $("#pair-note").textContent = "请输入 6 位配对码";
    return;
  }
  setStatus("配对中");
  const { publicJwk } = await deviceKeyPair();
  const response = await fetch("/api/pair", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ code, device_name: "OmniDoer Lite", device_public_key: JSON.stringify(publicJwk) })
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    $("#pair-note").textContent = payload.error || "配对失败";
    setStatus("未配对");
    return;
  }
  localStorage.setItem("omnidoer_device_id", payload.device.device_id);
  localStorage.setItem("omnidoer_session_id", payload.session.session_id);
  localStorage.setItem("omnidoer_csrf_token", payload.csrf_token);
  $("#pair-note").textContent = `已配对 ${payload.device.device_id}`;
  setStatus("已配对");
  await loadState();
  startChatStream();
}

function stableAssociatedData(request) {
  const data = {
    origin: request.origin,
    request_id: request.request_id,
    request_type: request.request_type
  };
  const deviceId = localStorage.getItem("omnidoer_device_id");
  if (deviceId) data.device_id = deviceId;
  if (request.expires_at) data.expires_at = request.expires_at;
  return encoder.encode(JSON.stringify(Object.keys(data).sort().reduce((acc, key) => (acc[key] = data[key], acc), {})));
}

async function encryptForBroker(payload, request) {
  const broker = await signedFetch("/api/broker-key", { cache: "no-store" }).then((r) => r.json());
  const brokerKey = await crypto.subtle.importKey("jwk", broker.web_public_jwk, { name: "ECDH", namedCurve: "P-256" }, false, []);
  const ephemeral = await crypto.subtle.generateKey({ name: "ECDH", namedCurve: "P-256" }, true, ["deriveBits"]);
  const sharedBits = await crypto.subtle.deriveBits({ name: "ECDH", public: brokerKey }, ephemeral.privateKey, 256);
  const baseKey = await crypto.subtle.importKey("raw", sharedBits, "HKDF", false, ["deriveKey"]);
  const salt = await crypto.subtle.digest("SHA-256", stableAssociatedData(request));
  const key = await crypto.subtle.deriveKey({ name: "HKDF", hash: "SHA-256", salt, info: encoder.encode("omnidoer-control-web-v1") }, baseKey, { name: "AES-GCM", length: 256 }, false, ["encrypt"]);
  const nonce = crypto.getRandomValues(new Uint8Array(12));
  const ciphertext = await crypto.subtle.encrypt({ name: "AES-GCM", iv: nonce, additionalData: stableAssociatedData(request) }, key, encoder.encode(JSON.stringify(payload)));
  return {
    version: "web-p256-v1",
    ephemeral_public_jwk: await crypto.subtle.exportKey("jwk", ephemeral.publicKey),
    nonce: b64url(nonce),
    ciphertext: b64url(ciphertext),
    request_id: request.request_id,
    origin: request.origin,
    request_type: request.request_type,
    device_id: localStorage.getItem("omnidoer_device_id") || undefined,
    expires_at: request.expires_at
  };
}

function requestLabel(request) {
  return {
    credential: "凭证",
    totp: "TOTP",
    one_time_code: "验证码",
    sms_code: "短信码",
    email_code: "邮箱码",
    payment_approval: "支付审批",
    oauth_approval: "授权审批",
    account_delete: "删除账号",
    password_change: "修改密码",
    two_factor_change: "双因子变更",
    console_restart: "重启同步"
  }[request.request_type] || request.request_type;
}

function secretFields(request) {
  const fields = request.requested_fields?.length ? request.requested_fields : ["value"];
  return fields.slice(0, 4);
}

function renderRequests(requests = []) {
  const root = $("#requests");
  root.textContent = "";
  const active = requests.filter((request) => ["pending", "user_control", "fulfilled", "approved"].includes(request.status));
  if (!active.length) {
    root.innerHTML = '<p class="meta">暂无核心审批请求。</p>';
    return;
  }
  active.forEach((request) => {
    const item = document.createElement("article");
    item.className = "request";
    item.dataset.risk = request.risk_level || "low";
    item.innerHTML = `<strong>${requestLabel(request)}</strong><div>${escapeHtml(request.action_summary || request.origin || "")}</div><div class="meta">${escapeHtml(request.origin || "")} · ${escapeHtml(request.status || "")}</div>`;
    const actions = document.createElement("div");
    actions.className = "actions";
    if (CORE_SECRET_TYPES.has(request.request_type)) {
      const payload = {};
      secretFields(request).forEach((field) => {
        const wrap = document.createElement("label");
        wrap.className = "field";
        wrap.textContent = field;
        const input = document.createElement("input");
        input.type = field.toLowerCase().includes("password") ? "password" : "text";
        input.autocomplete = "off";
        input.oninput = () => { payload[field] = input.value; };
        wrap.append(input);
        item.append(wrap);
      });
      const submit = button("提交到保险柜", async () => {
        const envelope = await encryptForBroker({ fields: payload, save_to_vault: Boolean(request.save_to_vault) }, request);
        await signedFetch(`/api/requests/${encodeURIComponent(request.request_id)}/submit`, {
          method: "POST",
          headers: { "content-type": "application/json", ...csrfHeaders() },
          body: JSON.stringify({ envelope })
        });
        await loadState();
      });
      actions.append(submit);
    }
    if (HIGH_RISK_TYPES.has(request.request_type)) {
      actions.append(button("确认", () => postRequestAction(request, "approve"), "secondary"));
      actions.append(button("拒绝", () => postRequestAction(request, "deny"), "danger"));
    }
    item.append(actions);
    root.append(item);
  });
}

function button(text, onClick, className = "") {
  const node = document.createElement("button");
  node.type = "button";
  node.textContent = text;
  if (className) node.className = className;
  node.onclick = async () => {
    node.disabled = true;
    try { await onClick(); } finally { node.disabled = false; }
  };
  return node;
}

async function postRequestAction(request, action) {
  const body = action === "approve" && ["payment_approval", "console_restart"].includes(request.request_type)
    ? { explicit_user_confirmation: true, request_id: request.request_id }
    : {};
  await signedFetch(`/api/requests/${encodeURIComponent(request.request_id)}/${action}`, {
    method: "POST",
    headers: { "content-type": "application/json", ...csrfHeaders() },
    body: JSON.stringify(body)
  });
  await loadState();
}

function renderSessions(payload = {}) {
  const select = $("#session-select");
  const sessions = (payload.sessions || []).filter((session) => session.status === "open");
  select.textContent = "";
  sessions.forEach((session) => {
    const option = document.createElement("option");
    option.value = session.session_id;
    option.textContent = session.title || session.session_id;
    select.append(option);
  });
  if (sessions.some((session) => session.session_id === activeSessionId)) select.value = activeSessionId;
  else if (sessions[0]) activeSessionId = sessions[0].session_id;
  localStorage.setItem("omnidoer_lite_active_session", activeSessionId);
}

function messageKey(message) {
  return message.message_id || message.client_message_id || `${message.role}_${message.sequence}`;
}

function createMessageNode(message) {
  const item = document.createElement("article");
  const meta = document.createElement("div");
  const text = document.createElement("div");
  meta.className = "meta";
  text.className = "text";
  item.append(meta, text);
  updateMessageNode(item, message);
  return item;
}

function updateMessageNode(item, message) {
  const pending = ["queued", "sending"].includes(message.status);
  const className = `message ${message.role || ""} ${pending ? "pending" : ""}`;
  if (item.className !== className) item.className = className;
  const meta = item.firstChild;
  const text = item.lastChild;
  const metaText = `${message.role === "user" ? "你" : "OmniDoer"} · ${message.status || ""}`;
  if (meta.textContent !== metaText) meta.textContent = metaText;
  const body = message.text || "";
  if (text.textContent !== body) text.textContent = body;
}

function renderChatNow(chat = {}) {
  const root = $("#messages");
  const messages = (chat.messages || []).filter((message) => !String(message.client_message_id || "").startsWith("omnidoer_auto_status_"));
  const fp = JSON.stringify([messages.length, messages.at(-1)?.message_id, messages.at(-1)?.updated_at, chat.terminal?.text?.slice(-160)]);
  if (fp === lastFingerprint) return;
  lastFingerprint = fp;
  const stick = root.scrollHeight - root.scrollTop - root.clientHeight < 80;
  const visible = messages.slice(-24);
  const visibleKeys = new Set(visible.map(messageKey));
  Array.from(renderedMessageNodes.entries()).forEach(([key, node]) => {
    if (!visibleKeys.has(key)) {
      node.remove();
      renderedMessageNodes.delete(key);
    }
  });
  const fragment = document.createDocumentFragment();
  visible.forEach((message) => {
    const key = messageKey(message);
    let node = renderedMessageNodes.get(key);
    if (!node) {
      node = createMessageNode(message);
      renderedMessageNodes.set(key, node);
    } else {
      updateMessageNode(node, message);
    }
    fragment.append(node);
  });
  root.append(fragment);
  const terminal = $("#terminal");
  if (chat.terminal?.text) {
    const terminalTail = chat.terminal.text.slice(-5000);
    terminal.hidden = false;
    if (terminalTail !== renderedTerminalTail) {
      terminal.textContent = terminalTail;
      renderedTerminalTail = terminalTail;
    }
    terminal.scrollTop = terminal.scrollHeight;
  } else {
    terminal.hidden = true;
    renderedTerminalTail = "";
  }
  if (stick) root.scrollTop = root.scrollHeight;
}

function renderChat(chat = {}) {
  pendingChatPayload = chat;
  if (chatRenderFrame) return;
  chatRenderFrame = requestAnimationFrame(() => {
    chatRenderFrame = 0;
    const payload = pendingChatPayload;
    pendingChatPayload = null;
    renderChatNow(payload || {});
  });
}

async function loadState() {
  const response = await signedFetch(`/api/lite/state?session_id=${encodeURIComponent(activeSessionId)}`, { cache: "no-store" });
  if (response.status === 401) {
    setStatus("未配对");
    $("#pair-card").hidden = false;
    return;
  }
  const payload = await response.json();
  $("#pair-card").hidden = true;
  setStatus("已连接");
  renderSessions(payload.sessions);
  renderRequests(payload.requests);
  renderChat(payload.chat);
}

function applyChatPayload(payload) {
  if (!payload || payload.session_id !== activeSessionId) return;
  renderChat(payload);
}

async function streamChatOnce(signal) {
  const response = await signedFetch(
    `/api/chat/events?stream=1&snapshots=1200&interval=0.5&compact=1&limit=24&session_id=${encodeURIComponent(activeSessionId)}`,
    { cache: "no-store", timeoutMs: 600000, signal }
  );
  if (!response.ok || !response.body) throw new Error("chat stream unavailable");
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (!signal.aborted) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() || "";
    blocks.forEach((block) => {
      let event = "message";
      let data = "";
      block.split("\n").forEach((line) => {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        if (line.startsWith("data:")) data += line.slice(5).trim();
      });
      if (event === "chat" && data) applyChatPayload(JSON.parse(data));
    });
  }
}

async function startStateLoop() {
  while (true) {
    try {
      await loadState();
      await sleep(2500);
    } catch {
      setStatus("重连中");
      await sleep(1600);
    }
  }
}

async function sendMessage(event) {
  event.preventDefault();
  const input = $("#chat-input");
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  await signedFetch("/api/chat/messages", {
    method: "POST",
    headers: { "content-type": "application/json", ...csrfHeaders() },
    body: JSON.stringify({ text, session_id: activeSessionId, client_message_id: `lite_${Date.now()}_${Math.random().toString(16).slice(2)}` })
  });
  await loadState();
}

async function startChatStream() {
  if (streamAbort) streamAbort.abort();
  streamAbort = new AbortController();
  while (!streamAbort.signal.aborted) {
    try {
      await streamChatOnce(streamAbort.signal);
    } catch {
      setStatus("重连中");
      await sleep(900);
    }
  }
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]));
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

$("#pair-button").onclick = pair;
$("#refresh-button").onclick = loadState;
$("#chat-form").onsubmit = sendMessage;
$("#session-select").onchange = () => {
  activeSessionId = $("#session-select").value || "default";
  localStorage.setItem("omnidoer_lite_active_session", activeSessionId);
  lastFingerprint = "";
  renderedMessageNodes.clear();
  $("#messages").textContent = "";
  renderedTerminalTail = "";
  $("#terminal").hidden = true;
  loadState();
  startChatStream();
};

loadState().finally(() => {
  startStateLoop();
  startChatStream();
});
