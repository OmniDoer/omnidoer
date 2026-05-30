"""Pairing and session authentication helpers for Control Service."""

from __future__ import annotations

from dataclasses import dataclass

from omnidoer.omni_control.devices import Device, DeviceStore
from omnidoer.omni_control.device_signing import (
    DeviceNonceStore,
    device_signature_message,
    load_ec_public_key,
    verify_ecdsa_signature,
)
from omnidoer.omni_control.pairing import PairingStore
from omnidoer.omni_control.sessions import ControlSession, SessionStore


@dataclass(frozen=True)
class PairingResult:
    device: Device
    session: ControlSession
    session_token: str
    csrf_token: str

    def to_public_dict(self) -> dict:
        return {
            "device": self.device.to_public_dict(),
            "session": self.session.to_public_dict(),
            "csrf_token": self.csrf_token,
        }


def pair_device(
    *,
    code: str,
    device_name: str,
    device_public_key: str,
    pairing_store: PairingStore | None = None,
    device_store: DeviceStore | None = None,
    session_store: SessionStore | None = None,
) -> PairingResult:
    pairing_store = pairing_store or PairingStore()
    device_store = device_store or DeviceStore()
    session_store = session_store or SessionStore()
    load_ec_public_key(device_public_key)
    pairing_store.consume(code)
    device = device_store.register(name=device_name, public_key=device_public_key)
    session, token = session_store.create(device_id=device.device_id)
    return PairingResult(device=device, session=session, session_token=token, csrf_token=session.csrf_token)


def authenticate_session(
    *,
    session_id: str,
    session_token: str,
    device_store: DeviceStore | None = None,
    session_store: SessionStore | None = None,
) -> ControlSession:
    device_store = device_store or DeviceStore()
    session_store = session_store or SessionStore()
    session = session_store.authenticate(session_id, session_token)
    device_store.touch(session.device_id)
    return session


def authenticate_signed_session_request(
    *,
    session_id: str,
    session_token: str,
    device_id: str,
    method: str,
    path: str,
    timestamp: str,
    nonce: str,
    signature: str,
    device_store: DeviceStore | None = None,
    session_store: SessionStore | None = None,
    nonce_store: DeviceNonceStore | None = None,
) -> ControlSession:
    device_store = device_store or DeviceStore()
    session = authenticate_session(
        session_id=session_id,
        session_token=session_token,
        device_store=device_store,
        session_store=session_store,
    )
    if session.device_id != device_id:
        raise PermissionError("device does not own session")
    device = device_store.get(device_id)
    message = device_signature_message(
        device_id=device_id,
        session_id=session_id,
        method=method,
        path=path,
        timestamp=timestamp,
        nonce=nonce,
    )
    verify_ecdsa_signature(public_key=device.public_key, signature_b64=signature, message=message)
    nonce_store = nonce_store or DeviceNonceStore()
    nonce_store.consume(device_id=device_id, nonce=nonce, timestamp=timestamp)
    return session
