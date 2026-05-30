import importlib.util
import unittest

from omnidoer.omni_mcp.runtime import reset_runtime_for_tests
from omnidoer.omni_mcp.tools import call_tool
from tests.util_demo import DemoServerFixture


@unittest.skipIf(importlib.util.find_spec("playwright") is None, "playwright not installed")
class McpBrowserToolsTest(unittest.TestCase):
    def tearDown(self) -> None:
        reset_runtime_for_tests()

    def test_mcp_browser_open_observe_and_origin(self) -> None:
        with DemoServerFixture() as demo:
            opened = call_tool("browser.open", {"url": f"{demo.origin}/login"})
            if opened.get("status") == "unavailable":
                self.skipTest("playwright chromium unavailable")
            self.assertEqual(opened["status"], "opened")
            origin = call_tool("browser.current_origin", {})
            self.assertEqual(origin["origin"], demo.origin)
            typed = call_tool("browser.type_text", {"selector": "#email", "text": "demo"})
            self.assertEqual(typed["status"], "typed")
            rejected = call_tool("browser.type_text", {"selector": "#password", "text": "not-for-model", "secret": True})
            self.assertEqual(rejected["status"], "rejected")
            observation = call_tool("browser.observe", {})
            self.assertEqual(observation["status"], "ok")
            self.assertIn("nodes", observation["observation"])
            self.assertNotIn("not-for-model", repr(observation))

    def test_mcp_browser_detects_challenge_and_antibot(self) -> None:
        with DemoServerFixture() as demo:
            opened = call_tool("browser.open", {"url": f"{demo.origin}/captcha"})
            if opened.get("status") == "unavailable":
                self.skipTest("playwright chromium unavailable")
            challenge = call_tool("browser.detect_challenge", {})
            self.assertEqual(challenge["challenge_type"], "captcha")
            self.assertTrue(challenge["requires_user_interaction"])
            call_tool("browser.open", {"url": f"{demo.origin}/antibot"})
            antibot = call_tool("browser.detect_antibot", {})
            self.assertTrue(antibot["antibot_detected"])
            self.assertTrue(antibot["requires_human_takeover"])


if __name__ == "__main__":
    unittest.main()
