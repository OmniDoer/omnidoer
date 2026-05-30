import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from omnidoer.omni_control.requests import RequestStore
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

    def test_control_input_secret_does_not_echo_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "OMNIDOER_HOME": tmp,
                "OMNIDOER_CONTROL_TEST_MODE": "1",
                "OMNIDOER_TEST_USERNAME": "demo",
                "OMNIDOER_TEST_PASSWORD": "super-secret-password",
            }
            store = RequestStore(Path(tmp) / "control_requests.json")
            req = store.create(
                "credential",
                origin="http://127.0.0.1:8765",
                top_level_url="http://127.0.0.1:8765/login",
                action_summary="login",
                requested_fields=["username", "password"],
            )
            result = self.run_cli(["control", "input-secret", req.request_id], env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            combined = result.stdout + result.stderr
            self.assertNotIn("super-secret-password", combined)
            self.assertIn("Secret Broker", combined)

    def test_control_submit_task_queues_local_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {"OMNIDOER_HOME": tmp}
            result = self.run_cli(["control", "submit-task", "Use the local demo"], env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("queued task", result.stdout)
            tasks = TaskStore(Path(tmp) / "control_tasks.json").list()
            self.assertEqual(len(tasks), 1)
            self.assertEqual(tasks[0].text, "Use the local demo")


if __name__ == "__main__":
    unittest.main()
