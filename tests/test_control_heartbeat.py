import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from omnidoer.omni_control.chat import ChatStore
from omnidoer.omni_control.heartbeat import (
    HeartbeatRunner,
    HeartbeatTaskStore,
    chat_session_idle,
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

    def test_heartbeat_round_robins_persistent_tasks(self) -> None:
        old_home = os.environ.get("OMNIDOER_HOME")
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                configure_heartbeat(
                    enabled=True,
                    interval="1h",
                    min_idle="0s",
                )
                task_store = HeartbeatTaskStore()
                first = task_store.create(
                    "处理 NeuroGolf 提交队列",
                    title="neurogolf",
                    position="back",
                )
                second = task_store.create(
                    "处理 ROGII wellbore 队列",
                    title="rogii",
                    position="back",
                )

                first_result = HeartbeatRunner().run_once(force=True)
                second_result = HeartbeatRunner().run_once(force=True)

                self.assertEqual(first_result["heartbeat_task_id"], first.task_id)
                self.assertEqual(second_result["heartbeat_task_id"], second.task_id)
                messages = ChatStore().list(limit=1000)
                self.assertIn("任务ID", messages[0].text)
                self.assertIn(first.task_id, messages[0].text)
                self.assertIn(second.task_id, messages[1].text)
                status = HeartbeatRunner().status()
                self.assertEqual(status["last_task_id"], second.task_id)
                self.assertEqual(status["task_queue"]["enabled_count"], 2)
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_heartbeat_random_insert_is_persisted(self) -> None:
        old_home = os.environ.get("OMNIDOER_HOME")
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                store = HeartbeatTaskStore()
                first = store.create("first", position="back")
                second = store.create("second", position="back")
                with patch("omnidoer.omni_control.heartbeat.random.randrange", return_value=1):
                    inserted = store.create("inserted", position="random")

                order = HeartbeatTaskStore().status()["order"]

                self.assertEqual(order, [first.task_id, inserted.task_id, second.task_id])
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_heartbeat_slash_command_manages_tasks(self) -> None:
        old_home = os.environ.get("OMNIDOER_HOME")
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                added = heartbeat_command_text(["/heartbeat", "add", "轮询", "漏洞扫描"], cwd=tmp)
                tasks = HeartbeatTaskStore().list(include_disabled=True)
                listed = heartbeat_command_text(["/heartbeat", "tasks"], cwd=tmp)
                removed = heartbeat_command_text(["/heartbeat", "remove", tasks[0].task_id], cwd=tmp)

                self.assertIn("Heartbeat task queued", added)
                self.assertIn(tasks[0].task_id, listed)
                self.assertIn("漏洞扫描", listed)
                self.assertIn("Heartbeat task removed", removed)
                self.assertEqual(HeartbeatTaskStore().list(include_disabled=True), [])
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

    def test_heartbeat_ignores_stale_non_user_streaming_messages(self) -> None:
        old_home = os.environ.get("OMNIDOER_HOME")
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                store = ChatStore()
                message = store.append(
                    role="assistant",
                    text="stale output",
                    status="streaming",
                    source="tui_bridge",
                )
                now = message.updated_at + 3600

                idle, reason, _ = chat_session_idle(
                    store=store,
                    min_idle_seconds=0,
                    now=now,
                    stale_non_user_active_seconds=1800,
                )

                self.assertTrue(idle)
                self.assertEqual(reason, "idle")
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
