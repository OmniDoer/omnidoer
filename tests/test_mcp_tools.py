import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from threading import Thread
from pathlib import Path
from unittest.mock import patch

from omnidoer.omni_control.requests import RequestStore
from omnidoer.omni_control.tasks import TaskStore
from omnidoer.omni_mcp.tools import ALLOWED_TOOLS, call_tool, forbidden_tool_names
from omnidoer.omni_control.cloud import build_config
from omnidoer.omni_control.runtime import record_control_service_runtime


class McpToolsTest(unittest.TestCase):
    def test_allowed_tools_exclude_forbidden(self) -> None:
        self.assertTrue(forbidden_tool_names().isdisjoint(ALLOWED_TOOLS))
        self.assertIn("credential.request_from_user", ALLOWED_TOOLS)
        self.assertIn("credential.create_interactive", ALLOWED_TOOLS)
        self.assertIn("takeover.request_user_control", ALLOWED_TOOLS)
        self.assertIn("registration.request_user_handoff", ALLOWED_TOOLS)
        self.assertIn("browser.observe_accessibility", ALLOWED_TOOLS)
        self.assertIn("browser.select", ALLOWED_TOOLS)
        self.assertIn("browser.upload_file", ALLOWED_TOOLS)
        self.assertIn("control.create_pairing", ALLOWED_TOOLS)
        self.assertIn("control.wait_request", ALLOWED_TOOLS)
        self.assertIn("control.next_user_task", ALLOWED_TOOLS)
        self.assertIn("control.list_chat_messages", ALLOWED_TOOLS)
        self.assertIn("control.list_chat_records", ALLOWED_TOOLS)
        self.assertIn("control.next_user_message", ALLOWED_TOOLS)
        self.assertIn("control.publish_chat_record", ALLOWED_TOOLS)
        self.assertIn("control.publish_chat_message", ALLOWED_TOOLS)

    def test_tool_result_status_only(self) -> None:
        result = call_tool("credential.request_from_user", {})
        self.assertFalse(result["secret_exposed_to_model"])
        self.assertNotIn("password", result)

    def test_next_user_task_claims_local_control_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                task = TaskStore().create("Use OmniDoer tools on the local demo")
                result = call_tool("control.next_user_task", {})
                self.assertEqual(result["status"], "ok")
                self.assertEqual(result["task"]["task_id"], task.task_id)
                self.assertEqual(result["task"]["status"], "claimed")
                self.assertFalse(result["submitted_to_openai_api_by_control_client"])
                empty = call_tool("control.next_user_task", {})
                self.assertEqual(empty["status"], "empty")
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_chat_tools_claim_and_publish_messages_without_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                from omnidoer.omni_control.chat import ChatStore

                user = ChatStore().append(role="user", text="Hello")
                result = call_tool("control.next_user_message", {})
                self.assertEqual(result["status"], "ok")
                self.assertEqual(result["message"]["message_id"], user.message_id)
                self.assertFalse(result["secret_exposed_to_model"])
                published = call_tool("control.publish_chat_message", {"text": "Hi", "reply_to_message_id": user.message_id})
                self.assertEqual(published["status"], "ok")
                self.assertEqual(published["message"]["role"], "assistant")
                self.assertEqual(ChatStore().get(user.message_id).status, "completed")
                record = call_tool("control.publish_chat_record", {"record_type": "tool_call", "text": "control.next_user_message"})
                self.assertEqual(record["status"], "ok")
                self.assertEqual(record["record"]["record_type"], "tool_call")
                messages = call_tool("control.list_chat_messages", {})
                self.assertEqual(len(messages["messages"]), 2)
                self.assertGreaterEqual(len(messages["records"]), 3)
                self.assertFalse(messages["control_client_calls_model"])
                records = call_tool("control.list_chat_records", {})
                self.assertTrue(any(item["record_type"] == "tool_call" for item in records["records"]))
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_browser_tools_pause_while_user_takeover_is_active(self) -> None:
        class FakeBrowser:
            def current_origin(self):
                return "https://example.com"

            def current_url(self):
                return "https://example.com/paused"

        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                request = RequestStore().create(
                    "human_takeover",
                    origin="https://example.com",
                    top_level_url="https://example.com/paused",
                    action_summary="user took over browser",
                    browser_context_id="mcp-browser",
                )
                with patch("omnidoer.omni_mcp.runtime.get_browser", return_value=FakeBrowser()):
                    paused = call_tool("browser.current_origin", {"takeover_wait_timeout_seconds": 0})
                self.assertEqual(paused["status"], "paused_for_human_takeover")
                self.assertEqual(paused["request"]["request_id"], request.request_id)
                self.assertTrue(paused["resume_after_user_releases_control"])
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_browser_tools_resume_after_user_releases_control(self) -> None:
        class FakeBrowser:
            def current_origin(self):
                return "https://example.com"

            def current_url(self):
                return "https://example.com/resumed"

        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                request = RequestStore().create(
                    "human_takeover",
                    origin="https://example.com",
                    top_level_url="https://example.com/resumed",
                    action_summary="user took over browser",
                    browser_context_id="mcp-browser",
                )

                def release_later() -> None:
                    time.sleep(0.1)
                    RequestStore().release_takeover(request.request_id)

                Thread(target=release_later, daemon=True).start()
                with patch("omnidoer.omni_mcp.runtime.get_browser", return_value=FakeBrowser()):
                    result = call_tool("browser.current_origin", {"takeover_wait_timeout_seconds": 2})
                self.assertEqual(result["status"], "ok")
                self.assertEqual(result["origin"], "https://example.com")
                self.assertEqual(result["url"], "https://example.com/resumed")
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_browser_tools_process_takeover_input_while_waiting_for_release(self) -> None:
        class FakeBrowser:
            def __init__(self):
                self.events = []
                self.frames = []

            def current_origin(self):
                return "https://example.com"

            def current_url(self):
                return "https://example.com/takeover"

            def takeover_frame(self, *, frame_profile=None):
                self.frames.append(frame_profile)
                return {
                    "frame_id": f"mcp_{frame_profile}",
                    "captured_at": time.time(),
                    "url": self.current_url(),
                    "origin": self.current_origin(),
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
                from omnidoer.omni_takeover.cross_process import enqueue_input_event, read_frame

                browser = FakeBrowser()
                request = RequestStore().create(
                    "human_takeover",
                    origin="https://example.com",
                    top_level_url="https://example.com/takeover",
                    action_summary="user took over browser",
                    browser_context_id="mcp-browser",
                )
                enqueue_input_event("mcp-browser", request.request_id, {"event_type": "type", "text": "not logged"})

                def release_after_input() -> None:
                    deadline = time.time() + 2
                    while not browser.events and time.time() < deadline:
                        time.sleep(0.05)
                    RequestStore().release_takeover(request.request_id)

                Thread(target=release_after_input, daemon=True).start()
                with patch("omnidoer.omni_mcp.runtime.get_browser", return_value=browser):
                    result = call_tool("browser.current_origin", {"takeover_wait_timeout_seconds": 3})
                self.assertEqual(result["status"], "ok")
                self.assertEqual(browser.events, ["type"])
                frame = read_frame("mcp-browser", max_age_seconds=10)
                self.assertIsNotNone(frame)
                assert frame is not None
                self.assertIn("balanced", browser.frames)
                self.assertIn(frame["frame_id"], {"mcp_balanced", "mcp_data_saver"})
                self.assertNotIn("not logged", repr(result))
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_browser_detect_antibot_creates_takeover_request(self) -> None:
        class FakeBrowser:
            def current_origin(self):
                return "https://example.com"

            def current_url(self):
                return "https://example.com/antibot"

            def detect_antibot(self):
                return True

        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                with patch("omnidoer.omni_mcp.runtime.get_browser", return_value=FakeBrowser()):
                    result = call_tool("browser.detect_antibot", {})
                self.assertEqual(result["status"], "ok")
                self.assertTrue(result["requires_human_takeover"])
                self.assertTrue(result["agent_paused"])
                self.assertTrue(result["takeover_created"])
                self.assertFalse(result["reused"])
                self.assertEqual(result["request"]["request_type"], "human_takeover")
                self.assertEqual(result["request"]["browser_context_id"], "mcp-browser")
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_browser_open_auto_pauses_when_challenge_is_detected(self) -> None:
        class FakeBrowser:
            def __init__(self):
                self.url = "https://example.com/start"

            def open(self, url):
                self.url = url
                return {"status": "opened", "url": url, "secret_exposed_to_model": False}

            def current_origin(self):
                return "https://example.com"

            def current_url(self):
                return self.url

            def detect_challenge(self):
                return "captcha" if "captcha" in self.url else None

            def detect_antibot(self):
                return False

        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                browser = FakeBrowser()
                with patch("omnidoer.omni_mcp.runtime.get_browser", return_value=browser):
                    result = call_tool("browser.open", {"url": "https://example.com/captcha"})
                self.assertEqual(result["status"], "paused_for_human_takeover")
                self.assertEqual(result["browser_action"], "browser.open")
                self.assertEqual(result["browser_action_result"]["status"], "opened")
                self.assertEqual(result["challenge_type"], "captcha")
                self.assertFalse(result["antibot_detected"])
                self.assertTrue(result["requires_human_takeover"])
                self.assertTrue(result["agent_paused"])
                self.assertTrue(result["takeover_created"])
                self.assertFalse(result["reused"])
                self.assertEqual(result["request"]["request_type"], "human_takeover")
                self.assertEqual(result["request"]["browser_context_id"], "mcp-browser")
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_browser_open_publishes_preview_before_and_after_action(self) -> None:
        class FakeBrowser:
            def __init__(self):
                self.url = "https://example.com/start"
                self.frames = []

            def open(self, url):
                self.url = url
                return {"status": "opened", "url": url, "secret_exposed_to_model": False}

            def current_origin(self):
                return "https://example.com"

            def current_url(self):
                return self.url

            def detect_challenge(self):
                return None

            def detect_antibot(self):
                return False

            def takeover_frame(self, *, frame_profile=None):
                self.frames.append((frame_profile, self.url))
                return {
                    "frame_id": f"frame_{len(self.frames)}",
                    "captured_at": time.time(),
                    "url": self.current_url(),
                    "origin": self.current_origin(),
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
                from omnidoer.omni_takeover.cross_process import read_frame

                browser = FakeBrowser()
                with patch("omnidoer.omni_mcp.runtime.get_browser", return_value=browser):
                    result = call_tool("browser.open", {"url": "https://example.com/after"})
                self.assertEqual(result["status"], "opened")
                self.assertEqual(browser.frames[0], ("data_saver", "https://example.com/start"))
                self.assertEqual(browser.frames[-1], ("data_saver", "https://example.com/after"))
                frame = read_frame("mcp-browser", max_age_seconds=10)
                self.assertIsNotNone(frame)
                assert frame is not None
                self.assertEqual(frame["url"], "https://example.com/after")
                self.assertNotIn("abcd", repr(result))
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_browser_open_auto_pause_can_wait_until_user_releases_control(self) -> None:
        class FakeBrowser:
            def __init__(self):
                self.url = "https://example.com/start"

            def open(self, url):
                self.url = url
                return {"status": "opened", "url": url, "secret_exposed_to_model": False}

            def current_origin(self):
                return "https://example.com"

            def current_url(self):
                return self.url

            def detect_challenge(self):
                return None

            def detect_antibot(self):
                return "antibot" in self.url

            def takeover_frame(self, *, frame_profile=None):
                return {
                    "frame_id": f"auto_{frame_profile}",
                    "captured_at": time.time(),
                    "url": self.current_url(),
                    "origin": self.current_origin(),
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
                def release_created_takeover() -> None:
                    deadline = time.time() + 2
                    while time.time() < deadline:
                        active = [
                            req
                            for req in RequestStore().list()
                            if req.browser_context_id == "mcp-browser" and req.status == "user_control"
                        ]
                        if active:
                            RequestStore().release_takeover(active[0].request_id)
                            return
                        time.sleep(0.05)

                Thread(target=release_created_takeover, daemon=True).start()
                with patch("omnidoer.omni_mcp.runtime.get_browser", return_value=FakeBrowser()):
                    result = call_tool(
                        "browser.open",
                        {"url": "https://example.com/antibot", "wait": True, "takeover_wait_timeout_seconds": 3},
                    )
                self.assertEqual(result["status"], "takeover_released")
                self.assertEqual(result["browser_action"], "browser.open")
                self.assertTrue(result["antibot_detected"])
                self.assertTrue(result["takeover_created"])
                self.assertTrue(result["agent_resumed"])
                self.assertFalse(result["agent_paused"])
                self.assertTrue(result["completed_by_user"])
                self.assertNotIn("abcd", repr(result))
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_browser_detect_challenge_creates_takeover_request(self) -> None:
        class FakeBrowser:
            def current_origin(self):
                return "https://example.com"

            def current_url(self):
                return "https://example.com/captcha"

            def detect_challenge(self):
                return "captcha"

        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                with patch("omnidoer.omni_mcp.runtime.get_browser", return_value=FakeBrowser()):
                    result = call_tool("browser.detect_challenge", {})
                self.assertEqual(result["status"], "ok")
                self.assertEqual(result["challenge_type"], "captcha")
                self.assertTrue(result["requires_user_interaction"])
                self.assertTrue(result["requires_human_takeover"])
                self.assertTrue(result["agent_paused"])
                self.assertTrue(result["takeover_created"])
                self.assertFalse(result["reused"])
                self.assertEqual(result["request"]["request_type"], "human_takeover")
                self.assertEqual(result["request"]["browser_context_id"], "mcp-browser")
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_browser_detect_challenge_reuses_existing_takeover_request(self) -> None:
        class FakeBrowser:
            def current_origin(self):
                return "https://example.com"

            def current_url(self):
                return "https://example.com/captcha"

            def detect_challenge(self):
                return "captcha"

        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                request = RequestStore().create(
                    "human_takeover",
                    origin="https://example.com",
                    top_level_url="https://example.com/captcha",
                    action_summary="captcha requires user takeover",
                    browser_context_id="mcp-browser",
                )
                with patch("omnidoer.omni_mcp.runtime.get_browser", return_value=FakeBrowser()):
                    result = call_tool("browser.detect_challenge", {"takeover_wait_timeout_seconds": 0})
                self.assertEqual(result["status"], "ok")
                self.assertEqual(result["challenge_type"], "captcha")
                self.assertFalse(result["takeover_created"])
                self.assertTrue(result["reused"])
                self.assertEqual(result["request"]["request_id"], request.request_id)
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_browser_detect_challenge_can_wait_until_user_releases_takeover(self) -> None:
        class FakeBrowser:
            def current_origin(self):
                return "https://example.com"

            def current_url(self):
                return "https://example.com/captcha"

            def detect_challenge(self):
                return "captcha"

            def takeover_frame(self, *, frame_profile=None):
                return {
                    "frame_id": f"wait_{frame_profile}",
                    "captured_at": time.time(),
                    "url": self.current_url(),
                    "origin": self.current_origin(),
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
                def release_created_takeover() -> None:
                    deadline = time.time() + 2
                    while time.time() < deadline:
                        active = [
                            req
                            for req in RequestStore().list()
                            if req.browser_context_id == "mcp-browser" and req.status == "user_control"
                        ]
                        if active:
                            RequestStore().release_takeover(active[0].request_id)
                            return
                        time.sleep(0.05)

                Thread(target=release_created_takeover, daemon=True).start()
                with patch("omnidoer.omni_mcp.runtime.get_browser", return_value=FakeBrowser()):
                    result = call_tool("browser.detect_challenge", {"wait": True, "takeover_wait_timeout_seconds": 3})
                self.assertEqual(result["status"], "takeover_released")
                self.assertEqual(result["challenge_type"], "captcha")
                self.assertTrue(result["takeover_created"])
                self.assertTrue(result["agent_resumed"])
                self.assertFalse(result["agent_paused"])
                self.assertTrue(result["completed_by_user"])
                self.assertNotIn("abcd", repr(result))
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_create_pairing_tool_returns_reusable_invite_without_long_lived_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                result = call_tool(
                    "control.create_pairing",
                    {"public_url": "https://agent.example.com", "expires": "30m"},
                )
                self.assertEqual(result["status"], "pairing_created")
                self.assertRegex(result["pairing_code"], r"^\d{6}$")
                self.assertIn("https://agent.example.com/pair?code=", result["pairing_url"])
                self.assertNotIn("##", result["qr_ascii"])
                self.assertGreater(sum(result["qr_ascii"].count(ch) for ch in "█▀▄"), 100)
                self.assertFalse(result["one_time_pairing"])
                self.assertEqual(result["max_uses"], 10)
                self.assertEqual(result["remaining_uses"], 10)
                self.assertTrue(result["paired_sessions_are_cached"])
                self.assertTrue(result["pairing_code_model_visible"])
                self.assertFalse(result["secret_exposed_to_model"])
                self.assertNotIn("session_token", repr(result))
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_create_pairing_tool_uses_running_control_service_public_url(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            old_public_url = os.environ.get("OMNIDOER_CONTROL_PUBLIC_URL")
            os.environ["OMNIDOER_HOME"] = tmp
            os.environ.pop("OMNIDOER_CONTROL_PUBLIC_URL", None)
            try:
                record_control_service_runtime(
                    build_config(
                        host="0.0.0.0",
                        port=8787,
                        cloud_direct=True,
                        public_url="https://agent.example.com",
                        tls_self_signed_dev=True,
                    )
                )
                result = call_tool("control.create_pairing", {"expires": "30m"})
                self.assertEqual(result["status"], "pairing_created")
                self.assertRegex(result["pairing_code"], r"^\d{6}$")
                self.assertIn("https://agent.example.com/pair?code=", result["pairing_url"])
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home
                if old_public_url is None:
                    os.environ.pop("OMNIDOER_CONTROL_PUBLIC_URL", None)
                else:
                    os.environ["OMNIDOER_CONTROL_PUBLIC_URL"] = old_public_url

    def test_wait_request_returns_after_control_client_submission_without_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                store = RequestStore(Path(tmp) / "control_requests.json")
                request = store.create(
                    "credential",
                    origin="https://github.com",
                    top_level_url="https://github.com/settings/tokens",
                    action_summary="Migrate PAT",
                )

                def submit_later() -> None:
                    time.sleep(0.2)
                    store.submit_ciphertext(request.request_id, {"ciphertext": "secret-never-echo"})

                worker = Thread(target=submit_later)
                worker.start()
                result = call_tool(
                    "control.wait_request",
                    {"request_id": request.request_id, "timeout": "2s", "require_ciphertext": True},
                )
                worker.join(timeout=2)
                self.assertEqual(result["status"], "ok")
                self.assertTrue(result["completed_by_user"])
                self.assertTrue(result["has_ciphertext"])
                self.assertNotIn("secret-never-echo", repr(result))
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_request_tools_create_control_requests_without_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                common = {"origin": "http://127.0.0.1:8765", "top_level_url": "http://127.0.0.1:8765/login"}
                credential = call_tool(
                    "credential.request_from_user",
                    {**common, "reason": "login", "fields": ["username", "password"]},
                )
                self.assertEqual(credential["status"], "credential_request_created")
                self.assertNotIn("super-secret", repr(credential))

                interactive = call_tool(
                    "credential.create_interactive",
                    {**common, "reason": "first login", "fields": ["username", "password"]},
                )
                self.assertEqual(interactive["status"], "credential_request_created")
                self.assertEqual(interactive["request"]["request_type"], "credential")
                self.assertNotIn("password_value", repr(interactive))

                pat = call_tool(
                    "credential.request_from_user",
                    {
                        **common,
                        "reason": "GitHub token migration",
                        "fields": ["username", "password"],
                        "password_label": "GitHub PAT",
                    },
                )
                self.assertEqual(pat["status"], "credential_request_created")
                self.assertEqual(pat["request"]["requested_fields"], ["username", "password"])
                self.assertEqual(pat["request"]["structured_details"]["credential_labels"]["password"], "GitHub PAT")
                self.assertNotIn("token-value", repr(pat))

                challenge = call_tool(
                    "challenge.request_user_interaction",
                    {**common, "challenge_type": "sms", "reason": "verify user"},
                )
                self.assertEqual(challenge["status"], "challenge_request_created")
                status = call_tool("challenge.status", {"request_id": challenge["request"]["request_id"]})
                self.assertEqual(status["status"], "pending")
                self.assertNotIn("code", status)

                takeover = call_tool("takeover.request_user_control", {**common, "reason": "anti-bot page"})
                self.assertEqual(takeover["status"], "takeover_request_created")
                self.assertTrue(takeover["takeover_created"])
                self.assertFalse(takeover["reused"])
                takeover_status = call_tool("takeover.status", {"request_id": takeover["request"]["request_id"]})
                self.assertEqual(takeover_status["control_owner"], "user")
                repeated_takeover = call_tool("takeover.request_user_control", {**common, "reason": "anti-bot page"})
                self.assertEqual(repeated_takeover["status"], "takeover_request_active")
                self.assertFalse(repeated_takeover["takeover_created"])
                self.assertTrue(repeated_takeover["reused"])
                self.assertEqual(repeated_takeover["request"]["request_id"], takeover["request"]["request_id"])
                repeated_without_origin = call_tool("takeover.request_user_control", {})
                self.assertEqual(repeated_without_origin["status"], "takeover_request_active")
                self.assertTrue(repeated_without_origin["reused"])
                self.assertEqual(repeated_without_origin["request"]["request_id"], takeover["request"]["request_id"])
                RequestStore().release_takeover(takeover["request"]["request_id"])

                registration = call_tool(
                    "registration.request_user_handoff",
                    {**common, "top_level_url": "http://127.0.0.1:8765/register", "reason": "new account required"},
                )
                self.assertEqual(registration["status"], "registration_handoff_created")
                self.assertEqual(registration["request"]["request_type"], "account_registration")
                self.assertTrue(registration["handoff_created"])
                self.assertFalse(registration["reused"])
                self.assertTrue(registration["agent_paused"])
                repeated_registration = call_tool(
                    "registration.request_user_handoff",
                    {**common, "top_level_url": "http://127.0.0.1:8765/register", "reason": "new account required"},
                )
                self.assertEqual(repeated_registration["status"], "registration_handoff_active")
                self.assertFalse(repeated_registration["handoff_created"])
                self.assertTrue(repeated_registration["reused"])
                self.assertEqual(repeated_registration["request"]["request_id"], registration["request"]["request_id"])
                self.assertNotIn("password", repr(registration))

                approval = call_tool(
                    "approval.request",
                    {**common, "action_summary": "mock payment", "risk_level": "high", "structured_details": {"amount": "12.34"}},
                )
                self.assertEqual(approval["status"], "approval_request_created")
                self.assertEqual(approval["request"]["structured_details"]["amount"], "12.34")
                payment = call_tool("payment.prepare_review", common)
                self.assertTrue(payment["requires_user_approval"])
                policy = call_tool("policy.explain_current_block", {"action_type": "account_registration"})
                self.assertEqual(policy["decision"], "require_takeover")
                self.assertIn("registration", policy["reason"])
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_takeover_request_tool_can_wait_until_user_releases_control(self) -> None:
        class FakeBrowser:
            def __init__(self):
                self.events = []
                self.frames = []

            def current_origin(self):
                return "https://example.com"

            def current_url(self):
                return "https://example.com/antibot"

            def takeover_frame(self, *, frame_profile=None):
                self.frames.append(frame_profile)
                return {
                    "frame_id": f"explicit_{frame_profile}",
                    "captured_at": time.time(),
                    "url": self.current_url(),
                    "origin": self.current_origin(),
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
                from omnidoer.omni_takeover.cross_process import enqueue_input_event, read_frame

                browser = FakeBrowser()

                def release_created_takeover() -> None:
                    deadline = time.time() + 2
                    queued = False
                    while time.time() < deadline:
                        active = [
                            req
                            for req in RequestStore().list()
                            if req.browser_context_id == "mcp-browser" and req.status == "user_control"
                        ]
                        if active:
                            if not queued:
                                enqueue_input_event("mcp-browser", active[0].request_id, {"event_type": "type", "text": "not logged"})
                                queued = True
                            if browser.events:
                                RequestStore().release_takeover(active[0].request_id)
                                return
                        time.sleep(0.05)

                Thread(target=release_created_takeover, daemon=True).start()
                with patch("omnidoer.omni_mcp.runtime.current_browser", return_value=browser):
                    result = call_tool(
                        "takeover.request_user_control",
                        {
                            "origin": "https://example.com",
                            "top_level_url": "https://example.com/antibot",
                            "reason": "user takeover required",
                            "wait": True,
                            "takeover_wait_timeout_seconds": 3,
                        },
                    )
                self.assertEqual(result["status"], "takeover_released")
                self.assertTrue(result["takeover_created"])
                self.assertFalse(result["reused"])
                self.assertTrue(result["agent_resumed"])
                self.assertFalse(result["agent_paused"])
                self.assertTrue(result["completed_by_user"])
                self.assertEqual(browser.events, ["type"])
                self.assertIn("balanced", browser.frames)
                frame = read_frame("mcp-browser", max_age_seconds=10)
                self.assertIsNotNone(frame)
                assert frame is not None
                self.assertEqual(frame["frame_id"], "explicit_balanced")
                self.assertNotIn("not logged", repr(result))
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_mcp_self_test_command(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "omnidoer.omni_cli.main", "mcp", "serve", "--self-test"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("mcp self-test passed", result.stdout)

    def test_mcp_initialize_returns_standard_capabilities(self) -> None:
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2025-06-18"},
        }
        result = subprocess.run(
            [sys.executable, "-m", "omnidoer.omni_cli.main", "mcp", "serve"],
            input=json.dumps(request) + "\n",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=5,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        response = json.loads(result.stdout)
        self.assertEqual(response["id"], 1)
        self.assertEqual(response["result"]["protocolVersion"], "2025-06-18")
        self.assertIn("capabilities", response["result"])
        self.assertIn("tools", response["result"]["capabilities"])
        self.assertEqual(response["result"]["serverInfo"]["name"], "omnidoer")


if __name__ == "__main__":
    unittest.main()
