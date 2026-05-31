import importlib.util
import os
import tempfile
import unittest
from http.server import ThreadingHTTPServer
from threading import Thread

from omnidoer.omni_control.cloud import build_config
from omnidoer.omni_control.pairing import PairingStore
from omnidoer.omni_control.server import ControlHandler


@unittest.skipIf(importlib.util.find_spec("playwright") is None, "playwright not installed")
class ControlPwaCachedSessionTest(unittest.TestCase):
    def test_pwa_reuses_cached_pairing_session_after_reload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
            base = f"http://127.0.0.1:{server.server_address[1]}"
            server.omnidoer_config = build_config(
                host="127.0.0.1",
                port=server.server_address[1],
                cloud_direct=True,
                public_url=base,
                insecure_dev_public=True,
            )  # type: ignore[attr-defined]
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                pairing = PairingStore().create(public_url=base, ttl_seconds=600)
                from playwright.sync_api import Error as PlaywrightError
                from playwright.sync_api import expect
                from playwright.sync_api import sync_playwright

                with sync_playwright() as p:
                    browser = None
                    try:
                        try:
                            browser = p.chromium.launch(headless=True)
                        except PlaywrightError as exc:
                            self.skipTest(f"playwright browser unavailable: {type(exc).__name__}")
                        page = browser.new_page(viewport={"width": 390, "height": 844})
                        page.goto(f"{base}/pair?code={pairing.code}&pairing_id={pairing.pairing_id}", wait_until="domcontentloaded")
                        self.assertEqual(page.evaluate("window.location.search"), "")
                        self.assertEqual(page.locator("#pairing-code").input_value(), pairing.code)
                        page.click("#pair-device")
                        expect(page.locator("#pairing-status")).to_contain_text("Paired PWA Control Client", timeout=5000)
                        device_id = page.evaluate("localStorage.getItem('omnidoer_device_id')")
                        session_id = page.evaluate("localStorage.getItem('omnidoer_session_id')")
                        self.assertTrue(device_id)
                        self.assertTrue(session_id)

                        page.goto(base, wait_until="domcontentloaded")
                        expect(page.locator("#pairing-status")).to_contain_text("Requests load automatically", timeout=5000)
                        self.assertIn(device_id, page.locator("#pairing-current-device").inner_text())
                        self.assertEqual(page.evaluate("localStorage.getItem('omnidoer_device_id')"), device_id)
                        self.assertEqual(page.evaluate("localStorage.getItem('omnidoer_session_id')"), session_id)
                        self.assertFalse(page.locator("#forget-local-pairing").is_disabled())
                    finally:
                        if browser is not None:
                            browser.close()
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home


if __name__ == "__main__":
    unittest.main()
