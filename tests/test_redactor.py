import unittest

from omnidoer.omni_observer import REDACTED, redact_dom_snapshot, redact_text


class RedactorTest(unittest.TestCase):
    def test_redacts_secret_like_text(self) -> None:
        text = "Authorization: Bearer test_token_should_be_redacted_000000000000"
        self.assertEqual(redact_text(text), f"Authorization: {REDACTED}")

    def test_redacts_card_like_text(self) -> None:
        self.assertEqual(redact_text("card 4111 1111 1111 1111"), f"card {REDACTED}")

    def test_redacts_password_input_value(self) -> None:
        snapshot = {
            "tag": "input",
            "type": "password",
            "name": "password",
            "value": "fake-visible-secret",
        }
        redacted = redact_dom_snapshot(snapshot)
        self.assertEqual(redacted["value"], REDACTED)
        self.assertNotIn("fake-visible-secret", repr(redacted))

    def test_redacts_accessibility_secret_value(self) -> None:
        tree = {
            "role": "textbox",
            "name": "one-time code",
            "description": "TOTP 123456",
            "children": [{"name": "Email demo@example.test"}],
        }
        redacted = redact_dom_snapshot(tree)
        self.assertEqual(redacted["description"], REDACTED)
        self.assertNotIn("123456", repr(redacted))
        self.assertNotIn("demo@example.test", repr(redacted))


if __name__ == "__main__":
    unittest.main()
