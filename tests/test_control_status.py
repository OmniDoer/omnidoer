import json
import os
import tempfile
import time
import unittest
from http.server import ThreadingHTTPServer
from threading import Thread
from unittest.mock import patch
from urllib.error import HTTPError
from urllib import request as urllib_request

from omnidoer.omni_control.chat import ChatStore
from omnidoer.omni_control.cloud import build_config
from omnidoer.omni_control.requests import RequestStore
from omnidoer.omni_control.server import (
    CONSOLE_RESTART_REQUEST_RENEW_WINDOW_SECONDS,
    CONSOLE_RESTART_REQUEST_TTL_SECONDS,
    ControlHandler,
    ensure_current_session_sync_request,
)
from omnidoer.omni_control.sessions import ControlSession


class ControlStatusTest(unittest.TestCase):
    def test_status_reports_active_tui_waiting_for_bridge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = build_config(host="127.0.0.1", port=8787)
            server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
            server.omnidoer_config = config  # type: ignore[attr-defined]
            server.omnidoer_chat_thread_id = "thread_active"  # type: ignore[attr-defined]
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with patch("omnidoer.omni_control.chat_runner.live_tui_bridge_active", return_value=False), patch(
                    "omnidoer.omni_control.chat_runner.live_tui_session_active",
                    return_value=True,
                ), patch(
                    "omnidoer.omni_control.chat_runner.native_console_bridge_install_status",
                    return_value={"ready": True, "reason": "ready", "codex_binary": "/usr/local/lib/omnidoer/codex"},
                ), patch(
                    "omnidoer.omni_control.chat_runner.active_tui_process_bridge_status",
                    return_value={
                        "active": True,
                        "pid": 1234,
                        "native_bridge_ready": False,
                        "installed_bridge_ready": True,
                        "running_binary_matches_installed": False,
                        "executable_deleted": True,
                        "reason": "running_binary_deleted",
                    },
                ), patch(
                    "omnidoer.omni_control.tui_legacy_relay.legacy_tui_relay_status",
                    return_value={"active": True, "transport": "tmux", "pane_id": "%1"},
                ):
                    with urllib_request.urlopen(
                        f"http://127.0.0.1:{server.server_address[1]}/api/status",
                        timeout=5,
                    ) as response:
                        payload = json.loads(response.read().decode())
                self.assertEqual(payload["chat_runner"]["thread_id"], "thread_active")
                self.assertTrue(payload["chat_runner"]["tui_session_active"])
                self.assertFalse(payload["chat_runner"]["tui_bridge_active"])
                self.assertTrue(payload["chat_runner"]["waiting_for_tui_bridge"])
                self.assertTrue(payload["chat_runner"]["restart_required"])
                self.assertEqual(payload["chat_runner"]["restart_command"], "omnidoer console resume thread_active")
                self.assertIn("bridge_heartbeat_age_seconds", payload["chat_runner"])
                self.assertFalse(payload["chat_runner"]["detached_thread_resume_allowed"])
                self.assertTrue(payload["chat_runner"]["native_console_bridge"]["ready"])
                self.assertEqual(payload["chat_runner"]["active_tui_process_bridge"]["reason"], "running_binary_deleted")
                self.assertTrue(payload["chat_runner"]["legacy_tui_relay"]["active"])
                diagnostics = payload["chat_runner"]["sync_diagnostics"]
                self.assertEqual(diagnostics["state"], "legacy_terminal_relay")
                self.assertTrue(diagnostics["current_cli_reachable"])
                self.assertFalse(diagnostics["current_cli_context_attached"])
                self.assertEqual(diagnostics["phone_to_current_cli_delivery"], "terminal_relay")
                self.assertEqual(diagnostics["current_cli_to_phone_stream"], "terminal_snapshot")
                self.assertTrue(diagnostics["restart_ready"])
                self.assertTrue(diagnostics["restart_current_console_available"])
                self.assertFalse(diagnostics["manual_resume_available"])
                self.assertEqual(diagnostics["activation_action"], "restart_current_console")
                self.assertEqual(diagnostics["activation_blocker"], "running_binary_deleted")
                self.assertFalse(diagnostics["native_sync_active"])
                self.assertFalse(diagnostics["detached_thread_resume_allowed"])
                self.assertFalse(diagnostics["active_cli_binary_has_native_bridge"])
                self.assertTrue(diagnostics["active_cli_binary_deleted"])
            finally:
                server.shutdown()
                server.server_close()

    def test_status_reports_bound_thread_waiting_even_without_live_tui(self) -> None:
        config = build_config(host="127.0.0.1", port=8787)
        server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
        server.omnidoer_config = config  # type: ignore[attr-defined]
        server.omnidoer_chat_thread_id = "thread_active"  # type: ignore[attr-defined]
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with patch("omnidoer.omni_control.chat_runner.live_tui_bridge_active", return_value=False), patch(
                "omnidoer.omni_control.chat_runner.live_tui_session_active",
                return_value=False,
            ), patch(
                "omnidoer.omni_control.chat_runner.native_console_bridge_install_status",
                return_value={"ready": False, "reason": "missing_bridge_markers"},
            ), patch(
                "omnidoer.omni_control.chat_runner.active_tui_process_bridge_status",
                return_value={"active": False, "reason": "live_tui_process_not_found"},
            ), patch(
                "omnidoer.omni_control.tui_legacy_relay.legacy_tui_relay_status",
                return_value={"active": False, "reason": "tmux_pane_not_found"},
            ):
                with urllib_request.urlopen(
                    f"http://127.0.0.1:{server.server_address[1]}/api/status",
                    timeout=5,
                ) as response:
                    payload = json.loads(response.read().decode())
            self.assertEqual(payload["chat_runner"]["thread_id"], "thread_active")
            self.assertFalse(payload["chat_runner"]["tui_session_active"])
            self.assertTrue(payload["chat_runner"]["waiting_for_tui_bridge"])
            self.assertTrue(payload["chat_runner"]["restart_required"])
            self.assertEqual(payload["chat_runner"]["restart_command"], "omnidoer console resume thread_active")
            self.assertFalse(payload["chat_runner"]["native_console_bridge"]["ready"])
            self.assertFalse(payload["chat_runner"]["legacy_tui_relay"]["active"])
            self.assertFalse(payload["chat_runner"]["detached_thread_resume_allowed"])
            diagnostics = payload["chat_runner"]["sync_diagnostics"]
            self.assertEqual(diagnostics["state"], "bound_thread_without_live_cli")
            self.assertFalse(diagnostics["current_cli_reachable"])
            self.assertEqual(diagnostics["phone_to_current_cli_delivery"], "not_connected")
            self.assertFalse(diagnostics["restart_ready"])
            self.assertFalse(diagnostics["restart_current_console_available"])
            self.assertFalse(diagnostics["manual_resume_available"])
            self.assertEqual(diagnostics["activation_action"], "update_native_bridge")
            self.assertFalse(diagnostics["detached_thread_resume_allowed"])
        finally:
            server.shutdown()
            server.server_close()

    def test_restart_bridge_endpoint_requires_confirmation_and_respawns_console(self) -> None:
        config = build_config(host="127.0.0.1", port=8787)
        server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
        server.omnidoer_config = config  # type: ignore[attr-defined]
        server.omnidoer_chat_thread_id = "thread_active"  # type: ignore[attr-defined]
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            missing_confirmation = urllib_request.Request(
                f"http://127.0.0.1:{server.server_address[1]}/api/console/restart-bridge",
                data=json.dumps({}).encode(),
                headers={"content-type": "application/json"},
                method="POST",
            )
            with self.assertRaises(HTTPError) as raised:
                urllib_request.urlopen(missing_confirmation, timeout=5)
            self.assertEqual(raised.exception.code, 400)

            with patch(
                "omnidoer.omni_control.tui_legacy_relay.restart_tmux_pane_for_bridge",
                return_value={
                    "status": "restart_started",
                    "pane_id": "%1",
                    "thread_id": "thread_active",
                    "command": "omnidoer console resume thread_active",
                    "secret_exposed_to_model": False,
                },
            ) as restart:
                request = urllib_request.Request(
                    f"http://127.0.0.1:{server.server_address[1]}/api/console/restart-bridge",
                    data=json.dumps({"confirm_restart": True}).encode(),
                    headers={"content-type": "application/json"},
                    method="POST",
                )
                with urllib_request.urlopen(request, timeout=5) as response:
                    payload = json.loads(response.read().decode())
            self.assertEqual(payload["status"], "restart_started")
            self.assertEqual(payload["pane_id"], "%1")
            restart.assert_called_once_with("thread_active", restart_command="omnidoer console resume thread_active")
        finally:
            server.shutdown()
            server.server_close()

    def test_restart_bridge_request_requires_approval_before_respawn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            config = build_config(host="127.0.0.1", port=8787)
            server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
            server.omnidoer_config = config  # type: ignore[attr-defined]
            server.omnidoer_chat_thread_id = "thread_active"  # type: ignore[attr-defined]
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with patch("omnidoer.omni_control.chat_runner.live_tui_bridge_active", return_value=False), patch(
                    "omnidoer.omni_control.chat_runner.native_console_bridge_install_status",
                    return_value={"ready": True, "reason": "ready"},
                ), patch(
                    "omnidoer.omni_control.chat_runner.active_tui_process_bridge_status",
                    return_value={"active": True, "pid": 1234, "reason": "running_binary_deleted"},
                ), patch(
                    "omnidoer.omni_control.tui_legacy_relay.legacy_tui_relay_status",
                    return_value={"active": True, "transport": "tmux", "pane_id": "%1"},
                ):
                    create = urllib_request.Request(
                        f"http://127.0.0.1:{server.server_address[1]}/api/console/restart-bridge/request",
                        data=b"{}",
                        headers={"content-type": "application/json"},
                        method="POST",
                    )
                    with urllib_request.urlopen(create, timeout=5) as response:
                        created = json.loads(response.read().decode())
                self.assertEqual(created["status"], "approval_request_created")
                approval = created["request"]
                self.assertEqual(approval["request_type"], "console_restart")
                self.assertEqual(approval["status"], "pending")
                self.assertIsNone(approval["allowed_device_id"])
                self.assertEqual(approval["structured_details"]["thread_id"], "thread_active")
                self.assertEqual(approval["structured_details"]["legacy_pane_id"], "%1")

                approve_url = f"http://127.0.0.1:{server.server_address[1]}/api/requests/{approval['request_id']}/approve"
                with self.assertRaises(HTTPError) as missing_confirmation:
                    urllib_request.urlopen(
                        urllib_request.Request(
                            approve_url,
                            data=b"{}",
                            headers={"content-type": "application/json"},
                            method="POST",
                        ),
                        timeout=5,
                    )
                self.assertEqual(missing_confirmation.exception.code, 400)
                self.assertEqual(RequestStore().get(approval["request_id"]).status, "pending")

                with patch(
                    "omnidoer.omni_control.tui_legacy_relay.restart_tmux_pane_for_bridge",
                    return_value={
                        "status": "restart_started",
                        "pane_id": "%1",
                        "thread_id": "thread_active",
                        "command": "omnidoer console resume thread_active",
                        "secret_exposed_to_model": False,
                    },
                ) as restart:
                    approve = urllib_request.Request(
                        approve_url,
                        data=json.dumps(
                            {
                                "explicit_user_confirmation": True,
                                "request_id": approval["request_id"],
                            }
                        ).encode(),
                        headers={"content-type": "application/json"},
                        method="POST",
                    )
                    with urllib_request.urlopen(approve, timeout=5) as response:
                        approved = json.loads(response.read().decode())
                self.assertEqual(approved["status"], "consumed")
                self.assertEqual(approved["console_restart"]["status"], "restart_started")
                restart.assert_called_once_with("thread_active", restart_command="omnidoer console resume thread_active")
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_console_restart_request_is_visible_to_any_paired_device(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            config = build_config(
                host="0.0.0.0",
                port=8787,
                public_url="https://example.test:8787",
                cloud_direct=True,
                insecure_dev_public=True,
            )
            server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
            server.omnidoer_config = config  # type: ignore[attr-defined]
            server.omnidoer_chat_thread_id = "thread_active"  # type: ignore[attr-defined]
            handler = object.__new__(ControlHandler)
            handler.server = server
            session = ControlSession(
                session_id="sess_a",
                device_id="device_a",
                token_hash="hash",
                csrf_token="csrf",
                expires_at=9999999999,
            )
            try:
                with patch("omnidoer.omni_control.chat_runner.live_tui_bridge_active", return_value=False), patch(
                    "omnidoer.omni_control.chat_runner.live_tui_session_active",
                    return_value=True,
                ), patch(
                    "omnidoer.omni_control.chat_runner.native_console_bridge_install_status",
                    return_value={"ready": True, "reason": "ready"},
                ), patch(
                    "omnidoer.omni_control.chat_runner.active_tui_process_bridge_status",
                    return_value={"active": True, "pid": 1234, "reason": "running_binary_deleted"},
                ), patch(
                    "omnidoer.omni_control.tui_legacy_relay.legacy_tui_relay_status",
                    return_value={"active": True, "transport": "tmux", "pane_id": "%1"},
                ):
                    request, reused = handler._create_console_restart_request(RequestStore(), session)
                self.assertFalse(reused)
                self.assertIsNone(request.allowed_device_id)
                self.assertTrue(handler._request_allowed_for_session(request, None))
                self.assertTrue(
                    handler._request_allowed_for_session(
                        request,
                        ControlSession(
                            session_id="sess_b",
                            device_id="device_b",
                            token_hash="hash",
                            csrf_token="csrf",
                            expires_at=9999999999,
                        ),
                    )
                )
            finally:
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_console_restart_request_reuse_refreshes_expiring_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            config = build_config(
                host="0.0.0.0",
                port=8787,
                public_url="https://example.test:8787",
                cloud_direct=True,
                insecure_dev_public=True,
            )
            server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
            server.omnidoer_config = config  # type: ignore[attr-defined]
            server.omnidoer_chat_thread_id = "thread_active"  # type: ignore[attr-defined]
            handler = object.__new__(ControlHandler)
            handler.server = server
            session = ControlSession(
                session_id="sess_a",
                device_id="device_a",
                token_hash="hash",
                csrf_token="csrf",
                expires_at=9999999999,
            )
            try:
                with patch("omnidoer.omni_control.chat_runner.live_tui_bridge_active", return_value=False), patch(
                    "omnidoer.omni_control.chat_runner.live_tui_session_active",
                    return_value=True,
                ), patch(
                    "omnidoer.omni_control.chat_runner.native_console_bridge_install_status",
                    return_value={"ready": True, "reason": "ready"},
                ), patch(
                    "omnidoer.omni_control.chat_runner.active_tui_process_bridge_status",
                    return_value={"active": True, "pid": 1234, "reason": "running_binary_deleted"},
                ), patch(
                    "omnidoer.omni_control.tui_legacy_relay.legacy_tui_relay_status",
                    return_value={"active": True, "transport": "tmux", "pane_id": "%1"},
                ):
                    request, reused = handler._create_console_restart_request(RequestStore(), session)
                self.assertFalse(reused)
                self.assertGreater(request.expires_at, time.time() + CONSOLE_RESTART_REQUEST_TTL_SECONDS - 5)

                request.expires_at = time.time() + CONSOLE_RESTART_REQUEST_RENEW_WINDOW_SECONDS - 1
                RequestStore().update(request)

                with patch("omnidoer.omni_control.chat_runner.live_tui_bridge_active", return_value=False), patch(
                    "omnidoer.omni_control.chat_runner.live_tui_session_active",
                    return_value=True,
                ), patch(
                    "omnidoer.omni_control.chat_runner.native_console_bridge_install_status",
                    return_value={"ready": True, "reason": "ready"},
                ), patch(
                    "omnidoer.omni_control.chat_runner.active_tui_process_bridge_status",
                    return_value={"active": True, "pid": 5678, "reason": "running_binary_deleted"},
                ), patch(
                    "omnidoer.omni_control.tui_legacy_relay.legacy_tui_relay_status",
                    return_value={"active": True, "transport": "tmux", "pane_id": "%2"},
                ):
                    renewed, reused = handler._create_console_restart_request(RequestStore(), session)

                self.assertTrue(reused)
                self.assertEqual(renewed.request_id, request.request_id)
                self.assertGreater(renewed.expires_at, time.time() + CONSOLE_RESTART_REQUEST_TTL_SECONDS - 5)
                self.assertEqual(renewed.structured_details["active_cli_pid"], 5678)
                self.assertEqual(renewed.structured_details["legacy_pane_id"], "%2")
            finally:
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_current_session_sync_request_helper_renews_without_active_browser_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            config = build_config(
                host="0.0.0.0",
                port=8787,
                public_url="https://example.test:8787",
                cloud_direct=True,
                insecure_dev_public=True,
            )
            try:
                with patch("omnidoer.omni_control.chat_runner.live_tui_bridge_active", return_value=False), patch(
                    "omnidoer.omni_control.chat_runner.live_tui_session_active",
                    return_value=True,
                ), patch(
                    "omnidoer.omni_control.chat_runner.native_console_bridge_install_status",
                    return_value={"ready": True, "reason": "ready"},
                ), patch(
                    "omnidoer.omni_control.chat_runner.active_tui_process_bridge_status",
                    return_value={"active": True, "pid": 1234, "reason": "running_binary_deleted"},
                ), patch(
                    "omnidoer.omni_control.tui_legacy_relay.legacy_tui_relay_status",
                    return_value={"active": True, "transport": "tmux", "pane_id": "%1"},
                ):
                    request = ensure_current_session_sync_request(
                        RequestStore(),
                        public_url=config.public_url,
                        chat_thread_id="thread_active",
                        requires_pairing=False,
                    )
                self.assertIsNotNone(request)
                assert request is not None
                self.assertEqual(request.request_type, "console_restart")
                self.assertEqual(request.status, "pending")

                request.expires_at = time.time() + CONSOLE_RESTART_REQUEST_RENEW_WINDOW_SECONDS - 1
                RequestStore().update(request)

                with patch("omnidoer.omni_control.chat_runner.live_tui_bridge_active", return_value=False), patch(
                    "omnidoer.omni_control.chat_runner.live_tui_session_active",
                    return_value=True,
                ), patch(
                    "omnidoer.omni_control.chat_runner.native_console_bridge_install_status",
                    return_value={"ready": True, "reason": "ready"},
                ), patch(
                    "omnidoer.omni_control.chat_runner.active_tui_process_bridge_status",
                    return_value={"active": True, "pid": 5678, "reason": "running_binary_deleted"},
                ), patch(
                    "omnidoer.omni_control.tui_legacy_relay.legacy_tui_relay_status",
                    return_value={"active": True, "transport": "tmux", "pane_id": "%2"},
                ):
                    renewed = ensure_current_session_sync_request(
                        RequestStore(),
                        public_url=config.public_url,
                        chat_thread_id="thread_active",
                        requires_pairing=False,
                    )

                self.assertIsNotNone(renewed)
                assert renewed is not None
                self.assertEqual(renewed.request_id, request.request_id)
                self.assertGreater(renewed.expires_at, time.time() + CONSOLE_RESTART_REQUEST_TTL_SECONDS - 5)
                self.assertEqual(renewed.structured_details["active_cli_pid"], 5678)
                self.assertEqual(renewed.structured_details["legacy_pane_id"], "%2")
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_visible_requests_auto_creates_console_restart_request_when_sync_needed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            config = build_config(host="127.0.0.1", port=8787)
            server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
            server.omnidoer_config = config  # type: ignore[attr-defined]
            server.omnidoer_chat_thread_id = "thread_active"  # type: ignore[attr-defined]
            handler = object.__new__(ControlHandler)
            handler.server = server
            try:
                with patch("omnidoer.omni_control.chat_runner.live_tui_bridge_active", return_value=False), patch(
                    "omnidoer.omni_control.chat_runner.live_tui_session_active",
                    return_value=True,
                ), patch(
                    "omnidoer.omni_control.chat_runner.native_console_bridge_install_status",
                    return_value={"ready": True, "reason": "ready"},
                ), patch(
                    "omnidoer.omni_control.chat_runner.active_tui_process_bridge_status",
                    return_value={"active": True, "pid": 1234, "reason": "running_binary_deleted"},
                ), patch(
                    "omnidoer.omni_control.tui_legacy_relay.legacy_tui_relay_status",
                    return_value={"active": True, "transport": "tmux", "pane_id": "%1"},
                ):
                    visible = handler._visible_requests(RequestStore(), None)

                console_requests = [request for request in visible if request.request_type == "console_restart"]
                self.assertEqual(len(console_requests), 1)
                self.assertEqual(console_requests[0].status, "pending")
                self.assertEqual(console_requests[0].structured_details["activation_action"], "restart_current_console")
                self.assertTrue(console_requests[0].structured_details["restart_current_console_available"])

                with patch("omnidoer.omni_control.chat_runner.live_tui_bridge_active", return_value=False), patch(
                    "omnidoer.omni_control.chat_runner.live_tui_session_active",
                    return_value=True,
                ), patch(
                    "omnidoer.omni_control.chat_runner.native_console_bridge_install_status",
                    return_value={"ready": True, "reason": "ready"},
                ), patch(
                    "omnidoer.omni_control.chat_runner.active_tui_process_bridge_status",
                    return_value={"active": True, "pid": 1234, "reason": "running_binary_deleted"},
                ), patch(
                    "omnidoer.omni_control.tui_legacy_relay.legacy_tui_relay_status",
                    return_value={"active": True, "transport": "tmux", "pane_id": "%1"},
                ):
                    visible_again = handler._visible_requests(RequestStore(), None)
                self.assertEqual(
                    [request.request_id for request in visible_again if request.request_type == "console_restart"],
                    [console_requests[0].request_id],
                )
            finally:
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_visible_requests_does_not_create_console_restart_when_native_sync_active(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            config = build_config(host="127.0.0.1", port=8787)
            server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
            server.omnidoer_config = config  # type: ignore[attr-defined]
            server.omnidoer_chat_thread_id = "thread_active"  # type: ignore[attr-defined]
            handler = object.__new__(ControlHandler)
            handler.server = server
            try:
                with patch("omnidoer.omni_control.chat_runner.live_tui_bridge_active", return_value=True), patch(
                    "omnidoer.omni_control.chat_runner.live_tui_session_active",
                    return_value=True,
                ), patch(
                    "omnidoer.omni_control.chat_runner.native_console_bridge_install_status",
                    return_value={"ready": True, "reason": "ready"},
                ), patch(
                    "omnidoer.omni_control.chat_runner.active_tui_process_bridge_status",
                    return_value={"active": True, "pid": 1234, "reason": "native_bridge_active"},
                ), patch(
                    "omnidoer.omni_control.chat_runner.active_mcp_sidecar_status",
                    return_value={"active": True, "restart_required": False, "browser_takeover_relay_current": True, "reason": "ready"},
                ):
                    visible = handler._visible_requests(RequestStore(), None)
                self.assertEqual([request for request in visible if request.request_type == "console_restart"], [])
                self.assertEqual([request for request in RequestStore().list() if request.request_type == "console_restart"], [])
            finally:
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_visible_requests_creates_console_restart_when_mcp_sidecar_is_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            config = build_config(host="127.0.0.1", port=8787)
            server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
            server.omnidoer_config = config  # type: ignore[attr-defined]
            server.omnidoer_chat_thread_id = "thread_active"  # type: ignore[attr-defined]
            handler = object.__new__(ControlHandler)
            handler.server = server
            try:
                with patch("omnidoer.omni_control.chat_runner.live_tui_bridge_active", return_value=True), patch(
                    "omnidoer.omni_control.chat_runner.live_tui_session_active",
                    return_value=True,
                ), patch(
                    "omnidoer.omni_control.chat_runner.native_console_bridge_install_status",
                    return_value={"ready": True, "reason": "ready"},
                ), patch(
                    "omnidoer.omni_control.chat_runner.active_tui_process_bridge_status",
                    return_value={"active": True, "pid": 1234, "reason": "native_bridge_active"},
                ), patch(
                    "omnidoer.omni_control.chat_runner.active_mcp_sidecar_status",
                    return_value={
                        "active": True,
                        "restart_required": True,
                        "browser_takeover_relay_current": False,
                        "reason": "source_updated_after_sidecar_start",
                    },
                ):
                    visible = handler._visible_requests(RequestStore(), None)
                restart_requests = [request for request in visible if request.request_type == "console_restart"]
                self.assertEqual(len(restart_requests), 1)
                details = restart_requests[0].structured_details
                self.assertFalse(details["requires_restart_for_native_sync"])
                self.assertTrue(details["requires_restart_for_browser_takeover_relay"])
                self.assertTrue(details["restart_browser_takeover_relay_available"])
            finally:
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_takeover_release_queues_continue_instruction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            config = build_config(host="127.0.0.1", port=8787)
            server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
            server.omnidoer_config = config  # type: ignore[attr-defined]
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                takeover = RequestStore().create(
                    "human_takeover",
                    origin="https://example.com",
                    top_level_url="https://example.com/work",
                    action_summary="user controls browser",
                    browser_context_id="browser-context",
                )
                release = urllib_request.Request(
                    f"http://127.0.0.1:{server.server_address[1]}/api/requests/{takeover.request_id}/release",
                    data=b"{}",
                    headers={"content-type": "application/json"},
                    method="POST",
                )
                with urllib_request.urlopen(release, timeout=5) as response:
                    payload = json.loads(response.read().decode())
                self.assertEqual(payload["status"], "released")
                self.assertEqual(payload["agent_continue"]["message"]["role"], "user")
                self.assertTrue(payload["agent_continue"]["message"]["client_message_id"].startswith("control_continue_"))
                self.assertEqual(ChatStore().list()[0].client_message_id, payload["agent_continue"]["message"]["client_message_id"])
                self.assertFalse(payload["agent_continue"]["live_console_delivery"]["secret_exposed_to_model"])
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home


if __name__ == "__main__":
    unittest.main()
