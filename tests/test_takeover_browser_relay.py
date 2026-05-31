import os
import json
import tempfile
import time
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.error import HTTPError

from omnidoer.omni_browser.controller import BrowserController
from omnidoer.omni_control.requests import RequestStore
from omnidoer.omni_control.server import ControlHandler
from omnidoer.omni_takeover.browser_worker import BrowserContextWorker
from omnidoer.omni_takeover.cross_process import consume_input_events, read_frame, start_browser_relay, write_context_status, write_frame
from omnidoer.omni_takeover.models import InputEvent
from omnidoer.omni_takeover.relay import apply_input_event, release_control, request_user_control, start_stream
from omnidoer.omni_takeover.sessions import registered_browser_context
from tests.util_demo import DemoServerFixture


class TakeoverBrowserRelayTest(unittest.TestCase):
    def test_control_server_cross_process_browser_context_relay(self) -> None:
        class FakeBrowser:
            def current_url(self):
                return "http://127.0.0.1:8765/antibot"

            def current_origin(self):
                return "http://127.0.0.1:8765"

        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            control_server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
            Thread(target=control_server.serve_forever, daemon=True).start()
            try:
                write_context_status("cross-browser", FakeBrowser())
                frame = {
                    "frame_id": "frame_cross",
                    "captured_at": 2000000000.0,
                    "url": "http://127.0.0.1:8765/antibot",
                    "origin": "http://127.0.0.1:8765",
                    "viewport": {"width": 320, "height": 240},
                    "content_type": "image/jpeg",
                    "data_b64": "abcd",
                    "transport": {"profile": "balanced"},
                    "for_control_client_only": True,
                    "not_for_llm": True,
                }
                write_frame("cross-browser", frame)
                base = f"http://127.0.0.1:{control_server.server_address[1]}"
                from urllib.request import Request, urlopen

                contexts = json.loads(urlopen(f"{base}/api/browser/contexts", timeout=5).read().decode())
                self.assertTrue(any(context["browser_context_id"] == "cross-browser" for context in contexts["contexts"]))
                preview_frame = json.loads(urlopen(f"{base}/api/browser/contexts/cross-browser/frame", timeout=5).read().decode())
                self.assertEqual(preview_frame["frame_id"], "frame_cross")
                self.assertTrue(preview_frame["preview_only"])

                body = json.dumps({"reason": "user paused browser"}).encode()
                request_payload = json.loads(
                    urlopen(
                        Request(
                            f"{base}/api/browser/contexts/cross-browser/takeover",
                            data=body,
                            headers={"content-type": "application/json"},
                            method="POST",
                        ),
                        timeout=5,
                    )
                    .read()
                    .decode()
                )
                self.assertEqual(request_payload["browser_context_id"], "cross-browser")
                request_id = request_payload["request_id"]

                delivered_frame = json.loads(urlopen(f"{base}/api/requests/{request_id}/frame", timeout=5).read().decode())
                self.assertEqual(delivered_frame["frame_id"], "frame_cross")
                self.assertEqual(RequestStore().get(request_id).takeover_frame_id, "frame_cross")

                input_body = json.dumps({"event_type": "tap", "frame_id": "frame_cross", "x": 10, "y": 10}).encode()
                queued = json.loads(
                    urlopen(
                        Request(
                            f"{base}/api/requests/{request_id}/input",
                            data=input_body,
                            headers={"content-type": "application/json"},
                            method="POST",
                        ),
                        timeout=5,
                    )
                    .read()
                    .decode()
                )
                self.assertEqual(queued["status"], "event_queued")
                events = consume_input_events("cross-browser")
                self.assertEqual(events[0]["event"]["event_type"], "tap")
            finally:
                control_server.shutdown()
                control_server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_cross_process_relay_publishes_preview_frames_before_takeover(self) -> None:
        class FakeBrowser:
            def current_url(self):
                return "https://example.com/working"

            def current_origin(self):
                return "https://example.com"

            def takeover_frame(self, *, frame_profile=None):
                return {
                    "frame_id": f"preview_{frame_profile}",
                    "captured_at": 2000000000.0,
                    "url": "https://example.com/working",
                    "origin": "https://example.com",
                    "viewport": {"width": 320, "height": 240},
                    "content_type": "image/jpeg",
                    "data_b64": "abcd",
                    "transport": {"profile": frame_profile},
                    "for_control_client_only": True,
                    "not_for_llm": True,
                }

        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            relay = start_browser_relay("preview-browser", FakeBrowser(), poll_interval=0.1)
            try:
                frame = None
                for _ in range(30):
                    frame = read_frame("preview-browser", max_age_seconds=10)
                    if frame:
                        break
                    time.sleep(0.1)
                self.assertIsNotNone(frame)
                assert frame is not None
                self.assertEqual(frame["frame_id"], "preview_data_saver")
                self.assertEqual(frame["transport"]["profile"], "data_saver")
            finally:
                relay.stop()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

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
                    self.assertEqual(frame["content_type"], "image/jpeg")
                    self.assertEqual(frame["transport"]["profile"], "balanced")
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
                        out_of_bounds_body = json.dumps(
                            {"event_type": "tap", "frame_id": frame["frame_id"], "x": frame["viewport"]["width"], "y": 0}
                        ).encode()
                        with self.assertRaises(HTTPError) as out_of_bounds:
                            urlopen(
                                Request(
                                    f"{base}/api/requests/{request.request_id}/input",
                                    data=out_of_bounds_body,
                                    headers={"content-type": "application/json"},
                                    method="POST",
                                ),
                                timeout=5,
                            )
                        self.assertEqual(out_of_bounds.exception.code, 400)
                        error_payload = json.loads(out_of_bounds.exception.read().decode())
                        self.assertEqual(error_payload["error"], "takeover_coordinates_out_of_bounds")
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
