import os
import json
import tempfile
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.error import HTTPError

from omnidoer.omni_browser.controller import BrowserController
from omnidoer.omni_control.server import ControlHandler
from omnidoer.omni_takeover.browser_worker import BrowserContextWorker
from omnidoer.omni_takeover.models import InputEvent
from omnidoer.omni_takeover.relay import apply_input_event, release_control, request_user_control, start_stream
from omnidoer.omni_takeover.sessions import registered_browser_context
from tests.util_demo import DemoServerFixture


class TakeoverBrowserRelayTest(unittest.TestCase):
    def test_browser_frame_and_input_event_relay(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, DemoServerFixture() as demo:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                try:
                    browser_context = BrowserController()
                    browser = browser_context.__enter__()
                except Exception as exc:
                    self.skipTest(f"playwright chromium unavailable: {type(exc).__name__}")
                try:
                    browser.open(f"{demo.origin}/antibot")
                    request = request_user_control(
                        origin=demo.origin,
                        top_level_url=f"{demo.origin}/antibot",
                        reason="browser relay test",
                    )
                    frame = start_stream(request.request_id, browser_controller=browser)
                    self.assertEqual(frame["content_type"], "image/png")
                    self.assertGreater(len(frame["data_b64"]), 100)
                    self.assertTrue(frame["for_control_client_only"])
                    self.assertTrue(frame["not_for_llm"])
                    browser.page.locator("#takeover").click()
                    apply_input_event(request.request_id, InputEvent("type", text="sensitive-takeover-input"), browser_controller=browser)
                    value = browser.page.locator("#takeover").input_value()
                    self.assertEqual(value, "sensitive-takeover-input")
                    result = release_control(request.request_id)
                    self.assertEqual(result["status"], "user_completed_takeover")
                finally:
                    browser_context.__exit__(None, None, None)

                raw_audit = (Path(tmp) / "audit.jsonl").read_text()
                self.assertIn("takeover_input_event", raw_audit)
                self.assertNotIn("sensitive-takeover-input", raw_audit)
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_control_server_frame_and_input_endpoints(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, DemoServerFixture() as demo:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            control_server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
            Thread(target=control_server.serve_forever, daemon=True).start()
            try:
                try:
                    worker = BrowserContextWorker(f"{demo.origin}/antibot").start()
                except Exception as exc:
                    self.skipTest(f"playwright chromium unavailable: {type(exc).__name__}")
                try:
                    request = request_user_control(
                        origin=demo.origin,
                        top_level_url=f"{demo.origin}/antibot",
                        reason="server endpoint relay test",
                        browser_context_id="ctx-test",
                    )
                    base = f"http://127.0.0.1:{control_server.server_address[1]}"
                    with registered_browser_context("ctx-test", worker):
                        from urllib.request import Request, urlopen

                        frame = json.loads(urlopen(f"{base}/api/requests/{request.request_id}/frame", timeout=5).read().decode())
                        self.assertTrue(frame["for_control_client_only"])
                        self.assertGreater(len(frame["data_b64"]), 100)
                        self.assertIn("frame_id", frame)
                        body = json.dumps({"event_type": "tap", "frame_id": frame["frame_id"], "x": 90, "y": 150}).encode()
                        urlopen(
                            Request(
                                f"{base}/api/requests/{request.request_id}/input",
                                data=body,
                                headers={"content-type": "application/json"},
                                method="POST",
                            ),
                            timeout=5,
                        )
                        body = json.dumps({"event_type": "type", "frame_id": frame["frame_id"], "text": "endpoint-sensitive-input"}).encode()
                        urlopen(
                            Request(
                                f"{base}/api/requests/{request.request_id}/input",
                                data=body,
                                headers={"content-type": "application/json"},
                                method="POST",
                            ),
                            timeout=5,
                        )
                        stale_body = json.dumps({"event_type": "type", "frame_id": "stale-frame", "text": "stale-sensitive-input"}).encode()
                        with self.assertRaises(HTTPError) as stale:
                            urlopen(
                                Request(
                                    f"{base}/api/requests/{request.request_id}/input",
                                    data=stale_body,
                                    headers={"content-type": "application/json"},
                                    method="POST",
                                ),
                                timeout=5,
                            )
                        self.assertEqual(stale.exception.code, 409)
                finally:
                    worker.stop()
                raw_audit = (Path(tmp) / "audit.jsonl").read_text()
                self.assertIn("takeover_input_event", raw_audit)
                self.assertNotIn("endpoint-sensitive-input", raw_audit)
                self.assertNotIn("stale-sensitive-input", raw_audit)
            finally:
                control_server.shutdown()
                control_server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home


if __name__ == "__main__":
    unittest.main()
