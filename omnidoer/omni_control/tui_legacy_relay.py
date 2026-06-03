"""Compatibility relay for already-running TUI sessions.

The Rust TUI bridge is the preferred path. This relay is only for an older
interactive console process that is already running inside tmux and therefore
cannot hot-load the bridge code until the user restarts it.
"""

from __future__ import annotations

import os
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from omnidoer.omni_control.chat import ChatStore
from omnidoer.omni_control.chat_runner import live_tui_bridge_active

TERMINAL_CAPTURE_LINES = 120
TERMINAL_RECORD_LIMIT = 6000


@dataclass(frozen=True)
class TuiProcess:
    pid: int
    tty: str
    cmdline: list[str]


@dataclass(frozen=True)
class TmuxPane:
    pane_id: str
    tty: str
    current_command: str
    pane_pid: int | None = None
    process_pid: int | None = None


def _cmdline_is_interactive_tui_for_thread(cmdline: list[str], thread_id: str) -> bool:
    if not cmdline or not thread_id:
        return False
    args = cmdline[1:]
    if "exec" in args:
        return False
    return "resume" in args and thread_id in args


def _process_tty(entry: Path) -> str | None:
    for fd_name in ("0", "1", "2"):
        try:
            target = os.readlink(entry / "fd" / fd_name)
        except OSError:
            continue
        if target.startswith("/dev/pts/") or target.startswith("/dev/tty"):
            return target
    return None


def live_tui_process_for_thread(thread_id: str | None, *, proc_root: Path | str = "/proc") -> TuiProcess | None:
    if not thread_id:
        return None
    root = Path(proc_root)
    try:
        entries = list(root.iterdir())
    except OSError:
        return None
    for entry in entries:
        if not entry.name.isdigit():
            continue
        try:
            raw = (entry / "cmdline").read_bytes()
        except OSError:
            continue
        if not raw:
            continue
        cmdline = [part.decode("utf-8", "ignore") for part in raw.split(b"\0") if part]
        if not _cmdline_is_interactive_tui_for_thread(cmdline, thread_id):
            continue
        tty = _process_tty(entry)
        if tty:
            return TuiProcess(pid=int(entry.name), tty=tty, cmdline=cmdline)
    return None


def list_tmux_panes() -> list[TmuxPane]:
    try:
        output = subprocess.check_output(
            [
                "tmux",
                "list-panes",
                "-a",
                "-F",
                "#{pane_id}\t#{pane_tty}\t#{pane_current_command}\t#{pane_pid}",
            ],
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    panes: list[TmuxPane] = []
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) < 4:
            continue
        pane_pid = int(parts[3]) if parts[3].isdigit() else None
        panes.append(TmuxPane(pane_id=parts[0], tty=parts[1], current_command=parts[2], pane_pid=pane_pid))
    return panes


def find_tmux_pane_for_thread(thread_id: str | None) -> TmuxPane | None:
    process = live_tui_process_for_thread(thread_id)
    if process is None:
        return None
    for pane in list_tmux_panes():
        if pane.tty == process.tty:
            return TmuxPane(
                pane_id=pane.pane_id,
                tty=pane.tty,
                current_command=pane.current_command,
                pane_pid=pane.pane_pid,
                process_pid=process.pid,
            )
    return None


def legacy_tui_relay_status(thread_id: str | None) -> dict[str, object]:
    if live_tui_bridge_active(thread_id):
        return {"active": False, "reason": "rust_bridge_active"}
    pane = find_tmux_pane_for_thread(thread_id)
    if pane is None:
        return {"active": False, "reason": "tmux_pane_not_found"}
    return {
        "active": True,
        "transport": "tmux",
        "pane_id": pane.pane_id,
        "tty": pane.tty,
        "process_pid": pane.process_pid,
        "current_command": pane.current_command,
        "capabilities": {
            "message_injection": True,
            "interrupt_on_pause": True,
            "terminal_snapshot": True,
            "terminal_delta_records": True,
            "structured_stream": False,
        },
    }


