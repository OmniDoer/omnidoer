const $ = (selector) => document.querySelector(selector);
const encoder = new TextEncoder();
const API_TIMEOUT_MS = 9000;
const CORE_SECRET_TYPES = new Set(["credential", "totp", "one_time_code", "sms_code", "email_code"]);
const HIGH_RISK_TYPES = new Set(["payment_approval", "oauth_approval", "account_delete", "password_change", "two_factor_change", "console_restart"]);
const LITE_CHAT_COMMANDS = [
  { command: "/status", description: "查看运行状态" },
  { command: "/compact", description: "压缩当前上下文" },
  { command: "/heartbeat", description: "管理空闲 HEARTBEAT.md 任务", argument: "status|enable|disable|run" },
  { command: "/connect-password", description: "查看或设置固定连接密码", argument: "status|set" },
  { command: "/vault", description: "管理 Vault 凭证", argument: "list|add|delete" },
  { command: "/help", description: "显示可用指令" }
];
let activeSessionId = localStorage.getItem("omnidoer_lite_active_session") || "default";
let lastFingerprint = "";
let streamAbort = null;
let pendingChatPayload = null;
let chatRenderFrame = 0;
const renderedMessageNodes = new Map();
let renderedTerminalTail = "";
let renderedLiveTerminalKey = "";
let selectedFiles = [];
let manualScrollPauseUntil = 0;
const requestDrafts = new Map();
let renderedRequestSignature = "";
let pendingRequestPayload = null;
let currentFilePath = ".";
let credentialPayloadCache = null;
let filePayloadCache = null;
let activeView = localStorage.getItem("omnidoer_lite_view") || "terminal";
let commandMenuIndex = 0;

function setStatus(text) {
  $("#status").textContent = text;
}

function markReady() {
  document.body.classList.add("ready");
}

function switchView(view) {
  activeView = view || "terminal";
  localStorage.setItem("omnidoer_lite_view", activeView);
  document.querySelectorAll("[data-view]").forEach((panel) => {
    panel.hidden = panel.dataset.view !== activeView;
  });
  document.querySelectorAll("[data-tab]").forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.tab === activeView);
  });
  if (activeView === "passwords") loadCredentials();
  if (activeView === "files") loadFiles(currentFilePath);
  if (activeView === "requests") loadState({ forceRequests: true });
  if (activeView === "terminal") $("#chat-input").focus({ preventScroll: true });
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
  await loadState({ forceRequests: true });
  startChatStream();
}

async function passwordLogin() {
  const password = $("#fixed-password").value;
  if (!password) {
    $("#pair-note").textContent = "请输入固定连接密码";
    return;
  }
  setStatus("连接中");
  const { publicJwk } = await deviceKeyPair();
  const response = await fetch("/api/password-login", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ password, device_name: "OmniDoer Lite", device_public_key: JSON.stringify(publicJwk) })
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    $("#pair-note").textContent = payload.reason || payload.error || "连接失败";
    setStatus("未连接");
    return;
  }
  localStorage.setItem("omnidoer_device_id", payload.device.device_id);
  localStorage.setItem("omnidoer_session_id", payload.session.session_id);
  localStorage.setItem("omnidoer_csrf_token", payload.csrf_token);
  $("#fixed-password").value = "";
  $("#pair-note").textContent = `已连接 ${payload.device.device_id}`;
  setStatus("已连接");
  await loadState({ forceRequests: true });
  await loadCredentials();
  await loadFiles(currentFilePath);
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
  const requestForAad = {
    ...request,
    device_id: localStorage.getItem("omnidoer_device_id") || undefined,
    expires_at: request.expires_at
  };
  const broker = await signedFetch("/api/broker-key", { cache: "no-store" }).then((r) => r.json());
  const brokerKey = await crypto.subtle.importKey("jwk", broker.web_public_jwk, { name: "ECDH", namedCurve: "P-256" }, false, []);
  const ephemeral = await crypto.subtle.generateKey({ name: "ECDH", namedCurve: "P-256" }, true, ["deriveBits"]);
  const sharedBits = await crypto.subtle.deriveBits({ name: "ECDH", public: brokerKey }, ephemeral.privateKey, 256);
  const baseKey = await crypto.subtle.importKey("raw", sharedBits, "HKDF", false, ["deriveKey"]);
  const salt = await crypto.subtle.digest("SHA-256", stableAssociatedData(requestForAad));
  const key = await crypto.subtle.deriveKey({ name: "HKDF", hash: "SHA-256", salt, info: encoder.encode("omnidoer-control-web-v1") }, baseKey, { name: "AES-GCM", length: 256 }, false, ["encrypt"]);
  const nonce = crypto.getRandomValues(new Uint8Array(12));
  const aad = stableAssociatedData(requestForAad);
  const ciphertext = await crypto.subtle.encrypt({ name: "AES-GCM", iv: nonce, additionalData: aad }, key, encoder.encode(JSON.stringify(payload)));
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

