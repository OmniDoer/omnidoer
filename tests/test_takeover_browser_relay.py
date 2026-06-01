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
from omnidoer.omni_takeover.cross_process import (
    CONTEXT_MAX_AGE_SECONDS,
    FRAME_MAX_AGE_SECONDS,
    consume_input_events,
    enqueue_input_event,
    list_contexts,
    read_frame,
    start_browser_relay,
    wait_for_input_event_result,
    write_context_status,
    write_frame,
    write_input_event_result,
)
from omnidoer.omni_takeover.models import InputEvent
from omnidoer.omni_takeover.relay import apply_input_event, release_control, request_user_control, start_stream
from omnidoer.omni_takeover.sessions import registered_browser_context
from tests.util_demo import DemoServerFixture


class TakeoverBrowserRelayTest(unittest.TestCase):
    def test_registered_browser_context_starts_worker_control_relay_hooks(self) -> None:
        class RelayAwareBrowser:
            def __init__(self):
                self.started = []
                self.stopped = []

            def start_control_relay(self, browser_context_id):
                self.started.append(browser_context_id)

            def stop_control_relay(self, browser_context_id=None):
                self.stopped.append(browser_context_id)

        browser = RelayAwareBrowser()
        with registered_browser_context("hooked-browser", browser):
            self.assertEqual(browser.started, ["hooked-browser"])
            self.assertEqual(browser.stopped, [])
        self.assertEqual(browser.stopped, ["hooked-browser"])

    def test_registered_browser_context_clears_cross_process_relay_on_exit(self) -> None:
        class FakeBrowser:
            def current_url(self):
                return "https://example.com/checkout"

            def current_origin(self):
                return "https://example.com"

        frame = {
            "frame_id": "frame_closed",
            "captured_at": time.time(),
            "url": "https://example.com/checkout",
            "origin": "https://example.com",
            "viewport": {"width": 320, "height": 240},
            "content_type": "image/jpeg",
            "data_b64": "abcd",
            "transport": {"profile": "data_saver"},
            "for_control_client_only": True,
            "not_for_llm": True,
        }
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                with registered_browser_context("cleanup-browser", FakeBrowser()):
                    write_context_status("cleanup-browser", FakeBrowser())
                    write_frame("cleanup-browser", frame)
                    self.assertTrue(any(context["browser_context_id"] == "cleanup-browser" for context in list_contexts()))
                    self.assertEqual(read_frame("cleanup-browser")["frame_id"], "frame_closed")
                self.assertFalse(any(context["browser_context_id"] == "cleanup-browser" for context in list_contexts()))
                self.assertIsNone(read_frame("cleanup-browser"))
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

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
                repeated_payload = json.loads(
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
                self.assertEqual(repeated_payload["request_id"], request_id)
                self.assertTrue(repeated_payload["reused"])

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
                pending = json.loads(
                    urlopen(f"{base}/api/browser/contexts/cross-browser/input-results/{queued['event_id']}", timeout=5).read().decode()
                )
                self.assertEqual(pending["status"], "pending")
                write_input_event_result("cross-browser", queued["event_id"], {"status": "event_applied", "request_id": request_id})
                result = json.loads(
                    urlopen(f"{base}/api/browser/contexts/cross-browser/input-results/{queued['event_id']}", timeout=5).read().decode()
                )
                self.assertEqual(result["status"], "event_applied")
                self.assertEqual(result["request_id"], request_id)
                self.assertFalse(result["secret_exposed_to_model"])
                pending_again = json.loads(
                    urlopen(f"{base}/api/browser/contexts/cross-browser/input-results/{queued['event_id']}", timeout=5).read().decode()
                )
                self.assertEqual(pending_again["status"], "pending")

                delayed = enqueue_input_event("cross-browser", request_id, {"event_type": "tap", "frame_id": "frame_cross", "x": 11, "y": 11})

                def ack_later() -> None:
                    time.sleep(0.05)
                    write_input_event_result("cross-browser", delayed["event_id"], {"status": "event_applied", "request_id": request_id})

                Thread(target=ack_later, daemon=True).start()
                long_poll_result = json.loads(
                    urlopen(
                        f"{base}/api/browser/contexts/cross-browser/input-results/{delayed['event_id']}?wait=1",
                        timeout=5,
                    )
                    .read()
                    .decode()
                )
                self.assertEqual(long_poll_result["status"], "event_applied")
                self.assertEqual(long_poll_result["request_id"], request_id)
                long_poll_consumed = json.loads(
                    urlopen(f"{base}/api/browser/contexts/cross-browser/input-results/{delayed['event_id']}", timeout=5).read().decode()
                )
                self.assertEqual(long_poll_consumed["status"], "pending")
            finally:
                control_server.shutdown()
                control_server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_browser_relay_keeps_mobile_pause_entry_visible_beyond_short_poll_gap(self) -> None:
        class FakeBrowser:
            def current_url(self):
                return "https://example.com/working"

            def current_origin(self):
                return "https://example.com"

        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                write_context_status("mobile-preview", FakeBrowser())
                status_path = Path(tmp) / "browser_relay" / "mobile-preview" / "status.json"
                stale_but_visible = time.time() - 60
                payload = json.loads(status_path.read_text())
                payload["updated_at"] = stale_but_visible
                status_path.write_text(json.dumps(payload))

                contexts = list_contexts()
                self.assertTrue(any(context["browser_context_id"] == "mobile-preview" for context in contexts))
                self.assertLess(60, CONTEXT_MAX_AGE_SECONDS)

                expired = time.time() - CONTEXT_MAX_AGE_SECONDS - 1
                payload["updated_at"] = expired
                status_path.write_text(json.dumps(payload))
                contexts = list_contexts()
                self.assertFalse(any(context["browser_context_id"] == "mobile-preview" for context in contexts))
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_browser_contexts_are_ordered_by_recent_activity_for_mobile_preview(self) -> None:
        class FakeBrowser:
            def __init__(self, url):
                self.url = url

            def current_url(self):
                return self.url

            def current_origin(self):
                return "https://example.com"

        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                write_context_status("aaa-older-browser", FakeBrowser("https://example.com/older"))
                time.sleep(0.01)
                write_context_status("zzz-current-browser", FakeBrowser("https://example.com/current"))

                contexts = list_contexts()
                self.assertGreaterEqual(len(contexts), 2)
                self.assertEqual(contexts[0]["browser_context_id"], "zzz-current-browser")
                self.assertEqual(contexts[0]["current_url"], "https://example.com/current")
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_browser_preview_frame_survives_mobile_reconnect_window(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                frame = {
                    "frame_id": "frame_mobile_preview",
                    "captured_at": time.time() - 20,
                    "url": "https://example.com/working",
                    "origin": "https://example.com",
                    "viewport": {"width": 320, "height": 240},
                    "content_type": "image/jpeg",
                    "data_b64": "abcd",
                    "transport": {"profile": "data_saver"},
                    "for_control_client_only": True,
                    "not_for_llm": True,
                }
                write_frame("mobile-preview-frame", frame)
                frame_path = Path(tmp) / "browser_relay" / "mobile-preview-frame" / "frame.json"
                stale_but_visible = time.time() - 20
                payload = json.loads(frame_path.read_text())
                payload["relay_updated_at"] = stale_but_visible
                frame_path.write_text(json.dumps(payload))

                self.assertEqual(read_frame("mobile-preview-frame")["frame_id"], "frame_mobile_preview")
                self.assertGreater(FRAME_MAX_AGE_SECONDS, 20)

                expired = time.time() - FRAME_MAX_AGE_SECONDS - 1
                payload["relay_updated_at"] = expired
                frame_path.write_text(json.dumps(payload))
                self.assertIsNone(read_frame("mobile-preview-frame"))
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_control_server_takeover_frame_requires_real_browser_frame(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            control_server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
            Thread(target=control_server.serve_forever, daemon=True).start()
            try:
                request = request_user_control(
                    origin="https://example.com",
                    top_level_url="https://example.com/antibot",
                    reason="missing browser frame",
                    browser_context_id="missing-browser-frame",
                )
                from urllib.request import urlopen

                base = f"http://127.0.0.1:{control_server.server_address[1]}"
                with self.assertRaises(HTTPError) as raised:
                    urlopen(f"{base}/api/requests/{request.request_id}/frame", timeout=5)
                self.assertEqual(raised.exception.code, 409)
                body = json.loads(raised.exception.read().decode())
                self.assertEqual(body["error"], "browser_frame_unavailable")
                self.assertFalse(body["secret_exposed_to_model"])
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

    def test_cross_process_browser_relay_acknowledges_input_events(self) -> None:
        class FakeBrowser:
            def __init__(self):
                self.events = []

            def current_url(self):
                return "https://example.com/working"

            def current_origin(self):
                return "https://example.com"

            def takeover_frame(self, *, frame_profile=None):
                return {
                    "frame_id": f"ack_{frame_profile}",
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

            def apply_user_input_event(self, event):
                self.events.append(event.event_type)
                return {"status": "event_applied"}

        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            browser = FakeBrowser()
            request = request_user_control(
                origin="https://example.com",
                top_level_url="https://example.com/working",
                reason="ack test",
                browser_context_id="ack-browser",
            )
            relay = start_browser_relay("ack-browser", browser, poll_interval=0.05)
            try:
                queued = enqueue_input_event("ack-browser", request.request_id, {"event_type": "type", "text": "sensitive-input"})
                result = wait_for_input_event_result("ack-browser", queued["event_id"], timeout_seconds=2)
                self.assertIsNotNone(result)
                assert result is not None
                self.assertEqual(result["status"], "event_applied")
                self.assertEqual(browser.events, ["type"])
                self.assertNotIn("sensitive-input", repr(result))
            finally:
                relay.stop()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_publish_browser_relay_tick_processes_preview_and_inputs_on_owner_thread(self) -> None:
        class FakeBrowser:
            def __init__(self):
                self.events = []
                self.frames = []

            def current_url(self):
                return "https://example.com/working"

            def current_origin(self):
                return "https://example.com"

            def takeover_frame(self, *, frame_profile=None):
                self.frames.append(frame_profile)
                return {
                    "frame_id": f"owner_{frame_profile}",
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

            def apply_user_input_event(self, event):
                self.events.append(event.event_type)
                return {"status": "event_applied"}

        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                from omnidoer.omni_takeover.cross_process import publish_browser_relay_tick

                browser = FakeBrowser()
                request = request_user_control(
                    origin="https://example.com",
                    top_level_url="https://example.com/working",
                    reason="owner thread relay",
                    browser_context_id="owner-browser",
                )
                queued = enqueue_input_event("owner-browser", request.request_id, {"event_type": "type", "text": "hidden"})
                publish_browser_relay_tick("owner-browser", browser)

                frame = read_frame("owner-browser", max_age_seconds=10)
                self.assertIsNotNone(frame)
                assert frame is not None
                self.assertEqual(frame["frame_id"], "owner_balanced")
                self.assertEqual(browser.frames, ["balanced"])
                result = wait_for_input_event_result("owner-browser", queued["event_id"], timeout_seconds=0.1)
                self.assertIsNotNone(result)
                assert result is not None
                self.assertEqual(result["status"], "event_applied")
                self.assertEqual(browser.events, ["type"])
                self.assertNotIn("hidden", repr(result))
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_publish_browser_relay_tick_can_force_preview_frames(self) -> None:
        class FakeBrowser:
            def __init__(self):
                self.frames = []

            def current_url(self):
                return "https://example.com/preview"

            def current_origin(self):
                return "https://example.com"

            def takeover_frame(self, *, frame_profile=None):
                self.frames.append(frame_profile)
                return {
                    "frame_id": f"preview_{len(self.frames)}",
                    "captured_at": 2000000000.0,
                    "url": "https://example.com/preview",
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
            try:
                from omnidoer.omni_takeover.cross_process import publish_browser_relay_tick

                browser = FakeBrowser()
                last_preview = publish_browser_relay_tick("preview-browser", browser)
                last_preview = publish_browser_relay_tick(
                    "preview-browser",
                    browser,
                    last_preview_frame_at=last_preview,
                )
                publish_browser_relay_tick(
                    "preview-browser",
                    browser,
                    last_preview_frame_at=last_preview,
                    force_preview_frame=True,
                )

                self.assertEqual(browser.frames, ["data_saver", "data_saver"])
                frame = read_frame("preview-browser", max_age_seconds=10)
                self.assertIsNotNone(frame)
                assert frame is not None
                self.assertEqual(frame["frame_id"], "preview_2")
            finally:
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
