import json
import os
import subprocess
import sys
import tempfile
import unittest

from omnidoer.omni_control.tasks import TaskStore
from omnidoer.omni_mcp.tools import ALLOWED_TOOLS, call_tool, forbidden_tool_names


class McpToolsTest(unittest.TestCase):
    def test_allowed_tools_exclude_forbidden(self) -> None:
        self.assertTrue(forbidden_tool_names().isdisjoint(ALLOWED_TOOLS))
        self.assertIn("credential.request_from_user", ALLOWED_TOOLS)
        self.assertIn("takeover.request_user_control", ALLOWED_TOOLS)
        self.assertIn("control.next_user_task", ALLOWED_TOOLS)

    def test_tool_result_status_only(self) -> None:
        result = call_tool("credential.request_from_user", {})
        self.assertFalse(result["secret_exposed_to_model"])
        self.assertNotIn("password", result)

    def test_next_user_task_claims_local_control_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                task = TaskStore().create("Use OmniDoer tools on the local demo")
                result = call_tool("control.next_user_task", {})
                self.assertEqual(result["status"], "ok")
                self.assertEqual(result["task"]["task_id"], task.task_id)
                self.assertEqual(result["task"]["status"], "claimed")
                self.assertFalse(result["submitted_to_openai_api_by_control_client"])
                empty = call_tool("control.next_user_task", {})
                self.assertEqual(empty["status"], "empty")
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_mcp_self_test_command(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "omnidoer.omni_cli.main", "mcp", "serve", "--self-test"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("mcp self-test passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