function requestDraftKey(request, field) {
  return `${request.request_id}:${field}`;
}

function captureRequestDrafts() {
  document.querySelectorAll("[data-request-id][data-secret-field]").forEach((input) => {
    requestDrafts.set(`${input.dataset.requestId}:${input.dataset.secretField}`, input.value);
  });
}

function pruneRequestDrafts(activeRequests = []) {
  const activeIds = new Set(activeRequests.map((request) => request.request_id));
  Array.from(requestDrafts.keys()).forEach((key) => {
    if (!activeIds.has(key.split(":")[0])) requestDrafts.delete(key);
  });
}

function activeLiteRequests(requests = []) {
  return requests.filter((request) => ["pending", "user_control"].includes(request.status));
}

function requestSignature(requests = []) {
  return JSON.stringify(requests.map((request) => ({
    id: request.request_id,
    type: request.request_type,
    status: request.status,
    origin: request.origin,
    summary: request.action_summary,
    risk: request.risk_level,
    fields: request.requested_fields || [],
    save: Boolean(request.save_to_vault)
  })));
}

function requestDraftHasValue() {
  return Array.from(requestDrafts.values()).some((value) => String(value || "").length > 0);
}

function requestInputEditing() {
  const active = document.activeElement;
  return Boolean(active && active.closest?.("#requests") && active.matches?.("[data-secret-field], input, textarea"));
}

function flushPendingRequestRender() {
  if (!pendingRequestPayload || requestInputEditing() || requestDraftHasValue()) return;
  const pending = pendingRequestPayload;
  pendingRequestPayload = null;
  renderRequests(pending.requests, { force: true });
}

