import os
import tempfile
import unittest

from omnidoer.omni_approval.approval import decide, request_approval, verify_approval_scope
from omnidoer.omni_control.requests import RequestStore


class ApprovalTest(unittest.TestCase):
    def test_approval_modes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            old_mode = os.environ.get("OMNIDOER_APPROVAL_MODE")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                store = RequestStore()
                req = request_approval(
                    origin="http://127.0.0.1:8765",
                    top_level_url="http://127.0.0.1:8765/checkout",
                    action_summary="Pay local mock merchant",
                    risk_level="medium",
                    structured_details={"merchant": "Demo", "amount": "12.34", "currency": "USD"},
                    store=store,
                )
                self.assertEqual(req.structured_details["merchant"], "Demo")
                self.assertRegex(req.approval_fingerprint or "", r"^[0-9a-f]{64}$")
                self.assertEqual(req.to_public_dict()["structured_details"]["amount"], "12.34")
                os.environ["OMNIDOER_APPROVAL_MODE"] = "deny"
                self.assertEqual(decide(req.request_id, store=store), "denied")
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home
                if old_mode is None:
                    os.environ.pop("OMNIDOER_APPROVAL_MODE", None)
                else:
                    os.environ["OMNIDOER_APPROVAL_MODE"] = old_mode

    def test_approval_scope_detects_changed_payment_details(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                store = RequestStore()
                details = {
                    "merchant": "Demo",
                    "amount": "12.34",
                    "currency": "USD",
                    "final_button": "Pay 12.34 USD",
                    "after_approval": "Submit exact reviewed payment",
                }
                req = request_approval(
                    origin="https://checkout.example",
                    top_level_url="https://checkout.example/pay",
                    action_summary="Submit reviewed payment",
                    risk_level="high",
                    structured_details=details,
                    store=store,
                )
                store.approve(req.request_id)
                verified = verify_approval_scope(
                    req.request_id,
                    origin="https://checkout.example",
                    top_level_url="https://checkout.example/pay",
                    action_summary="Submit reviewed payment",
                    structured_details=details,
                    store=store,
                )
                self.assertEqual(verified.request_id, req.request_id)
                with self.assertRaises(PermissionError):
                    verify_approval_scope(
                        req.request_id,
                        origin="https://checkout.example",
                        top_level_url="https://checkout.example/pay",
                        action_summary="Submit reviewed payment",
                        structured_details={**details, "amount": "99.00"},
                        store=store,
                    )
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_approval_scope_uses_raw_details_even_when_public_view_redacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                store = RequestStore()
                details = {
                    "recipient": "payee-a@example.test",
                    "amount": "12.34",
                    "currency": "USD",
                    "final_button": "Send payment",
                }
                req = request_approval(
                    origin="https://checkout.example",
                    top_level_url="https://checkout.example/pay",
                    action_summary="Submit reviewed payment",
                    risk_level="high",
                    structured_details=details,
                    store=store,
                )
                self.assertEqual(req.to_public_dict()["structured_details"]["recipient"], "[REDACTED]")
                store.approve(req.request_id)
                with self.assertRaises(PermissionError):
                    verify_approval_scope(
                        req.request_id,
                        origin="https://checkout.example",
                        top_level_url="https://checkout.example/pay",
                        action_summary="Submit reviewed payment",
                        structured_details={**details, "recipient": "payee-b@example.test"},
                        store=store,
                    )
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home


if __name__ == "__main__":
    unittest.main()
