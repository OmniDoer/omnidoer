import json
import tempfile
import unittest
from pathlib import Path

from omnidoer.omni_vault.vault import Vault


class VaultTest(unittest.TestCase):
    def test_vault_encrypts_secret_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            vault = Vault.create(path, "test-passphrase")
            credential_id = vault.add_credential(
                username="demo",
                password="fake-password-never-plain",
                totp_seed="fake-totp-seed-never-plain",
                allowed_origins=["http://127.0.0.1:8765"],
            )
            raw = path.read_text()
            self.assertNotIn("fake-password-never-plain", raw)
            self.assertNotIn("fake-totp-seed-never-plain", raw)
            unlocked = Vault.load(path, "test-passphrase")
            secret = unlocked.decrypt_credential(credential_id)
            self.assertEqual(secret.username, "demo")
            self.assertEqual(secret.password, "fake-password-never-plain")
            self.assertEqual(secret.totp_seed, "fake-totp-seed-never-plain")

    def test_wrong_passphrase_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            vault = Vault.create(path, "right-passphrase")
            credential_id = vault.add_credential(
                username="demo",
                password="fake-password-never-plain",
                allowed_origins=["http://127.0.0.1:8765"],
            )
            wrong = Vault.load(path, "wrong-passphrase")
            with self.assertRaises(Exception):
                wrong.decrypt_credential(credential_id)

    def test_list_metadata_without_passphrase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            Vault.create(path, "test-passphrase").add_credential(
                username="demo",
                password="fake-password-never-plain",
                allowed_origins=["http://127.0.0.1:8765"],
            )
            locked = Vault.load(path)
            metadata = locked.list_metadata()
            self.assertEqual(metadata[0].username, "demo")
            self.assertEqual(metadata[0].allowed_origins, ["http://127.0.0.1:8765"])


if __name__ == "__main__":
    unittest.main()
