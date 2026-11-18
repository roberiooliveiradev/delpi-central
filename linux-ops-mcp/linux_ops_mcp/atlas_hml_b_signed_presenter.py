"""Signed-envelope presenter candidate for ATLAS HML READ (source-only).

Verifies Ed25519 envelope + key fingerprint + generation + payload continuity
before producing a blocked READ presentation. Never opens Docker, never enables
PREPARE/ACT, never attests origin independent of the same-host producer.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .atlas_hml_b_continuity_store import (
    HMLContinuityRecord,
    HMLContinuityStore,
    HMLContinuityStoreError,
)
from .atlas_hml_b_lifecycle import HMLLifecycleError, HMLLifecycleSupervisor
from .atlas_hml_b_snapshot_continuity import (
    HMLSnapshotContinuityError,
    HMLSnapshotContinuityState,
    review_snapshot_continuity,
)
from .atlas_hml_b_snapshot_trust import (
    HMLSnapshotTrustError,
    HMLTrustKeyring,
    verify_signed_snapshot_envelope,
)

_BLOCKS = (
    "SIGNED_PRESENTER_SOURCE_ONLY",
    "SNAPSHOT_ORIGIN_NOT_ATTESTED",
    "SAME_HOST_ROOT_PRODUCER_UNTRUSTED",
    "SEC_01_TO_10_PENDING",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)
_PREFIX = b"atlas.hml.snapshot-envelope.v1"


class HMLSignedPresenterError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class HMLSignedPresentation:
    generation: int
    key_id: str
    payload: bytes
    status: str = "blocked"
    signature_verified: bool = False
    continuity_accepted: bool = False
    snapshot_origin_attested: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False
    blocks: tuple[str, ...] = _BLOCKS


def _payload_from_signed_message(signed_message: bytes) -> bytes:
    if type(signed_message) is not bytes or not signed_message.startswith(_PREFIX + b"\x00"):
        raise HMLSignedPresenterError("HML_SIGNED_PRESENTER_PAYLOAD_UNAVAILABLE")
    rest = signed_message[len(_PREFIX) + 1 :]
    sep = rest.find(b"\x00")
    if sep < 0:
        raise HMLSignedPresenterError("HML_SIGNED_PRESENTER_PAYLOAD_UNAVAILABLE")
    payload = rest[sep + 1 :]
    if not payload:
        raise HMLSignedPresenterError("HML_SIGNED_PRESENTER_PAYLOAD_UNAVAILABLE")
    return payload


def present_verified_signed_envelope(
    envelope: bytes, *,
    keyring: HMLTrustKeyring,
    now: datetime,
    continuity: HMLContinuityStore | None = None,
    lifecycle: HMLLifecycleSupervisor | None = None,
    previous_payload_state: HMLSnapshotContinuityState | None = None,
) -> HMLSignedPresentation:
    """Verify signature and payload continuity; always returns blocked READ material."""
    if (
        type(envelope) is not bytes
        or not 1 <= len(envelope) <= 65536
        or type(keyring) is not HMLTrustKeyring
        or type(now) is not datetime
        or now.tzinfo is None
    ):
        raise HMLSignedPresenterError("HML_SIGNED_PRESENTER_INPUT_DENIED")
    life = lifecycle or HMLLifecycleSupervisor()
    try:
        if life.state.value == "init":
            life.mark_available()
        life.begin_observe()
    except HMLLifecycleError as exc:
        raise HMLSignedPresenterError(exc.code) from None
    try:
        verified = verify_signed_snapshot_envelope(envelope, keyring=keyring, now=now)
        env = verified.envelope
        payload = _payload_from_signed_message(env.signed_message)
        review_snapshot_continuity(
            payload, now=now, previous=previous_payload_state,
        )
        if continuity is not None:
            continuity.commit(HMLContinuityRecord(
                generation=env.generation,
                digest=env.payload_sha256,
                observed_at=env.produced_at,
                container_id=env.diagnostic.container_id,
                image_id=env.diagnostic.image_id,
                updated_at=now,
            ))
        life.end_observe()
    except (
        HMLSnapshotTrustError, HMLSnapshotContinuityError,
        HMLContinuityStoreError, HMLLifecycleError, HMLSignedPresenterError,
    ) as exc:
        try:
            life.end_observe()
        except HMLLifecycleError:
            pass
        try:
            life.mark_integrity_compromised()
        except HMLLifecycleError:
            pass
        code = getattr(exc, "code", "HML_SIGNED_PRESENTER_FAILED")
        raise HMLSignedPresenterError(code) from None
    return HMLSignedPresentation(
        generation=env.generation,
        key_id=env.key_id,
        payload=payload,
        signature_verified=True,
        continuity_accepted=True,
    )


def load_and_present_signed_envelope_file(
    path: Path, *,
    keyring: HMLTrustKeyring,
    now: datetime,
    owner_uid: int,
    expected_gid: int,
    continuity: HMLContinuityStore | None = None,
) -> HMLSignedPresentation:
    """Read a sealed envelope from an absolute disposable path (no Docker)."""
    if (
        type(path) is not type(Path("/"))
        or not path.is_absolute()
        or type(owner_uid) is not int
        or type(expected_gid) is not int
    ):
        raise HMLSignedPresenterError("HML_SIGNED_PRESENTER_PATH_DENIED")
    try:
        st = path.stat()
        if st.st_uid != owner_uid or st.st_gid != expected_gid:
            raise HMLSignedPresenterError("HML_SIGNED_PRESENTER_OWNERSHIP_DENIED")
        raw = path.read_bytes()
    except OSError:
        raise HMLSignedPresenterError("HML_SIGNED_PRESENTER_READ_DENIED") from None
    return present_verified_signed_envelope(
        raw, keyring=keyring, now=now, continuity=continuity,
    )
