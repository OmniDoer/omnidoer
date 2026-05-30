import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tests.util_demo import DemoServerFixture
from omnidoer.omni_agent.demo_agent import run_task
from omnidoer.omni_vault.vault import Vault


class E2EDemoLoginTest(unittest.TestCase):
    def test_login_download_invoice_with_control_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, DemoServerFixture() as demo:
            old = {key: os.environ.get(key) for key in (
                "OMNIDOER_HOME",
                "OMNIDOER_TEST_PASSPHRASE",
                "OMNIDOER_TEST_USERNAME",
                "OMNIDOER_TEST_PASSWORD",
                "OMNIDOER_TEST_SMS_CODE",
                "OMNIDOER_CONTROL_TEST_MODE",
                "OMNIDOER_CHALLENGE_TEST_MODE",
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
                }
            )
            try:
                vault_path = Path(tmp) / "vault.json"
                Vault.create(vault_path, os.environ["OMNIDOER_TEST_PASSPHRASE"])
                args = SimpleNamespace(
                    task="登录 demo 网站并下载我的发票",
                    vault=str(vault_path),
                    passphrase_env="OMNIDOER_TEST_PASSPHRASE",
                    demo_origin=demo.origin,
                    control_origin="http://127.0.0.1:8787",
                )
                self.assertEqual(run_task(args), 0)
                self.assertTrue(Path(".omnidoer/downloads/omnidoer-demo-invoice.txt").exists())
                raw_vault = vault_path.read_text()
                self.assertNotIn("demo-password-change-me", raw_vault)
            finally:
                for key, value in old.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value


if __name__ == "__main__":
    unittest.main()
