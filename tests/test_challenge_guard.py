import os
import tempfile
import unittest
from pathlib import Path

from omnidoer.omni_agent.challenge_guard import resolve_current_browser_challenge
from omnidoer.omni_control.requests import RequestStore
from omnidoer.omni_takeover.models import InputEvent


class FakeGuardBrowser:
    def __init__(self, *, url: str, challenge_type: str | None = None, antibot: bool = False):
        self.url = url
        self.challenge_type = challenge_type
        self.antibot = antibot
        self.filled: list[tuple[str, str, bool]] = []
        self.events: list[InputEvent] = []
        self.keys: list[str] = []
        self.clicks: list[str] = []

    def current_url(self) -> str:
        return self.url

    def detect_antibot(self) -> bool:
        return self.antibot

    def detect_challenge(self) -> str | None:
        return self.challenge_type

    def takeover_frame(self) -> dict:
        return {
            "content_type": "image/png",
            "data_b64": "frame",
            "for_control_client_only": True,
            "not_for_llm": True,
        }

    def click(self, selector: str) -> dict:
        self.clicks.append(selector)
        return {"status": "clicked", "secret_exposed_to_model": False}

    def apply_user_input_event(self, event: InputEvent) -> dict:
        self.events.append(event)
        return {"status": "event_applied", "secret_exposed_to_model": False}

    def fill_field(self, selector: str, value: str, *, secret: bool = False) -> dict:
        self.filled.append((selector, value, secret))
        return {"status": "filled", "secret": secret, "secret_exposed_to_model": False}

    def press_key(self, key: str) -> dict:
        self.keys.append(key)
        return {"status": "key_pressed", "secret_exposed_to_model": False}


class ChallengeGuardTest(unittest.TestCase):
    def test_totp_routes_to_challenge_relay_without_returning_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old = {key: os.environ.get(key) for key in ("OMNIDOER_HOME", "OMNIDOER_CHALLENGE_TEST_MODE", "OMNIDOER_TEST_SMS_CODE")}
            os.environ["OMNIDOER_HOME"] = tmp
            os.environ["OMNIDOER_CHALLENGE_TEST_MODE"] = "1"
            os.environ["OMNIDOER_TEST_SMS_CODE"] = "987654"
            try:
                store = RequestStore(Path(tmp) / "requests.json")
                browser = FakeGuardBrowser(url="http://127.0.0.1:8765/totp", challenge_type="totp")
                result = resolve_current_browser_challenge(
                    origin="http://127.0.0.1:8765",
                    browser=browser,
                    browser_context_id="fake",
                    store=store,
                )
                self.assertEqual(result.status, "challenge_completed")
                self.assertEqual(result.mode, "challenge_relay")
                self.assertTrue(result.agent_resumed)
                self.assertFalse(result.secret_exposed_to_model)
                self.assertNotIn("987654", repr(result.to_public_dict()))
                self.assertEqual(browser.clicks, ["button[type='submit']"])
                self.assertTrue(browser.filled[0][2])
                raw_audit = (Path(tmp) / "audit.jsonl").read_text()
                self.assertIn("agent_resumed_after_challenge", raw_audit)
                self.assertNotIn("987654", raw_audit)
            finally:
                for key, value in old.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value

    def test_antibot_routes_to_human_takeover_without_logging_user_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old = {key: os.environ.get(key) for key in ("OMNIDOER_HOME", "OMNIDOER_TAKEOVER_TEST_MODE", "OMNIDOER_TEST_TAKEOVER_ACTIONS")}
            os.environ["OMNIDOER_HOME"] = tmp
            os.environ["OMNIDOER_TAKEOVER_TEST_MODE"] = "1"
            os.environ["OMNIDOER_TEST_TAKEOVER_ACTIONS"] = "type:takeover-sensitive-text;release"
            try:
                store = RequestStore(Path(tmp) / "requests.json")
                browser = FakeGuardBrowser(url="http://127.0.0.1:8765/antibot", antibot=True)
                result = resolve_current_browser_challenge(
                    origin="http://127.0.0.1:8765",
                    browser=browser,
                    browser_context_id="fake",
                    store=store,
                )
                self.assertEqual(result.status, "user_completed_takeover")
                self.assertEqual(result.mode, "human_takeover")
                self.assertEqual(result.challenge_type, "antibot")
                self.assertTrue(result.agent_resumed)
                self.assertFalse(result.secret_exposed_to_model)
                raw_audit = (Path(tmp) / "audit.jsonl").read_text()
                self.assertIn("agent_resumed_after_takeover", raw_audit)
                self.assertIn("takeover_input_event", raw_audit)
                self.assertNotIn("takeover-sensitive-text", raw_audit)
            finally:
                for key, value in old.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value


if __name__ == "__main__":
    unittest.main()
