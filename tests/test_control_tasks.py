import json
import os
import stat
import tempfile
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib import request as urllib_request

from omnidoer.omni_control.server import ControlHandler
from omnidoer.omni_control.tasks import TaskStore


class ControlTaskStoreTest(unittest.TestCase):
    def test_task_lifecycle_and_single_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = TaskStore(Path(tmp) / "tasks.json")
            task = store.create("Download the local demo invoice")
            self.assertEqual(stat.S_IMODE(store.path.stat().st_mode), 0o600)
            self.assertEqual(task.status, "pending")
            claimed = store.next_pending()
            self.assertIsNotNone(claimed)
            assert claimed is not None
            self.assertEqual(claimed.task_id, task.task_id)
            self.assertEqual(claimed.status, "claimed")
            self.assertIsNone(store.next_pending())
            completed = store.complete(task.task_id)
            self.assertEqual(completed.status, "completed")

    def test_task_text_is_not_for_secret_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            task = TaskStore(Path(tmp) / "tasks.json").create("Run a local demo task")
            public = task.to_public_dict()
            self.assertFalse(public["secret_fields_allowed"])
            self.assertFalse(public["submitted_to_openai_api_by_control_client"])


class ControlTaskApiTest(unittest.TestCase):
    def test_control_server_task_api(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                create = urllib_request.Request(
                    f"{base}/api/tasks",
                    data=json.dumps({"text": "Queue a Codex task"}).encode(),
                    headers={"content-type": "application/json"},
                    method="POST",
                )
                with urllib_request.urlopen(create, timeout=5) as response:
                    self.assertEqual(response.status, 201)
                    task = json.loads(response.read().decode())
                self.assertEqual(task["status"], "pending")

                next_req = urllib_request.Request(
                    f"{base}/api/tasks/next",
                    data=json.dumps({"claim": True}).encode(),
                    headers={"content-type": "application/json"},
                    method="POST",
                )
                with urllib_request.urlopen(next_req, timeout=5) as response:
                    claimed = json.loads(response.read().decode())
                self.assertEqual(claimed["status"], "claimed")
                self.assertEqual(claimed["task_id"], task["task_id"])

                with urllib_request.urlopen(f"{base}/api/tasks", timeout=5) as response:
                    tasks = json.loads(response.read().decode())
                self.assertEqual(tasks[0]["status"], "claimed")
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home


if __name__ == "__main__":
    unittest.main()
