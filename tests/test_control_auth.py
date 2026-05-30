import tempfile
import unittest
from pathlib import Path

from omnidoer.omni_control.csrf import verify_csrf
from omnidoer.omni_control.sessions import SessionStore


class ControlAuthTest(unittest.TestCase):
    def test_session_token_is_hashed_and_csrf_checked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = SessionStore(Path(tmp) / "sessions.json")
            session, token = store.create(device_id="dev_1")
            raw = Path(tmp, "sessions.json").read_text()
            self.assertNotIn(token, raw)
            self.assertTrue(verify_csrf(session.csrf_token, session.csrf_token))
            self.assertFalse(verify_csrf(session.csrf_token, "wrong"))


if __name__ == "__main__":
    unittest.main()
