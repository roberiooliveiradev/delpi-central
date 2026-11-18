"""Integrated HML local-signing pipeline candidate (source-only fixtures).

Chains: claim → signing intent → local signer → sealed envelope → atomic
publish → public verify → continuity commit. Always status=blocked.
Does not open Docker, systemd, MCP or host /run paths.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .atlas_hml_b_continuity_store import (
    HMLContinuityCommitResult,
    HMLContinuityRecord,
    HMLContinuityStore,
    HMLContinuityStoreError,
)
from .atlas_hml_b_external_signing_intent import (
    HMLExternalSigningError,
    prepare_signing_intent,
    seal_externally_signed_intent,
)
from .atlas_hml_b_lifecycle import (
    HMLLifecycleDiagnostic,
    HMLLifecycleError,
    HMLLifecycleSupervisor,
)
from .atlas_hml_b_local_signer import HMLLocalSigner, HMLLocalSignerError
from .atlas_hml_b_signed_producer import (
    HMLSignedProducerError,
    _publish_envelope_bytes,
)
from .atlas_hml_b_snapshot_trust import (
    HMLSnapshotTrustError,
    HMLTrustKeyring,
    verify_signed_snapshot_envelope,
)
from .atlas_hml_snapshot_publisher_candidate import (
    HMLSnapshotPublishError,
    _publish_in_review_directory,
)
from .deploy_host_source import RuntimeContainer

_BLOCKS = (
    "PIPELINE_USES_LOCAL_SAME_HOST_SIGNER",
    "ROOT_CAN_STILL_COMPROMISE_LOCAL_PRIVATE_KEY",
    "NOT_AN_OPERATIONAL_ACTIVATION",
    "SEC_01_TO_10_PENDING",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)


class HMLLocalPipelineError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class HMLLocalPipelineResult:
    envelope: bytes
    generation: int
    key_id: str
    continuity: HMLContinuityCommitResult | None
    lifecycle: HMLLifecycleDiagnostic
    status: str = "blocked"
    signature_verified: bool = False
    authenticity_independent: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False
    blocks: tuple[str, ...] = _BLOCKS


def run_local_signed_hml_pipeline(
    container: RuntimeContainer, *,
    directory: Path,
    owner_uid: int,
    expected_gid: int,
    observed_at: datetime,
    generation: int,
    signer: HMLLocalSigner,
    keyring: HMLTrustKeyring,
    peer_uid: int,
    continuity: HMLContinuityStore | None = None,
    lifecycle: HMLLifecycleSupervisor | None = None,
) -> HMLLocalPipelineResult:
    """Execute the disposable integrated pipeline; never enables PREPARE/ACT."""
    if (
        type(container) is not RuntimeContainer
        or type(directory) is not type(Path("/"))
        or not directory.is_absolute()
        or type(signer) is not HMLLocalSigner
        or type(keyring) is not HMLTrustKeyring
        or type(peer_uid) is not int
        or type(generation) is not int
    ):
        raise HMLLocalPipelineError("HML_LOCAL_PIPELINE_INPUT_INVALID")
    life = lifecycle or HMLLifecycleSupervisor()
    try:
        if life.state.value == "init":
            life.mark_available()
        life.begin_observe()
    except HMLLifecycleError as exc:
        raise HMLLocalPipelineError(exc.code) from None
    try:
        intent = prepare_signing_intent(
            container, observed_at=observed_at,
            generation=generation, key_id=signer.key_id,
        )
        signed = signer.sign_intent(
            intent, now=observed_at, peer_uid=peer_uid,
            expected_generation=generation,
        )
        sealed = seal_externally_signed_intent(
            intent, signature=signed.signature, keyring=keyring, now=observed_at,
        )
        _publish_in_review_directory(
            directory, raw=intent.payload, owner_uid=owner_uid,
            expected_gid=expected_gid, now=observed_at,
        )
        _publish_envelope_bytes(
            directory, raw=sealed.envelope, owner_uid=owner_uid,
            expected_gid=expected_gid,
        )
        verified = verify_signed_snapshot_envelope(
            sealed.envelope, now=observed_at, keyring=keyring,
        )
        continuity_result = None
        if continuity is not None:
            continuity_result = continuity.commit(HMLContinuityRecord(
                generation=generation,
                digest=verified.envelope.payload_sha256,
                observed_at=observed_at,
                container_id=container.container_id,
                image_id=container.image_id,
                updated_at=observed_at,
            ))
        life.end_observe()
        return HMLLocalPipelineResult(
            envelope=sealed.envelope,
            generation=generation,
            key_id=signer.key_id,
            continuity=continuity_result,
            lifecycle=life.diagnose("OK"),
            signature_verified=verified.signature_verified,
        )
    except (
        HMLLocalSignerError, HMLExternalSigningError, HMLSnapshotTrustError,
        HMLSnapshotPublishError, HMLSignedProducerError, HMLContinuityStoreError,
        HMLLifecycleError,
    ) as exc:
        try:
            life.end_observe()
        except HMLLifecycleError:
            pass
        code = getattr(exc, "code", "HML_LOCAL_PIPELINE_FAILED")
        if code in {
            "HML_LOCAL_SIGNER_REPLAY",
            "HML_TRUST_SIGNATURE_INVALID",
            "HML_CONTINUITY_STORE_CORRUPT",
            "HML_CONTINUITY_STORE_REPLAY",
            "HML_LOCAL_SIGNER_GENERATION_REGRESSION",
        }:
            try:
                life.mark_integrity_compromised()
            except HMLLifecycleError:
                pass
        else:
            try:
                life.mark_failure("SNAPSHOT_INVALID")
            except HMLLifecycleError:
                pass
        raise HMLLocalPipelineError(code) from None
