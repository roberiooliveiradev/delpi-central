"""G2-S4-S2b-P2 offline Ed25519 proof for an independently pretrusted device key.

NO enrollment, key adoption, TPM attestation, token consumption, Keycloak,
S2S privilege, HTTP endpoint or remote access is implemented here.
"""
from __future__ import annotations

import base64
import json
import re
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

AUDIENCE = "delpi-it-portal-workstation-inventory-enrollment-v1"
MIN_TTL = 60
MAX_TTL = 600
MAX_SKEW = timedelta(seconds=30)
NONCE_RE = re.compile(r"^[A-Za-z0-9_-]{43}$")
SIGNATURE_RE = re.compile(r"^[A-Za-z0-9_-]{86}$")


def _uuid(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("identificador invalido")
    try:
        normalized = str(uuid.UUID(value))
    except (ValueError, AttributeError, TypeError):
        raise ValueError("identificador invalido") from None
    if normalized != value or uuid.UUID(value).int == 0:
        raise ValueError("identificador invalido")
    return normalized


@dataclass(frozen=True)
class DeviceProofChallenge:
    ticket_id: str
    workstation_id: str
    nonce: str
    issued_at: datetime
    expires_at: datetime
    audience: str = AUDIENCE


def create_challenge(ticket_id: str, workstation_id: str, *,
                     now: datetime | None = None, ttl_seconds: int = 180) -> DeviceProofChallenge:
    ticket = _uuid(ticket_id)
    workstation = _uuid(workstation_id)
    if type(ttl_seconds) is not int or not MIN_TTL <= ttl_seconds <= MAX_TTL:
        raise ValueError("duracao invalida")
    moment = now if now is not None else datetime.now(timezone.utc)
    if not isinstance(moment, datetime) or moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError("relogio UTC obrigatorio")
    moment = moment.astimezone(timezone.utc)
    return DeviceProofChallenge(ticket, workstation, secrets.token_urlsafe(32), moment,
                                moment + timedelta(seconds=ttl_seconds))


def canonical_challenge(challenge: DeviceProofChallenge) -> bytes:
    if not isinstance(challenge, DeviceProofChallenge):
        raise ValueError("desafio invalido")
    ticket = _uuid(challenge.ticket_id)
    machine = _uuid(challenge.workstation_id)
    if challenge.audience != AUDIENCE or not isinstance(challenge.nonce, str) or not NONCE_RE.fullmatch(challenge.nonce):
        raise ValueError("desafio invalido")
    start, stop = challenge.issued_at, challenge.expires_at
    if not isinstance(start, datetime) or not isinstance(stop, datetime) or start.tzinfo is None or stop.tzinfo is None:
        raise ValueError("tempo invalido")
    start = start.astimezone(timezone.utc)
    stop = stop.astimezone(timezone.utc)
    if start.microsecond or stop.microsecond or not MIN_TTL <= (stop - start).total_seconds() <= MAX_TTL:
        raise ValueError("tempo invalido")
    fields = {
        "audience": AUDIENCE,
        "expires_at": stop.isoformat().replace("+00:00", "Z"),
        "issued_at": start.isoformat().replace("+00:00", "Z"),
        "nonce": challenge.nonce,
        "ticket_id": ticket,
        "workstation_id": machine,
    }
    return json.dumps(fields, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def verify_pretrusted_device_proof(challenge: DeviceProofChallenge, signature_b64url: str,
                                   trusted_public_key: bytes, *, ticket_id: str,
                                   workstation_id: str, now: datetime | None = None) -> bool:
    """Only verify possession of a PRETRUSTED key; DB anti-replay is separate."""
    try:
        expected_ticket, expected_machine = _uuid(ticket_id), _uuid(workstation_id)
        if challenge.ticket_id != expected_ticket or challenge.workstation_id != expected_machine:
            return False
        message = canonical_challenge(challenge)
        clock = now if now is not None else datetime.now(timezone.utc)
        if not isinstance(clock, datetime) or clock.tzinfo is None or clock.utcoffset() is None:
            return False
        clock = clock.astimezone(timezone.utc)
        if clock < challenge.issued_at - MAX_SKEW or clock >= challenge.expires_at:
            return False
        if not isinstance(signature_b64url, str) or not SIGNATURE_RE.fullmatch(signature_b64url):
            return False
        if not isinstance(trusted_public_key, bytes) or len(trusted_public_key) != 32:
            return False
        signature = base64.urlsafe_b64decode(signature_b64url + "==")
        if len(signature) != 64 or base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii") != signature_b64url:
            return False
        Ed25519PublicKey.from_public_bytes(trusted_public_key).verify(signature, message)
        return True
    except (ValueError, TypeError, AttributeError, InvalidSignature):
        return False
