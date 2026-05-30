import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from omnidoer.omni_agent.demo_agent import run_task
from tests.util_demo import DemoServerFixture


class E2EDemoRegistrationHandoffTest(unittest.TestCase):
    def test_registration_is_completed_by_user_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, DemoServerFixture() as demo:
            old = {
                key: os.environ.get(key)
                for key in (
                    "OMNIDOER_HOME",
                    "OMNIDOER_TAKEOVER_TEST_MODE",
                    "OMNIDOER_TEST_USERNAME",
                    "OMNIDOER_TEST_PASSWORD",
                    "OMNIDOER_TEST_EMAIL_CODE",
                )
            }
            os.environ["OMNIDOER_HOME"] = tmp
            os.environ["OMNIDOER_TAKEOVER_TEST_MODE"] = "1"
            os.environ["OMNIDOER_TEST_USERNAME"] = "new-demo@example.test"
            os.environ["OMNIDOER_TEST_PASSWORD"] = "new-demo-password"
            os.environ["OMNIDOER_TEST_EMAIL_CODE"] = "654321"
            try:
                args = SimpleNamespace(
                    task="注册 demo 网站账号",
                    vault="",
                    passphrase_env=None,
                    demo_origin=demo.origin,
                    control_origin="",
                )
                self.assertEqual(run_task(args), 0)
                raw_audit = (Path(tmp) / "audit.jsonl").read_text()
                self.assertIn("registration_handoff_started", raw_audit)
                self.assertIn("registration_handoff_completed", raw_audit)
                self.assertIn("takeover_released", raw_audit)
                self.assertNotIn("new-demo-password", raw_audit)
                self.assertNotIn("654321", raw_audit)
            finally:
                for key, value in old.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value


if __name__ == "__main__":
    unittest.main()
