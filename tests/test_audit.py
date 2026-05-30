import tempfile
import unittest
import stat
from pathlib import Path

from omnidoer.omni_audit.audit import AuditLog


class AuditTest(unittest.TestCase):
    def test_hash_chain_and_redaction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "audit.jsonl"
            audit = AuditLog(path)
            audit.append("credential_fill", origin="http://127.0.0.1:8765", password="fake-password")
            audit.append("challenge_completed", sms_code="123456", status="ok")
            audit.append("challenge_text", message="SMS code: 654321", challenge_answer="user-completed")
            audit.append("takeover_input_event", user_input="typed-sensitive-value", input_event_type="type")
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            raw = path.read_text()
            self.assertNotIn("fake-password", raw)
            self.assertNotIn("123456", raw)
            self.assertNotIn("654321", raw)
            self.assertNotIn("user-completed", raw)
            self.assertNotIn("typed-sensitive-value", raw)
            self.assertTrue(audit.verify())

    def test_tamper_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "audit.jsonl"
            audit = AuditLog(path)
            audit.append("event", status="ok")
            text = path.read_text().replace("ok", "changed")
            path.write_text(text)
            self.assertFalse(audit.verify())


if __name__ == "__main__":
    unittest.main()
