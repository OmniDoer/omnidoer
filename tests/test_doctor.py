import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from omnidoer.omni_cli.doctor import _check_chromium, _run_codex_login_status, collect_checks


class FakeChromium:
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail

    def launch(self, *, headless: bool):
        if self.should_fail:
            raise RuntimeError("missing chromium")
        return SimpleNamespace(close=lambda: None)


class FakePlaywrightContext:
    def __init__(self, should_fail: bool = False):
        self.chromium = FakeChromium(should_fail=should_fail)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class DoctorTest(unittest.TestCase):
    def test_doctor_does_not_require_api_key(self) -> None:
        old = os.environ.pop("OPENAI_API_KEY", None)
        try:
            checks = collect_checks()
            by_name = {check.name: check for check in checks}
            self.assertIn("openai_api_key", by_name)
            self.assertIn("OK", by_name["openai_api_key"].detail)
            self.assertNotEqual(by_name["openai_api_key"].status, "required")
        finally:
            if old is not None:
                os.environ["OPENAI_API_KEY"] = old

    def test_doctor_reports_api_key_set_but_not_used(self) -> None:
        old = os.environ.get("OPENAI_API_KEY")
        os.environ["OPENAI_API_KEY"] = "not-a-real-key"
        try:
            checks = collect_checks()
            openai_check = {check.name: check for check in checks}["openai_api_key"]
            self.assertEqual(openai_check.status, "set_not_used")
            self.assertIn("will not use it by default", openai_check.detail)
            self.assertNotIn("not-a-real-key", openai_check.detail)
        finally:
            if old is None:
                os.environ.pop("OPENAI_API_KEY", None)
            else:
                os.environ["OPENAI_API_KEY"] = old

    def test_codex_login_status_classifies_chatgpt_mode(self) -> None:
        with patch("shutil.which", return_value="/usr/bin/codex"), patch(
            "subprocess.run",
            return_value=SimpleNamespace(stdout="Logged in using ChatGPT\n", returncode=0),
        ):
            mode, detail = _run_codex_login_status()
        self.assertEqual(mode, "chatgpt")
        self.assertIn("subscription-backed", detail)

    def test_codex_login_status_classifies_api_key_mode(self) -> None:
        with patch("shutil.which", return_value="/usr/bin/codex"), patch(
            "subprocess.run",
            return_value=SimpleNamespace(stdout="Logged in using API key\n", returncode=0),
        ):
            mode, detail = _run_codex_login_status()
        self.assertEqual(mode, "api_key")
        self.assertIn("OpenAI Platform API billing", detail)

    def test_codex_login_status_does_not_print_status_output(self) -> None:
        with patch("shutil.which", return_value="/usr/bin/codex"), patch(
            "subprocess.run",
            return_value=SimpleNamespace(stdout="access token secret-token-value\n", returncode=0),
        ):
            mode, detail = _run_codex_login_status()
        self.assertEqual(mode, "unknown")
        self.assertNotIn("secret-token-value", detail)

    def test_chromium_check_launches_browser(self) -> None:
        with patch("playwright.sync_api.sync_playwright", return_value=FakePlaywrightContext()):
            check = _check_chromium()
        self.assertEqual(check.name, "chromium")
        self.assertEqual(check.status, "ok")
        self.assertIn("launched", check.detail)

    def test_chromium_check_reports_launch_failure_without_secret_output(self) -> None:
        with patch("playwright.sync_api.sync_playwright", return_value=FakePlaywrightContext(should_fail=True)):
            check = _check_chromium()
        self.assertEqual(check.name, "chromium")
        self.assertEqual(check.status, "missing")
        self.assertIn("playwright install chromium", check.detail)


if __name__ == "__main__":
    unittest.main()
