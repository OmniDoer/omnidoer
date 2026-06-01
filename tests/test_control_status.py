import json
import tempfile
import unittest
from http.server import ThreadingHTTPServer
from threading import Thread
from unittest.mock import patch
from urllib.error import HTTPError
from urllib import request as urllib_request

from omnidoer.omni_control.cloud import build_config
from omnidoer.omni_control.server import ControlHandler


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


if __name__ == "__main__":
    unittest.main()
