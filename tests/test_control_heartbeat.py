import os
import tempfile
import unittest
from pathlib import Path

from omnidoer.omni_control.chat import ChatStore
from omnidoer.omni_control.heartbeat import (
    HeartbeatRunner,
    configure_heartbeat,
    heartbeat_command_text,
)


class ControlHeartbeatTest(unittest.TestCase):
    def test_heartbeat_queues_task_when_enabled_and_idle(self) -> None:
        old_home = os.environ.get("OMNIDOER_HOME")
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["OMNIDOER_HOME"] = tmp
            heartbeat_file = Path(tmp) / "HEARTBEAT.md"
            heartbeat_file.write_text("执行安全监控", encoding="utf-8")
            try:
                configure_heartbeat(
                    enabled=True,
                    interval="1s",
                    min_idle="0s",
                    heartbeat_file=heartbeat_file,
                )

                result = HeartbeatRunner().run_once()

                self.assertEqual(result["status"], "queued")
                messages = ChatStore().list(limit=1000)
                self.assertEqual(len(messages), 1)
                self.assertEqual(messages[0].source, "heartbeat")
                self.assertIn("执行安全监控", messages[0].text)
                self.assertFalse(result["secret_fields_allowed"])
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_heartbeat_skips_when_chat_has_pending_work(self) -> None:
        old_home = os.environ.get("OMNIDOER_HOME")
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["OMNIDOER_HOME"] = tmp
            heartbeat_file = Path(tmp) / "HEARTBEAT.md"
            heartbeat_file.write_text("执行安全监控", encoding="utf-8")
            try:
                configure_heartbeat(
                    enabled=True,
                    interval="1s",
                    min_idle="0s",
                    heartbeat_file=heartbeat_file,
                )
                ChatStore().append(role="user", text="user task")

                result = HeartbeatRunner().run_once()

                self.assertEqual(result["status"], "skipped")
                self.assertEqual(result["reason"], "active_queued_message")
                self.assertEqual(len(ChatStore().list(limit=1000)), 1)
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_slash_command_status_is_local_control_response(self) -> None:
        old_home = os.environ.get("OMNIDOER_HOME")
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                text = heartbeat_command_text(["/heartbeat", "status"], cwd=tmp)

                self.assertIn("OmniDoer heartbeat", text)
                self.assertIn("Secret exposure: false", text)
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home
