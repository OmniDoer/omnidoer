import unittest
from pathlib import Path

from omnidoer.omni_control.server import static_root


class ControlUiContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = (static_root() / "index.html").read_text()

    def test_secret_explanation_present(self) -> None:
        self.assertIn("Secret Broker", self.html)
        self.assertIn("Not sent to Agent/LLM context", self.html)
        self.assertIn("MCP return values", self.html)

    def test_password_inputs_are_password_type(self) -> None:
        self.assertIn('id="password" type="password"', self.html)
        self.assertIn('id="totp-seed" type="password"', self.html)

    def test_challenge_no_bypass_explanation_present(self) -> None:
        self.assertIn("does not bypass CAPTCHA/MFA/Passkey/WebAuthn/3DS", self.html)
        self.assertIn("completed by you, not by the Agent", self.html)

    def test_takeover_explanation_present(self) -> None:
        self.assertIn("Agent paused", self.html)
        self.assertIn("User in control", self.html)
        self.assertIn("Release Control", self.html)

    def test_payment_fields_present(self) -> None:
        for label in ("Merchant", "Amount", "Currency", "Origin"):
            self.assertIn(label, self.html)

    def test_app_uses_webcrypto_and_request_api(self) -> None:
        app = (static_root() / "app.js").read_text()
        self.assertIn("crypto.subtle", app)
        self.assertIn("/api/requests", app)
        self.assertIn("submitEncrypted", app)
        self.assertIn("web-p256-v1", app)

    def test_takeover_ui_sends_rich_input_events(self) -> None:
        app = (static_root() / "app.js").read_text()
        for event_type in ("drag", "long_press", "scroll", "type", "key"):
            self.assertIn(f'event_type: "{event_type}"', app)
        self.assertIn("Text to controlled browser", app)
        self.assertIn("installTakeoverPointerHandlers", app)


if __name__ == "__main__":
    unittest.main()
