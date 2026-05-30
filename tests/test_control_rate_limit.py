import json
import os
import tempfile
import unittest
from http.server import ThreadingHTTPServer
from threading import Thread
from urllib import error as urllib_error
from urllib import request as urllib_request

from cryptography.hazmat.primitives.asymmetric import ec

from omnidoer.omni_control.cloud import build_config
from omnidoer.omni_control.csrf import CSRF_HEADER
from omnidoer.omni_control.device_signing import DEVICE_ID_HEADER, DEVICE_NONCE_HEADER, DEVICE_SIG_HEADER, DEVICE_TS_HEADER
from omnidoer.omni_control.pairing import PairingStore
from omnidoer.omni_control.rate_limit import RateLimiter
from omnidoer.omni_control.server import CONTROL_MUTATION_RATE_LIMIT, ControlHandler
from tests.test_control_auth import public_jwk, sign_request


PROXY_HEADERS = {"x-forwarded-proto": "https"}


class ControlRateLimitTest(unittest.TestCase):
    def test_lockout_after_failures(self) -> None:
        limiter = RateLimiter(max_attempts=2, window_seconds=60, lockout_seconds=120)
        limiter.record_failure("pair:1", now=100)
        limiter.record_failure("pair:1", now=101)
        with self.assertRaises(PermissionError):
            limiter.check("pair:1", now=102)
        with self.assertRaises(PermissionError):
            limiter.check("pair:1", now=150)
        limiter.check("pair:1", now=223)

    def test_check_and_record_limits_attempts(self) -> None:
        limiter = RateLimiter(max_attempts=2, window_seconds=60, lockout_seconds=120)
        limiter.check_and_record("submit:dev", now=100)
        limiter.check_and_record("submit:dev", now=101)
        with self.assertRaises(PermissionError):
            limiter.check_and_record("submit:dev", now=102)

    def test_cloud_direct_mutating_api_is_rate_limited(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            old_max = CONTROL_MUTATION_RATE_LIMIT.max_attempts
            old_window = CONTROL_MUTATION_RATE_LIMIT.window_seconds
            old_lockout = CONTROL_MUTATION_RATE_LIMIT.lockout_seconds
            os.environ["OMNIDOER_HOME"] = tmp
            CONTROL_MUTATION_RATE_LIMIT.clear_all()
            CONTROL_MUTATION_RATE_LIMIT.max_attempts = 2
            CONTROL_MUTATION_RATE_LIMIT.window_seconds = 60
            CONTROL_MUTATION_RATE_LIMIT.lockout_seconds = 120
            config = build_config(
                host="127.0.0.1",
                port=8787,
                cloud_direct=True,
                public_url="https://agent.example.com",
                behind_reverse_proxy=True,
            )
            server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
            server.omnidoer_config = config  # type: ignore[attr-defined]
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                pairing = PairingStore().create(public_url=config.public_url, ttl_seconds=600)
                device_key = ec.generate_private_key(ec.SECP256R1())
                pair_request = urllib_request.Request(
                    f"{base}/api/pair",
                    data=json.dumps({"code": pairing.code, "device_name": "Phone", "device_public_key": public_jwk(device_key)}).encode(),
                    headers={"content-type": "application/json", "origin": config.public_origin, **PROXY_HEADERS},
                    method="POST",
                )
                with urllib_request.urlopen(pair_request, timeout=5) as response:
                    cookie = response.headers["set-cookie"]
                    body = json.loads(response.read().decode())
                device_id = body["device"]["device_id"]
                session_id = body["session"]["session_id"]
                csrf = body["csrf_token"]

                def post_task(nonce: str):
                    signed = sign_request(device_key, device_id=device_id, session_id=session_id, method="POST", path="/api/tasks", nonce=nonce)
                    return urllib_request.Request(
                        f"{base}/api/tasks",
                        data=json.dumps({"text": "local task"}).encode(),
                        headers={
                            "content-type": "application/json",
                            "origin": config.public_origin,
                            "cookie": cookie,
                            CSRF_HEADER: csrf,
                            **PROXY_HEADERS,
                            DEVICE_ID_HEADER: device_id,
                            DEVICE_TS_HEADER: signed["timestamp"],
                            DEVICE_NONCE_HEADER: signed["nonce"],
                            DEVICE_SIG_HEADER: signed["signature"],
                        },
                        method="POST",
                    )

                self.assertEqual(urllib_request.urlopen(post_task("nonce-rate-1"), timeout=5).status, 201)
                self.assertEqual(urllib_request.urlopen(post_task("nonce-rate-2"), timeout=5).status, 201)
                with self.assertRaises(urllib_error.HTTPError) as raised:
                    urllib_request.urlopen(post_task("nonce-rate-3"), timeout=5)
                self.assertEqual(raised.exception.code, 429)
            finally:
                server.shutdown()
                server.server_close()
                CONTROL_MUTATION_RATE_LIMIT.clear_all()
                CONTROL_MUTATION_RATE_LIMIT.max_attempts = old_max
                CONTROL_MUTATION_RATE_LIMIT.window_seconds = old_window
                CONTROL_MUTATION_RATE_LIMIT.lockout_seconds = old_lockout
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home


if __name__ == "__main__":
    unittest.main()
