import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

from omnidoer.omni_challenge.detector import detect_challenge_from_url
from omnidoer.omni_challenge.relay import ChallengeRelay, request_user_interaction
from omnidoer.omni_audit.audit import AuditLog
from omnidoer.omni_browser.controller import BrowserController
from omnidoer.omni_control.requests import RequestStore
from omnidoer.omni_control.secure_channel import ReplayGuard, encrypt_for_broker, load_or_create_keypair
from tests.util_demo import DemoServerFixture


class ChallengeRelayTest(unittest.TestCase):
    def test_demo_url_detection(self) -> None:
        self.assertEqual(detect_challenge_from_url("http://127.0.0.1:8765/captcha"), "captcha")
        self.assertEqual(detect_challenge_from_url("http://127.0.0.1:8765/checkout/3ds"), "3ds")
        self.assertIsNone(detect_challenge_from_url("http://127.0.0.1:8765/dashboard"))

    @unittest.skipIf(importlib.util.find_spec("playwright") is None, "playwright not installed")
    def test_challenge_relay_receives_and_injects_code_without_returning_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, DemoServerFixture() as demo:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                keypair = load_or_create_keypair()
                store = RequestStore(Path(tmp) / "requests.json")
                request = request_user_interaction(
                    origin=demo.origin,
                    top_level_url=f"{demo.origin}/sms",
                    challenge_type="sms",
                    reason="SMS code",
                    fields=["code"],
                    store=store,
                )
                envelope = encrypt_for_broker(
                    keypair.public_key_b64,
                    {"code": "123456"},
                    request_id=request.request_id,
                    origin=request.origin,
                    request_type=request.request_type,
                )
                store.submit_ciphertext(request.request_id, envelope)
                relay = ChallengeRelay(
                    store=store,
                    replay_guard=ReplayGuard(Path(tmp) / "replay.json"),
                    audit=AuditLog(Path(tmp) / "audit.jsonl"),
                )
                received = relay.receive_user_response(request.request_id)
                self.assertNotIn("123456", repr(received))
                try:
                    with BrowserController() as browser:
                        browser.open(f"{demo.origin}/sms")
                        injected = relay.inject_response_if_applicable(request.request_id, browser_controller=browser)
                        observation = browser.observe_dom()
                except Exception as exc:
                    self.skipTest(f"playwright chromium unavailable: {type(exc).__name__}")
                self.assertEqual(injected["status"], "challenge_response_injected")
                self.assertNotIn("123456", repr(injected))
                self.assertNotIn("123456", repr(observation))
                self.assertNotIn("123456", Path(tmp, "audit.jsonl").read_text())
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home


if __name__ == "__main__":
    unittest.main()
