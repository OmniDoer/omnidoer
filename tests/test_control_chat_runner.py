import json
import os
import stat
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

from omnidoer.omni_control.chat import ChatStore
from omnidoer.omni_control.chat_runner import ChatRunner, live_tui_bridge_active, live_tui_session_active


class ControlChatRunnerTest(unittest.TestCase):
    def test_chat_runner_defers_to_live_tui_bridge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                heartbeat = Path(tmp) / "control_chat_bridge_heartbeat"
                heartbeat.write_text("live")
                store = ChatStore()
                user = store.append(role="user", text="Use the active TUI")

                self.assertTrue(live_tui_bridge_active())
                self.assertIsNone(ChatRunner(codex_bin="/does/not/exist", cwd=tmp).run_once())
                self.assertEqual(store.get(user.message_id).status, "queued")
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

    def test_bound_thread_runner_can_require_live_tui(self) -> None:
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
                    require_live_tui_for_thread=True,
                )
                with patch("omnidoer.omni_control.chat_runner.live_tui_session_active", return_value=False):
                    self.assertIsNone(runner.run_once())
                self.assertEqual(store.get(user.message_id).status, "queued")
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_codex_json_events_stream_into_chat_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
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
                self.assertEqual(store.get(user.message_id).status, "claimed")
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
                ChatRunner(codex_bin=str(fake_codex), cwd=tmp, thread_id="thread_active").run_once()

                argv = json.loads(argv_path.read_text())
                self.assertEqual(argv[:2], ["exec", "resume"])
                self.assertIn("--json", argv)
                self.assertIn("thread_active", argv)
                self.assertEqual(argv[-1], "Use the active context")
                self.assertTrue(any("Resuming Codex thread thread_active" in record.text for record in ChatStore().list_records()))
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home


if __name__ == "__main__":
    unittest.main()
