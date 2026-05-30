import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from omnidoer.omni_agent.demo_agent import run_task
from omnidoer.omni_vault.vault import Vault
from tests.util_demo import DemoServerFixture


@unittest.skipIf(importlib.util.find_spec("playwright") is None, "playwright not installed")
class E2EDemoGuardedBrowserTest(unittest.TestCase):
    def test_guarded_browser_handles_2fa_then_antibot_takeover_and_resumes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, DemoServerFixture() as demo:
            old = {
                key: os.environ.get(key)
                for key in (
                    "OMNIDOER_HOME",
                    "OMNIDOER_TEST_PASSPHRASE",
                    "OMNIDOER_TEST_USERNAME",
                    "OMNIDOER_TEST_PASSWORD",
                    "OMNIDOER_TEST_SMS_CODE",
                    "OMNIDOER_CONTROL_TEST_MODE",
                    "OMNIDOER_CHALLENGE_TEST_MODE",
                    "OMNIDOER_TAKEOVER_TEST_MODE",
                    "OMNIDOER_TEST_TAKEOVER_ACTIONS",
                )
            }
            os.environ.update(
                {
                    "OMNIDOER_HOME": tmp,
                    "OMNIDOER_TEST_PASSPHRASE": "test-passphrase-change-me",
                    "OMNIDOER_TEST_USERNAME": "demo",
                    "OMNIDOER_TEST_PASSWORD": "demo-password-change-me",
                    "OMNIDOER_TEST_SMS_CODE": "123456",
                    "OMNIDOER_CONTROL_TEST_MODE": "1",
                    "OMNIDOER_CHALLENGE_TEST_MODE": "1",
                    "OMNIDOER_TAKEOVER_TEST_MODE": "1",
                    "OMNIDOER_TEST_TAKEOVER_ACTIONS": "type:user-completed;release",
                }
            )
            try:
                vault_path = Path(tmp) / "vault.json"
                Vault.create(vault_path, os.environ["OMNIDOER_TEST_PASSPHRASE"])
                args = SimpleNamespace(
                    task="guarded browser 2FA 智能切换",
                    vault=str(vault_path),
                    passphrase_env="OMNIDOER_TEST_PASSPHRASE",
                    demo_origin=demo.origin,
                    control_origin="http://127.0.0.1:8787",
                )
                try:
                    self.assertEqual(run_task(args), 0)
                except Exception as exc:
                    message = str(exc)
                    if "Playwright" in message or "Executable doesn't exist" in message or "BrowserType.launch" in message:
                        self.skipTest(f"playwright chromium unavailable: {type(exc).__name__}")
                    raise
                raw_audit = (Path(tmp) / "audit.jsonl").read_text()
                self.assertIn("agent_resumed_after_challenge", raw_audit)
                self.assertIn("agent_resumed_after_takeover", raw_audit)
                self.assertIn("guarded_browser_task_completed", raw_audit)
                self.assertIn("challenge_relay", raw_audit)
                self.assertIn("human_takeover", raw_audit)
                self.assertNotIn("demo-password-change-me", raw_audit)
                self.assertNotIn("123456", raw_audit)
                self.assertNotIn("user-completed", raw_audit)
                self.assertNotIn("demo-password-change-me", vault_path.read_text())
            finally:
                for key, value in old.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value


if __name__ == "__main__":
    unittest.main()
