import importlib.util
import unittest

from omnidoer.omni_browser.challenge_view import challenge_view
from omnidoer.omni_browser.forms import resolve_form_action
from omnidoer.omni_browser.takeover_view import takeover_view


class BrowserControllerContractTest(unittest.TestCase):
    def test_form_action_resolution(self) -> None:
        self.assertEqual(resolve_form_action("https://example.com/login", "/submit"), "https://example.com/submit")

    def test_challenge_view_not_for_llm(self) -> None:
        view = challenge_view("https://example.com", "https://example.com/captcha", "captcha")
        self.assertTrue(view["not_for_llm"])
        self.assertTrue(view["completed_by_user_required"])

    def test_takeover_view_pauses_agent(self) -> None:
        view = takeover_view("https://example.com", "https://example.com/antibot", "anti-bot")
        self.assertEqual(view["agent_status"], "paused")
        self.assertEqual(view["control_owner"], "user")
        self.assertTrue(view["not_for_llm"])

    @unittest.skipIf(importlib.util.find_spec("playwright") is None, "playwright not installed")
    def test_playwright_importable_when_installed(self) -> None:
        from omnidoer.omni_browser.controller import BrowserController

        self.assertIsNotNone(BrowserController)


if __name__ == "__main__":
    unittest.main()
