"""G2-S4-S2b-P1: offline, unrouted one-time workstation inventory tickets.

A ticket proves only possession of an opaque bearer value; it does NOT
attest the Windows device, authorize Keycloak, or grant snapshot ingestion.
There is deliberately no HTTP entrypoint or runtime activation here.
"""
from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import uuid
from dataclasses import dataclass

MIN_TTL_SECONDS = 60
MAX_TTL_SECONDS = 600
DEFAULT_TTL_SECONDS = 300
TOKEN_BYTES = 32
TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_-]{43}$")
DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class UnroutedTicket:
    ticket_id: str
    workstation_id: str
    token_digest: str
    ttl_seconds: int
    # This metadata object deliberately never contains the opaque secret.


def _workstation_uuid(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("workstation_id invalido")
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError):
        raise ValueError("workstation_id invalido") from None
    if parsed.int == 0 or str(parsed) != value:
        raise ValueError("workstation_id invalido")
    return str(parsed)


def ticket_digest(opaque_token: str) -> str:
    """Safe fingerprint for a cryptographically random, canonical 256-bit token."""
    if not isinstance(opaque_token, str) or not TOKEN_PATTERN.fullmatch(opaque_token):
        raise ValueError("ticket invalido")
    return hashlib.sha256(opaque_token.encode("ascii")).hexdigest()


def matches_ticket(opaque_token: str, stored_digest: str) -> bool:
    """No credential text in exceptions or result; compare digests in constant time."""
    if not isinstance(stored_digest, str) or not DIGEST_PATTERN.fullmatch(stored_digest):
        return False
    try:
        fingerprint = ticket_digest(opaque_token)
    except ValueError:
        return False
    return hmac.compare_digest(fingerprint, stored_digest)


def new_unrouted_ticket(
    workstation_id: str, *, ttl_seconds: int = DEFAULT_TTL_SECONDS
) -> tuple[UnroutedTicket, str]:
    """Return (safe metadata, transient secret) separately; no IO or activation."""
    target = _workstation_uuid(workstation_id)
    if type(ttl_seconds) is not int or not MIN_TTL_SECONDS <= ttl_seconds <= MAX_TTL_SECONDS:
        raise ValueError("duracao do ticket fora do limite")
    opaque = secrets.token_urlsafe(TOKEN_BYTES)
    metadata = UnroutedTicket(
        ticket_id=str(uuid.uuid4()),
        workstation_id=target,
        token_digest=ticket_digest(opaque),
        ttl_seconds=ttl_seconds,
    )
    return metadata, opaque
