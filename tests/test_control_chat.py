import json
import os
import stat
import tempfile
import time
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib import request as urllib_request
from unittest.mock import patch

from omnidoer.omni_control.chat import (
    MAX_CHAT_MESSAGES,
    MAX_CHAT_RECORDS,
    ChatStore,
    chat_message_is_cli_command,
    chat_text_is_cli_command,
)
from omnidoer.omni_control.chat_uploads import ChatUploadStore
from omnidoer.omni_control.server import (
    CHAT_STREAM_DEFAULT_SNAPSHOTS,
    CHAT_STREAM_HEARTBEAT_SECONDS,
    CHAT_STREAM_MAX_SNAPSHOTS,
    ControlHandler,
    _extract_latest_terminal_quota_lines,
    _terminal_quota_summary,
)
from omnidoer.omni_control.tui_legacy_relay import TmuxPane


class ControlChatStoreTest(unittest.TestCase):
    def test_chat_lifecycle_and_streaming_delta(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ChatStore(Path(tmp) / "chat.json")
            user = store.append(role="user", text="Hello from the client")
            self.assertEqual(stat.S_IMODE(store.path.stat().st_mode), 0o600)
            self.assertEqual(user.status, "queued")
            claimed = store.next_user_message()
            self.assertIsNotNone(claimed)
            assert claimed is not None
            self.assertEqual(claimed.message_id, user.message_id)
            self.assertEqual(claimed.status, "claimed")
            assistant = store.append(role="assistant", text="", status="streaming", reply_to_message_id=user.message_id)
            updated = store.append_delta(assistant.message_id, "Hi")
            self.assertEqual(updated.text, "Hi")
            completed = store.complete(assistant.message_id, text="Hi there")
            self.assertEqual(completed.status, "completed")
            self.assertEqual(completed.text, "Hi there")
            records = store.list_records()
            self.assertGreaterEqual(len(records), 5)
            self.assertEqual(records[-2].record_type, "delta")
            self.assertEqual(records[-2].text, "Hi")
            public = completed.to_public_dict()
            self.assertFalse(public["secret_fields_allowed"])
            self.assertFalse(public["control_client_calls_model"])

    def test_control_pause_and_continue_messages_have_delivery_priority(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ChatStore(Path(tmp) / "chat.json")
            older = store.append(role="user", text="normal queued message")
            continue_message = store.append(
                role="user",
                text="Continue Agent",
                client_message_id="control_continue_123",
            )
            cli_command = store.append(
                role="user",
                text="/status",
                client_message_id="control_cli_789",
            )
            pause = store.append(
                role="user",
                text="Pause Agent now",
                client_message_id="control_pause_456",
            )

            first = store.next_user_message()
            second = store.next_user_message()
            third = store.next_user_message()
            fourth = store.next_user_message()

            self.assertIsNotNone(first)
            self.assertIsNotNone(second)
            self.assertIsNotNone(third)
            self.assertIsNotNone(fourth)
            assert first is not None
            assert second is not None
            assert third is not None
            assert fourth is not None
            self.assertEqual(first.message_id, pause.message_id)
            self.assertEqual(second.message_id, continue_message.message_id)
            self.assertEqual(third.message_id, cli_command.message_id)
            self.assertEqual(fourth.message_id, older.message_id)

    def test_cli_command_detection_matches_mobile_slash_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ChatStore(Path(tmp) / "chat.json")
            message = store.append(role="user", text="  /status")
            prefixed = store.append(
                role="user",
                text="status",
                client_message_id="control_cli_123",
            )

            self.assertTrue(chat_text_is_cli_command("  /status"))
            self.assertTrue(chat_text_is_cli_command("/quota now"))
            self.assertFalse(chat_text_is_cli_command("please run /status"))
            self.assertTrue(chat_message_is_cli_command(message))
            self.assertTrue(chat_message_is_cli_command(prefixed))

    def test_chat_message_appends_attachment_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ChatStore(Path(tmp) / "chat.json")
            message = store.append(
                role="user",
                text="Please inspect this",
                attachments=[
                    {
                        "upload_id": "upl_demo",
                        "filename": "screen.png",
                        "path": "/tmp/omnidoer/screen.png",
                        "size": 1234,
                        "content_type": "image/png",
                        "created_at": 100.0,
                        "expires_at": 200.0,
                    }
                ],
            )
            self.assertIn("Please inspect this", message.text)
            self.assertIn("filename: screen.png", message.text)
            self.assertIn("path: /tmp/omnidoer/screen.png", message.text)
            self.assertIn("size: 1234 bytes", message.text)
            self.assertEqual(message.attachments[0]["filename"], "screen.png")

    def test_chat_records_are_pruned_to_about_five_screens(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ChatStore(Path(tmp) / "chat.json")
            for index in range(MAX_CHAT_RECORDS + 40):
                store.append_record(record_type="note", text=f"record {index}", role="system")
            records = store.list_records(limit=1000)
            self.assertLessEqual(len(records), MAX_CHAT_RECORDS)
            self.assertEqual(records[0].text, "record 40")
            self.assertEqual(records[-1].text, f"record {MAX_CHAT_RECORDS + 39}")

    def test_completed_chat_messages_are_pruned_to_recent_window(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ChatStore(Path(tmp) / "chat.json")
            for index in range(MAX_CHAT_MESSAGES + 20):
                message = store.append(role="user", text=f"done {index}")
                store.complete(message.message_id)
            messages = store.list(limit=1000)
            self.assertLessEqual(len(messages), MAX_CHAT_MESSAGES)
            self.assertEqual(messages[0].text, "done 20")
            self.assertEqual(messages[-1].text, f"done {MAX_CHAT_MESSAGES + 19}")


class ControlChatUploadStoreTest(unittest.TestCase):
    def test_upload_store_saves_and_cleans_expired_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ChatUploadStore(Path(tmp) / "uploads")
            upload = store.save(filename="../unsafe screen.png", content=b"demo", content_type="image/png", ttl_seconds=24 * 3600)
            path = Path(upload.path)
            self.assertTrue(path.exists())
            self.assertEqual(path.read_bytes(), b"demo")
            self.assertEqual(upload.filename, "unsafe_screen.png")
            self.assertEqual(upload.size, 4)
            old = time.time() - 25 * 3600
            os.utime(path, (old, old))
            self.assertEqual(store.cleanup_expired(ttl_seconds=24 * 3600), 1)
            self.assertFalse(path.exists())


class ControlChatApiTest(unittest.TestCase):
    def test_chat_stream_defaults_keep_mobile_realtime_connection_longer(self) -> None:
        self.assertEqual(CHAT_STREAM_DEFAULT_SNAPSHOTS, 1200)
        self.assertEqual(CHAT_STREAM_MAX_SNAPSHOTS, 1200)
        self.assertEqual(CHAT_STREAM_HEARTBEAT_SECONDS, 30.0)

    def test_terminal_quota_parser_returns_latest_status_block(self) -> None:
        snapshot = """
│  Context window:              70% left (80K used / 258K)            │
│  OmniDoer Usage limit:        80% left (resets 00:10)               │
╰─────────────────────────────────────────────────────────────────────╯

╭─────────────────────────────────────────────────────────────────────╮
│  Context window:              69% left (88.4K used / 258K)          │
│  OmniDoer Usage limit:        [████████████████████] 100% left      │
│                               (resets 01:21)                        │
│  GPT-5.3-Codex-Spark limit:                                         │
│  5h limit:                    [████████████████████] 100% left      │
│                               (resets 06:21)                        │
│  Weekly limit:                [████████████████████] 100% left      │
│                               (resets 01:21 on 10 Jun)              │
╰─────────────────────────────────────────────────────────────────────╯
"""
        self.assertEqual(
            _extract_latest_terminal_quota_lines(snapshot),
            [
                "Context window: 69% left (88.4K used / 258K)",
                "OmniDoer Usage limit: 100% left (resets 01:21)",
                "GPT-5.3-Codex-Spark limit:",
                "5h limit: 100% left (resets 06:21)",
                "Weekly limit: 100% left (resets 01:21 on 10 Jun)",
            ],
        )
        self.assertEqual(
            _terminal_quota_summary(_extract_latest_terminal_quota_lines(snapshot)),
            {
                "lines": [
                    "Context window: 69% left (88.4K used / 258K)",
                    "OmniDoer Usage limit: 100% left (resets 01:21)",
                    "GPT-5.3-Codex-Spark limit:",
                    "5h limit: 100% left (resets 06:21)",
                    "Weekly limit: 100% left (resets 01:21 on 10 Jun)",
                ],
                "omnidoer_percent_left": 100.0,
                "codex_5h_percent_left": 100.0,
                "codex_weekly_percent_left": 100.0,
            },
        )

    def test_status_api_includes_terminal_quota_percentages(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
        server.omnidoer_chat_thread_id = "thread_active"  # type: ignore[attr-defined]
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_address[1]}"
        terminal_snapshot = """
╭────────────────────────────────────────────────────────────╮
│  Context window:              69% left (88.4K used / 258K) │
│  OmniDoer Usage limit:        [████████████████████] 88% left │
│  5h limit:                    [████████████████████] 76% left │
│  Weekly limit:                [████████████████████] 54% left │
╰────────────────────────────────────────────────────────────╯
"""
        try:
            with patch(
                "omnidoer.omni_control.tui_legacy_relay.find_tmux_pane_for_thread",
                return_value=TmuxPane(pane_id="%1", tty="/dev/pts/2", current_command="codex", process_pid=99),
            ), patch(
                "omnidoer.omni_control.tui_legacy_relay.capture_tmux_pane",
                return_value=terminal_snapshot,
            ):
                with urllib_request.urlopen(f"{base}/api/status", timeout=5) as response:
                    self.assertEqual(response.status, 200)
                    payload = json.loads(response.read().decode())
            self.assertEqual(payload["quota"]["omnidoer_percent_left"], 88.0)
            self.assertEqual(payload["quota"]["codex_5h_percent_left"], 76.0)
            self.assertEqual(payload["quota"]["codex_weekly_percent_left"], 54.0)
        finally:
            server.shutdown()

    def test_chat_message_post_attempts_immediate_legacy_console_delivery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
            server.omnidoer_chat_thread_id = "thread_active"  # type: ignore[attr-defined]
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_address[1]}"
            pane = TmuxPane(pane_id="%1", tty="/dev/pts/2", current_command="codex", process_pid=99)
            injected: list[tuple[str, str]] = []
            try:
                create = urllib_request.Request(
                    f"{base}/api/chat/messages",
                    data=json.dumps({"text": "hello current console"}).encode(),
                    headers={"content-type": "application/json"},
                    method="POST",
                )
                with patch("omnidoer.omni_control.chat_runner.live_tui_bridge_active", return_value=False), patch(
                    "omnidoer.omni_control.tui_legacy_relay.live_tui_bridge_active",
                    return_value=False,
                ), patch(
                    "omnidoer.omni_control.tui_legacy_relay.find_tmux_pane_for_thread",
                    return_value=pane,
                ), patch(
                    "omnidoer.omni_control.tui_legacy_relay.inject_text_into_tmux_pane",
                    side_effect=lambda pane_id, text: injected.append((pane_id, text)),
                ):
                    with urllib_request.urlopen(create, timeout=5) as response:
                        self.assertEqual(response.status, 201)
                        message = json.loads(response.read().decode())

                self.assertEqual(injected, [("%1", "hello current console")])
                self.assertEqual(message["status"], "completed")
                self.assertTrue(message["delivered_to_agent"])
                self.assertEqual(message["live_console_delivery"]["attempted"], True)
                self.assertEqual(message["live_console_delivery"]["delivered"], True)
                self.assertEqual(message["live_console_delivery"]["pane_id"], "%1")
                records = ChatStore().list_records(limit=100)
                self.assertTrue(any(record.source == "legacy_tui_relay" for record in records))
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_chat_message_post_delivers_the_new_message_not_older_queue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
            server.omnidoer_chat_thread_id = "thread_active"  # type: ignore[attr-defined]
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_address[1]}"
            pane = TmuxPane(pane_id="%1", tty="/dev/pts/2", current_command="codex", process_pid=99)
            injected: list[tuple[str, str]] = []
            try:
                older = ChatStore().append(role="user", text="older queued message")
                create = urllib_request.Request(
                    f"{base}/api/chat/messages",
                    data=json.dumps({"text": "fresh phone message"}).encode(),
                    headers={"content-type": "application/json"},
                    method="POST",
                )
                with patch("omnidoer.omni_control.chat_runner.live_tui_bridge_active", return_value=False), patch(
                    "omnidoer.omni_control.tui_legacy_relay.live_tui_bridge_active",
                    return_value=False,
                ), patch(
                    "omnidoer.omni_control.tui_legacy_relay.find_tmux_pane_for_thread",
                    return_value=pane,
                ), patch(
                    "omnidoer.omni_control.tui_legacy_relay.inject_text_into_tmux_pane",
                    side_effect=lambda pane_id, text: injected.append((pane_id, text)),
                ):
                    with urllib_request.urlopen(create, timeout=5) as response:
                        self.assertEqual(response.status, 201)
                        message = json.loads(response.read().decode())

                self.assertEqual(injected, [("%1", "fresh phone message")])
                self.assertEqual(ChatStore().get(older.message_id).status, "queued")
                self.assertEqual(message["status"], "completed")
                self.assertEqual(message["live_console_delivery"]["delivered"], True)
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_mobile_status_slash_command_is_handled_locally_not_queued(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
            server.omnidoer_chat_thread_id = "thread_active"  # type: ignore[attr-defined]
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                create = urllib_request.Request(
                    f"{base}/api/chat/messages",
                    data=json.dumps({"text": "/status", "client_message_id": "control_cli_1"}).encode(),
                    headers={"content-type": "application/json"},
                    method="POST",
                )
                with urllib_request.urlopen(create, timeout=5) as response:
                    self.assertEqual(response.status, 201)
                    message = json.loads(response.read().decode())

                self.assertEqual(message["status"], "completed")
                self.assertEqual(message["live_console_delivery"]["reason"], "handled_by_control_service")
                self.assertEqual(message["live_console_delivery"]["submitted_to_model"], False)
                self.assertIn("cli_command_response", message)
                self.assertIn("OmniDoer status", message["cli_command_response"]["text"])
                self.assertIsNone(ChatStore().next_user_message())
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_mobile_status_slash_command_includes_terminal_quota_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
            server.omnidoer_chat_thread_id = "thread_active"  # type: ignore[attr-defined]
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_address[1]}"
            terminal_snapshot = """
╭────────────────────────────────────────────────────────────╮
│  Context window:              69% left (88.4K used / 258K) │
│  OmniDoer Usage limit:        [████████████████████] 100% left │
│                               (resets 01:21)              │
│  GPT-5.3-Codex-Spark limit:                               │
│  5h limit:                    [████████████████████] 100% left │
│                               (resets 06:21)              │
│  Weekly limit:                [████████████████████] 100% left │
│                               (resets 01:21 on 10 Jun)    │
╰────────────────────────────────────────────────────────────╯
"""
            try:
                create = urllib_request.Request(
                    f"{base}/api/chat/messages",
                    data=json.dumps({"text": "/status", "client_message_id": "control_cli_1"}).encode(),
                    headers={"content-type": "application/json"},
                    method="POST",
                )
                with patch(
                    "omnidoer.omni_control.tui_legacy_relay.find_tmux_pane_for_thread",
                    return_value=TmuxPane(pane_id="%1", tty="/dev/pts/2", current_command="codex", process_pid=99),
                ), patch(
                    "omnidoer.omni_control.tui_legacy_relay.capture_tmux_pane",
                    return_value=terminal_snapshot,
                ):
                    with urllib_request.urlopen(create, timeout=5) as response:
                        self.assertEqual(response.status, 201)
                        message = json.loads(response.read().decode())

                text = message["cli_command_response"]["text"]
                self.assertIn("Quota:", text)
                self.assertIn("Context window: 69% left (88.4K used / 258K)", text)
                self.assertIn("OmniDoer Usage limit: 100% left (resets 01:21)", text)
                self.assertIn("5h limit: 100% left (resets 06:21)", text)
                self.assertIn("Weekly limit: 100% left (resets 01:21 on 10 Jun)", text)
                self.assertIn("Model submission: false", text)
                self.assertIsNone(ChatStore().next_user_message())
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_mobile_unknown_slash_command_is_not_queued_when_bridge_needs_restart(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
            server.omnidoer_chat_thread_id = "thread_active"  # type: ignore[attr-defined]
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                create = urllib_request.Request(
                    f"{base}/api/chat/messages",
                    data=json.dumps({"text": "/resume thread_demo", "client_message_id": "control_cli_2"}).encode(),
                    headers={"content-type": "application/json"},
                    method="POST",
                )
                with patch("omnidoer.omni_control.chat_runner.live_tui_bridge_active", return_value=True), patch(
                    "omnidoer.omni_control.chat_runner.native_console_bridge_install_status",
                    return_value={"ready": True, "reason": "ready"},
                ), patch(
                    "omnidoer.omni_control.chat_runner.active_tui_process_bridge_status",
                    return_value={"active": True, "restart_required": True, "reason": "running_binary_deleted"},
                ):
                    with urllib_request.urlopen(create, timeout=5) as response:
                        self.assertEqual(response.status, 201)
                        message = json.loads(response.read().decode())

                self.assertEqual(message["status"], "completed")
                self.assertEqual(message["live_console_delivery"]["reason"], "running_binary_deleted")
                self.assertEqual(message["live_console_delivery"]["submitted_to_model"], False)
                self.assertIn("not sent to the model", message["cli_command_response"]["text"])
                self.assertIsNone(ChatStore().next_user_message())
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_mobile_model_slash_command_is_handled_locally_even_when_bridge_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
            server.omnidoer_chat_thread_id = "thread_active"  # type: ignore[attr-defined]
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                create = urllib_request.Request(
                    f"{base}/api/chat/messages",
                    data=json.dumps({"text": "/model", "client_message_id": "control_cli_model"}).encode(),
                    headers={"content-type": "application/json"},
                    method="POST",
                )
                with patch("omnidoer.omni_control.chat_runner.live_tui_bridge_active", return_value=True), patch(
                    "omnidoer.omni_control.chat_runner.native_console_bridge_install_status",
                    return_value={"ready": True, "reason": "ready"},
                ), patch(
                    "omnidoer.omni_control.chat_runner.active_tui_process_bridge_status",
                    return_value={"active": True, "restart_required": False, "reason": "ready"},
                ):
                    with urllib_request.urlopen(create, timeout=5) as response:
                        self.assertEqual(response.status, 201)
                        message = json.loads(response.read().decode())

                self.assertEqual(message["status"], "completed")
                self.assertEqual(message["live_console_delivery"]["reason"], "handled_by_control_service")
                self.assertEqual(message["live_console_delivery"]["submitted_to_model"], False)
                self.assertIn("mobile Control Client cannot render", message["cli_command_response"]["text"])
                self.assertIsNone(ChatStore().next_user_message())
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_control_server_chat_api_and_sse_stream(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                create = urllib_request.Request(
                    f"{base}/api/chat/messages",
                    data=json.dumps({"text": "Queue a chat message"}).encode(),
                    headers={"content-type": "application/json"},
                    method="POST",
                )
                with urllib_request.urlopen(create, timeout=5) as response:
                    self.assertEqual(response.status, 201)
                    message = json.loads(response.read().decode())
                self.assertEqual(message["role"], "user")
                self.assertEqual(message["status"], "queued")

                next_req = urllib_request.Request(
                    f"{base}/api/chat/messages/next",
                    data=json.dumps({"claim": True}).encode(),
                    headers={"content-type": "application/json"},
                    method="POST",
                )
                with urllib_request.urlopen(next_req, timeout=5) as response:
                    claimed = json.loads(response.read().decode())
                self.assertEqual(claimed["status"], "ok")
                self.assertEqual(claimed["message"]["status"], "claimed")

                assistant_req = urllib_request.Request(
                    f"{base}/api/chat/messages/assistant",
                    data=json.dumps({"text": "", "status": "streaming", "reply_to_message_id": message["message_id"]}).encode(),
                    headers={"content-type": "application/json"},
                    method="POST",
                )
                with urllib_request.urlopen(assistant_req, timeout=5) as response:
                    assistant = json.loads(response.read().decode())
                delta_req = urllib_request.Request(
                    f"{base}/api/chat/messages/{assistant['message_id']}/delta",
                    data=json.dumps({"delta": "streamed"}).encode(),
                    headers={"content-type": "application/json"},
                    method="POST",
                )
                with urllib_request.urlopen(delta_req, timeout=5) as response:
                    updated = json.loads(response.read().decode())
                self.assertEqual(updated["text"], "streamed")

                with urllib_request.urlopen(f"{base}/api/chat/messages", timeout=5) as response:
                    payload = json.loads(response.read().decode())
                self.assertEqual(len(payload["messages"]), 2)
                self.assertGreaterEqual(len(payload["records"]), 4)
                self.assertEqual(payload["records"][-1]["record_type"], "delta")
                self.assertFalse(payload["control_client_calls_model"])
                self.assertEqual(payload["retention"]["approx_screen_count"], 5)

                with urllib_request.urlopen(f"{base}/api/chat/events?stream=1&snapshots=1&interval=0", timeout=5) as response:
                    stream = response.read().decode()
                self.assertIn("event: chat", stream)
                self.assertIn("streamed", stream)

                with urllib_request.urlopen(f"{base}/api/chat/events?stream=1&snapshots=2&interval=0.01", timeout=5) as response:
                    unchanged_stream = response.read().decode()
                self.assertEqual(unchanged_stream.count("event: chat"), 1)

                with patch("omnidoer.omni_control.server.CHAT_STREAM_HEARTBEAT_SECONDS", 0.0):
                    with urllib_request.urlopen(f"{base}/api/chat/events?stream=1&snapshots=2&interval=0", timeout=5) as response:
                        heartbeat_stream = response.read().decode()
                self.assertEqual(heartbeat_stream.count("event: chat"), 1)
                self.assertIn("event: heartbeat", heartbeat_stream)
                self.assertIn('"secret_exposed_to_model":false', heartbeat_stream)
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_control_server_chat_attachment_upload_and_message_append(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
            server.omnidoer_chat_upload_ttl_seconds = 24 * 3600  # type: ignore[attr-defined]
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_address[1]}"
            boundary = "----omnidoer-test-boundary"
            body = (
                f"--{boundary}\r\n"
                'Content-Disposition: form-data; name="files"; filename="demo.png"\r\n'
                "Content-Type: image/png\r\n\r\n"
                "PNGDATA\r\n"
                f"--{boundary}--\r\n"
            ).encode()
            try:
                upload_req = urllib_request.Request(
                    f"{base}/api/chat/attachments",
                    data=body,
                    headers={"content-type": f"multipart/form-data; boundary={boundary}"},
                    method="POST",
                )
                with urllib_request.urlopen(upload_req, timeout=5) as response:
                    self.assertEqual(response.status, 201)
                    upload_payload = json.loads(response.read().decode())
                attachment = upload_payload["attachments"][0]
                self.assertEqual(attachment["filename"], "demo.png")
                self.assertEqual(attachment["size"], 7)
                self.assertTrue(Path(attachment["path"]).is_file())

                create = urllib_request.Request(
                    f"{base}/api/chat/messages",
                    data=json.dumps({"text": "Use this file", "attachments": [attachment]}).encode(),
                    headers={"content-type": "application/json"},
                    method="POST",
                )
                with urllib_request.urlopen(create, timeout=5) as response:
                    message = json.loads(response.read().decode())
                self.assertIn("Use this file", message["text"])
                self.assertIn("filename: demo.png", message["text"])
                self.assertIn("size: 7 bytes", message["text"])
                self.assertEqual(message["attachments"][0]["filename"], "demo.png")

                bad = urllib_request.Request(
                    f"{base}/api/chat/messages",
                    data=json.dumps(
                        {
                            "text": "bad path",
                            "attachments": [
                                {
                                    "filename": "shadow",
                                    "path": "/etc/shadow",
                                    "size": 1,
                                }
                            ],
                        }
                    ).encode(),
                    headers={"content-type": "application/json"},
                    method="POST",
                )
                with self.assertRaises(Exception):
                    urllib_request.urlopen(bad, timeout=5)
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home


if __name__ == "__main__":
    unittest.main()
