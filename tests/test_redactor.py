import unittest

from omnidoer.omni_observer import REDACTED, redact_dom_snapshot, redact_text


class RedactorTest(unittest.TestCase):
    def test_redacts_secret_like_text(self) -> None:
        text = "Authorization: Bearer test_token_should_be_redacted_000000000000"
        self.assertEqual(redact_text(text), f"Authorization: {REDACTED}")

    def test_redacts_card_like_text(self) -> None:
        self.assertEqual(redact_text("card 4111 1111 1111 1111"), f"card {REDACTED}")

    def test_redacts_challenge_answer_text(self) -> None:
        self.assertEqual(redact_text("SMS code: 654321"), REDACTED)
        self.assertEqual(redact_text("challenge answer user-completed"), REDACTED)

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

    def test_redacts_takeover_user_input_keys(self) -> None:
        event = {"event_type": "type", "user_input": "typed-sensitive-value", "input_text": "another-sensitive-value"}
        redacted = redact_dom_snapshot(event)
        self.assertEqual(redacted["user_input"], REDACTED)
        self.assertEqual(redacted["input_text"], REDACTED)
        self.assertNotIn("typed-sensitive-value", repr(redacted))
        self.assertNotIn("another-sensitive-value", repr(redacted))

    def test_redacts_error_fields_that_may_echo_user_input(self) -> None:
        event = {
            "event_type": "takeover_input_failed",
            "error_message": "remote browser echoed typed-sensitive-value",
            "exception": "challenge answer user-completed",
            "status": "rejected",
        }
        redacted = redact_dom_snapshot(event)
        self.assertEqual(redacted["error_message"], REDACTED)
        self.assertEqual(redacted["exception"], REDACTED)
        self.assertEqual(redacted["status"], "rejected")
        self.assertNotIn("typed-sensitive-value", repr(redacted))
        self.assertNotIn("user-completed", repr(redacted))

    def test_keeps_credential_label_text_without_secret_values(self) -> None:
        details = {
            "credential_labels": {
                "username": "GitHub username",
                "password": "GitHub PAT",
                "backup": "github_pat_secret_value_000000000000",
            }
        }
        redacted = redact_dom_snapshot(details)
        self.assertEqual(redacted["credential_labels"]["username"], "GitHub username")
        self.assertEqual(redacted["credential_labels"]["password"], "GitHub PAT")
        self.assertEqual(redacted["credential_labels"]["backup"], REDACTED)
        self.assertNotIn("github_pat_secret", repr(redacted))


if __name__ == "__main__":
    unittest.main()
