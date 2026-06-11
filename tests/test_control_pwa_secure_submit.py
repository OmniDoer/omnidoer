import os
import tempfile
import unittest
from http.server import ThreadingHTTPServer
from threading import Thread
from pathlib import Path

from omnidoer.omni_control.requests import RequestStore
from omnidoer.omni_control.secure_channel import decrypt_control_envelope
from omnidoer.omni_control.server import ControlHandler, LiteControlHandler


class ControlPwaSecureSubmitTest(unittest.TestCase):
    def test_lite_request_poll_does_not_replace_focused_secret_input(self) -> None:
        try:
            from playwright.sync_api import sync_playwright
        except Exception:
            self.skipTest("playwright is not installed")

        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            server = ThreadingHTTPServer(("127.0.0.1", 0), LiteControlHandler)
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                request = {
                    "request_id": "req-lite-draft",
                    "request_type": "credential",
                    "status": "pending",
                    "origin": "https://www.kaggle.com",
                    "action_summary": "Kaggle Legacy API Credentials",
                    "requested_fields": ["username", "password"],
                    "risk_level": "low",
                    "save_to_vault": True,
                }
                url = f"http://127.0.0.1:{server.server_address[1]}"
                try:
                    with sync_playwright() as playwright:
                        browser = playwright.chromium.launch(headless=True)
                        page = browser.new_page()
                        page.goto(url, wait_until="domcontentloaded")
                        page.evaluate("(request) => renderRequests([request], { force: true })", request)
                        page.fill("[data-secret-field='password']", "draft-secret")
                        page.evaluate("window.__litePasswordInputBeforeRerender = document.querySelector(\"[data-secret-field='password']\")")
                        page.evaluate("(request) => renderRequests([request])", request)
                        self.assertTrue(
                            page.evaluate("window.__litePasswordInputBeforeRerender === document.querySelector(\"[data-secret-field='password']\")")
                        )
                        self.assertEqual(page.locator("[data-secret-field='password']").input_value(), "draft-secret")
                        self.assertEqual(page.evaluate("document.activeElement?.dataset.secretField"), "password")
                        browser.close()
                except Exception as exc:
                    self.skipTest(f"playwright chromium unavailable: {type(exc).__name__}")
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_pwa_preserves_credential_draft_during_request_rerender(self) -> None:
        try:
            from playwright.sync_api import sync_playwright
        except Exception:
            self.skipTest("playwright is not installed")

        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                RequestStore(Path(tmp) / "control_requests.json").create(
                    "credential",
                    origin="http://127.0.0.1:8765",
                    top_level_url="http://127.0.0.1:8765/login",
                    action_summary="login",
                    requested_fields=["username", "password"],
                )
                url = f"http://127.0.0.1:{server.server_address[1]}"
                try:
                    with sync_playwright() as playwright:
                        browser = playwright.chromium.launch(headless=True)
                        page = browser.new_page()
                        page.goto(url, wait_until="domcontentloaded")
                        page.wait_for_selector("#username")
                        page.fill("#username", "demo")
                        page.fill("#password", "draft-secret")
                        page.evaluate("window.__passwordInputBeforeRerender = document.querySelector('#password')")
                        page.evaluate("renderRequestList(cachedRequests)")
                        self.assertTrue(page.evaluate("window.__passwordInputBeforeRerender === document.querySelector('#password')"))
                        self.assertEqual(page.locator("#username").input_value(), "demo")
                        self.assertEqual(page.locator("#password").input_value(), "draft-secret")
                        self.assertEqual(page.evaluate("document.activeElement?.dataset.secretField"), "password")
                        browser.close()
                except Exception as exc:
                    self.skipTest(f"playwright chromium unavailable: {type(exc).__name__}")
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_pwa_encrypts_credential_before_submit(self) -> None:
        try:
            from playwright.sync_api import sync_playwright
        except Exception:
            self.skipTest("playwright is not installed")

        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                store = RequestStore(Path(tmp) / "control_requests.json")
                request = store.create(
                    "credential",
                    origin="http://127.0.0.1:8765",
                    top_level_url="http://127.0.0.1:8765/login",
                    action_summary="login",
                    requested_fields=["username", "password"],
                )
                url = f"http://127.0.0.1:{server.server_address[1]}"
                try:
                    with sync_playwright() as playwright:
                        browser = playwright.chromium.launch(headless=True)
                        page = browser.new_page()
                        page.goto(url, wait_until="domcontentloaded")
                        page.fill("#username", "demo")
                        page.fill("#password", "pwa-secret")
                        page.click("text=Submit Credential")
                        page.wait_for_function(
                            "() => document.querySelector('#requests-list').innerText.includes('fulfilled')",
                            timeout=5000,
                        )
                        browser.close()
                except Exception as exc:
                    self.skipTest(f"playwright chromium unavailable: {type(exc).__name__}")

                fulfilled = RequestStore(Path(tmp) / "control_requests.json").get(request.request_id)
                self.assertEqual(fulfilled.status, "fulfilled")
                self.assertEqual(fulfilled.response_ciphertext["version"], "web-p256-v1")
                self.assertNotIn("pwa-secret", repr(fulfilled.to_public_dict()))
                self.assertNotIn("pwa-secret", repr(fulfilled.response_ciphertext))
                payload = decrypt_control_envelope(
                    fulfilled.response_ciphertext,
                    request_id=fulfilled.request_id,
                    origin=fulfilled.origin,
                    request_type=fulfilled.request_type,
                )
                self.assertEqual(payload["password"], "pwa-secret")
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home


if __name__ == "__main__":
    unittest.main()
