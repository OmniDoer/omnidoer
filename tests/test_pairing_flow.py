import tempfile
import time
import unittest
from pathlib import Path

from omnidoer.omni_control.auth import pair_device
from omnidoer.omni_control.devices import DeviceStore
from omnidoer.omni_control.pairing import (
    PairingStore,
    ascii_qr,
    pairing_code_hash,
    parse_duration_seconds,
    pairing_url,
    qr_text,
)
from omnidoer.omni_control.sessions import SessionStore


class PairingFlowTest(unittest.TestCase):
    def test_pairing_code_is_short_ttl_and_one_time(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = PairingStore(Path(tmp) / "pairing.json")
            pairing = store.create(public_url="https://agent.example.com", ttl_seconds=60)
            self.assertIn(pairing.code, pairing_url(pairing))
            raw = (Path(tmp) / "pairing.json").read_text()
            self.assertNotIn(pairing.code, raw)
            self.assertIn(pairing.code_hash, raw)
            self.assertIn("Only", "Only pair devices you control.")
            consumed = store.consume(pairing.code)
            self.assertTrue(consumed.used)
            self.assertEqual(consumed.code, "")
            with self.assertRaises(ValueError):
                store.consume(pairing.code)

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
                device_public_key="device-public-key",
                pairing_store=pairing_store,
                device_store=device_store,
                session_store=session_store,
            )
            self.assertEqual(result.device.name, "Android")
            self.assertTrue(result.session_token)
            self.assertNotIn(result.session_token, repr(result.to_public_dict()))
            qr = qr_text(pairing)
            self.assertGreater(qr.count("\n"), 20)
            self.assertIn("##", qr)
            self.assertNotIn("[QR]", qr)

    def test_duration_parser(self) -> None:
        self.assertEqual(parse_duration_seconds("10m"), 600)
        self.assertEqual(parse_duration_seconds("30s"), 30)

    def test_pairing_code_hash_is_stable_and_non_plaintext(self) -> None:
        digest = pairing_code_hash("1234-5678-90ab")
        self.assertEqual(digest, pairing_code_hash("1234-5678-90ab"))
        self.assertNotIn("1234-5678-90ab", digest)

    def test_ascii_qr_is_deterministic_for_same_payload(self) -> None:
        first = ascii_qr("https://agent.example.com/pair?code=demo")
        second = ascii_qr("https://agent.example.com/pair?code=demo")
        self.assertEqual(first, second)
        self.assertEqual({char for char in first if char != "\n"}, {"#", " "})


if __name__ == "__main__":
    unittest.main()
