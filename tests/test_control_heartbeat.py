import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from omnidoer.omni_cli.main import build_parser
from omnidoer.omni_control.chat import ChatStore
from omnidoer.omni_control.heartbeat import (
    HeartbeatRunner,
    HeartbeatTaskStore,
    chat_session_idle,
    configure_heartbeat,
    effective_task_weight,
    heartbeat_command_text,
)


class ControlHeartbeatTest(unittest.TestCase):
    def test_control_serve_no_heartbeat_flag_defaults_off(self) -> None:
        parser = build_parser()

        default_args = parser.parse_args(["control", "serve"])
        disabled_args = parser.parse_args(["control", "serve", "--no-heartbeat"])

        self.assertFalse(default_args.no_heartbeat)
        self.assertTrue(disabled_args.no_heartbeat)

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

    def test_queued_task_interrupts_active_chat(self) -> None:
        old_home = os.environ.get("OMNIDOER_HOME")
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                configure_heartbeat(enabled=True, interval="1s", min_idle="5m")
                task = HeartbeatTaskStore().create(
                    "执行周期性 Kaggle 轮询",
                    title="kaggle",
                    position="back",
                )
                ChatStore().append(role="assistant", text="long running", status="streaming")

                result = HeartbeatRunner().run_once()

                self.assertEqual(result["status"], "queued")
                self.assertEqual(result["heartbeat_task_id"], task.task_id)
                self.assertEqual(len(ChatStore().list(limit=1000)), 2)
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_fixed_interval_task_waits_until_due_then_takes_priority(self) -> None:
        old_home = os.environ.get("OMNIDOER_HOME")
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                configure_heartbeat(enabled=True, interval="1s", min_idle="0s")
                store = HeartbeatTaskStore()
                kaggle = store.create("Kaggle work", title="kaggle", position="back")
                vuln = store.create(
                    "漏洞扫描",
                    title="crypto-vulnerability-scan",
                    min_interval_seconds=4 * 60 * 60,
                    position="back",
                )
                now = 1_000_000.0

                first = HeartbeatTaskStore().next_task(now=now)
                second = HeartbeatTaskStore().next_task(now=now + 60)
                third = HeartbeatTaskStore().next_task(now=now + 4 * 60 * 60 + 1)

                self.assertEqual(first.task_id, vuln.task_id)
                self.assertEqual(second.task_id, kaggle.task_id)
                self.assertEqual(third.task_id, vuln.task_id)
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_deadline_increases_effective_weight(self) -> None:
        old_home = os.environ.get("OMNIDOER_HOME")
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                store = HeartbeatTaskStore()
                near = store.create(
                    "near",
                    deadline_utc="2026-06-23T23:59:00Z",
                    position="back",
                    weight=1,
                )
                far = store.create(
                    "far",
                    deadline_utc="2026-11-02T23:59:00Z",
                    position="back",
                    weight=1,
                )
                now = 1_781_222_400.0  # 2026-06-12T00:00:00Z

                self.assertGreater(effective_task_weight(near, now), effective_task_weight(far, now))
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
