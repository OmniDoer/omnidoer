import tempfile
import time
import unittest
import stat
from pathlib import Path

from omnidoer.omni_control.requests import RequestStore, wait_for_request_completion
from omnidoer.omni_takeover.models import InputEvent


class ControlRequestTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.store = RequestStore(Path(self.tmp.name) / "requests.json")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_create_and_public_dict_excludes_ciphertext(self) -> None:
        req = self.store.create(
            "credential",
            origin="http://127.0.0.1:8765",
            top_level_url="http://127.0.0.1:8765/login",
            action_summary="login",
            requested_fields=["username", "password"],
            allowed_device_id="dev_phone",
        )
        self.assertEqual(req.status, "pending")
        public = req.to_public_dict()
        self.assertNotIn("response_ciphertext", public)
        self.assertEqual(public["allowed_device_id"], "dev_phone")
        self.assertFalse(public["secret_exposed_to_model"])
        mode = stat.S_IMODE(self.store.path.stat().st_mode)
        self.assertEqual(mode, 0o600)

    def test_public_structured_details_are_redacted(self) -> None:
        req = self.store.create(
            "payment_approval",
            origin="http://127.0.0.1:8765",
            top_level_url="http://127.0.0.1:8765/checkout",
            action_summary="pay",
            structured_details={"merchant": "Demo", "card": "4111 1111 1111 1111"},
        )
        public = req.to_public_dict()
        self.assertEqual(public["structured_details"]["merchant"], "Demo")
        self.assertEqual(public["structured_details"]["card"], "[REDACTED]")

    def test_ttl_expiry(self) -> None:
        req = self.store.create(
            "sms_code",
            origin="http://127.0.0.1:8765",
            top_level_url="http://127.0.0.1:8765/sms",
            action_summary="sms",
            ttl_seconds=-1,
        )
        self.assertEqual(self.store.get(req.request_id).status, "expired")

    def test_submit_is_single_use(self) -> None:
        req = self.store.create(
            "credential",
            origin="http://127.0.0.1:8765",
            top_level_url="http://127.0.0.1:8765/login",
            action_summary="login",
        )
        self.store.submit_ciphertext(req.request_id, {"ciphertext": "opaque"})
        with self.assertRaises(ValueError):
            self.store.submit_ciphertext(req.request_id, {"ciphertext": "opaque"})

    def test_completion_is_audited_and_waitable_without_exposing_ciphertext(self) -> None:
        req = self.store.create(
            "credential",
            origin="https://github.com",
            top_level_url="https://github.com/settings/tokens",
            action_summary="Migrate PAT",
        )
        self.store.submit_ciphertext(req.request_id, {"ciphertext": "secret-never-echo"})
        completed = wait_for_request_completion(req.request_id, store=self.store, require_ciphertext=True)
        public = completed.to_public_dict()
        self.assertEqual(completed.status, "fulfilled")
        self.assertNotIn("response_ciphertext", public)
        audit = (Path(self.tmp.name) / "audit.log").read_text()
        self.assertIn("control_request_created", audit)
        self.assertIn("control_request_completed", audit)
        self.assertIn('"has_ciphertext": true', audit)
        self.assertNotIn("secret-never-echo", audit)

    def test_expired_requests_cannot_transition(self) -> None:
        approval = self.store.create(
            "payment_approval",
            origin="http://127.0.0.1:8765",
            top_level_url="http://127.0.0.1:8765/checkout",
            action_summary="approve",
            ttl_seconds=-1,
        )
        with self.assertRaises(ValueError):
            self.store.approve(approval.request_id)
        self.assertEqual(self.store.get(approval.request_id).status, "expired")

        challenge = self.store.create(
            "sms_code",
            origin="http://127.0.0.1:8765",
            top_level_url="http://127.0.0.1:8765/sms",
            action_summary="sms",
            ttl_seconds=-1,
        )
        with self.assertRaises(ValueError):
            self.store.mark_challenge_completed(challenge.request_id)
        self.assertEqual(self.store.get(challenge.request_id).status, "expired")

        takeover = self.store.create(
            "human_takeover",
            origin="http://127.0.0.1:8765",
            top_level_url="http://127.0.0.1:8765/antibot",
            action_summary="take over",
            ttl_seconds=-1,
        )
        with self.assertRaises(ValueError):
            self.store.release_takeover(takeover.request_id)
        self.assertEqual(self.store.get(takeover.request_id).status, "expired")

    def test_approval_is_consumed_once_after_user_approval(self) -> None:
        approval = self.store.create(
            "payment_approval",
            origin="https://checkout.example",
            top_level_url="https://checkout.example/pay",
            action_summary="approve",
        )
        approved = self.store.approve(approval.request_id)
        self.assertEqual(approved.status, "approved")
        self.assertFalse(approved.used)
        consumed = self.store.consume_approval(approval.request_id)
        self.assertEqual(consumed.status, "consumed")
        self.assertTrue(consumed.used)
        with self.assertRaises(ValueError) as reused:
            self.store.consume_approval(approval.request_id)
        self.assertEqual(str(reused.exception), "request already used")

    def test_user_control_and_fulfilled_requests_expire_in_lists(self) -> None:
        takeover = self.store.create(
            "account_registration",
            origin="https://example.com",
            top_level_url="https://example.com/register",
            action_summary="register",
            ttl_seconds=-1,
        )
        challenge = self.store.create(
            "sms_code",
            origin="https://example.com",
            top_level_url="https://example.com/sms",
            action_summary="sms",
            ttl_seconds=60,
        )
        self.store.submit_ciphertext(challenge.request_id, {"ciphertext": "opaque"})
        loaded = self.store._load()
        loaded[challenge.request_id].expires_at = time.time() - 1
        self.store._save(loaded)

        self.assertEqual(self.store.get(takeover.request_id).status, "expired")
        self.assertEqual(self.store.get(challenge.request_id).status, "expired")
        active_ids = {request.request_id for request in self.store.list()}
        self.assertNotIn(takeover.request_id, active_ids)
        self.assertNotIn(challenge.request_id, active_ids)

    def test_fulfilled_challenge_can_be_marked_completed_once(self) -> None:
        req = self.store.create(
            "sms_code",
            origin="http://127.0.0.1:8765",
            top_level_url="http://127.0.0.1:8765/sms",
            action_summary="sms",
        )
        self.store.submit_ciphertext(req.request_id, {"ciphertext": "opaque"})
        completed = self.store.mark_challenge_completed(req.request_id)
        self.assertEqual(completed.status, "challenge_completed")
        self.assertTrue(completed.completed_by_user)
        with self.assertRaises(ValueError):
            self.store.mark_challenge_completed(req.request_id)

    def test_takeover_state_flow(self) -> None:
        req = self.store.create(
            "human_takeover",
            origin="http://127.0.0.1:8765",
            top_level_url="http://127.0.0.1:8765/antibot",
            action_summary="take over",
            takeover_reason="high intensity anti-bot",
        )
        self.assertEqual(req.status, "user_control")
        self.assertEqual(req.control_owner, "user")
        released = self.store.release_takeover(req.request_id)
        self.assertEqual(released.status, "released")
        self.assertEqual(released.control_owner, "agent")
        self.assertTrue(released.completed_by_user)
        self.assertFalse(released.bypassed)

    def test_takeover_frame_binding_flow(self) -> None:
        req = self.store.create(
            "human_takeover",
            origin="http://127.0.0.1:8765",
            top_level_url="http://127.0.0.1:8765/antibot",
            action_summary="take over",
        )
        frame = {"frame_id": "frame-current", "captured_at": time.time(), "viewport": {"width": 320, "height": 180}}
        updated = self.store.record_takeover_frame(req.request_id, frame)
        self.assertEqual(updated.takeover_frame_id, "frame-current")
        self.assertEqual(updated.takeover_frame_viewport_width, 320)
        self.assertEqual(updated.takeover_frame_viewport_height, 180)
        self.assertEqual(self.store.validate_takeover_frame(req.request_id, "frame-current").request_id, req.request_id)
        self.assertEqual(self.store.validate_takeover_input(req.request_id, InputEvent("tap", frame_id="frame-current", x=319, y=179)).request_id, req.request_id)
        with self.assertRaises(ValueError) as out_of_bounds:
            self.store.validate_takeover_input(req.request_id, InputEvent("tap", frame_id="frame-current", x=320, y=179))
        self.assertEqual(str(out_of_bounds.exception), "takeover coordinates out of frame bounds")
        with self.assertRaises(ValueError) as drag_out_of_bounds:
            self.store.validate_takeover_input(req.request_id, InputEvent("drag", frame_id="frame-current", x=0, y=0, to_x=-1, to_y=10))
        self.assertEqual(str(drag_out_of_bounds.exception), "takeover coordinates out of frame bounds")
        with self.assertRaises(ValueError) as mismatch:
            self.store.validate_takeover_frame(req.request_id, "frame-old")
        self.assertEqual(str(mismatch.exception), "stale takeover frame")

        loaded = self.store._load()
        loaded[req.request_id].takeover_frame_captured_at = time.time() - 31
        self.store._save(loaded)
        with self.assertRaises(ValueError) as stale:
            self.store.validate_takeover_frame(req.request_id, "frame-current")
        self.assertEqual(str(stale.exception), "stale takeover frame")

    def test_account_registration_uses_user_control_flow(self) -> None:
        req = self.store.create(
            "account_registration",
            origin="https://example.com",
            top_level_url="https://example.com/register",
            action_summary="user completes registration",
            takeover_reason="site requires a new account",
        )
        self.assertEqual(req.status, "user_control")
        self.assertEqual(req.control_owner, "user")
        public = req.to_public_dict()
        self.assertEqual(public["request_type"], "account_registration")
        self.assertFalse(public["secret_exposed_to_model"])
        released = self.store.release_takeover(req.request_id)
        self.assertEqual(released.status, "released")
        self.assertTrue(released.completed_by_user)


if __name__ == "__main__":
    unittest.main()
