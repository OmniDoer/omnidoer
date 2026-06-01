import os
import tempfile
import importlib.util
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import quote

from omnidoer.omni_mcp.runtime import get_browser, reset_runtime_for_tests
from omnidoer.omni_mcp.tools import call_tool
from omnidoer.omni_control.requests import RequestStore
from omnidoer.omni_control.secure_channel import encrypt_for_broker, load_or_create_keypair
from omnidoer.omni_vault.vault import Vault
from tests.util_demo import DemoServerFixture


@unittest.skipIf(importlib.util.find_spec("playwright") is None, "playwright not installed")
class McpBrowserToolsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._home_tmp = tempfile.TemporaryDirectory()
        self._old_home = os.environ.get("OMNIDOER_HOME")
        os.environ["OMNIDOER_HOME"] = self._home_tmp.name

    def tearDown(self) -> None:
        reset_runtime_for_tests()
        if self._old_home is None:
            os.environ.pop("OMNIDOER_HOME", None)
        else:
            os.environ["OMNIDOER_HOME"] = self._old_home
        self._home_tmp.cleanup()

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

    def test_mcp_browser_uses_non_headless_user_agent(self) -> None:
        opened = call_tool("browser.open", {"url": "data:text/html,<p>ua</p>"})
        if opened.get("status") == "unavailable":
            self.skipTest("playwright chromium unavailable")
        user_agent = get_browser().page.evaluate("navigator.userAgent")
        self.assertIn("Chrome/", user_agent)
        self.assertNotIn("HeadlessChrome", user_agent)

    def test_mcp_browser_detects_challenge_and_antibot(self) -> None:
        with DemoServerFixture() as demo:
            opened = call_tool("browser.open", {"url": f"{demo.origin}/captcha", "auto_takeover": False})
            if opened.get("status") == "unavailable":
                self.skipTest("playwright chromium unavailable")
            challenge = call_tool("browser.detect_challenge", {})
            self.assertEqual(challenge["challenge_type"], "captcha")
            self.assertTrue(challenge["requires_user_interaction"])
            self.assertTrue(challenge["requires_human_takeover"])
            self.assertTrue(challenge["agent_paused"])
            self.assertTrue(challenge["takeover_created"])
            self.assertEqual(challenge["request"]["browser_context_id"], "mcp-browser")
            RequestStore().release_takeover(challenge["request"]["request_id"])
            call_tool("browser.open", {"url": f"{demo.origin}/antibot", "auto_takeover": False})
            antibot = call_tool("browser.detect_antibot", {})
            self.assertTrue(antibot["antibot_detected"])
            self.assertTrue(antibot["requires_human_takeover"])
            self.assertTrue(antibot["agent_paused"])
            self.assertTrue(antibot["takeover_created"])
            self.assertEqual(antibot["request"]["browser_context_id"], "mcp-browser")
            RequestStore().release_takeover(antibot["request"]["request_id"])

    def test_mcp_browser_open_auto_pauses_on_challenge(self) -> None:
        with DemoServerFixture() as demo:
            opened = call_tool("browser.open", {"url": f"{demo.origin}/captcha"})
            if opened.get("status") == "unavailable":
                self.skipTest("playwright chromium unavailable")
            self.assertEqual(opened["status"], "paused_for_human_takeover")
            self.assertEqual(opened["browser_action"], "browser.open")
            self.assertEqual(opened["browser_action_result"]["status"], "opened")
            self.assertEqual(opened["challenge_type"], "captcha")
            self.assertTrue(opened["requires_human_takeover"])
            self.assertTrue(opened["agent_paused"])
            self.assertTrue(opened["takeover_created"])
            self.assertEqual(opened["request"]["browser_context_id"], "mcp-browser")
            RequestStore().release_takeover(opened["request"]["request_id"])

    def test_mcp_browser_click_auto_pauses_after_navigation_to_antibot(self) -> None:
        class ClickNavigationHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("content-type", "text/html; charset=utf-8")
                self.end_headers()
                if self.path == "/start":
                    self.wfile.write(b"<a id='go' href='/antibot'>Go</a>")
                else:
                    self.wfile.write(b"<h1>antibot</h1>")

            def log_message(self, *_args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), ClickNavigationHandler)
        Thread(target=server.serve_forever, daemon=True).start()
        try:
            base = f"http://127.0.0.1:{server.server_address[1]}"
            opened = call_tool("browser.open", {"url": f"{base}/start"})
            if opened.get("status") == "unavailable":
                self.skipTest("playwright chromium unavailable")
            clicked = call_tool("browser.click", {"selector": "#go"})
            self.assertEqual(clicked["status"], "paused_for_human_takeover")
            self.assertEqual(clicked["browser_action"], "browser.click")
            self.assertEqual(clicked["browser_action_result"]["status"], "clicked")
            self.assertTrue(clicked["antibot_detected"])
            self.assertTrue(clicked["requires_human_takeover"])
            self.assertTrue(clicked["agent_paused"])
            self.assertTrue(clicked["takeover_created"])
            self.assertEqual(clicked["request"]["browser_context_id"], "mcp-browser")
            RequestStore().release_takeover(clicked["request"]["request_id"])
        finally:
            server.shutdown()
            server.server_close()

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

    def test_sensitive_payment_click_requires_matching_approval_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                html = quote(
                    """
<form id="pay-form" action="/pay" onsubmit="event.preventDefault(); window.clickedCount += 1;">
  <input type="hidden" name="merchant" value="Demo Store">
  <input type="hidden" name="amount" value="12.34">
  <input type="hidden" name="currency" value="USD">
  <button id="pay" type="submit">Pay 12.34 USD</button>
</form>
<script>window.clickedCount = 0;</script>
"""
                )
                opened = call_tool("browser.open", {"url": f"data:text/html,{html}"})
                if opened.get("status") == "unavailable":
                    self.skipTest("playwright chromium unavailable")

                blocked = call_tool("browser.click", {"selector": "#pay"})
                self.assertEqual(blocked["status"], "approval_required")
                self.assertEqual(blocked["blocked_action"], "payment_submit")
                request = blocked["request"]
                self.assertEqual(request["request_type"], "payment_approval")
                self.assertEqual(request["structured_details"]["merchant"], "Demo Store")
                self.assertEqual(request["structured_details"]["amount"], "12.34")
                self.assertRegex(request["approval_fingerprint"], r"^[0-9a-f]{64}$")
                self.assertEqual(get_browser().page.evaluate("window.clickedCount"), 0)

                RequestStore().approve(request["request_id"])
                get_browser().page.evaluate("document.querySelector('[name=amount]').value = '99.00'")
                mismatch = call_tool("browser.click", {"selector": "#pay", "approval_request_id": request["request_id"]})
                self.assertEqual(mismatch["status"], "approval_scope_mismatch")
                self.assertEqual(get_browser().page.evaluate("window.clickedCount"), 0)

                get_browser().page.evaluate("document.querySelector('[name=amount]').value = '12.34'")
                clicked = call_tool("browser.click", {"selector": "#pay", "approval_request_id": request["request_id"]})
                self.assertEqual(clicked["status"], "clicked")
                self.assertEqual(get_browser().page.evaluate("window.clickedCount"), 1)
                self.assertEqual(RequestStore().get(request["request_id"]).status, "consumed")
                replay = call_tool("browser.click", {"selector": "#pay", "approval_request_id": request["request_id"]})
                self.assertEqual(replay["status"], "approval_scope_mismatch")
                self.assertIn("not approved", replay["reason"])
                self.assertEqual(get_browser().page.evaluate("window.clickedCount"), 1)
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_mcp_credential_fill_uses_vault_without_returning_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, DemoServerFixture() as demo:
            vault_path = Path(tmp) / "vault.json"
            passphrase_env = "OMNIDOER_TEST_MCP_VAULT_PASSPHRASE"
            passphrase_file = Path(tmp) / "vault-passphrase"
            passphrase_file.write_text("test-passphrase\n")
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
                    {"credential_id": credential_id, "vault_path": str(vault_path), "passphrase_file": str(passphrase_file)},
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

    def test_mcp_credential_fill_accepts_one_time_request_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, DemoServerFixture() as demo:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                keypair = load_or_create_keypair()
                request = RequestStore().create(
                    "credential",
                    origin=demo.origin,
                    top_level_url=f"{demo.origin}/login",
                    action_summary="one-time login",
                    requested_fields=["username", "password"],
                    save_to_vault=False,
                )
                envelope = encrypt_for_broker(
                    keypair.public_key_b64,
                    {"username": "demo", "password": "one-time-mcp-password"},
                    request_id=request.request_id,
                    origin=request.origin,
                    request_type=request.request_type,
                )
                RequestStore().submit_ciphertext(request.request_id, envelope)
                opened = call_tool("browser.open", {"url": f"{demo.origin}/login"})
                if opened.get("status") == "unavailable":
                    self.skipTest("playwright chromium unavailable")
                filled = call_tool("credential.fill_current_origin_login", {"request_id": request.request_id})
                self.assertEqual(filled["status"], "credential_received_and_filled")
                self.assertNotIn("one-time-mcp-password", repr(filled))
                observation = call_tool("browser.observe", {})
                self.assertNotIn("one-time-mcp-password", repr(observation))
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home


if __name__ == "__main__":
    unittest.main()
