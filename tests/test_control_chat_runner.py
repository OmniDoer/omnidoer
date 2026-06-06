import json
import os
import stat
import tempfile
import textwrap
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from omnidoer.omni_control.chat import ChatStore
from omnidoer.omni_control.chat_runner import (
    ChatRunner,
    active_mcp_sidecar_status,
    active_tui_process_bridge_status,
    browser_takeover_readiness,
    control_chat_sync_diagnostics,
    live_tui_bridge_active,
    live_tui_session_active,
    native_console_bridge_install_status,
    tui_bridge_heartbeat_age_seconds,
    tui_bridge_heartbeat_status,
)


class ControlChatRunnerTest(unittest.TestCase):
    def test_chat_runner_defers_to_live_tui_bridge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            old_thread = os.environ.pop("OMNIDOER_CHAT_THREAD_ID", None)
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                heartbeat = Path(tmp) / "control_chat_bridge_heartbeat"
                heartbeat.write_text("live")
                store = ChatStore()
                user = store.append(role="user", text="Use the active TUI")

                self.assertTrue(live_tui_bridge_active())
                self.assertTrue(live_tui_bridge_active("thread_active"))
                self.assertIsNone(ChatRunner(codex_bin="/does/not/exist", cwd=tmp).run_once())
                self.assertEqual(store.get(user.message_id).status, "queued")
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home
                if old_thread is not None:
                    os.environ["OMNIDOER_CHAT_THREAD_ID"] = old_thread

    def test_structured_tui_bridge_heartbeat_is_thread_bound(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                heartbeat = Path(tmp) / "control_chat_bridge_heartbeat"
                heartbeat.write_text(
                    json.dumps(
                        {
                            "version": 1,
                            "pid": 1234,
                            "thread_id": "thread_active",
                            "updated_at_ms": 123456,
                        }
                    )
                )
                now = time.time()
                os.utime(heartbeat, (now, now))

                self.assertTrue(live_tui_bridge_active("thread_active", now=now + 1))
                self.assertFalse(live_tui_bridge_active("other_thread", now=now + 1))
                self.assertTrue(live_tui_bridge_active(now=now + 1))

                status = tui_bridge_heartbeat_status("other_thread", now=now + 1)
                self.assertFalse(status["active"])
                self.assertEqual(status["reason"], "thread_mismatch")
                self.assertEqual(status["thread_id"], "thread_active")
                self.assertFalse(status["thread_matches"])
                self.assertEqual(status["pid"], 1234)
                self.assertEqual(status["format"], "json")
                self.assertIsNotNone(tui_bridge_heartbeat_age_seconds("other_thread", now=now + 1))
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_chat_runner_defers_to_live_interactive_tui_for_thread(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                proc_root = Path(tmp) / "proc"
                proc_root.mkdir()
                tui = proc_root / "1234"
                tui.mkdir()
                tui.joinpath("cmdline").write_bytes(
                    b"/usr/local/lib/omnidoer/codex\0resume\0thread_active\0"
                )
                exec_runner = proc_root / "5678"
                exec_runner.mkdir()
                exec_runner.joinpath("cmdline").write_bytes(
                    b"/usr/local/lib/omnidoer/codex\0exec\0resume\0--json\0thread_active\0"
                )

                store = ChatStore()
                user = store.append(role="user", text="Keep this for the active TUI")

                self.assertTrue(live_tui_session_active("thread_active", proc_root=proc_root))
                self.assertFalse(live_tui_session_active("other_thread", proc_root=proc_root))
                runner = ChatRunner(codex_bin="/does/not/exist", cwd=tmp, thread_id="thread_active")
                with patch("omnidoer.omni_control.chat_runner.live_tui_session_active", return_value=True):
                    self.assertIsNone(runner.run_once())
                self.assertEqual(store.get(user.message_id).status, "queued")
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_bound_thread_runner_defers_without_explicit_detached_resume(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                store = ChatStore()
                user = store.append(role="user", text="Do not launch a detached thread")

                runner = ChatRunner(
                    store=store,
                    codex_bin="/does/not/exist",
                    cwd=tmp,
                    thread_id="thread_active",
                )
                with patch("omnidoer.omni_control.chat_runner.live_tui_session_active", return_value=False):
                    self.assertIsNone(runner.run_once())
                self.assertEqual(store.get(user.message_id).status, "queued")
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_chat_runner_does_not_send_cli_commands_to_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            old_thread = os.environ.pop("OMNIDOER_CHAT_THREAD_ID", None)
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                fake_codex = Path(tmp) / "fake-codex"
                fake_codex.write_text("#!/bin/sh\necho should-not-run > ran\n")
                fake_codex.chmod(fake_codex.stat().st_mode | stat.S_IXUSR)

                store = ChatStore()
                user = store.append(
                    role="user",
                    text="/status",
                    client_message_id="control_cli_123",
                )
                result = ChatRunner(store=store, codex_bin=str(fake_codex), cwd=tmp).run_once()

                self.assertIsNotNone(result)
                assert result is not None
                self.assertEqual(result.source, "control_service")
                self.assertIn("not sent to the model", result.text)
                self.assertFalse((Path(tmp) / "ran").exists())
                self.assertEqual(store.get(user.message_id).status, "completed")
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home
                if old_thread is not None:
                    os.environ["OMNIDOER_CHAT_THREAD_ID"] = old_thread

    def test_native_console_bridge_install_status_detects_required_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            binary = Path(tmp) / "codex"
            binary.write_bytes(
                b"prefix control_chat_bridge_heartbeat middle chat-log-user suffix "
                b"failed to publish OmniDoer user chat message"
            )
            binary.chmod(binary.stat().st_mode | stat.S_IXUSR)

            ready = native_console_bridge_install_status(str(binary))
            self.assertTrue(ready["ready"])
            self.assertEqual(ready["reason"], "ready")

            old = Path(tmp) / "old-codex"
            old.write_bytes(b"control_chat_bridge_heartbeat")
            old.chmod(old.stat().st_mode | stat.S_IXUSR)
            stale = native_console_bridge_install_status(str(old))
            self.assertFalse(stale["ready"])
            self.assertEqual(stale["reason"], "missing_bridge_markers")
            self.assertIn("chat-log-user", stale["missing_markers"])

    def test_active_tui_process_bridge_status_reports_stale_running_binary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proc_root = Path(tmp) / "proc"
            proc_root.mkdir()
            tui = proc_root / "1234"
            tui.mkdir()
            tui.joinpath("cmdline").write_bytes(
                b"/usr/local/lib/omnidoer/codex\0resume\0thread_active\0"
            )
            tui.joinpath("exe").write_bytes(b"old codex without bridge")
            installed = Path(tmp) / "codex"
            installed.write_bytes(
                b"control_chat_bridge_heartbeat chat-log-user "
                b"failed to publish OmniDoer user chat message"
            )
            installed.chmod(installed.stat().st_mode | stat.S_IXUSR)

            status = active_tui_process_bridge_status(
                "thread_active",
                proc_root=proc_root,
                codex_bin=str(installed),
            )

            self.assertTrue(status["active"])
            self.assertEqual(status["pid"], 1234)
            self.assertFalse(status["native_bridge_ready"])
            self.assertTrue(status["installed_bridge_ready"])
            self.assertTrue(status["restart_required"])
            self.assertEqual(status["reason"], "running_binary_missing_bridge_markers")

    def test_active_mcp_sidecar_status_reports_source_updated_after_start(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proc_root = Path(tmp) / "proc"
            proc_root.mkdir()
            proc_root.joinpath("stat").write_text("btime 1000\n")
            ticks = os.sysconf("SC_CLK_TCK")

            tui = proc_root / "1234"
            tui.mkdir()
            tui.joinpath("cmdline").write_bytes(b"/usr/local/lib/omnidoer/codex\0resume\0thread_active\0")
            tui.joinpath("stat").write_text(f"1234 (codex) S 1 {'0 ' * 17}{int(5 * ticks)} 0\n")

            sidecar = proc_root / "1235"
            sidecar.mkdir()
            sidecar.joinpath("cmdline").write_bytes(b"/usr/bin/python3\0/usr/local/bin/omnidoer\0mcp\0serve\0")
            sidecar.joinpath("stat").write_text(f"1235 (python3) S 1234 {'0 ' * 17}{int(6 * ticks)} 0\n")

            source = Path(tmp) / "runtime.py"
            source.write_text("updated source")
            os.utime(source, (1010, 1010))

            status = active_mcp_sidecar_status(
                "thread_active",
                proc_root=proc_root,
                source_files=(source,),
            )

            self.assertTrue(status["active"])
            self.assertEqual(status["pid"], 1235)
            self.assertEqual(status["parent_tui_pid"], 1234)
            self.assertTrue(status["restart_required"])
            self.assertFalse(status["browser_takeover_relay_current"])
            self.assertEqual(status["reason"], "source_updated_after_sidecar_start")
            self.assertEqual(status["stale_required_sources"], [str(source)])

    def test_active_mcp_sidecar_status_reports_current_relay_feature(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proc_root = Path(tmp) / "proc"
            proc_root.mkdir()
            proc_root.joinpath("stat").write_text("btime 1000\n")
            ticks = os.sysconf("SC_CLK_TCK")

            tui = proc_root / "1234"
            tui.mkdir()
            tui.joinpath("cmdline").write_bytes(b"/usr/local/lib/omnidoer/codex\0resume\0thread_active\0")
            tui.joinpath("stat").write_text(f"1234 (codex) S 1 {'0 ' * 17}{int(20 * ticks)} 0\n")

            sidecar = proc_root / "1235"
            sidecar.mkdir()
            sidecar.joinpath("cmdline").write_bytes(b"/usr/bin/python3\0/usr/local/bin/omnidoer\0mcp\0serve\0")
            sidecar.joinpath("stat").write_text(f"1235 (python3) S 1234 {'0 ' * 17}{int(21 * ticks)} 0\n")

            source = Path(tmp) / "runtime.py"
            source.write_text("BrowserContextWorker start_control_relay publish_browser_relay_tick apply_user_input_event")
            os.utime(source, (1010, 1010))

            status = active_mcp_sidecar_status(
                "thread_active",
                proc_root=proc_root,
                source_files=(source,),
                feature_markers={source: (b"BrowserContextWorker", b"start_control_relay")},
            )

            self.assertTrue(status["active"])
            self.assertFalse(status["restart_required"])
            self.assertTrue(status["browser_takeover_relay_feature_installed"])
            self.assertTrue(status["browser_takeover_relay_current"])
            self.assertEqual(status["reason"], "ready")
            self.assertEqual(status["required_sources"]["feature_marker_count"], 2)
            self.assertEqual(status["required_sources"]["missing_feature_markers"], [])

    def test_active_mcp_sidecar_status_reports_missing_relay_feature_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proc_root = Path(tmp) / "proc"
            proc_root.mkdir()
            proc_root.joinpath("stat").write_text("btime 1000\n")
            ticks = os.sysconf("SC_CLK_TCK")

            tui = proc_root / "1234"
            tui.mkdir()
            tui.joinpath("cmdline").write_bytes(b"/usr/local/lib/omnidoer/codex\0resume\0thread_active\0")
            tui.joinpath("stat").write_text(f"1234 (codex) S 1 {'0 ' * 17}{int(20 * ticks)} 0\n")

            sidecar = proc_root / "1235"
            sidecar.mkdir()
            sidecar.joinpath("cmdline").write_bytes(b"/usr/bin/python3\0/usr/local/bin/omnidoer\0mcp\0serve\0")
            sidecar.joinpath("stat").write_text(f"1235 (python3) S 1234 {'0 ' * 17}{int(21 * ticks)} 0\n")

            source = Path(tmp) / "runtime.py"
            source.write_text("old runtime")
            os.utime(source, (1010, 1010))

            status = active_mcp_sidecar_status(
                "thread_active",
                proc_root=proc_root,
                source_files=(source,),
                feature_markers={source: (b"BrowserContextWorker",)},
            )

            self.assertTrue(status["active"])
            self.assertFalse(status["restart_required"])
            self.assertFalse(status["browser_takeover_relay_feature_installed"])
            self.assertFalse(status["browser_takeover_relay_current"])
            self.assertEqual(status["reason"], "browser_takeover_relay_feature_missing")
            self.assertEqual(
                status["required_sources"]["missing_feature_markers"],
                [{"path": str(source), "marker": "BrowserContextWorker"}],
            )

    def test_control_chat_sync_diagnostics_describes_legacy_and_native_states(self) -> None:
        legacy = control_chat_sync_diagnostics(
            thread_id="thread_demo",
            tui_bridge_active=False,
            tui_session_active=True,
            install_status={"ready": True},
            legacy_relay={"active": True},
            active_process_bridge={
                "native_bridge_ready": False,
                "executable_deleted": True,
                "running_binary_matches_installed": False,
                "reason": "running_binary_deleted",
            },
            mcp_sidecar={"active": True, "restart_required": True, "reason": "source_updated_after_sidecar_start"},
            bridge_heartbeat_age_seconds=None,
        )
        self.assertEqual(legacy["state"], "legacy_terminal_relay")
        self.assertTrue(legacy["current_cli_reachable"])
        self.assertFalse(legacy["current_cli_context_attached"])
        self.assertEqual(legacy["phone_to_current_cli_delivery"], "terminal_relay")
        self.assertTrue(legacy["restart_ready"])
        self.assertTrue(legacy["restart_current_console_available"])
        self.assertFalse(legacy["manual_resume_available"])
        self.assertTrue(legacy["mcp_sidecar_active"])
        self.assertTrue(legacy["requires_restart_for_browser_takeover_relay"])
        self.assertFalse(legacy["restart_browser_takeover_relay_available"])

        native_with_stale_sidecar = control_chat_sync_diagnostics(
            thread_id="thread_demo",
            tui_bridge_active=True,
            tui_session_active=True,
            install_status={"ready": True},
            legacy_relay={"active": False},
            active_process_bridge={"native_bridge_ready": True, "running_binary_matches_installed": True},
            mcp_sidecar={"active": True, "restart_required": True, "reason": "source_updated_after_sidecar_start"},
            bridge_heartbeat_age_seconds=0.2,
        )
        self.assertTrue(native_with_stale_sidecar["native_sync_active"])
        self.assertTrue(native_with_stale_sidecar["requires_restart_for_browser_takeover_relay"])
        self.assertTrue(native_with_stale_sidecar["restart_browser_takeover_relay_available"])
        self.assertFalse(native_with_stale_sidecar["browser_takeover_relay_feature_installed"])
        self.assertIsNone(native_with_stale_sidecar["browser_takeover_relay_verification_signal"])
        self.assertFalse(native_with_stale_sidecar["requires_restart_for_native_sync"])
        self.assertEqual(legacy["activation_action"], "restart_current_console")
        self.assertEqual(legacy["activation_blocker"], "running_binary_deleted")
        self.assertFalse(legacy["native_sync_active"])
        self.assertFalse(legacy["detached_thread_resume_allowed"])
        self.assertFalse(legacy["active_cli_binary_has_native_bridge"])
        self.assertTrue(legacy["active_cli_binary_deleted"])
        self.assertEqual(legacy["active_cli_binary_reason"], "running_binary_deleted")

        manual_resume = control_chat_sync_diagnostics(
            thread_id="thread_demo",
            tui_bridge_active=False,
            tui_session_active=False,
            install_status={"ready": True},
            legacy_relay={"active": False},
            active_process_bridge={"active": False, "reason": "live_tui_process_not_found"},
        )
        self.assertEqual(manual_resume["state"], "bound_thread_without_live_cli")
        self.assertFalse(manual_resume["restart_ready"])
        self.assertFalse(manual_resume["restart_current_console_available"])
        self.assertTrue(manual_resume["manual_resume_available"])
        self.assertEqual(manual_resume["activation_action"], "manual_resume_console")

        native = control_chat_sync_diagnostics(
            thread_id="thread_demo",
            tui_bridge_active=True,
            tui_session_active=True,
            install_status={"ready": True},
            legacy_relay={"active": False},
            bridge_heartbeat_age_seconds=0.2,
        )
        self.assertEqual(native["state"], "native_bridge_active")
        self.assertTrue(native["native_sync_active"])
        self.assertTrue(native["current_cli_context_attached"])
        self.assertEqual(native["current_cli_to_phone_stream"], "structured_records")
        self.assertFalse(native["requires_restart_for_native_sync"])
        self.assertEqual(native["activation_action"], "none")
        self.assertEqual(native["verification_signal"], "control_chat_bridge_heartbeat")
        self.assertFalse(native["detached_thread_resume_allowed"])

        native_with_current_relay = control_chat_sync_diagnostics(
            thread_id="thread_demo",
            tui_bridge_active=True,
            tui_session_active=True,
            install_status={"ready": True},
            legacy_relay={"active": False},
            mcp_sidecar={
                "active": True,
                "restart_required": False,
                "browser_takeover_relay_feature_installed": True,
                "browser_takeover_relay_current": True,
                "reason": "ready",
            },
            bridge_heartbeat_age_seconds=0.2,
        )
        self.assertTrue(native_with_current_relay["browser_takeover_relay_feature_installed"])
        self.assertTrue(native_with_current_relay["browser_takeover_relay_current"])
        self.assertEqual(
            native_with_current_relay["browser_takeover_relay_verification_signal"],
            "mcp_sidecar_feature_markers_and_start_time",
        )

    def test_browser_takeover_readiness_separates_sync_and_relay_states(self) -> None:
        needs_sync = browser_takeover_readiness(
            diagnostics={
                "thread_bound": True,
                "native_sync_active": False,
                "requires_restart_for_native_sync": True,
                "current_cli_reachable": True,
            },
            mcp_sidecar={"active": True},
        )
        self.assertFalse(needs_sync["ready"])
        self.assertEqual(needs_sync["state"], "needs_current_session_sync")
        self.assertTrue(needs_sync["requires_current_session_sync"])
        self.assertEqual(needs_sync["frame_stream"], "unavailable")

        needs_agent_restart = browser_takeover_readiness(
            diagnostics={
                "thread_bound": True,
                "native_sync_active": True,
                "current_cli_reachable": True,
                "mcp_sidecar_active": True,
                "mcp_sidecar_restart_required": True,
                "requires_restart_for_browser_takeover_relay": True,
                "browser_takeover_relay_feature_installed": True,
            },
            mcp_sidecar={"active": True, "restart_required": True},
        )
        self.assertFalse(needs_agent_restart["ready"])
        self.assertEqual(needs_agent_restart["state"], "needs_agent_restart")
        self.assertTrue(needs_agent_restart["requires_agent_restart"])
        self.assertEqual(needs_agent_restart["phone_to_browser_input"], "available_after_agent_restart")

        ready = browser_takeover_readiness(
            diagnostics={
                "thread_bound": True,
                "native_sync_active": True,
                "current_cli_reachable": True,
                "mcp_sidecar_active": True,
                "browser_takeover_relay_current": True,
            },
            mcp_sidecar={"active": True, "browser_takeover_relay_current": True},
        )
        self.assertTrue(ready["ready"])
        self.assertEqual(ready["state"], "ready")
        self.assertEqual(ready["frame_stream"], "ready")
        self.assertEqual(ready["verification_signal"], "mcp_sidecar_feature_markers_and_start_time")

    def test_codex_json_events_stream_into_chat_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            old_thread = os.environ.pop("OMNIDOER_CHAT_THREAD_ID", None)
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                fake_codex = Path(tmp) / "fake-codex"
                fake_codex.write_text(
                    textwrap.dedent(
                        """\
                        #!/usr/bin/env python3
                        import json

                        events = [
                            {"type": "thread.started", "thread_id": "thread_demo"},
                            {"type": "turn.started"},
                            {"type": "item.started", "item": {"id": "item_msg", "type": "agent_message", "text": "Hello"}},
                            {"type": "item.updated", "item": {"id": "item_msg", "type": "agent_message", "text": "Hello there"}},
                            {"type": "item.started", "item": {"id": "item_cmd", "type": "command_execution", "command": "date", "aggregated_output": "", "status": "in_progress", "exit_code": None}},
                            {"type": "item.completed", "item": {"id": "item_cmd", "type": "command_execution", "command": "date", "aggregated_output": "Sun", "status": "completed", "exit_code": 0}},
                            {"type": "turn.completed", "usage": {"input_tokens": 1, "cached_input_tokens": 0, "output_tokens": 2, "reasoning_output_tokens": 0}},
                        ]
                        for event in events:
                            print(json.dumps(event), flush=True)
                        """
                    )
                )
                fake_codex.chmod(fake_codex.stat().st_mode | stat.S_IXUSR)

                store = ChatStore()
                user = store.append(role="user", text="Use OmniDoer from the client")
                result = ChatRunner(codex_bin=str(fake_codex), cwd=tmp).run_once()

                self.assertIsNotNone(result)
                assert result is not None
                self.assertEqual(result.role, "assistant")
                self.assertEqual(store.get(user.message_id).status, "completed")
                messages = store.list()
                assistant = [message for message in messages if message.role == "assistant"][0]
                self.assertEqual(assistant.status, "completed")
                self.assertEqual(assistant.text, "Hello there")
                records = store.list_records(limit=1000)
                record_types = [record.record_type for record in records]
                self.assertIn("delta", record_types)
                self.assertIn("tool_call", record_types)
                self.assertIn("tool_output", record_types)
                self.assertTrue(any("Codex turn completed" in record.text for record in records))
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home
                if old_thread is not None:
                    os.environ["OMNIDOER_CHAT_THREAD_ID"] = old_thread

    def test_chat_runner_can_resume_bound_codex_thread(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                argv_path = Path(tmp) / "argv.json"
                fake_codex = Path(tmp) / "fake-codex"
                fake_codex.write_text(
                    textwrap.dedent(
                        f"""\
                        #!/usr/bin/env python3
                        import json
                        import sys

                        {str(argv_path)!r}
                        open({str(argv_path)!r}, "w").write(json.dumps(sys.argv[1:]))
                        print(json.dumps({{"type": "item.started", "item": {{"id": "item_msg", "type": "agent_message", "text": "Bound"}}}}), flush=True)
                        print(json.dumps({{"type": "turn.completed", "usage": {{}}}}), flush=True)
                        """
                    )
                )
                fake_codex.chmod(fake_codex.stat().st_mode | stat.S_IXUSR)

                ChatStore().append(role="user", text="Use the active context")
                ChatRunner(
                    codex_bin=str(fake_codex),
                    cwd=tmp,
                    thread_id="thread_active",
                    allow_detached_thread_resume=True,
                ).run_once()

                argv = json.loads(argv_path.read_text())
                self.assertEqual(argv[:2], ["exec", "resume"])
                self.assertIn("--json", argv)
                self.assertIn("thread_active", argv)
                self.assertIn("OmniDoer control capability", argv[-1])
                self.assertIn("omnidoer cred request", argv[-1])
                self.assertIn("User request:\nUse the active context", argv[-1])
                self.assertTrue(any("Resuming Codex thread thread_active" in record.text for record in ChatStore().list_records()))
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home


if __name__ == "__main__":
    unittest.main()
