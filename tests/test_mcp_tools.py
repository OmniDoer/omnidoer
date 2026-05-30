import json
import subprocess
import sys
import unittest

from omnidoer.omni_mcp.tools import ALLOWED_TOOLS, call_tool, forbidden_tool_names


class McpToolsTest(unittest.TestCase):
    def test_allowed_tools_exclude_forbidden(self) -> None:
        self.assertTrue(forbidden_tool_names().isdisjoint(ALLOWED_TOOLS))
        self.assertIn("credential.request_from_user", ALLOWED_TOOLS)
        self.assertIn("takeover.request_user_control", ALLOWED_TOOLS)

    def test_tool_result_status_only(self) -> None:
        result = call_tool("credential.request_from_user", {})
        self.assertFalse(result["secret_exposed_to_model"])
        self.assertNotIn("password", result)

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
