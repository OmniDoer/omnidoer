"""Bridge queued Control Client chat messages to Codex JSON events."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

from omnidoer.omni_control.chat import ChatMessage, ChatStore
from omnidoer.omni_control.chat_uploads import image_attachment_paths


DEFAULT_RECORD_TEXT_LIMIT = 6000


def find_codex_binary(explicit: str | None = None) -> str | None:
    candidates = [
        explicit,
        os.environ.get("OMNIDOER_CHAT_CODEX_BIN"),
        os.environ.get("OMNIDOER_CODEX_BIN"),
        os.environ.get("OMNIDOER_REAL_CODEX"),
        "/usr/local/lib/omnidoer/codex",
        shutil.which("codex"),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate)
        if path.is_file() and os.access(path, os.X_OK):
            return str(path)
    return None


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _clip(text: str, limit: int = DEFAULT_RECORD_TEXT_LIMIT) -> str:
    if len(text) <= limit:
        return text
    omitted = len(text) - limit
    return f"{text[:limit]}\n...[truncated {omitted} chars]"


def _status(value: str | None) -> str:
    return value or "unknown"


class CodexJsonEventBridge:
    def __init__(self, store: ChatStore, assistant: ChatMessage):
        self.store = store
        self.assistant = assistant
        self.item_text_by_id: dict[str, str] = {}

    def record(self, record_type: str, text: str, *, role: str | None = None, data: dict[str, Any] | None = None) -> None:
        self.store.append_record(
            record_type=record_type,
            text=_clip(text),
            role=role,
            message_id=self.assistant.message_id,
            source="codex_exec_json",
            data=data or {},
        )

    def handle(self, event: dict[str, Any]) -> None:
        event_type = str(event.get("type") or "")
        if event_type == "thread.started":
            self.record("status", f"Codex thread started: {event.get('thread_id')}", role="system", data={"event": event_type})
            return
        if event_type == "turn.started":
            self.record("status", "Codex turn started.", role="system", data={"event": event_type})
            return
        if event_type == "turn.completed":
            usage = event.get("usage") if isinstance(event.get("usage"), dict) else {}
            self.record("status", f"Codex turn completed. usage={_json_text(usage)}", role="system", data={"event": event_type})
            return
        if event_type == "turn.failed":
            error = event.get("error") if isinstance(event.get("error"), dict) else {}
            self.record("error", f"Codex turn failed: {_json_text(error)}", role="system", data={"event": event_type})
            return
        if event_type == "error":
            self.record("error", str(event.get("message") or _json_text(event)), role="system", data={"event": event_type})
            return
        if event_type in {"item.started", "item.updated", "item.completed"}:
            item = event.get("item")
            if isinstance(item, dict):
                self._handle_item(item, event_type)
            return
        self.record("note", _json_text(event), role="system", data={"event": event_type or "unknown"})

    def _handle_item(self, item: dict[str, Any], event_type: str) -> None:
        item_type = str(item.get("type") or "")
        item_id = str(item.get("id") or "")
        if item_type == "agent_message":
            self._handle_agent_message(item, item_id)
            return
        if item_type == "reasoning":
            text = str(item.get("text") or "")
            if text:
                self.record("note", f"Reasoning summary:\n{text}", role="assistant", data={"event": event_type, "item_id": item_id})
            return
        if item_type == "command_execution":
            self._handle_command_execution(item, event_type, item_id)
            return
        if item_type == "mcp_tool_call":
            self._handle_mcp_tool_call(item, event_type, item_id)
            return
        if item_type == "file_change":
            self.record("note", f"File changes: {_json_text(item.get('changes') or [])}", role="assistant", data={"event": event_type, "item_id": item_id})
            return
        if item_type == "web_search":
            self.record("tool_call", f"Web search: {_json_text(item)}", role="assistant", data={"event": event_type, "item_id": item_id})
            return
        if item_type == "todo_list":
            self.record("status", f"Plan update: {_json_text(item.get('items') or [])}", role="assistant", data={"event": event_type, "item_id": item_id})
            return
        if item_type == "error":
            self.record("error", str(item.get("message") or _json_text(item)), role="system", data={"event": event_type, "item_id": item_id})
            return
        self.record("note", _json_text(item), role="system", data={"event": event_type, "item_id": item_id, "item_type": item_type})

    def _handle_agent_message(self, item: dict[str, Any], item_id: str) -> None:
        text = str(item.get("text") or "")
        previous = self.item_text_by_id.get(item_id, "")
        if not text or text == previous:
            return
        if text.startswith(previous):
            delta = text[len(previous) :]
        else:
            delta = text
        self.item_text_by_id[item_id] = text
        self.assistant = self.store.append_delta(self.assistant.message_id, delta)

    def _handle_command_execution(self, item: dict[str, Any], event_type: str, item_id: str) -> None:
        command = str(item.get("command") or "")
        status = _status(item.get("status"))
        if event_type == "item.started":
            self.record("tool_call", f"$ {command}", role="assistant", data={"event": event_type, "item_id": item_id, "status": status})
            return
        output = str(item.get("aggregated_output") or "")
        previous = self.item_text_by_id.get(item_id, "")
        if output.startswith(previous):
            delta = output[len(previous) :]
        else:
            delta = output
        self.item_text_by_id[item_id] = output
        exit_code = item.get("exit_code")
        body = delta or f"status={status}"
        if event_type == "item.completed":
            body = f"{body}\nexit_code={exit_code} status={status}".strip()
        self.record("tool_output", body, role="assistant", data={"event": event_type, "item_id": item_id, "status": status, "exit_code": exit_code})

    def _handle_mcp_tool_call(self, item: dict[str, Any], event_type: str, item_id: str) -> None:
        name = ".".join(part for part in (item.get("server"), item.get("tool")) if part)
        status = _status(item.get("status"))
        if event_type == "item.started":
            arguments = item.get("arguments") if isinstance(item.get("arguments"), dict) else {}
            self.record("tool_call", f"{name} {_json_text(arguments)}".strip(), role="assistant", data={"event": event_type, "item_id": item_id, "status": status})
            return
        if item.get("error"):
            text = f"{name} failed: {_json_text(item.get('error'))}"
            record_type = "error"
        else:
            text = f"{name} {status}: {_json_text(item.get('result') or {})}"
            record_type = "tool_output"
        self.record(record_type, text, role="assistant", data={"event": event_type, "item_id": item_id, "status": status})


class ChatRunner:
    def __init__(
        self,
        *,
        store: ChatStore | None = None,
        codex_bin: str | None = None,
        cwd: str | Path | None = None,
        extra_args: list[str] | None = None,
        poll_interval: float = 1.0,
    ):
        self.store = store or ChatStore()
        self.codex_bin = codex_bin
        self.cwd = Path(cwd or os.environ.get("OMNIDOER_CHAT_RUNNER_CWD") or os.getcwd())
        self.extra_args = extra_args if extra_args is not None else shlex.split(os.environ.get("OMNIDOER_CHAT_CODEX_ARGS", ""))
        self.poll_interval = poll_interval

    def run_once(self) -> ChatMessage | None:
        user_message = self.store.next_user_message(claim=True)
        if user_message is None:
            return None
        assistant = self.store.append(
            role="assistant",
            text="",
            status="streaming",
            source="codex_exec",
            reply_to_message_id=user_message.message_id,
        )
        bridge = CodexJsonEventBridge(self.store, assistant)
        codex = find_codex_binary(self.codex_bin)
        if not codex:
            bridge.record("error", "Codex CLI binary was not found; cannot process Control Client chat.", role="system")
            return self.store.complete(assistant.message_id, text="Codex CLI binary was not found.")
        bridge.record("status", f"Launching Codex JSON stream in {self.cwd}", role="system")
        image_args = []
        for image_path in image_attachment_paths(user_message.attachments):
            image_args.extend(["--image", image_path])
        command = [
            codex,
            "exec",
            "--json",
            "--cd",
            str(self.cwd),
            "--skip-git-repo-check",
            *image_args,
            *self.extra_args,
            "--",
            user_message.text,
        ]
        env = self._subprocess_env()
        try:
            with subprocess.Popen(
                command,
                cwd=self.cwd,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            ) as proc:
                assert proc.stdout is not None
                for line in proc.stdout:
                    self._handle_process_line(line, bridge)
                return_code = proc.wait()
        except Exception as exc:
            bridge.record("error", f"Codex JSON runner failed: {type(exc).__name__}", role="system")
            return self.store.complete(assistant.message_id, text=f"Codex JSON runner failed: {type(exc).__name__}")
        if return_code != 0:
            bridge.record("error", f"Codex process exited with code {return_code}.", role="system")
        return self.store.complete(assistant.message_id)

    def run_forever(self, stop_event: threading.Event | None = None) -> None:
        stop = stop_event or threading.Event()
        while not stop.is_set():
            processed = self.run_once()
            if processed is None:
                stop.wait(max(0.1, self.poll_interval))

    def _handle_process_line(self, line: str, bridge: CodexJsonEventBridge) -> None:
        text = line.rstrip("\n")
        if not text:
            return
        try:
            event = json.loads(text)
        except json.JSONDecodeError:
            bridge.record("note", text, role="system", data={"event": "stdout"})
            return
        if isinstance(event, dict):
            bridge.handle(event)
        else:
            bridge.record("note", _json_text(event), role="system", data={"event": "stdout"})

    def _subprocess_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env.setdefault("OMNIDOER_CONSOLE", "1")
        env.setdefault("OMNIDOER_CODEX_BRAND", "omnidoer")
        env.setdefault("CODEX_CLI_BRAND", "omnidoer")
        return env


def start_chat_runner_thread(
    *,
    codex_bin: str | None = None,
    cwd: str | Path | None = None,
    extra_args: list[str] | None = None,
    poll_interval: float = 1.0,
) -> threading.Thread:
    runner = ChatRunner(codex_bin=codex_bin, cwd=cwd, extra_args=extra_args, poll_interval=poll_interval)
    thread = threading.Thread(target=runner.run_forever, name="omnidoer-chat-runner", daemon=True)
    thread.start()
    return thread
