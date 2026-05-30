import unittest

from omnidoer.omni_broker.broker import fill_login_status, validate_fill
from omnidoer.omni_vault.models import CredentialSecret


class BrokerOriginTest(unittest.TestCase):
    def test_validate_exact_origin(self) -> None:
        decision = validate_fill("http://127.0.0.1:8765/login", ["http://127.0.0.1:8765"])
        self.assertEqual(decision.origin, "http://127.0.0.1:8765")

    def test_rejects_wrong_origin(self) -> None:
        with self.assertRaises(PermissionError):
            validate_fill("https://evil.example/login", ["https://example.com"])

    def test_fill_result_contains_status_only(self) -> None:
        result = fill_login_status(
            "http://127.0.0.1:8765/login",
            ["http://127.0.0.1:8765"],
            CredentialSecret(username="demo", password="fake-password-never-returned"),
        ).to_dict()
        self.assertNotIn("fake-password-never-returned", repr(result))
        self.assertFalse(result["secret_exposed_to_model"])


if __name__ == "__main__":
    unittest.main()