def capture_tmux_pane(pane_id: str, *, line_count: int = 80) -> str:
    start = f"-{max(1, min(line_count, 1000))}"
    try:
        return subprocess.check_output(
            ["tmux", "capture-pane", "-pJ", "-S", start, "-t", pane_id],
            text=True,
            timeout=5,
        ).rstrip()
    except (OSError, subprocess.SubprocessError):
        return ""


def legacy_tui_terminal_snapshot(thread_id: str | None, *, line_count: int = 80) -> dict[str, object]:
    status = legacy_tui_relay_status(thread_id)
    if not status.get("active"):
        return {"available": False, **status}
    text = capture_tmux_pane(str(status["pane_id"]), line_count=line_count)
    return {"available": bool(text), "text": text, **status}


def inject_text_into_tmux_pane(pane_id: str, text: str) -> None:
    buffer_name = f"omnidoer-control-{os.getpid()}"
    subprocess.run(
        ["tmux", "load-buffer", "-b", buffer_name, "-"],
        input=text,
        text=True,
        check=True,
        timeout=5,
    )
    try:
        subprocess.run(["tmux", "paste-buffer", "-b", buffer_name, "-t", pane_id], check=True, timeout=5)
        subprocess.run(["tmux", "send-keys", "-t", pane_id, "Enter"], check=True, timeout=5)
    finally:
        subprocess.run(["tmux", "delete-buffer", "-b", buffer_name], check=False, timeout=5)


def interrupt_tmux_pane(pane_id: str) -> None:
    subprocess.run(["tmux", "send-keys", "-t", pane_id, "C-c"], check=True, timeout=5)


def restart_tmux_pane_for_bridge(thread_id: str | None, *, restart_command: str | None = None) -> dict[str, object]:
    if not thread_id:
        raise ValueError("thread_id is required")
    pane = find_tmux_pane_for_thread(thread_id)
    if pane is None:
        raise ValueError("tmux pane was not found")
    command = restart_command or f"omnidoer console resume {thread_id}"
    subprocess.run(["tmux", "respawn-pane", "-k", "-t", pane.pane_id, command], check=True, timeout=5)
    return {
        "status": "restart_started",
        "pane_id": pane.pane_id,
        "thread_id": thread_id,
        "command": command,
        "secret_exposed_to_model": False,
    }


def message_requests_interrupt(message) -> bool:
    return str(message.client_message_id or "").startswith(("control_pause_", "omnidoer_pause_"))


def message_requests_priority_delivery(message) -> bool:
    return str(message.client_message_id or "").startswith(("control_pause_", "omnidoer_pause_", "control_continue_"))


def terminal_delta(previous: list[str], current: list[str]) -> list[str]:
    if not previous:
        return []
    if current == previous:
        return []
    common_prefix = 0
    for old, new in zip(previous, current):
        if old != new:
            break
        common_prefix += 1
    if common_prefix:
        return current[common_prefix:]
    max_overlap = min(len(previous), len(current))
    for overlap in range(max_overlap, 0, -1):
        if previous[-overlap:] == current[:overlap]:
            return current[overlap:]
    return current


def clip_terminal_record(lines: list[str], *, limit: int = TERMINAL_RECORD_LIMIT) -> str:
    text = "\n".join(line for line in lines if line.strip())
    if len(text) <= limit:
        return text
    omitted = len(text) - limit
    return f"{text[-limit:]}\n...[truncated {omitted} leading chars]"


def terminal_line_is_volatile(line: str) -> bool:
    text = line.strip()
    if not text:
        return True
    if "Working (" in text and "esc to interrupt" in text:
        return True
    if text.startswith("› Ask OmniDoer to do anything"):
        return True
    if "Pursuing goal" in text and "gpt-" in text:
        return True
    return False


def stable_terminal_lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if not terminal_line_is_volatile(line)]


