import os
import tempfile
import importlib.util
import unittest
from pathlib import Path
from urllib.parse import quote

from omnidoer.omni_mcp.runtime import reset_runtime_for_tests
from omnidoer.omni_mcp.tools import call_tool
from omnidoer.omni_control.requests import RequestStore
from omnidoer.omni_vault.vault import Vault
from tests.util_demo import DemoServerFixture


@unittest.skipIf(importlib.util.find_spec("playwright") is None, "playwright not installed")
class McpBrowserToolsTest(unittest.TestCase):
    def tearDown(self) -> None:
        reset_runtime_for_tests()

    def test_mcp_browser_open_observe_and_origin(self) -> None:
        with DemoServerFixture() as demo:
            opened = call_tool("browser.open", {"url": f"{demo.origin}/login"})
            if opened.get("status") == "unavailable":
                self.skipTest("playwright chromium unavailable")
            self.assertEqual(opened["status"], "opened")
            origin = call_tool("browser.current_origin", {})
            self.assertEqual(origin["origin"], demo.origin)
            typed = call_tool("browser.type_text", {"selector": "#email", "text": "demo"})
            self.assertEqual(typed["status"], "typed")
            rejected = call_tool("browser.type_text", {"selector": "#password", "text": "not-for-model"})
            self.assertEqual(rejected["status"], "rejected")
            self.assertIn("Secret Broker", rejected["reason"])
            observation = call_tool("browser.observe", {})
            self.assertEqual(observation["status"], "ok")
            self.assertIn("nodes", observation["observation"])
            self.assertNotIn("not-for-model", repr(observation))
            accessibility = call_tool("browser.observe_accessibility", {})
            self.assertEqual(accessibility["status"], "ok")
            self.assertNotIn("not-for-model", repr(accessibility))

    def test_mcp_browser_detects_challenge_and_antibot(self) -> None:
        with DemoServerFixture() as demo:
            opened = call_tool("browser.open", {"url": f"{demo.origin}/captcha"})
            if opened.get("status") == "unavailable":
                self.skipTest("playwright chromium unavailable")
            challenge = call_tool("browser.detect_challenge", {})
            self.assertEqual(challenge["challenge_type"], "captcha")
            self.assertTrue(challenge["requires_user_interaction"])
            call_tool("browser.open", {"url": f"{demo.origin}/antibot"})
            antibot = call_tool("browser.detect_antibot", {})
            self.assertTrue(antibot["antibot_detected"])
            self.assertTrue(antibot["requires_human_takeover"])

    def test_mcp_browser_selects_plain_form_values(self) -> None:
        html = quote("<select id='mode'><option value='slow'>Slow</option><option value='fast'>Fast</option></select>")
        opened = call_tool("browser.open", {"url": f"data:text/html,{html}"})
        if opened.get("status") == "unavailable":
            self.skipTest("playwright chromium unavailable")
        selected = call_tool("browser.select", {"selector": "#mode", "value": "fast"})
        self.assertEqual(selected["status"], "selected")

    def test_mcp_browser_uploads_file_without_returning_contents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            upload_path = Path(tmp) / "upload.txt"
            upload_path.write_text("local file body must not be returned")
            html = quote("<input id='file' type='file'>")
            opened = call_tool("browser.open", {"url": f"data:text/html,{html}"})
            if opened.get("status") == "unavailable":
                self.skipTest("playwright chromium unavailable")
            uploaded = call_tool("browser.upload_file", {"selector": "#file", "path": str(upload_path)})
            self.assertEqual(uploaded["status"], "uploaded")
            self.assertEqual(uploaded["filename"], "upload.txt")
            self.assertNotIn("local file body", repr(uploaded))

    def test_sensitive_file_upload_requires_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            upload_path = Path(tmp) / "sensitive.txt"
            upload_path.write_text("sensitive upload body")
            try:
                html = quote("<input id='file' type='file'>")
                opened = call_tool("browser.open", {"url": f"data:text/html,{html}"})
                if opened.get("status") == "unavailable":
                    self.skipTest("playwright chromium unavailable")
                request = call_tool(
                    "browser.upload_file",
                    {"selector": "#file", "path": str(upload_path), "sensitive": True},
                )
                self.assertEqual(request["status"], "approval_required")
                self.assertEqual(request["request"]["request_type"], "file_upload")
                self.assertNotIn("sensitive upload body", repr(request))
                RequestStore().approve(request["request"]["request_id"])
                approved = call_tool(
                    "browser.upload_file",
                    {
                        "selector": "#file",
                        "path": str(upload_path),
                        "sensitive": True,
                        "approval_request_id": request["request"]["request_id"],
                    },
                )
                self.assertEqual(approved["status"], "uploaded")
                self.assertNotIn("sensitive upload body", repr(approved))
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_mcp_credential_fill_uses_vault_without_returning_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, DemoServerFixture() as demo:
            vault_path = Path(tmp) / "vault.json"
            passphrase_env = "OMNIDOER_TEST_MCP_VAULT_PASSPHRASE"
            old_passphrase = os.environ.get(passphrase_env)
            os.environ[passphrase_env] = "test-passphrase"
            try:
                vault = Vault.create(vault_path, os.environ[passphrase_env])
                credential_id = vault.add_credential(
                    username="demo",
                    password="mcp-vault-password",
                    totp_seed="JBSWY3DPEHPK3PXP",
                    allowed_origins=[demo.origin],
                )
                opened = call_tool("browser.open", {"url": f"{demo.origin}/login"})
                if opened.get("status") == "unavailable":
                    self.skipTest("playwright chromium unavailable")
                listed = call_tool("credential.list_for_current_origin", {"vault_path": str(vault_path)})
                self.assertEqual(listed["credentials"][0]["credential_id"], credential_id)
                filled = call_tool(
                    "credential.fill_current_origin_login",
                    {"credential_id": credential_id, "vault_path": str(vault_path), "passphrase_env": passphrase_env},
                )
                self.assertEqual(filled["status"], "credential_received_and_filled")
                self.assertNotIn("mcp-vault-password", repr(filled))
                observation = call_tool("browser.observe", {})
                self.assertNotIn("mcp-vault-password", repr(observation))
            finally:
                if old_passphrase is None:
                    os.environ.pop(passphrase_env, None)
                else:
                    os.environ[passphrase_env] = old_passphrase


if __name__ == "__main__":
    unittest.main()
