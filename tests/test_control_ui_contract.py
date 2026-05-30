import unittest
from pathlib import Path

from omnidoer.omni_control.server import static_root


class ControlUiContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = (static_root() / "index.html").read_text()
        cls.app = (static_root() / "app.js").read_text()

    def test_secret_explanation_present(self) -> None:
        self.assertIn("Secret Broker", self.html)
        self.assertIn("Not sent to Agent/LLM context", self.html)
        self.assertIn("MCP return values", self.html)

    def test_password_inputs_are_password_type(self) -> None:
        self.assertIn('id="password"', self.app)
        self.assertIn('data-secret-field="password" type="password"', self.app)
        self.assertIn('id="totp-seed"', self.app)
        self.assertIn('data-secret-field="totp_seed" type="password"', self.app)

    def test_challenge_no_bypass_explanation_present(self) -> None:
        self.assertIn("does not bypass CAPTCHA/MFA/Passkey/WebAuthn/3DS", self.html)
        self.assertIn("completed by you, not by the Agent", self.app)
        self.assertIn("No challenge answer is submitted to OmniDoer", self.app)
        self.assertIn('if (isVisualChallenge)', self.app)

    def test_takeover_explanation_present(self) -> None:
        self.assertIn("Agent paused", self.html)
        self.assertIn("User in control", self.html)
        self.assertIn("Release Control", self.html)
        self.assertIn("Registration Handoff", self.html)
        self.assertIn("does not automate fake or bulk registration", self.html)

    def test_payment_fields_present(self) -> None:
        for label in (
            "Merchant",
            "Amount",
            "Currency",
            "Origin",
            "Recipient",
            "Shipping address",
            "Billing method summary",
            "Subscription / renewal",
            "Refund / cancellation terms",
            "Final button text",
            "After approval",
        ):
            self.assertIn(label, self.html)

    def test_app_uses_webcrypto_and_request_api(self) -> None:
        app = (static_root() / "app.js").read_text()
        self.assertIn("crypto.subtle", app)
        self.assertIn("/api/requests", app)
        self.assertIn("submitEncrypted", app)
        self.assertIn("web-p256-v1", app)

    def test_task_panel_uses_local_queue_not_direct_model_api(self) -> None:
        self.assertIn("Chat / Task", self.html)
        self.assertIn("does not call OpenAI APIs or models directly", self.html)
        self.assertIn("control.next_user_task", self.html)
        app = (static_root() / "app.js").read_text()
        self.assertIn("/api/tasks", app)
        self.assertIn("submitTask", app)
        self.assertIn("local queue -> MCP control.next_user_task -> Codex CLI", app)

    def test_pairing_panel_and_cloud_csrf_contract_present(self) -> None:
        self.assertIn("Pair Device", self.html)
        self.assertIn("Only pair devices you control", self.html)
        self.assertIn("Server URL", self.html)
        self.assertIn("Broker fingerprint", self.html)
        self.assertIn("Web broker fingerprint", self.html)
        self.assertIn("Devices / Sessions", self.html)
        app = (static_root() / "app.js").read_text()
        self.assertIn("/api/pairing/", app)
        self.assertIn("loadPairingDetails", app)
        self.assertIn("pairing_id", app)
        self.assertIn("/api/pair", app)
        self.assertIn("/api/devices", app)
        self.assertIn("/api/sessions", app)
        self.assertIn("revokeDevice", app)
        self.assertIn("revokeSession", app)
        self.assertIn('signedFetch("/api/broker-key"', app)
        self.assertIn("omnidoer_device_id", app)
        self.assertIn("omnidoer_session_id", app)
        self.assertIn("x-omnidoer-csrf", app)
        self.assertIn("x-omnidoer-device-sig", app)
        self.assertIn("omnidoer-device-v1", app)
        self.assertIn("signedFetch", app)
        self.assertIn("device_id", app)
        self.assertIn("expires_at", app)

    def test_request_stream_uses_signed_fetch_not_eventsource(self) -> None:
        app = (static_root() / "app.js").read_text()
        self.assertIn("startRequestStream", app)
        self.assertIn("startRequestWebSocket", app)
        self.assertIn("new WebSocket", app)
        self.assertIn("/api/ws/requests", app)
        self.assertIn("deviceAuthSubprotocol", app)
        self.assertIn("omnidoer-v1.", app)
        self.assertIn("/api/events?stream=1", app)
        self.assertIn("ReadableStream", app)
        self.assertIn("signedFetch(\"/api/events?stream=1", app)
        self.assertNotIn("new EventSource", app)

    def test_takeover_ui_sends_rich_input_events(self) -> None:
        app = (static_root() / "app.js").read_text()
        for event_type in ("drag", "long_press", "scroll", "type", "key"):
            self.assertIn(f'event_type: "{event_type}"', app)
        self.assertIn("Text to controlled browser", app)
        self.assertIn("installTakeoverPointerHandlers", app)
        self.assertIn("startTakeoverFramePolling", app)
        self.assertIn("fetchTakeoverFrame", app)
        self.assertIn("setInterval(() => fetchTakeoverFrame", app)
        self.assertIn("stopTakeoverFramePolling", app)
        self.assertIn("account_registration", app)
        self.assertIn('request.request_type === "human_takeover" || request.request_type === "account_registration"', app)
        self.assertIn("Registration Handoff", app)

    def test_payment_request_renderer_uses_structured_details(self) -> None:
        app = (static_root() / "app.js").read_text()
        self.assertIn("request.structured_details", app)
        self.assertIn("Agent prepared action", app)
        self.assertIn("Submit only after approval", app)
        self.assertIn('"file_upload"', app)


if __name__ == "__main__":
    unittest.main()