class LegacyTuiRelay:
    def __init__(
        self,
        *,
        store: ChatStore | None = None,
        thread_id: str | None = None,
        poll_interval: float = 1.0,
    ):
        self.store = store or ChatStore()
        self.thread_id = thread_id
        self.poll_interval = poll_interval
        self._last_terminal_lines: list[str] = []

    def run_once(self) -> bool:
        if live_tui_bridge_active(self.thread_id):
            return False
        message = self.store.next_user_message(claim=False)
        if message is None:
            return False
        return self.run_message(message.message_id)

    def run_message(self, message_id: str) -> bool:
        if live_tui_bridge_active(self.thread_id):
            return False
        pane = find_tmux_pane_for_thread(self.thread_id)
        if pane is None:
            return False
        try:
            message = self.store.get(message_id)
        except KeyError:
            return False
        if message.role != "user" or message.status != "queued":
            return False
        try:
            if message_requests_interrupt(message):
                interrupt_tmux_pane(pane.pane_id)
            inject_text_into_tmux_pane(pane.pane_id, message.text)
        except Exception as exc:
            self.store.append_record(
                record_type="error",
                text=f"Legacy TUI terminal relay failed: {type(exc).__name__}",
                role="system",
                message_id=message.message_id,
                source="legacy_tui_relay",
                data={"pane_id": pane.pane_id, "thread_id": self.thread_id},
            )
            return False
        delivered = self.store.complete(message.message_id)
        self.store.append_record(
            record_type="status",
            text=f"Delivered Control Client message to live TUI terminal pane {pane.pane_id}.",
            role="system",
            message_id=delivered.message_id,
            source="legacy_tui_relay",
            data={
                "pane_id": pane.pane_id,
                "thread_id": self.thread_id,
                "transport": "tmux",
                "interrupted_turn": message_requests_interrupt(delivered),
            },
        )
        return True

    def publish_terminal_delta(self) -> bool:
        if live_tui_bridge_active(self.thread_id):
            self._last_terminal_lines = []
            return False
        pane = find_tmux_pane_for_thread(self.thread_id)
        if pane is None:
            self._last_terminal_lines = []
            return False
        text = capture_tmux_pane(pane.pane_id, line_count=TERMINAL_CAPTURE_LINES)
        current = stable_terminal_lines(text)
        if not self._last_terminal_lines:
            self._last_terminal_lines = current
            body = clip_terminal_record(current)
            if not body:
                return False
            self.store.append_record(
                record_type="terminal",
                text=body,
                role="assistant",
                source="legacy_tui_relay",
                data={
                    "pane_id": pane.pane_id,
                    "thread_id": self.thread_id,
                    "transport": "tmux",
                    "line_count": len(current),
                    "terminal_snapshot": True,
                    "terminal_delta": False,
                },
            )
            return True
        delta = terminal_delta(self._last_terminal_lines, current)
        self._last_terminal_lines = current
        body = clip_terminal_record(delta)
        if not body:
            return False
        self.store.append_record(
            record_type="terminal",
            text=body,
            role="assistant",
            source="legacy_tui_relay",
            data={
                "pane_id": pane.pane_id,
                "thread_id": self.thread_id,
                "transport": "tmux",
                "line_count": len(delta),
                "terminal_delta": True,
            },
        )
        return True

    def run_forever(self, stop_event: threading.Event | None = None) -> None:
        stop = stop_event or threading.Event()
        while not stop.is_set():
            self.run_once()
            self.publish_terminal_delta()
            stop.wait(max(0.1, self.poll_interval))


def start_legacy_tui_relay_thread(
    *,
    thread_id: str | None = None,
    poll_interval: float = 1.0,
) -> threading.Thread:
    relay = LegacyTuiRelay(thread_id=thread_id, poll_interval=poll_interval)
    thread = threading.Thread(target=relay.run_forever, name="omnidoer-legacy-tui-relay", daemon=True)
    thread.start()
    return thread
