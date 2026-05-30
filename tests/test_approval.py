import os
import tempfile
import unittest

from omnidoer.omni_approval.approval import decide, request_approval
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


if __name__ == "__main__":
    unittest.main()
