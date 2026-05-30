import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from omnidoer.omni_audit.audit import AuditLog
from omnidoer.omni_broker.broker import SecretBroker
from omnidoer.omni_control.requests import RequestStore
from omnidoer.omni_control.secure_channel import ReplayGuard
from omnidoer.omni_control.devices import DeviceStore
from omnidoer.omni_control.sessions import SessionStore
from omnidoer.omni_control.tasks import TaskStore


class CliTest(unittest.TestCase):
    def run_cli(self, args: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        merged = os.environ.copy()
        if env:
            merged.update(env)
        return subprocess.run(
            [sys.executable, "-m", "omnidoer.omni_cli.main", *args],
            cwd=Path(__file__).resolve().parents[1],
            env=merged,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_help(self) -> None:
        result = self.run_cli(["--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("doctor", result.stdout)

    def test_init_creates_private_state_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "state"
            result = self.run_cli(["init"], env={"OMNIDOER_HOME": str(home)})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(stat.S_IMODE(home.stat().st_mode), 0o700)

    def test_control_input_secret_does_not_echo_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            env = {
                "OMNIDOER_HOME": tmp,
                "OMNIDOER_CONTROL_TEST_MODE": "1",
                "OMNIDOER_TEST_USERNAME": "demo",
                "OMNIDOER_TEST_PASSWORD": "super-secret-password",
            }
            try:
                store = RequestStore(Path(tmp) / "control_requests.json")
                req = store.create(
                    "credential",
                    origin="http://127.0.0.1:8765",
                    top_level_url="http://127.0.0.1:8765/login",
                    action_summary="login",
                    requested_fields=["username", "password"],
                    allowed_device_id="dev_cli",
                )
                result = self.run_cli(["control", "input-secret", req.request_id], env=env)
                self.assertEqual(result.returncode, 0, result.stderr)
                combined = result.stdout + result.stderr
                self.assertNotIn("super-secret-password", combined)
                self.assertIn("Secret Broker", combined)
                stored = RequestStore(Path(tmp) / "control_requests.json").get(req.request_id)
                self.assertEqual(stored.response_ciphertext["device_id"], "dev_cli")
                self.assertEqual(float(stored.response_ciphertext["expires_at"]), stored.expires_at)
                broker = SecretBroker(
                    store=RequestStore(Path(tmp) / "control_requests.json"),
                    replay_guard=ReplayGuard(Path(tmp) / "replay.json"),
                    audit=AuditLog(Path(tmp) / "audit.jsonl"),
                )
                received = broker.receive_from_control_client(req.request_id)
                self.assertEqual(received["fields"], ["username", "password"])
                self.assertNotIn("super-secret-password", repr(received))
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_control_captcha_challenge_does_not_store_answer_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "OMNIDOER_HOME": tmp,
                "OMNIDOER_CHALLENGE_TEST_MODE": "1",
                "OMNIDOER_TEST_CAPTCHA_ACK": "user-completed-secret",
            }
            store = RequestStore(Path(tmp) / "control_requests.json")
            req = store.create(
                "captcha",
                origin="http://127.0.0.1:8765",
                top_level_url="http://127.0.0.1:8765/captcha",
                action_summary="captcha",
                requested_fields=["ack"],
                challenge_type="captcha",
            )
            result = self.run_cli(["control", "challenge", req.request_id], env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            combined = result.stdout + result.stderr
            self.assertNotIn("user-completed-secret", combined)
            stored = RequestStore(Path(tmp) / "control_requests.json").get(req.request_id)
            self.assertEqual(stored.status, "challenge_completed")
            self.assertIsNone(stored.response_ciphertext)

    def test_control_submit_task_queues_local_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {"OMNIDOER_HOME": tmp}
            result = self.run_cli(["control", "submit-task", "Use the local demo"], env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("queued task", result.stdout)
            tasks = TaskStore(Path(tmp) / "control_tasks.json").list()
            self.assertEqual(len(tasks), 1)
            self.assertEqual(tasks[0].text, "Use the local demo")

    def test_cloud_direct_cli_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {"OMNIDOER_HOME": tmp}
            refused = self.run_cli(["control", "serve", "--host", "0.0.0.0", "--port", "8787"], env=env)
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("0.0.0.0 requires explicit --cloud-direct", refused.stderr + refused.stdout)
            pair = self.run_cli(
                ["control", "pair", "--print-qr", "--expires", "10m", "--public-url", "https://agent.example.com"],
                env=env,
            )
            self.assertEqual(pair.returncode, 0, pair.stderr)
            self.assertIn("pairing_url=https://agent.example.com/pair", pair.stdout)
            self.assertIn("broker_fingerprint=", pair.stdout)
            self.assertIn("Only pair devices you control", pair.stdout)
            self.assertIn("qr_ascii_begin", pair.stdout)
            self.assertIn("qr_ascii_end", pair.stdout)
            self.assertGreater(pair.stdout.count("##"), 100)
            status = self.run_cli(["control", "security-status"], env=env)
            self.assertEqual(status.returncode, 0, status.stderr)
            self.assertIn('"mcp_publicly_exposed": false', status.stdout)

    def test_control_device_and_session_cli_redacts_tokens(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {"OMNIDOER_HOME": tmp}
            device = DeviceStore(Path(tmp) / "control_devices.json").register(name="Phone", public_key="pub")
            session, token = SessionStore(Path(tmp) / "control_sessions.json").create(device_id=device.device_id)

            devices = self.run_cli(["control", "devices"], env=env)
            self.assertEqual(devices.returncode, 0, devices.stderr)
            self.assertIn(device.device_id, devices.stdout)
            self.assertNotIn("pub", devices.stdout)

            sessions = self.run_cli(["control", "sessions"], env=env)
            self.assertEqual(sessions.returncode, 0, sessions.stderr)
            self.assertIn(session.session_id, sessions.stdout)
            self.assertNotIn(token, sessions.stdout)
            self.assertNotIn("token_hash", sessions.stdout)

            revoked = self.run_cli(["control", "revoke-device", device.device_id], env=env)
            self.assertEqual(revoked.returncode, 0, revoked.stderr)
            self.assertIn("revoked_sessions=1", revoked.stdout)


if __name__ == "__main__":
    unittest.main()
