const statusEl = document.createElement("p");
statusEl.textContent = "Local trusted mode. Remote mode requires pairing and broker fingerprint pinning.";
document.querySelector("main").prepend(statusEl);

async function encryptForBroker(payload, request) {
  return {
    localModePlaceholder: true,
    requestId: request.request_id,
    origin: request.origin,
    requestType: request.request_type,
    payload
  };
}
