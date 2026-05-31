import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from omnidoer.omni_control.chat import ChatStore
from omnidoer.omni_control.tui_legacy_relay import (
    LegacyTuiRelay,
    TmuxPane,
    stable_terminal_lines,
    terminal_delta,
    find_tmux_pane_for_thread,
    legacy_tui_relay_status,
    legacy_tui_terminal_snapshot,
    live_tui_process_for_thread,
)


class TuiLegacyRelayTest(unittest.TestCase):
    def test_finds_tmux_pane_for_live_tui_thread(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proc_root = Path(tmp) / "proc"
            proc_root.mkdir()
            process = proc_root / "1234"
            process.mkdir()
            process.joinpath("cmdline").write_bytes(
                b"/usr/local/lib/omnidoer/codex\0resume\0thread_active\0"
            )
            fd_dir = process / "fd"
            fd_dir.mkdir()
            fd_dir.joinpath("0").symlink_to("/dev/pts/9")

            found = live_tui_process_for_thread("thread_active", proc_root=proc_root)
            self.assertIsNotNone(found)
            assert found is not None
            self.assertEqual(found.tty, "/dev/pts/9")

            with patch(
                "omnidoer.omni_control.tui_legacy_relay.live_tui_process_for_thread",
                return_value=found,
            ), patch(
                "omnidoer.omni_control.tui_legacy_relay.list_tmux_panes",
                return_value=[TmuxPane(pane_id="%4", tty="/dev/pts/9", current_command="codex", pane_pid=42)],
            ):
                pane = find_tmux_pane_for_thread("thread_active")
            self.assertIsNotNone(pane)
            assert pane is not None
            self.assertEqual(pane.pane_id, "%4")
            self.assertEqual(pane.process_pid, 1234)

    def test_relay_claims_and_injects_queued_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                store = ChatStore()
                user = store.append(role="user", text="hello from phone")
                pane = TmuxPane(pane_id="%1", tty="/dev/pts/2", current_command="codex", process_pid=99)
                injected: list[tuple[str, str]] = []

                with patch("omnidoer.omni_control.tui_legacy_relay.live_tui_bridge_active", return_value=False), patch(
                    "omnidoer.omni_control.tui_legacy_relay.find_tmux_pane_for_thread",
                    return_value=pane,
                ), patch(
                    "omnidoer.omni_control.tui_legacy_relay.inject_text_into_tmux_pane",
                    side_effect=lambda pane_id, text: injected.append((pane_id, text)),
                ):
                    self.assertTrue(LegacyTuiRelay(store=store, thread_id="thread_active").run_once())

                self.assertEqual(injected, [("%1", "hello from phone")])
                self.assertEqual(store.get(user.message_id).status, "claimed")
                records = store.list_records(limit=100)
                self.assertTrue(any(record.source == "legacy_tui_relay" for record in records))
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_relay_interrupts_for_pause_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                store = ChatStore()
                user = store.append(
                    role="user",
                    text="Pause Agent",
                    client_message_id="control_pause_123",
                )
                pane = TmuxPane(pane_id="%1", tty="/dev/pts/2", current_command="codex", process_pid=99)
                injected: list[tuple[str, str]] = []
                interrupted: list[str] = []

                with patch("omnidoer.omni_control.tui_legacy_relay.live_tui_bridge_active", return_value=False), patch(
                    "omnidoer.omni_control.tui_legacy_relay.find_tmux_pane_for_thread",
                    return_value=pane,
                ), patch(
                    "omnidoer.omni_control.tui_legacy_relay.interrupt_tmux_pane",
                    side_effect=lambda pane_id: interrupted.append(pane_id),
                ), patch(
                    "omnidoer.omni_control.tui_legacy_relay.inject_text_into_tmux_pane",
                    side_effect=lambda pane_id, text: injected.append((pane_id, text)),
                ):
                    self.assertTrue(LegacyTuiRelay(store=store, thread_id="thread_active").run_once())

                self.assertEqual(interrupted, ["%1"])
                self.assertEqual(injected, [("%1", "Pause Agent")])
                self.assertEqual(store.get(user.message_id).status, "claimed")
                records = store.list_records(limit=100)
                self.assertTrue(any(record.data.get("interrupted_turn") is True for record in records))
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_status_and_terminal_snapshot_report_active_relay(self) -> None:
        pane = TmuxPane(pane_id="%1", tty="/dev/pts/2", current_command="codex", process_pid=99)
        with patch("omnidoer.omni_control.tui_legacy_relay.live_tui_bridge_active", return_value=False), patch(
            "omnidoer.omni_control.tui_legacy_relay.find_tmux_pane_for_thread",
            return_value=pane,
        ), patch(
            "omnidoer.omni_control.tui_legacy_relay.capture_tmux_pane",
            return_value="live terminal text",
        ):
            status = legacy_tui_relay_status("thread_active")
            snapshot = legacy_tui_terminal_snapshot("thread_active")
        self.assertTrue(status["active"])
        self.assertEqual(status["pane_id"], "%1")
        self.assertEqual(status["capabilities"]["interrupt_on_pause"], True)
        self.assertEqual(status["capabilities"]["terminal_delta_records"], True)
        self.assertEqual(status["capabilities"]["structured_stream"], False)
        self.assertTrue(snapshot["available"])
        self.assertEqual(snapshot["text"], "live terminal text")

    def test_terminal_delta_uses_line_overlap(self) -> None:
        previous = ["one", "two", "three"]
        current = ["two", "three", "four", "five"]
        self.assertEqual(terminal_delta(previous, current), ["four", "five"])
        self.assertEqual(terminal_delta(["one", "old"], ["one", "new"]), ["new"])

    def test_stable_terminal_lines_drop_volatile_tui_chrome(self) -> None:
        text = "\n".join(
            [
                "real output",
                "• Working (3m 49s • esc to interrupt)",
                "› Ask OmniDoer to do anything",
                "gpt-5.5 xhigh · ~ Pursuing goal (2h 49m)",
            ]
        )
        self.assertEqual(stable_terminal_lines(text), ["real output"])

    def test_relay_publishes_terminal_delta_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                store = ChatStore()
                pane = TmuxPane(pane_id="%1", tty="/dev/pts/2", current_command="codex", process_pid=99)
                relay = LegacyTuiRelay(store=store, thread_id="thread_active")
                with patch("omnidoer.omni_control.tui_legacy_relay.live_tui_bridge_active", return_value=False), patch(
                    "omnidoer.omni_control.tui_legacy_relay.find_tmux_pane_for_thread",
                    return_value=pane,
                ), patch(
                    "omnidoer.omni_control.tui_legacy_relay.capture_tmux_pane",
                    side_effect=["line one\nline two", "line one\nline two\nline three"],
                ):
                    self.assertFalse(relay.publish_terminal_delta())
                    self.assertTrue(relay.publish_terminal_delta())

                records = store.list_records(limit=100)
                terminal_records = [record for record in records if record.record_type == "terminal"]
                self.assertEqual(len(terminal_records), 1)
                self.assertEqual(terminal_records[0].text, "line three")
                self.assertEqual(terminal_records[0].data["terminal_delta"], True)
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home


if __name__ == "__main__":
    unittest.main()
