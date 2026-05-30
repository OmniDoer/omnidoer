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
        self.assertIn("registration.request_user_handoff", ALLOWED_TOOLS)
        self.assertIn("browser.select", ALLOWED_TOOLS)
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

    def test_request_tools_create_control_requests_without_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                common = {"origin": "http://127.0.0.1:8765", "top_level_url": "http://127.0.0.1:8765/login"}
                credential = call_tool(
                    "credential.request_from_user",
                    {**common, "reason": "login", "fields": ["username", "password"]},
                )
                self.assertEqual(credential["status"], "credential_request_created")
                self.assertNotIn("super-secret", repr(credential))

                challenge = call_tool(
                    "challenge.request_user_interaction",
                    {**common, "challenge_type": "sms", "reason": "verify user"},
                )
                self.assertEqual(challenge["status"], "challenge_request_created")
                status = call_tool("challenge.status", {"request_id": challenge["request"]["request_id"]})
                self.assertEqual(status["status"], "pending")
                self.assertNotIn("code", status)

                takeover = call_tool("takeover.request_user_control", {**common, "reason": "anti-bot page"})
                self.assertEqual(takeover["status"], "takeover_request_created")
                takeover_status = call_tool("takeover.status", {"request_id": takeover["request"]["request_id"]})
                self.assertEqual(takeover_status["control_owner"], "user")

                registration = call_tool(
                    "registration.request_user_handoff",
                    {**common, "top_level_url": "http://127.0.0.1:8765/register", "reason": "new account required"},
                )
                self.assertEqual(registration["status"], "registration_handoff_created")
                self.assertEqual(registration["request"]["request_type"], "account_registration")
                self.assertTrue(registration["agent_paused"])
                self.assertNotIn("password", repr(registration))

                approval = call_tool(
                    "approval.request",
                    {**common, "action_summary": "mock payment", "risk_level": "high", "structured_details": {"amount": "12.34"}},
                )
                self.assertEqual(approval["status"], "approval_request_created")
                self.assertEqual(approval["request"]["structured_details"]["amount"], "12.34")
                payment = call_tool("payment.prepare_review", common)
                self.assertTrue(payment["requires_user_approval"])
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
