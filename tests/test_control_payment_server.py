import json
import os
import tempfile
import unittest
from http.server import ThreadingHTTPServer
from threading import Thread
from urllib import request as urllib_request

from omnidoer.omni_control.requests import RequestStore
from omnidoer.omni_control.server import ControlHandler


class ControlPaymentServerTest(unittest.TestCase):
    def test_payment_approval_requires_explicit_user_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                approval = RequestStore().create(
                    "payment_approval",
                    origin="https://checkout.example",
                    top_level_url="https://checkout.example/pay",
                    action_summary="Submit payment",
                    structured_details={
                        "merchant": "Example Store",
                        "amount": "19.00",
                        "currency": "USD",
                        "final_button": "Pay now",
                    },
                )
                base = f"http://127.0.0.1:{server.server_address[1]}"
                approve_url = f"{base}/api/requests/{approval.request_id}/approve"

                with self.assertRaises(Exception) as missing_confirmation:
                    urllib_request.urlopen(urllib_request.Request(approve_url, data=b"{}", method="POST"), timeout=5)
                self.assertIn("400", str(missing_confirmation.exception))
                self.assertEqual(RequestStore().get(approval.request_id).status, "pending")

                body = json.dumps(
                    {
                        "explicit_user_confirmation": True,
                        "request_id": approval.request_id,
                    }
                ).encode()
                with urllib_request.urlopen(
                    urllib_request.Request(
                        approve_url,
                        data=body,
                        headers={"content-type": "application/json"},
                        method="POST",
                    ),
                    timeout=5,
                ) as response:
                    payload = json.loads(response.read().decode())
                self.assertEqual(payload["status"], "approved")
                self.assertTrue(payload["completed_by_user"])
                self.assertFalse(payload["secret_exposed_to_model"])
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home


if __name__ == "__main__":
    unittest.main()
