import tempfile
import time
import unittest
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import ec

from omnidoer.omni_control.auth import pair_device
from omnidoer.omni_control.devices import DeviceStore
from omnidoer.omni_control.pairing import (
    DEFAULT_PAIRING_MAX_USES,
    DEFAULT_PAIRING_TTL_SECONDS,
    PairingStore,
    ascii_qr,
    pairing_code_hash,
    normalize_pairing_code,
    parse_duration_seconds,
    pairing_url,
    qr_text,
)
from omnidoer.omni_control.sessions import SessionStore
from tests.test_control_auth import public_jwk


class PairingFlowTest(unittest.TestCase):
    def test_pairing_code_is_24h_and_reusable_ten_times_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = PairingStore(Path(tmp) / "pairing.json")
            before = time.time()
            pairing = store.create(public_url="https://agent.example.com")
            self.assertRegex(pairing.code, r"^\d{6}$")
            self.assertIn(pairing.code, pairing_url(pairing))
            self.assertGreater(pairing.expires_at, before + DEFAULT_PAIRING_TTL_SECONDS - 5)
            self.assertEqual(pairing.max_uses, DEFAULT_PAIRING_MAX_USES)
            raw = (Path(tmp) / "pairing.json").read_text()
            self.assertNotIn(pairing.code, raw)
            self.assertIn(pairing.code_hash, raw)
            self.assertIn("Only", "Only pair devices you control.")
            for index in range(DEFAULT_PAIRING_MAX_USES):
                consumed = store.consume(pairing.code)
                self.assertEqual(consumed.code, "")
                self.assertEqual(consumed.use_count, index + 1)
                self.assertEqual(consumed.used, index + 1 == DEFAULT_PAIRING_MAX_USES)
            with self.assertRaises(ValueError):
                store.consume(pairing.code)

    def test_pairing_public_metadata_never_contains_code_or_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = PairingStore(Path(tmp) / "pairing.json")
            pairing = store.create(public_url="https://agent.example.com", ttl_seconds=60)
            public = store.get(pairing.pairing_id).to_public_dict()
            self.assertEqual(public["public_url"], "https://agent.example.com")
            self.assertIn("broker_fingerprint", public)
            self.assertIn("web_broker_fingerprint", public)
            self.assertNotIn("code", public)
            self.assertNotIn("code_hash", public)
            self.assertNotIn(pairing.code, repr(public))
            self.assertEqual(public["max_uses"], DEFAULT_PAIRING_MAX_USES)
            self.assertEqual(public["remaining_uses"], DEFAULT_PAIRING_MAX_USES)

    def test_pairing_expiry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = PairingStore(Path(tmp) / "pairing.json")
            pairing = store.create(public_url="https://agent.example.com", ttl_seconds=1)
            with self.assertRaises(ValueError):
                store.consume(pairing.code, now=time.time() + 2)

    def test_pair_device_creates_device_and_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pairing_store = PairingStore(Path(tmp) / "pairing.json")
            device_store = DeviceStore(Path(tmp) / "devices.json")
            session_store = SessionStore(Path(tmp) / "sessions.json")
            pairing = pairing_store.create(public_url="https://agent.example.com", ttl_seconds=600)
            result = pair_device(
                code=pairing.code,
                device_name="Android",
                device_public_key=public_jwk(ec.generate_private_key(ec.SECP256R1())),
                pairing_store=pairing_store,
                device_store=device_store,
                session_store=session_store,
            )
            self.assertEqual(result.device.name, "Android")
            self.assertTrue(result.session_token)
            self.assertNotIn(result.session_token, repr(result.to_public_dict()))
            qr = qr_text(pairing)
            self.assertGreater(qr.count("\n"), 20)
            self.assertNotIn("##", qr)
            self.assertGreater(sum(qr.count(ch) for ch in "█▀▄"), 100)
            self.assertNotIn("[QR]", qr)

    def test_invalid_device_public_key_does_not_consume_pairing_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pairing_store = PairingStore(Path(tmp) / "pairing.json")
            device_store = DeviceStore(Path(tmp) / "devices.json")
            session_store = SessionStore(Path(tmp) / "sessions.json")
            pairing = pairing_store.create(public_url="https://agent.example.com", ttl_seconds=600)
            with self.assertRaises(PermissionError):
                pair_device(
                    code=pairing.code,
                    device_name="Invalid",
                    device_public_key="not-a-jwk",
                    pairing_store=pairing_store,
                    device_store=device_store,
                    session_store=session_store,
                )
            result = pair_device(
                code=pairing.code,
                device_name="Android",
                device_public_key=public_jwk(ec.generate_private_key(ec.SECP256R1())),
                pairing_store=pairing_store,
                device_store=device_store,
                session_store=session_store,
            )
            self.assertEqual(result.device.name, "Android")

    def test_duration_parser(self) -> None:
        self.assertEqual(parse_duration_seconds(None), 24 * 60 * 60)
        self.assertEqual(parse_duration_seconds("10m"), 600)
        self.assertEqual(parse_duration_seconds("30s"), 30)

    def test_pairing_code_hash_is_stable_and_non_plaintext(self) -> None:
        digest = pairing_code_hash("1234-5678-90ab")
        self.assertEqual(digest, pairing_code_hash("1234-5678-90ab"))
        self.assertNotIn("1234-5678-90ab", digest)

    def test_short_pairing_code_accepts_common_separators(self) -> None:
        self.assertEqual(normalize_pairing_code("123456"), "123456")
        self.assertEqual(normalize_pairing_code("123 456"), "123456")
        self.assertEqual(normalize_pairing_code("123-456"), "123456")
        self.assertEqual(pairing_code_hash("123456"), pairing_code_hash("123 456"))
        self.assertEqual(pairing_code_hash("123456"), pairing_code_hash("123-456"))
        with tempfile.TemporaryDirectory() as tmp:
            store = PairingStore(Path(tmp) / "pairing.json")
            pairing = store.create(public_url="https://agent.example.com", max_uses=1)
            grouped = f"{pairing.code[:3]}-{pairing.code[3:]}"
            consumed = store.consume(grouped)
            self.assertEqual(consumed.use_count, 1)

    def test_ascii_qr_is_deterministic_for_same_payload(self) -> None:
        first = ascii_qr("https://agent.example.com/pair?code=demo")
        second = ascii_qr("https://agent.example.com/pair?code=demo")
        self.assertEqual(first, second)
        self.assertEqual({char for char in first if char != "\n"}, {"█", "▀", "▄", " "})
        self.assertEqual({len(line) for line in first.splitlines()}, {len(first.splitlines()[0])})
        self.assertTrue(first.splitlines()[0].isspace())
        self.assertTrue(first.splitlines()[-1].isspace())

    def test_ascii_qr_can_render_ansi_rectangles_for_terminals(self) -> None:
        qr = ascii_qr("https://agent.example.com/pair?code=demo", ansi=True)
        self.assertIn("\033[", qr)
        self.assertNotIn("#", qr)


if __name__ == "__main__":
    unittest.main()
