import os
import json
import tempfile
import time
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from types import SimpleNamespace
from urllib import request as urllib_request
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric import ec

from omnidoer.omni_agent.demo_agent import _credential_from_control_or_vault
from omnidoer.omni_agent.demo_agent import run_task
from omnidoer.omni_control.cloud import build_config
from omnidoer.omni_control.csrf import CSRF_HEADER
from omnidoer.omni_control.device_signing import DEVICE_ID_HEADER, DEVICE_NONCE_HEADER, DEVICE_SIG_HEADER, DEVICE_TS_HEADER
from omnidoer.omni_control.pairing import PairingStore
from omnidoer.omni_control.secure_channel import encrypt_for_broker
from omnidoer.omni_control.server import ControlHandler
from omnidoer.omni_vault.vault import Vault
from tests.test_control_auth import public_jwk, sign_request
from tests.util_demo import DemoServerFixture


PROXY_HEADERS = {"x-forwarded-proto": "https"}


class E2EDemoLoginTest(unittest.TestCase):
    def test_control_credential_can_be_one_time_without_vault_save(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old = {key: os.environ.get(key) for key in ("OMNIDOER_HOME", "OMNIDOER_TEST_PASSPHRASE")}
            os.environ.update(
                {
                    "OMNIDOER_HOME": tmp,
                    "OMNIDOER_TEST_PASSPHRASE": "test-passphrase-change-me",
                }
            )
            try:
                vault_path = Path(tmp) / "vault.json"
                Vault.create(vault_path, os.environ["OMNIDOER_TEST_PASSPHRASE"])
                args = SimpleNamespace(vault=str(vault_path), passphrase_env="OMNIDOER_TEST_PASSPHRASE")
                with patch(
                    "omnidoer.omni_agent.demo_agent._wait_for_request_payload",
                    return_value={
                        "username": "demo",
                        "password": "one-time-password-never-save",
                        "save_to_vault": False,
                    },
                ):
                    credential_id, secret = _credential_from_control_or_vault(args, "https://example.com")
                self.assertTrue(credential_id.startswith("one_time:req_"))
                self.assertEqual(secret.password, "one-time-password-never-save")
                self.assertEqual(Vault.load(vault_path).list_metadata(), [])
                combined = vault_path.read_text() + (Path(tmp) / "audit.jsonl").read_text()
                self.assertNotIn("one-time-password-never-save", combined)
            finally:
                for key, value in old.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value

    def test_login_download_invoice_with_control_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, DemoServerFixture() as demo:
            old = {key: os.environ.get(key) for key in (
                "OMNIDOER_HOME",
                "OMNIDOER_TEST_PASSPHRASE",
                "OMNIDOER_TEST_USERNAME",
                "OMNIDOER_TEST_PASSWORD",
                "OMNIDOER_TEST_SMS_CODE",
                "OMNIDOER_CONTROL_TEST_MODE",
                "OMNIDOER_CHALLENGE_TEST_MODE",
            )}
            os.environ.update(
                {
                    "OMNIDOER_HOME": tmp,
                    "OMNIDOER_TEST_PASSPHRASE": "test-passphrase-change-me",
                    "OMNIDOER_TEST_USERNAME": "demo",
                    "OMNIDOER_TEST_PASSWORD": "demo-password-change-me",
                    "OMNIDOER_TEST_SMS_CODE": "123456",
                    "OMNIDOER_CONTROL_TEST_MODE": "1",
                    "OMNIDOER_CHALLENGE_TEST_MODE": "1",
                }
            )
            try:
                vault_path = Path(tmp) / "vault.json"
                Vault.create(vault_path, os.environ["OMNIDOER_TEST_PASSPHRASE"])
                args = SimpleNamespace(
                    task="登录 demo 网站并下载我的发票",
                    vault=str(vault_path),
                    passphrase_env="OMNIDOER_TEST_PASSPHRASE",
                    demo_origin=demo.origin,
                    control_origin="http://127.0.0.1:8787",
                )
                self.assertEqual(run_task(args), 0)
                self.assertTrue(Path(".omnidoer/downloads/omnidoer-demo-invoice.txt").exists())
                raw_vault = vault_path.read_text()
                self.assertNotIn("demo-password-change-me", raw_vault)
            finally:
                for key, value in old.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value

    def test_login_download_invoice_with_paired_control_service_submit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, DemoServerFixture() as demo:
            old = {
                key: os.environ.get(key)
                for key in (
                    "OMNIDOER_HOME",
                    "OMNIDOER_TEST_PASSPHRASE",
                    "OMNIDOER_TEST_USERNAME",
                    "OMNIDOER_TEST_PASSWORD",
                    "OMNIDOER_TEST_SMS_CODE",
                    "OMNIDOER_CONTROL_TEST_MODE",
                    "OMNIDOER_CHALLENGE_TEST_MODE",
                )
            }
            os.environ.update(
                {
                    "OMNIDOER_HOME": tmp,
                    "OMNIDOER_TEST_PASSPHRASE": "test-passphrase-change-me",
                    "OMNIDOER_TEST_USERNAME": "demo",
                    "OMNIDOER_TEST_PASSWORD": "demo-password-change-me",
                    "OMNIDOER_TEST_SMS_CODE": "123456",
                    "OMNIDOER_CHALLENGE_TEST_MODE": "1",
                }
            )
            os.environ.pop("OMNIDOER_CONTROL_TEST_MODE", None)
            server = None
            try:
                vault_path = Path(tmp) / "vault.json"
                Vault.create(vault_path, os.environ["OMNIDOER_TEST_PASSPHRASE"])
                config = build_config(
                    host="127.0.0.1",
                    port=8787,
                    cloud_direct=True,
                    public_url="https://agent.example.com",
                    behind_reverse_proxy=True,
                )
                server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
                server.omnidoer_config = config  # type: ignore[attr-defined]
                control_thread = Thread(target=server.serve_forever, daemon=True)
                control_thread.start()
                base = f"http://127.0.0.1:{server.server_address[1]}"

                pairing = PairingStore().create(public_url=config.public_url, ttl_seconds=600)
                device_key = ec.generate_private_key(ec.SECP256R1())
                pair_request = urllib_request.Request(
                    f"{base}/api/pair",
                    data=json.dumps(
                        {"code": pairing.code, "device_name": "Phone", "device_public_key": public_jwk(device_key)}
                    ).encode(),
                    headers={"content-type": "application/json", "origin": config.public_origin, **PROXY_HEADERS},
                    method="POST",
                )
                with urllib_request.urlopen(pair_request, timeout=5) as response:
                    cookie = response.headers["set-cookie"]
                    pair_body = json.loads(response.read().decode())
                device_id = pair_body["device"]["device_id"]
                session_id = pair_body["session"]["session_id"]
                csrf = pair_body["csrf_token"]
                nonce_counter = 0

                def signed_headers(method: str, path: str, *, origin: bool = False, csrf_token: bool = False) -> dict[str, str]:
                    nonlocal nonce_counter
                    nonce_counter += 1
                    signed = sign_request(
                        device_key,
                        device_id=device_id,
                        session_id=session_id,
                        method=method,
                        path=path,
                        nonce=f"nonce-e2e-{nonce_counter}",
                    )
                    headers = {
                        "cookie": cookie,
                        **PROXY_HEADERS,
                        DEVICE_ID_HEADER: device_id,
                        DEVICE_TS_HEADER: signed["timestamp"],
                        DEVICE_NONCE_HEADER: signed["nonce"],
                        DEVICE_SIG_HEADER: signed["signature"],
                    }
                    if origin:
                        headers["origin"] = config.public_origin
                    if csrf_token:
                        headers[CSRF_HEADER] = csrf
                    return headers

                def get_json(path: str):
                    request = urllib_request.Request(f"{base}{path}", headers=signed_headers("GET", path))
                    with urllib_request.urlopen(request, timeout=5) as response:
                        return json.loads(response.read().decode())

                def post_json(path: str, body: dict):
                    request = urllib_request.Request(
                        f"{base}{path}",
                        data=json.dumps(body).encode(),
                        headers={
                            "content-type": "application/json",
                            **signed_headers("POST", path, origin=True, csrf_token=True),
                        },
                        method="POST",
                    )
                    with urllib_request.urlopen(request, timeout=5) as response:
                        return json.loads(response.read().decode())

                args = SimpleNamespace(
                    task="登录 demo 网站并下载我的发票",
                    vault=str(vault_path),
                    passphrase_env="OMNIDOER_TEST_PASSPHRASE",
                    demo_origin=demo.origin,
                    control_origin=base,
                )
                result: dict[str, object] = {}

                def run_agent() -> None:
                    try:
                        result["status"] = run_task(args)
                    except BaseException as exc:
                        result["exception"] = exc

                agent_thread = Thread(target=run_agent, daemon=True)
                agent_thread.start()
                credential_request = None
                deadline = time.time() + 10
                while time.time() < deadline:
                    for item in get_json("/api/requests"):
                        if item["request_type"] == "credential" and item["origin"] == demo.origin:
                            credential_request = item
                            break
                    if credential_request is not None or not agent_thread.is_alive():
                        break
                    time.sleep(0.05)
                self.assertIsNotNone(credential_request, result)
                assert credential_request is not None

                broker_key = get_json("/api/broker-key")
                envelope = encrypt_for_broker(
                    broker_key["public_key"],
                    {"username": "demo", "password": "demo-password-change-me", "save_to_vault": True},
                    request_id=credential_request["request_id"],
                    origin=credential_request["origin"],
                    request_type=credential_request["request_type"],
                    device_id=device_id,
                    expires_at=credential_request["expires_at"],
                )
                submit_result = post_json(f"/api/requests/{credential_request['request_id']}/submit", {"envelope": envelope})
                self.assertEqual(submit_result["status"], "fulfilled")
                self.assertNotIn("demo-password-change-me", repr(submit_result))

                agent_thread.join(timeout=10)
                self.assertFalse(agent_thread.is_alive(), result)
                if "exception" in result:
                    raise result["exception"]  # type: ignore[misc]
                self.assertEqual(result["status"], 0)
                metadata = Vault.load(vault_path).list_metadata()
                self.assertEqual(len(metadata), 1)
                self.assertIn(demo.origin, metadata[0].allowed_origins)
                raw_vault = vault_path.read_text()
                raw_audit = (Path(tmp) / "audit.jsonl").read_text()
                self.assertIn("credential_saved", raw_audit)
                self.assertIn("login_completed", raw_audit)
                self.assertNotIn("demo-password-change-me", raw_vault + raw_audit)
                self.assertNotIn("123456", raw_audit)
            finally:
                if server is not None:
                    server.shutdown()
                    server.server_close()
                for key, value in old.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value


if __name__ == "__main__":
    unittest.main()
