"""Ed25519 snapshot trust candidate for ATLAS architecture B (source-only).

Presenter-side verification uses ONLY public keys from an injected keyring.
Private keys are accepted solely as caller-injected fixture material for local
tests and MUST never be committed. A producer that can also read the private
key on the same host can forge authenticity; this module documents that
dependency and never claims independent authenticity across trust domains.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from .atlas_hml_b_snapshot_envelope import (
    HMLSnapshotEnvelopeError,
    HMLSnapshotEnvelopeReview,
    build_unsigned_envelope_document,
    review_snapshot_envelope,
    seal_envelope_document,
    signing_message,
)

_KEY_ID = re.compile(r"[0-9a-f]{16,64}\Z")
_BLOCKS = (
    "SIGNATURE_VERIFIED_WITHIN_SHARED_HOST_TRUST_DOMAIN",
    "ROOT_WITH_PRIVATE_KEY_ACCESS_CAN_FORGE",
    "KEY_MATERIAL_MUST_NOT_LIVE_IN_GIT",
    "SEC_01_TO_10_PENDING",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)


class HMLSnapshotTrustError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class HMLPublicKeyRecord:
    key_id: str
    public_key: bytes
    revoked: bool = False


@dataclass(frozen=True, slots=True)
class HMLTrustKeyring:
    """Fail-closed public keyring; private keys are never stored here."""

    keys: tuple[HMLPublicKeyRecord, ...]

    def active_public(self, key_id: str) -> bytes:
        if type(key_id) is not str or _KEY_ID.fullmatch(key_id) is None:
            raise HMLSnapshotTrustError("HML_TRUST_KEY_ID_INVALID")
        matches = [item for item in self.keys if item.key_id == key_id]
        if len(matches) != 1:
            raise HMLSnapshotTrustError("HML_TRUST_KEY_UNKNOWN")
        record = matches[0]
        if record.revoked:
            raise HMLSnapshotTrustError("HML_TRUST_KEY_REVOKED")
        if type(record.public_key) is not bytes or len(record.public_key) != 32:
            raise HMLSnapshotTrustError("HML_TRUST_KEY_INVALID")
        if key_id_for_public_key(record.public_key) != key_id:
            raise HMLSnapshotTrustError("HML_TRUST_KEY_INVALID")
        return record.public_key


@dataclass(frozen=True, slots=True)
class HMLSnapshotTrustReview:
    envelope: HMLSnapshotEnvelopeReview
    status: str = "blocked"
    signature_verified: bool = False
    authenticity_independent: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False
    blocks: tuple[str, ...] = _BLOCKS


def key_id_for_public_key(public_key: bytes) -> str:
    if type(public_key) is not bytes or len(public_key) != 32:
        raise HMLSnapshotTrustError("HML_TRUST_KEY_INVALID")
    return hashlib.sha256(b"atlas.hml.key-id.v1\x00" + public_key).hexdigest()[:32]


def generate_fixture_keypair() -> tuple[bytes, bytes, str]:
    """CI/tmp-only keypair factory. Never persist the private key in Git."""
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes_raw()
    return private.private_bytes_raw(), public, key_id_for_public_key(public)


def build_keyring(
    *,
    active: tuple[tuple[str, bytes], ...],
    revoked: tuple[tuple[str, bytes], ...] = (),
) -> HMLTrustKeyring:
    records: list[HMLPublicKeyRecord] = []
    seen: set[str] = set()
    for key_id, public_key in (*active, *revoked):
        if (
            type(key_id) is not str or _KEY_ID.fullmatch(key_id) is None
            or type(public_key) is not bytes or len(public_key) != 32
            or key_id_for_public_key(public_key) != key_id
            or key_id in seen
        ):
            raise HMLSnapshotTrustError("HML_TRUST_KEYRING_INVALID")
        seen.add(key_id)
        records.append(HMLPublicKeyRecord(
            key_id=key_id,
            public_key=public_key,
            revoked=False,
        ))
    # Mark revoked after validating uniqueness across the whole set.
    revoked_ids = {key_id for key_id, _ in revoked}
    finalized = tuple(
        HMLPublicKeyRecord(
            key_id=item.key_id,
            public_key=item.public_key,
            revoked=item.key_id in revoked_ids,
        )
        for item in records
    )
    if not any(not item.revoked for item in finalized):
        raise HMLSnapshotTrustError("HML_TRUST_KEYRING_EMPTY")
    return HMLTrustKeyring(keys=finalized)


def sign_snapshot_envelope(
    payload: bytes, *,
    generation: int,
    produced_at,
    private_key: bytes,
    public_key: bytes,
) -> bytes:
    """Sign with caller-injected private key material (fixture/producer only)."""
    if type(private_key) is not bytes or len(private_key) != 32:
        raise HMLSnapshotTrustError("HML_TRUST_PRIVATE_KEY_INVALID")
    if type(public_key) is not bytes or len(public_key) != 32:
        raise HMLSnapshotTrustError("HML_TRUST_KEY_INVALID")
    key_id = key_id_for_public_key(public_key)
    try:
        document = build_unsigned_envelope_document(
            payload, generation=generation, produced_at=produced_at, key_id=key_id,
        )
        message = signing_message(
            generation=int(document["generation"]),
            produced_at=str(document["produced_at"]),
            payload_sha256=str(document["payload_sha256"]),
            key_id=key_id,
            payload=payload,
        )
        signature = Ed25519PrivateKey.from_private_bytes(private_key).sign(message)
    except HMLSnapshotEnvelopeError as exc:
        raise HMLSnapshotTrustError(exc.code) from None
    except (ValueError, TypeError):
        raise HMLSnapshotTrustError("HML_TRUST_SIGN_FAILED") from None
    try:
        return seal_envelope_document(document, signature=signature)
    except HMLSnapshotEnvelopeError as exc:
        raise HMLSnapshotTrustError(exc.code) from None


def verify_signed_snapshot_envelope(
    raw: bytes, *, now, keyring: HMLTrustKeyring,
) -> HMLSnapshotTrustReview:
    """Verify envelope + Ed25519 using public keys only; always status=blocked."""
    if type(keyring) is not HMLTrustKeyring:
        raise HMLSnapshotTrustError("HML_TRUST_KEYRING_INVALID")
    try:
        envelope = review_snapshot_envelope(raw, now=now)
    except HMLSnapshotEnvelopeError as exc:
        raise HMLSnapshotTrustError(exc.code) from None
    public = keyring.active_public(envelope.key_id)
    try:
        Ed25519PublicKey.from_public_bytes(public).verify(
            envelope.signature, envelope.signed_message,
        )
    except InvalidSignature:
        raise HMLSnapshotTrustError("HML_TRUST_SIGNATURE_INVALID") from None
    except (ValueError, TypeError):
        raise HMLSnapshotTrustError("HML_TRUST_SIGNATURE_UNVERIFIABLE") from None
    return HMLSnapshotTrustReview(
        envelope=envelope,
        signature_verified=True,
        # Same-host root + key access is still a shared trust domain.
        authenticity_independent=False,
    )
