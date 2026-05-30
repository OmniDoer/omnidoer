import tempfile
import unittest
from pathlib import Path

from omnidoer.omni_control.auth import authenticate_session
from omnidoer.omni_control.devices import DeviceStore
from omnidoer.omni_control.sessions import SessionStore


class DeviceSessionTest(unittest.TestCase):
    def test_device_and_session_revoke(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            devices = DeviceStore(Path(tmp) / "devices.json")
            sessions = SessionStore(Path(tmp) / "sessions.json")
            device = devices.register(name="Windows", public_key="pub")
            session, token = sessions.create(device_id=device.device_id)
            authenticated = authenticate_session(
                session_id=session.session_id,
                session_token=token,
                device_store=devices,
                session_store=sessions,
            )
            self.assertEqual(authenticated.device_id, device.device_id)
            sessions.revoke(session.session_id)
            with self.assertRaises(PermissionError):
                authenticate_session(
                    session_id=session.session_id,
                    session_token=token,
                    device_store=devices,
                    session_store=sessions,
                )

    def test_revoked_device_cannot_authenticate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            devices = DeviceStore(Path(tmp) / "devices.json")
            sessions = SessionStore(Path(tmp) / "sessions.json")
            device = devices.register(name="Phone", public_key="pub")
            session, token = sessions.create(device_id=device.device_id)
            devices.revoke(device.device_id)
            with self.assertRaises(PermissionError):
                authenticate_session(
                    session_id=session.session_id,
                    session_token=token,
                    device_store=devices,
                    session_store=sessions,
                )


if __name__ == "__main__":
    unittest.main()
