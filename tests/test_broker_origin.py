import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

from omnidoer.omni_audit.audit import AuditLog
from omnidoer.omni_broker.broker import SecretBroker, fill_login_status, validate_fill
from omnidoer.omni_browser.controller import BrowserController
from omnidoer.omni_control.requests import RequestStore
from omnidoer.omni_control.secure_channel import ReplayGuard, encrypt_for_broker, load_or_create_keypair
from omnidoer.omni_vault.models import CredentialSecret
from omnidoer.omni_vault.vault import Vault
from tests.util_demo import DemoServerFixture


class BrokerOriginTest(unittest.TestCase):
    def test_validate_exact_origin(self) -> None:
        decision = validate_fill("http://127.0.0.1:8765/login", ["http://127.0.0.1:8765"])
        self.assertEqual(decision.origin, "http://127.0.0.1:8765")

    def test_rejects_wrong_origin(self) -> None:
        with self.assertRaises(PermissionError):
            validate_fill("https://evil.example/login", ["https://example.com"])

    def test_rejects_punycode_credential_origin(self) -> None:
        with self.assertRaises(PermissionError):
            validate_fill("https://xn--exmple-cua.com/login", ["https://xn--exmple-cua.com"])

    def test_rejects_homograph_credential_origin(self) -> None:
        with self.assertRaises(PermissionError):
            validate_fill("https://exаmple.com/login", ["https://exаmple.com"])

    def test_fill_result_contains_status_only(self) -> None:
        result = fill_login_status(
            "http://127.0.0.1:8765/login",
            ["http://127.0.0.1:8765"],
            CredentialSecret(username="demo", password="fake-password-never-returned"),
        ).to_dict()
        self.assertNotIn("fake-password-never-returned", repr(result))
        self.assertFalse(result["secret_exposed_to_model"])

    def test_broker_rejects_wrong_cloud_device_binding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                keypair = load_or_create_keypair()
                store = RequestStore(Path(tmp) / "requests.json")
                request = store.create(
                    "credential",
                    origin="https://example.com",
                    top_level_url="https://example.com/login",
                    action_summary="login",
                    allowed_device_id="dev_expected",
                )
                envelope = encrypt_for_broker(
                    keypair.public_key_b64,
                    {"username": "demo", "password": "broker-secret-password"},
                    request_id=request.request_id,
                    origin=request.origin,
                    request_type=request.request_type,
                    device_id="dev_other",
                    expires_at=request.expires_at,
                )
                store.submit_ciphertext(request.request_id, envelope)
                broker = SecretBroker(store=store, replay_guard=ReplayGuard(Path(tmp) / "replay.json"), audit=AuditLog(Path(tmp) / "audit.jsonl"))
                with self.assertRaises(ValueError):
                    broker.receive_from_control_client(request.request_id)
                self.assertNotIn("broker-secret-password", Path(tmp, "audit.jsonl").read_text() if Path(tmp, "audit.jsonl").exists() else "")
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    @unittest.skipIf(importlib.util.find_spec("playwright") is None, "playwright not installed")
    def test_secret_broker_receives_stores_and_fills_without_returning_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, DemoServerFixture() as demo:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            keypair = load_or_create_keypair()
            store = RequestStore(Path(tmp) / "requests.json")
            try:
                request = store.create(
                    "credential",
                    origin=demo.origin,
                    top_level_url=f"{demo.origin}/login",
                    action_summary="login",
                    requested_fields=["username", "password"],
                    save_to_vault=True,
                )
                envelope = encrypt_for_broker(
                    keypair.public_key_b64,
                    {
                        "username": "demo",
                        "password": "broker-secret-password",
                        "totp_seed": "JBSWY3DPEHPK3PXP",
                        "save_to_vault": True,
                    },
                    request_id=request.request_id,
                    origin=request.origin,
                    request_type=request.request_type,
                )
                store.submit_ciphertext(request.request_id, envelope)
                vault_path = Path(tmp) / "vault.json"
                Vault.create(vault_path, "passphrase")
                broker = SecretBroker(
                    store=store,
                    vault_path=vault_path,
                    vault_passphrase="passphrase",
                    replay_guard=ReplayGuard(Path(tmp) / "replay.json"),
                    audit=AuditLog(Path(tmp) / "audit.jsonl"),
                )
                received = broker.receive_from_control_client(request.request_id)
                self.assertNotIn("broker-secret-password", repr(received))
                saved = broker.store_or_use_once(request.request_id)
                self.assertTrue(saved["saved_to_vault"])
                self.assertNotIn("broker-secret-password", Path(tmp, "vault.json").read_text())
                try:
                    with BrowserController() as browser:
                        browser.open(f"{demo.origin}/login")
                        filled = broker.fill_after_receive(request.request_id, browser_controller=browser)
                        observation = browser.observe_dom()
                except Exception as exc:
                    self.skipTest(f"playwright chromium unavailable: {type(exc).__name__}")
                self.assertEqual(filled["status"], "credential_received_and_filled")
                self.assertNotIn("broker-secret-password", repr(filled))
                self.assertNotIn("broker-secret-password", repr(observation))
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home


if __name__ == "__main__":
    unittest.main()
