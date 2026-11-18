"""Keyless signing-intent contract for ATLAS architecture B (source-only).

The Docker-facing producer can prepare a tightly scoped HML request WITHOUT
receiving a private signing key. The signature must arrive from an external
trust domain to provide meaningful separation. This library does not create
that domain, launch a signer, grant permissions or authenticate any caller.
An attacker controlling root can still forge Docker observations or tamper
with producer inputs. All resulting diagnostics remain blocked.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone

from .atlas_hml_b_snapshot_envelope import (
    HMLSnapshotEnvelopeError, build_unsigned_envelope_document,
    seal_envelope_document, signing_message,
)
from .atlas_hml_b_snapshot_trust import (
    HMLSnapshotTrustError, HMLTrustKeyring,
    verify_signed_snapshot_envelope,
)
from .atlas_hml_snapshot_candidate import (
    SnapshotContractError, review_untrusted_snapshot,
)
from .atlas_hml_snapshot_publisher_candidate import (
    HMLSnapshotPublishError, build_hml_snapshot_claim,
)
from .deploy_host_source import RuntimeContainer

_BLOCKS = (
    "EXTERNAL_SIGNER_IDENTITY_NOT_ATTESTED",
    "EXTERNAL_SIGNING_KEY_CUSTODY_NOT_ATTESTED",
    "DOCKER_ROOT_PRODUCER_CAN_FORGE_OBSERVATIONS",
    "SIGNING_INTENT_IS_NOT_AN_OPERATIONAL_APPROVAL",
    "SEC_01_TO_10_PENDING",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)


class HMLExternalSigningError(Exception):
    """Only predetermined sanitized error codes."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class HMLSigningIntent:
    payload: bytes
    generation: int
    produced_at: datetime
    key_id: str
    signing_bytes: bytes
    status: str = "blocked"
    key_custody_independent: bool = False
    producer_isolation_attested: bool = False
    can_execute: bool = False
    prepare_eligible: bool = False
    blocks: tuple[str, ...] = _BLOCKS


@dataclass(frozen=True, slots=True)
class HMLExternallySealedReview:
    envelope: bytes
    status: str = "blocked"
    signature_verified: bool = True
    signer_independently_attested: bool = False
    key_custody_independent: bool = False
    producer_isolation_attested: bool = False
    can_execute: bool = False
    prepare_eligible: bool = False
    blocks: tuple[str, ...] = _BLOCKS


def prepare_signing_intent(
    container: RuntimeContainer, *, observed_at: datetime,
    generation: int, key_id: str,
) -> HMLSigningIntent:
    """Build request WITHOUT accepting private key, signer URI or Docker path.

    This pure function never opens Docker or a filesystem. The opaque payload
    is a *claim*, not a statement about the genuine host or container.
    """
    if (
        type(container) is not RuntimeContainer
        or type(observed_at) is not datetime
        or observed_at.tzinfo is None or observed_at.utcoffset() is None
        or type(generation) is not int or not 1 <= generation < 2**63
        or type(key_id) is not str
    ):
        raise HMLExternalSigningError("HML_SIGNING_INTENT_INPUT_INVALID")
    try:
        claim = build_hml_snapshot_claim(container, observed_at=observed_at)
        document = build_unsigned_envelope_document(
            claim, generation=generation, produced_at=observed_at,
            key_id=key_id,
        )
        message = signing_message(
            generation=generation,
            produced_at=str(document["produced_at"]),
            payload_sha256=str(document["payload_sha256"]),
            key_id=key_id,
            payload=claim,
        )
    except (HMLSnapshotPublishError, HMLSnapshotEnvelopeError):
        raise HMLExternalSigningError("HML_SIGNING_INTENT_BUILD_DENIED") from None
    return HMLSigningIntent(
        payload=claim,
        generation=generation,
        produced_at=datetime.fromisoformat(
            str(document["produced_at"]).replace("Z", "+00:00")
        ),
        key_id=key_id,
        signing_bytes=message,
    )