function renderRequests(requests = [], options = {}) {
  captureRequestDrafts();
  const root = $("#requests");
  const active = activeLiteRequests(requests);
  const signature = requestSignature(active);
  if (!options.force && (signature === renderedRequestSignature || requestInputEditing() || requestDraftHasValue())) {
    if (signature !== renderedRequestSignature) pendingRequestPayload = { requests };
    return;
  }
  pendingRequestPayload = null;
  root.textContent = "";
  pruneRequestDrafts(active);
  renderedRequestSignature = signature;
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
      secretFields(request).forEach((field) => {
        const wrap = document.createElement("label");
        wrap.className = "field";
        wrap.textContent = field;
        const input = document.createElement("input");
        input.type = field.toLowerCase().includes("password") ? "password" : "text";
        input.autocomplete = "off";
        input.dataset.requestId = request.request_id;
        input.dataset.secretField = field;
        input.value = requestDrafts.get(requestDraftKey(request, field)) || "";
        input.oninput = () => { requestDrafts.set(requestDraftKey(request, field), input.value); };
        wrap.append(input);
        item.append(wrap);
      });
      const submit = button("提交到保险柜", async () => {
        const payload = {};
        secretFields(request).forEach((field) => {
          payload[field] = requestDrafts.get(requestDraftKey(request, field)) || "";
        });
        payload.save_to_vault = Boolean(request.save_to_vault);
        const envelope = await encryptForBroker(payload, request);
        await signedFetch(`/api/requests/${encodeURIComponent(request.request_id)}/submit`, {
          method: "POST",
          headers: { "content-type": "application/json", ...csrfHeaders() },
          body: JSON.stringify({ envelope })
        }).then(async (response) => {
          if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.reason || error.error || "submit_failed");
          }
        });
        secretFields(request).forEach((field) => requestDrafts.delete(requestDraftKey(request, field)));
        pendingRequestPayload = null;
        setStatus("已提交保险柜");
        await loadState({ forceRequests: true });
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

function renderCredentialRequests(requests = []) {
  const root = $("#credential-requests");
  root.textContent = "";
  const active = requests.filter((request) => ["pending", "user_control"].includes(request.status));
  if (!active.length) {
    root.innerHTML = '<p class="meta">暂无新的密码请求。</p>';
    return;
  }
  active.slice(0, 4).forEach((request) => {
    const item = document.createElement("article");
    item.className = "request";
    item.innerHTML = `<strong>${requestLabel(request)}</strong><div>${escapeHtml(request.action_summary || request.origin || "")}</div><div class="meta">${escapeHtml(request.origin || "")}</div>`;
    root.append(item);
  });
}

function credentialOriginsText(credential) {
  return (credential.allowed_origins || []).join(", ");
}

function credentialMetadata(credential) {
  return credential.metadata && typeof credential.metadata === "object" ? credential.metadata : {};
}

function credentialDisplayName(credential) {
  const metadata = credentialMetadata(credential);
  return metadata.name || metadata.label || credentialOriginsText(credential) || credential.credential_id;
}

function credentialSecondaryText(credential) {
  const metadata = credentialMetadata(credential);
  return [metadata.kind, metadata.source, metadata.notes].filter(Boolean).join(" · ");
}

function credentialSearchText(credential) {
  const metadata = credentialMetadata(credential);
  return [
    credential.username,
    credential.credential_id,
    credentialOriginsText(credential),
    metadata.name,
    metadata.label,
    metadata.kind,
    metadata.source,
    metadata.notes
  ].filter(Boolean).join(" ").toLowerCase();
}

function renderCredentials(payload = {}) {
  credentialPayloadCache = payload;
  renderCredentialRequests(payload.latest_requests || []);
  const root = $("#credentials");
  root.textContent = "";
  const query = ($("#credential-search")?.value || "").trim().toLowerCase();
  const credentials = (payload.credentials || []).filter((credential) => {
    if (!query) return true;
    return credentialSearchText(credential).includes(query);
  });
  if (!credentials.length) {
    root.innerHTML = `<p class="meta">${query ? "没有匹配的密码。" : payload.vault_exists ? "暂无已保存凭证。" : "Vault 尚未创建，保存第一条密码时会创建。"}</p>`;
    return;
  }
  const summary = document.createElement("p");
  summary.className = "meta";
  summary.textContent = query ? `匹配 ${credentials.length} / ${(payload.credentials || []).length} 条` : `已保存 ${credentials.length} 条`;
  root.append(summary);
  credentials.forEach((credential) => {
    const item = document.createElement("article");
    item.className = "credential";
    item.dataset.credentialId = credential.credential_id || "";
    item.dataset.origins = credentialOriginsText(credential);
    const title = document.createElement("strong");
    const origin = document.createElement("div");
    const meta = document.createElement("div");
    const actions = document.createElement("div");
    const secondary = credentialSecondaryText(credential);
    title.textContent = credentialDisplayName(credential);
    origin.className = "meta";
    origin.textContent = credentialOriginsText(credential) || "(no origin)";
    meta.className = "meta";
    meta.textContent = `${credential.username || "账号"} · ${credential.credential_id}`;
    actions.className = "actions";
    actions.append(
      button("查看/编辑", () => revealCredential(credential.credential_id), "secondary"),
      button("删除", () => deleteCredential(credential.credential_id), "danger")
    );
    if (secondary) {
      const note = document.createElement("div");
      note.className = "meta";
      note.textContent = secondary;
      item.append(title, origin, meta, note, actions);
    } else {
      item.append(title, origin, meta, actions);
    }
    root.append(item);
  });
}

function credentialBody() {
  return {
    passphrase: $("#vault-passphrase").value,
    allowed_origins: $("#credential-origin").value.split(",").map((item) => item.trim()).filter(Boolean),
    username: $("#credential-username").value.trim(),
    password: $("#credential-password").value,
    totp_seed: $("#credential-totp").value,
    create_vault: true
  };
}

function clearCredentialForm() {
  $("#credential-id").value = "";
  $("#credential-origin").value = "";
  $("#credential-username").value = "";
  $("#credential-password").value = "";
  $("#credential-totp").value = "";
}

async function loadCredentials() {
  const response = await signedFetch("/api/lite/credentials", { cache: "no-store" });
  if (!response.ok) return;
  renderCredentials(await response.json());
}

async function revealCredential(credentialId) {
  const passphrase = $("#vault-passphrase").value;
  if (!passphrase) {
    setStatus("需要 Vault 密码");
    $("#vault-passphrase").focus();
    return;
  }
  const response = await signedFetch(`/api/lite/credentials/${encodeURIComponent(credentialId)}/reveal`, {
    method: "POST",
    headers: { "content-type": "application/json", ...csrfHeaders() },
    body: JSON.stringify({ passphrase })
  });
  if (!response.ok) throw new Error("凭证解锁失败");
  const secret = await response.json();
  const current = Array.from($("#credentials").querySelectorAll(".credential")).find((item) => item.dataset.credentialId === credentialId);
  $("#credential-id").value = credentialId;
  $("#credential-origin").value = current?.dataset.origins || "";
  $("#credential-username").value = secret.username || "";
  $("#credential-password").value = secret.password || "";
  $("#credential-totp").value = secret.totp_seed || "";
  setStatus("凭证已载入");
}

async function saveCredential(event) {
  event.preventDefault();
  const credentialId = $("#credential-id").value;
  const response = await signedFetch(credentialId ? `/api/lite/credentials/${encodeURIComponent(credentialId)}` : "/api/lite/credentials", {
    method: credentialId ? "PUT" : "POST",
    headers: { "content-type": "application/json", ...csrfHeaders() },
    body: JSON.stringify(credentialBody())
  });
  if (!response.ok) throw new Error("凭证保存失败");
  renderCredentials(await response.json());
  clearCredentialForm();
  setStatus("凭证已保存");
}

async function deleteCredential(credentialId) {
  if (!confirm("删除这条密码凭证？")) return;
  const response = await signedFetch(`/api/lite/credentials/${encodeURIComponent(credentialId)}`, {
    method: "DELETE",
    headers: csrfHeaders()
  });
  if (!response.ok) throw new Error("凭证删除失败");
  renderCredentials(await response.json());
  clearCredentialForm();
  setStatus("凭证已删除");
}

function renderFiles(payload = {}) {
  filePayloadCache = payload;
  currentFilePath = payload.path || ".";
  $("#file-path").textContent = `${payload.root || ""} / ${currentFilePath}`;
  if (payload.type === "directory") {
    $("#file-editor").hidden = true;
    $("#file-actions").hidden = true;
  }
  const root = $("#files");
  root.textContent = "";
  const query = ($("#file-search")?.value || "").trim().toLowerCase();
  if (currentFilePath !== ".") {
    const parent = currentFilePath.split("/").slice(0, -1).join("/") || ".";
    root.append(fileItem({ name: "..", path: parent, type: "directory" }));
  }
  const entries = (payload.entries || []).filter((entry) => !query || [entry.name, entry.path, entry.type].join(" ").toLowerCase().includes(query));
  if (!entries.length && query) {
    root.innerHTML = '<p class="meta">没有匹配的文件。</p>';
    return;
  }
  entries.forEach((entry) => root.append(fileItem(entry)));
}

function fileItem(entry) {
  const item = document.createElement("div");
  const label = document.createElement("strong");
  const open = button(entry.type === "directory" ? "打开" : "编辑", () => entry.type === "directory" ? loadFiles(entry.path) : openFile(entry.path), "secondary");
  item.className = "file-item";
  label.textContent = `${entry.type === "directory" ? "[dir]" : "[file]"} ${entry.name}`;
  item.append(label, open);
  return item;
}

async function loadFiles(path = ".") {
  const response = await signedFetch(`/api/lite/files?path=${encodeURIComponent(path)}`, { cache: "no-store" });
  if (!response.ok) return;
  renderFiles(await response.json());
}

async function openFile(path) {
  const response = await signedFetch(`/api/lite/files/content?path=${encodeURIComponent(path)}`, { cache: "no-store" });
  if (!response.ok) throw new Error("文件不可编辑");
  const payload = await response.json();
  currentFilePath = payload.path;
  $("#file-path").textContent = payload.path;
  $("#file-editor").value = payload.content || "";
  $("#file-editor").hidden = false;
  $("#file-actions").hidden = false;
  setStatus("文件已打开");
}

async function saveFile() {
  if (!currentFilePath || currentFilePath === ".") {
    setStatus("请选择文件");
    return;
  }
  const response = await signedFetch("/api/lite/files/content", {
    method: "PUT",
    headers: { "content-type": "application/json", ...csrfHeaders() },
    body: JSON.stringify({ path: currentFilePath, content: $("#file-editor").value })
  });
  if (!response.ok) throw new Error("文件保存失败");
  setStatus("文件已保存");
}

async function newFile() {
  const path = $("#new-file-path").value.trim();
  if (!path) {
    setStatus("请输入文件路径");
    return;
  }
  currentFilePath = path;
  $("#file-editor").value = "";
  await saveFile();
  $("#new-file-path").value = "";
  $("#file-search").value = "";
  await openFile(path);
}

async function deleteFile() {
  if (!currentFilePath || currentFilePath === ".") return;
  if (!confirm(`删除 ${currentFilePath}？`)) return;
  const response = await signedFetch(`/api/lite/files?path=${encodeURIComponent(currentFilePath)}`, {
    method: "DELETE",
    headers: csrfHeaders()
  });
  if (!response.ok) throw new Error("删除失败");
  $("#file-editor").value = "";
  $("#file-editor").hidden = true;
  $("#file-actions").hidden = true;
  const parent = currentFilePath.split("/").slice(0, -1).join("/") || ".";
  currentFilePath = parent;
  await loadFiles(parent);
  setStatus("已删除");
}

function button(text, onClick, className = "") {
  const node = document.createElement("button");
  node.type = "button";
  node.textContent = text;
  if (className) node.className = className;
  node.onclick = async () => {
    node.disabled = true;
    try {
      await onClick();
    } catch (error) {
      setStatus(error?.message || "操作失败");
    } finally {
      node.disabled = false;
    }
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
  await loadState({ forceRequests: true });
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

function cleanedMessageText(message) {
  const rawBody = message.text || "";
  return (message.attachments || []).length
    ? (rawBody.replace(/\n\n\[Attachments\][\s\S]*$/m, "").trim() || "附件")
    : rawBody;
}

function messageSortValue(message) {
  const sequence = Number(message.sequence);
  if (Number.isFinite(sequence)) return sequence;
  const timestamp = Number(message.created_at || message.updated_at || 0);
  return Number.isFinite(timestamp) && timestamp > 0 ? timestamp * 1000 : Number.MAX_SAFE_INTEGER;
}

function sortMessagesChronologically(messages = []) {
  return [...messages].sort((a, b) => {
    const sortA = messageSortValue(a);
    const sortB = messageSortValue(b);
    if (sortA !== sortB) return sortA - sortB;
    return Number(a.created_at || 0) - Number(b.created_at || 0);
  });
}

function liveTerminalMessage(chat = {}, storedMessages = []) {
  const terminal = chat.terminal || {};
  const terminalText = String(terminal.text || "");
  if (!terminalText.trim() || !terminal.active) return null;
  const paneId = terminal.pane_id || "terminal";
  const latestUser = [...storedMessages].reverse().find((message) => message.role === "user");
  let liveText = terminalText;
  if (latestUser) {
    const anchor = cleanedMessageText(latestUser).trim();
    const index = anchor ? terminalText.lastIndexOf(anchor) : -1;
    if (index < 0) return null;
    liveText = terminalText.slice(index + anchor.length);
  } else if (storedMessages.length) {
    return null;
  }
  const tail = liveText.split("\n").slice(-48).join("\n").trim();
  if (!tail) return null;
  const baseSequence = Number(latestUser?.sequence);
  return {
    message_id: `live_terminal_${paneId}`,
    sequence: Number.isFinite(baseSequence) ? baseSequence + 0.5 : Number.MAX_SAFE_INTEGER,
    role: "assistant",
    status: "实时",
    text: tail,
    attachments: [],
    created_at: Number(latestUser?.created_at || 0) + 0.001,
    updated_at: Date.now() / 1000
  };
}

function createMessageNode(message) {
  const item = document.createElement("article");
  const meta = document.createElement("div");
  const text = document.createElement("div");
  const attachments = document.createElement("div");
  meta.className = "meta";
  text.className = "text";
  attachments.className = "attachment-list";
  item.append(meta, text, attachments);
  updateMessageNode(item, message);
  return item;
}

function updateMessageNode(item, message) {
  const pending = ["queued", "sending"].includes(message.status);
  const className = `message ${message.role || ""} ${pending ? "pending" : ""}`;
  if (item.className !== className) item.className = className;
  const meta = item.firstChild;
  const text = item.children[1];
  const attachments = item.children[2];
  const metaText = `${message.role === "user" ? "你" : "OmniDoer"} · ${message.status || ""}`;
  if (meta.textContent !== metaText) meta.textContent = metaText;
  const body = cleanedMessageText(message);
  if (text.textContent !== body) text.textContent = body;
  renderAttachmentList(attachments, message.attachments || []);
}

function attachmentUrl(attachment) {
  const uploadId = encodeURIComponent(attachment.upload_id || "");
  const filename = encodeURIComponent(attachment.filename || "download");
  return `/api/chat/attachments/${uploadId}/${filename}`;
}

function renderAttachmentList(root, attachments = []) {
  const fp = JSON.stringify(attachments.map((item) => [item.upload_id, item.filename, item.size, item.content_type]));
  if (root.dataset.fp === fp) return;
  root.dataset.fp = fp;
  root.textContent = "";
  root.hidden = !attachments.length;
  attachments.forEach((attachment) => {
    const item = document.createElement("div");
    const link = document.createElement("a");
    const meta = document.createElement("span");
    const url = attachmentUrl(attachment);
    item.className = "attachment";
    link.href = url;
    link.target = "_blank";
    link.rel = "noopener";
    link.textContent = attachment.filename || "download";
    meta.className = "meta";
    meta.textContent = `${Math.ceil(Number(attachment.size || 0) / 1024)} KB${attachment.expires_at ? " · 临时文件" : ""}`;
    if (String(attachment.content_type || "").startsWith("image/")) {
      const image = document.createElement("img");
      image.src = url;
      image.alt = attachment.filename || "";
      item.append(image);
    }
    item.append(link, meta);
    root.append(item);
  });
}

function renderChatNow(chat = {}) {
  const root = $("#messages");
  const storedMessages = sortMessagesChronologically(
    (chat.messages || []).filter((message) => !String(message.client_message_id || "").startsWith("omnidoer_auto_status_"))
  );
  const terminalMessage = liveTerminalMessage(chat, storedMessages);
  const messages = sortMessagesChronologically(terminalMessage ? [...storedMessages, terminalMessage] : storedMessages);
  const fp = JSON.stringify([messages.length, messages.at(-1)?.message_id, messages.at(-1)?.updated_at, terminalMessage?.text?.slice(-300)]);
  if (fp === lastFingerprint) return;
  lastFingerprint = fp;
  const nearBottom = root.scrollHeight - root.scrollTop - root.clientHeight < 80;
  const stick = nearBottom && Date.now() > manualScrollPauseUntil;
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
  terminal.hidden = true;
  terminal.textContent = "";
  renderedTerminalTail = "";
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

async function loadState(options = {}) {
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
  renderRequests(payload.requests, { force: Boolean(options.forceRequests) });
  renderChat(payload.chat);
}

function applyChatPayload(payload) {
  if (!payload || payload.session_id !== activeSessionId) return;
  renderChat(payload);
}

async function streamChatOnce(signal) {
  const response = await signedFetch(
    `/api/chat/events?stream=1&snapshots=1800&interval=0.18&compact=1&limit=24&session_id=${encodeURIComponent(activeSessionId)}`,
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
  const originalText = input.value;
  const text = originalText.trim();
  const files = [...selectedFiles];
  if (!text && !files.length) return;
  const clientMessageId = chatTextIsCliCommand(text)
    ? `control_cli_${Date.now()}_${Math.random().toString(16).slice(2)}`
    : `lite_${Date.now()}_${Math.random().toString(16).slice(2)}`;
  try {
    let attachments = [];
    if (files.length) {
      setStatus("上传中");
      attachments = await uploadChatAttachments(files);
    } else {
      setStatus("发送中");
    }
    const response = await signedFetch("/api/chat/messages", {
      method: "POST",
      headers: { "content-type": "application/json", ...csrfHeaders() },
      body: JSON.stringify({ text, attachments, session_id: activeSessionId, client_message_id: clientMessageId })
    });
    if (!response.ok) {
      throw new Error(await responseErrorText(response, "发送失败"));
    }
    input.value = "";
    hideChatCommandMenu();
    selectedFiles = [];
    $("#chat-files").value = "";
    renderSelectedFiles();
    setStatus("已发送");
    await loadState();
  } catch (error) {
    input.value = originalText;
    selectedFiles = files;
    renderSelectedFiles();
    setStatus(`发送失败：${error?.message || "网络错误"}`);
    input.focus({ preventScroll: true });
  }
}

async function uploadChatAttachments(files) {
  if (!files.length) return [];
  const form = new FormData();
  files.forEach((file) => form.append("files", file, file.name));
  const response = await signedFetch("/api/chat/attachments", {
    method: "POST",
    headers: csrfHeaders(),
    body: form
  });
  if (!response.ok) throw new Error(await responseErrorText(response, "上传失败"));
  const payload = await response.json();
  return payload.attachments || [];
}

async function responseErrorText(response, fallback) {
  try {
    const payload = await response.json();
    return payload.reason || payload.error || fallback;
  } catch {
    return fallback;
  }
}

function renderSelectedFiles() {
  const root = $("#selected-files");
  root.hidden = !selectedFiles.length;
  root.textContent = selectedFiles.map((file) => `${file.name} (${Math.ceil(file.size / 1024)} KB)`).join(" · ");
}

function filesFromClipboard(event) {
  const clipboard = event.clipboardData;
  if (!clipboard) return [];
  const files = Array.from(clipboard.files || []);
  if (files.length) return files;
  return Array.from(clipboard.items || [])
    .filter((item) => item.kind === "file")
    .map((item) => item.getAsFile())
    .filter(Boolean)
    .map((file, index) => file.name ? file : new File([file], `pasted-${Date.now()}-${index}.png`, { type: file.type || "image/png" }));
}

function handlePasteFiles(event) {
  const files = filesFromClipboard(event);
  if (!files.length) return;
  event.preventDefault();
  selectedFiles = [...selectedFiles, ...files];
  renderSelectedFiles();
  setStatus("已添加附件");
}

function handleChatInputKeydown(event) {
  if (handleCommandMenuKeydown(event)) return;
  if (event.key !== "Enter" || event.shiftKey || event.isComposing) return;
  event.preventDefault();
  $("#chat-form").requestSubmit();
}

function matchingLiteCommands(value) {
  const text = String(value || "");
  if (!text.startsWith("/") || /\s/.test(text) || text.includes("\n")) return [];
  const query = text.toLowerCase();
  return LITE_CHAT_COMMANDS.filter((item) => item.command.toLowerCase().startsWith(query));
}

function hideChatCommandMenu() {
  const menu = $("#chat-command-menu");
  if (!menu) return;
  menu.hidden = true;
  menu.textContent = "";
  commandMenuIndex = 0;
}

function completeLiteCommand(item) {
  if (!item) return;
  const input = $("#chat-input");
  input.value = `${item.command}${item.argument ? " " : ""}`;
  hideChatCommandMenu();
  input.focus({ preventScroll: true });
}

function renderChatCommandMenu() {
  const input = $("#chat-input");
  const menu = $("#chat-command-menu");
  if (!input || !menu) return;
  const matches = matchingLiteCommands(input.value);
  if (!matches.length) {
    hideChatCommandMenu();
    return;
  }
  commandMenuIndex = Math.min(commandMenuIndex, matches.length - 1);
  menu.textContent = "";
  matches.forEach((item, index) => {
    const button = document.createElement("button");
    const title = document.createElement("strong");
    const detail = document.createElement("span");
    button.type = "button";
    button.className = index === commandMenuIndex ? "active" : "";
    title.textContent = item.command;
    detail.textContent = item.argument ? `${item.argument} · ${item.description}` : item.description;
    button.append(title, detail);
    button.onpointerdown = (event) => {
      event.preventDefault();
      completeLiteCommand(item);
    };
    menu.append(button);
  });
  menu.hidden = false;
}

function handleCommandMenuKeydown(event) {
  const menu = $("#chat-command-menu");
  if (!menu || menu.hidden) return false;
  const matches = matchingLiteCommands($("#chat-input").value);
  if (!matches.length) return false;
  if (event.key === "ArrowDown") {
    event.preventDefault();
    commandMenuIndex = (commandMenuIndex + 1) % matches.length;
    renderChatCommandMenu();
    return true;
  }
  if (event.key === "ArrowUp") {
    event.preventDefault();
    commandMenuIndex = (commandMenuIndex - 1 + matches.length) % matches.length;
    renderChatCommandMenu();
    return true;
  }
  if (event.key === "Tab" || (event.key === "Enter" && !event.shiftKey)) {
    event.preventDefault();
    completeLiteCommand(matches[commandMenuIndex]);
    return true;
  }
  if (event.key === "Escape") {
    event.preventDefault();
    hideChatCommandMenu();
    return true;
  }
  return false;
}

function chatTextIsCliCommand(text) {
  const firstLine = String(text || "").trimStart().split(/\r?\n/, 1)[0].trim();
  return /^\/[A-Za-z][A-Za-z0-9-]*(?:\s|$)/.test(firstLine);
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
$("#password-login-button").onclick = passwordLogin;
$("#refresh-button").onclick = () => loadState({ forceRequests: true });
$("#credentials-refresh-button").onclick = loadCredentials;
$("#credential-form").onsubmit = saveCredential;
$("#credential-clear-button").onclick = clearCredentialForm;
$("#files-refresh-button").onclick = () => loadFiles(currentFilePath);
$("#new-file-button").onclick = newFile;
$("#file-save-button").onclick = saveFile;
$("#file-delete-button").onclick = deleteFile;
$("#credential-search").oninput = () => renderCredentials(credentialPayloadCache || {});
$("#file-search").oninput = () => renderFiles(filePayloadCache || {});
document.querySelectorAll("[data-tab]").forEach((tab) => {
  tab.onclick = () => switchView(tab.dataset.tab);
});
$("#chat-form").onsubmit = sendMessage;
$("#chat-files").onchange = () => {
  selectedFiles = Array.from($("#chat-files").files || []);
  renderSelectedFiles();
};
$("#chat-input").addEventListener("paste", handlePasteFiles);
$("#chat-input").addEventListener("input", renderChatCommandMenu);
$("#chat-input").addEventListener("keydown", handleChatInputKeydown);
$("#chat-input").addEventListener("blur", () => setTimeout(hideChatCommandMenu, 120));
$("#messages").addEventListener("paste", handlePasteFiles);
$("#messages").addEventListener("scroll", () => {
  const root = $("#messages");
  const nearBottom = root.scrollHeight - root.scrollTop - root.clientHeight < 80;
  if (!nearBottom) manualScrollPauseUntil = Date.now() + 2200;
}, { passive: true });
$("#requests").addEventListener("focusout", () => setTimeout(flushPendingRequestRender, 120));
$("#session-select").onchange = () => {
  activeSessionId = $("#session-select").value || "default";
  localStorage.setItem("omnidoer_lite_active_session", activeSessionId);
  lastFingerprint = "";
  renderedMessageNodes.clear();
  $("#messages").textContent = "";
  renderedTerminalTail = "";
  renderedLiveTerminalKey = "";
  $("#terminal").hidden = true;
  loadState({ forceRequests: true });
  startChatStream();
};

loadState({ forceRequests: true }).finally(() => {
  markReady();
  switchView(activeView);
  loadCredentials();
  loadFiles(currentFilePath);
  startStateLoop();
  startChatStream();
});

setTimeout(markReady, 1800);
