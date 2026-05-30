import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tests.util_demo import DemoServerFixture
from omnidoer.omni_agent.demo_agent import run_task
from omnidoer.omni_vault.vault import Vault


class E2EDemoCheckoutTest(unittest.TestCase):
    def run_checkout(self, mode: str) -> str:
        with tempfile.TemporaryDirectory() as tmp, DemoServerFixture() as demo:
            old = {key: os.environ.get(key) for key in (
                "OMNIDOER_HOME",
                "OMNIDOER_TEST_PASSPHRASE",
                "OMNIDOER_TEST_USERNAME",
                "OMNIDOER_TEST_PASSWORD",
                "OMNIDOER_TEST_SMS_CODE",
                "OMNIDOER_CONTROL_TEST_MODE",
                "OMNIDOER_CHALLENGE_TEST_MODE",
                "OMNIDOER_APPROVAL_MODE",
            )}
            os.environ.update(
                {
                    "OMNIDOER_HOME": tmp,
                    "OMNIDOER_TEST_PASSPHRASE": "test-passphrase-change-me",
                    "OMNIDOER_TEST_USERNAME": "demo",
                    "OMNIDOER_TEST_PASSWORD": "demo-password-change-me",
                    "OMNIDOER_TEST_SMS_CODE": "123456",
                    "OMNIDOER_CONTROL_TEST_MODE": "1",
                    "OMNIDOER_CHALLENGE_TEST_MODE": "1",
                    "OMNIDOER_APPROVAL_MODE": mode,
                }
            )
            try:
                vault_path = Path(tmp) / "vault.json"
                Vault.create(vault_path, os.environ["OMNIDOER_TEST_PASSPHRASE"])
                args = SimpleNamespace(
                    task="进入 checkout 并准备支付",
                    vault=str(vault_path),
                    passphrase_env="OMNIDOER_TEST_PASSPHRASE",
                    demo_origin=demo.origin,
                    control_origin="http://127.0.0.1:8787",
                )
                self.assertEqual(run_task(args), 0)
                return (Path(tmp) / "audit.jsonl").read_text()
            finally:
                for key, value in old.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value

    def test_checkout_deny_does_not_submit(self) -> None:
        audit = self.run_checkout("deny")
        self.assertIn("payment_denied", audit)
        self.assertNotIn("mock_payment_submitted", audit)

    def test_checkout_approve_submits_mock_payment(self) -> None:
        audit = self.run_checkout("approve")
        self.assertIn("mock_payment_submitted", audit)


if __name__ == "__main__":
    unittest.main()