def review_signing_intent_for_external_signer(
    intent: HMLSigningIntent, *, now: datetime, expected_generation: int,
) -> HMLSigningIntent:
    """Pure signer-side policy check. 'Pass' never authorizes actual signing.

    An external signer would also need kernel-verified client authentication,
    an isolated private-key boundary, a trusted monotonic counter and human
    change authorization. Those controls DO NOT exist in this function.
    """
    if (
        type(intent) is not HMLSigningIntent
        or type(now) is not datetime or now.tzinfo is None
        or now.utcoffset() is None
        or type(expected_generation) is not int
        or not 1 <= expected_generation < 2**63
    ):
        raise HMLExternalSigningError("HML_SIGNING_INTENT_POLICY_INVALID")
    if (
        type(intent.payload) is not bytes
        or type(intent.generation) is not int
        or type(intent.produced_at) is not datetime
        or intent.produced_at.tzinfo is None
        or intent.produced_at.utcoffset() is None
        or type(intent.key_id) is not str
        or type(intent.signing_bytes) is not bytes
    ):
        raise HMLExternalSigningError("HML_SIGNING_INTENT_POLICY_INVALID")
    if intent.generation != expected_generation:
        raise HMLExternalSigningError("HML_SIGNING_INTENT_COUNTER_DENIED")
    if (
        intent.status != "blocked" or intent.can_execute
        or intent.prepare_eligible or intent.key_custody_independent
        or intent.producer_isolation_attested
        or type(intent.blocks) is not tuple or intent.blocks != _BLOCKS
    ):
        raise HMLExternalSigningError("HML_SIGNING_INTENT_POLICY_INVALID")
    try:
        claim = review_untrusted_snapshot(intent.payload, now=now)
        payload_observed = datetime.fromisoformat(
            claim.observed_at_untrusted.replace("Z", "+00:00")
        )
        if payload_observed != intent.produced_at.astimezone(timezone.utc):
            raise ValueError("timestamp drift")
        document = build_unsigned_envelope_document(
            intent.payload, generation=intent.generation,
            produced_at=intent.produced_at, key_id=intent.key_id,
        )
        regenerated = signing_message(
            generation=intent.generation,
            produced_at=str(document["produced_at"]),
            payload_sha256=hashlib.sha256(intent.payload).hexdigest(),
            key_id=intent.key_id,
            payload=intent.payload,
        )
        if regenerated != intent.signing_bytes:
            raise ValueError("modified signing bytes")
    except (SnapshotContractError, HMLSnapshotEnvelopeError, ValueError, TypeError):
        raise HMLExternalSigningError("HML_SIGNING_INTENT_SCOPE_DENIED") from None
    return intent


def seal_externally_signed_intent(
    intent: HMLSigningIntent, *, signature: bytes,
    keyring: HMLTrustKeyring, now: datetime,
) -> HMLExternallySealedReview:
    """Keyless verify + seal; refuse any signature not matching the intent."""
    if type(intent) is not HMLSigningIntent:
        raise HMLExternalSigningError("HML_SIGNING_INTENT_POLICY_INVALID")
    review_signing_intent_for_external_signer(
        intent, now=now, expected_generation=intent.generation,
    )
    if type(signature) is not bytes or len(signature) != 64:
        raise HMLExternalSigningError("HML_SIGNING_SIGNATURE_INVALID")
    try:
        document = build_unsigned_envelope_document(
            intent.payload, generation=intent.generation,
            produced_at=intent.produced_at, key_id=intent.key_id,
        )
        sealed = seal_envelope_document(document, signature=signature)
        verified = verify_signed_snapshot_envelope(
            sealed, now=now, keyring=keyring,
        )
        if (
            not verified.signature_verified
            or verified.envelope.signed_message != intent.signing_bytes
            or verified.envelope.key_id != intent.key_id
        ):
            raise HMLExternalSigningError("HML_SIGNING_SIGNATURE_INVALID")
    except HMLExternalSigningError:
        raise
    except (HMLSnapshotEnvelopeError, HMLSnapshotTrustError):
        raise HMLExternalSigningError("HML_SIGNING_SIGNATURE_INVALID") from None
    return HMLExternallySealedReview(envelope=sealed)
