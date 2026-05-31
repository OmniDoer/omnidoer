import json
import tempfile
import unittest
from http.server import ThreadingHTTPServer
from threading import Thread
from unittest.mock import patch
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
                self.assertTrue(payload["chat_runner"]["legacy_tui_relay"]["active"])
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
            self.assertFalse(payload["chat_runner"]["legacy_tui_relay"]["active"])
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
