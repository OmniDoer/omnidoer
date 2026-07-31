import json
import os
import stat
import tempfile
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.request import Request, urlopen

from omnidoer.omni_control.deepseek_provider import (
    DEEPSEEK_KEY_PLACEHOLDER,
    prepare_runtime_config,
    upsert_api_key,
)
from omnidoer.omni_control.requests import RequestStore
from omnidoer.omni_control.secure_channel import encrypt_for_broker_web, load_or_create_web_keypair
from omnidoer.omni_control.server import ControlHandler
from omnidoer.omni_vault.vault import Vault


class DeepSeekProviderTest(unittest.TestCase):
    def test_existing_deepseek_llm_api_record_is_reused_without_reentry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vault_path = root / "vault.json"
            template_path = root / "template.yml"
            output_path = root / "run" / "deepseek.yml"
            passphrase = "legacy-provider-passphrase"
            api_key = "sk-existing-deepseek-provider-key"
            Vault.create(vault_path, passphrase).add_credential(
                username="api-key",
                password=api_key,
                allowed_origins=["https://api.deepseek.com"],
                metadata={"kind": "llm_api", "provider": "deepseek"},
            )
            template_path.write_text(f'api_key: "{DEEPSEEK_KEY_PLACEHOLDER}"\n')
            prepare_runtime_config(
                vault_path=vault_path,
                passphrase=passphrase,
                template_path=template_path,
                output_path=output_path,
            )
            self.assertIn(api_key, output_path.read_text())

    def test_vault_upsert_and_tmpfs_style_runtime_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vault_path = root / "vault.json"
            template_path = root / "template.yml"
            output_path = root / "run" / "deepseek.yml"
            passphrase = "test-vault-passphrase"
            first_key = "sk-test-deepseek-provider-0001"
            second_key = "sk-test-deepseek-provider-0002"
            vault = Vault.create(vault_path, passphrase)
            credential_id, created = upsert_api_key(vault, first_key)
            self.assertTrue(created)
            self.assertNotIn(first_key, vault_path.read_text())
            same_id, created = upsert_api_key(Vault.load(vault_path, passphrase), second_key)
            self.assertEqual(same_id, credential_id)
            self.assertFalse(created)
            self.assertNotIn(second_key, vault_path.read_text())

            template_path.write_text(f'api_key: "{DEEPSEEK_KEY_PLACEHOLDER}"\n')
            prepared = prepare_runtime_config(
                vault_path=vault_path,
                passphrase=passphrase,
                template_path=template_path,
                output_path=output_path,
            )
            self.assertEqual(prepared, output_path)
            self.assertIn(second_key, output_path.read_text())
            self.assertEqual(stat.S_IMODE(output_path.stat().st_mode), 0o600)

    def test_control_client_e2ee_submission_is_consumed_into_vault(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            vault_path = Path(tmp) / "vault.json"
            passphrase = "control-provider-test-passphrase"
            Vault.create(vault_path, passphrase)
            (Path(tmp) / "vault-passphrase").write_text(passphrase)
            server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
            server.omnidoer_deepseek_activate = lambda: {"bridge_active": True}
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            api_key = "sk-test-e2ee-deepseek-provider-1234"
            base_url = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                created = json.loads(
                    urlopen(Request(f"{base_url}/api/model-providers/deepseek/key-request", data=b"", method="POST")).read()
                )
                request = created["request"]
                envelope = encrypt_for_broker_web(
                    load_or_create_web_keypair().public_jwk,
                    {"username": "deepseek", "password": api_key, "save_to_vault": True},
                    request_id=request["request_id"],
                    origin=request["origin"],
                    request_type=request["request_type"],
                    expires_at=request["expires_at"],
                )
                body = json.dumps({"envelope": envelope}).encode()
                response = json.loads(
                    urlopen(
                        Request(
                            f"{base_url}/api/requests/{request['request_id']}/submit",
                            data=body,
                            headers={"content-type": "application/json"},
                            method="POST",
                        )
                    ).read()
                )
                self.assertEqual(response["status"], "consumed")
                self.assertFalse(response["secret_exposed_to_model"])
                self.assertNotIn(api_key, json.dumps(response))
                stored_request = RequestStore().get(request["request_id"])
                self.assertIsNone(stored_request.response_ciphertext)
                credentials = Vault.load(vault_path, passphrase).find_for_origin("https://api.deepseek.com")
                self.assertEqual(len(credentials), 1)
                secret = Vault.load(vault_path, passphrase).decrypt_credential(credentials[0].credential_id)
                self.assertEqual(secret.password, api_key)
                self.assertNotIn(api_key, (Path(tmp) / "audit.jsonl").read_text())
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home
