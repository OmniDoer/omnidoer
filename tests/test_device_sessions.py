import tempfile
import time
import unittest
from pathlib import Path

from omnidoer.omni_control.auth import authenticate_session
from omnidoer.omni_control.devices import DeviceStore
from omnidoer.omni_control.sessions import CONTROL_SESSION_TTL_SECONDS, SessionStore


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

    def test_revoke_for_device_revokes_all_device_sessions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sessions = SessionStore(Path(tmp) / "sessions.json")
            session_a, _token_a = sessions.create(device_id="dev_a")
            session_b, _token_b = sessions.create(device_id="dev_a")
            session_c, _token_c = sessions.create(device_id="dev_b")
            revoked = sessions.revoke_for_device("dev_a")
            self.assertEqual({session.session_id for session in revoked}, {session_a.session_id, session_b.session_id})
            all_sessions = {session.session_id: session for session in sessions.list()}
            self.assertTrue(all_sessions[session_a.session_id].revoked)
            self.assertTrue(all_sessions[session_b.session_id].revoked)
            self.assertFalse(all_sessions[session_c.session_id].revoked)

    def test_active_sessions_slide_expiry_to_reduce_repairing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sessions = SessionStore(Path(tmp) / "sessions.json")
            session, token = sessions.create(device_id="dev_phone", ttl_seconds=60)
            original_expires_at = session.expires_at
            authenticated = sessions.authenticate(session.session_id, token)
            self.assertGreater(authenticated.expires_at, original_expires_at)
            self.assertGreater(authenticated.expires_at, time.time() + CONTROL_SESSION_TTL_SECONDS - 60)


if __name__ == "__main__":
    unittest.main()
