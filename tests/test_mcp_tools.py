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
        self.assertIn("credential.create_interactive", ALLOWED_TOOLS)
        self.assertIn("takeover.request_user_control", ALLOWED_TOOLS)
        self.assertIn("registration.request_user_handoff", ALLOWED_TOOLS)
        self.assertIn("browser.observe_accessibility", ALLOWED_TOOLS)
        self.assertIn("browser.select", ALLOWED_TOOLS)
        self.assertIn("browser.upload_file", ALLOWED_TOOLS)
        self.assertIn("control.create_pairing", ALLOWED_TOOLS)
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

    def test_create_pairing_tool_returns_short_lived_invite_without_long_lived_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                result = call_tool(
                    "control.create_pairing",
                    {"public_url": "https://agent.example.com", "expires": "30m"},
                )
                self.assertEqual(result["status"], "pairing_created")
                self.assertIn("https://agent.example.com/pair?code=", result["pairing_url"])
                self.assertTrue(result["one_time_pairing"])
                self.assertTrue(result["paired_sessions_are_cached"])
                self.assertTrue(result["pairing_code_model_visible"])
                self.assertFalse(result["secret_exposed_to_model"])
                self.assertNotIn("session_token", repr(result))
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

                interactive = call_tool(
                    "credential.create_interactive",
                    {**common, "reason": "first login", "fields": ["username", "password"]},
                )
                self.assertEqual(interactive["status"], "credential_request_created")
                self.assertEqual(interactive["request"]["request_type"], "credential")
                self.assertNotIn("password_value", repr(interactive))

                pat = call_tool(
                    "credential.request_from_user",
                    {
                        **common,
                        "reason": "GitHub token migration",
                        "fields": ["username", "password"],
                        "password_label": "GitHub PAT",
                    },
                )
                self.assertEqual(pat["status"], "credential_request_created")
                self.assertEqual(pat["request"]["requested_fields"], ["username", "password"])
                self.assertEqual(pat["request"]["structured_details"]["credential_labels"]["password"], "GitHub PAT")
                self.assertNotIn("token-value", repr(pat))

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
                policy = call_tool("policy.explain_current_block", {"action_type": "account_registration"})
                self.assertEqual(policy["decision"], "require_takeover")
                self.assertIn("registration", policy["reason"])
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

    def test_mcp_initialize_returns_standard_capabilities(self) -> None:
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2025-06-18"},
        }
        result = subprocess.run(
            [sys.executable, "-m", "omnidoer.omni_cli.main", "mcp", "serve"],
            input=json.dumps(request) + "\n",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=5,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        response = json.loads(result.stdout)
        self.assertEqual(response["id"], 1)
        self.assertEqual(response["result"]["protocolVersion"], "2025-06-18")
        self.assertIn("capabilities", response["result"])
        self.assertIn("tools", response["result"]["capabilities"])
        self.assertEqual(response["result"]["serverInfo"]["name"], "omnidoer")


if __name__ == "__main__":
    unittest.main()
