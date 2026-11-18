"""Disposable end-to-end signed pipeline over a real AF_UNIX socket (source-only).

Collect (fixture observation) -> snapshot publish -> bridge -> signer-owned
listen -> signature -> independent verify -> continuity commit -> recovery floor.
Runs only inside an explicit disposable fixture directory. Reuses stage 66-73
primitives; never installs services, never opens Docker Engine, never enables
PREPARE/ACT.
"""
from __future__ import annotations

import os
import stat
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .atlas_hml_b_continuity_store import HMLContinuityRecord, HMLContinuityStore
from .atlas_hml_b_counter_recovery import assert_generation_floor
from .atlas_hml_b_external_signing_intent import prepare_signing_intent
from .atlas_hml_b_key_lifecycle import generate_ephemeral_keypair
from .atlas_hml_b_local_signer import HMLLocalSigner
from .atlas_hml_b_nonroot_sign_bridge import (
    build_nonroot_signing_intent,
    request_signature_via_nonroot_uds,
)
from .atlas_hml_b_signer_listen import start_background_signer_listen_fixture
from .atlas_hml_b_snapshot_trust import build_keyring, verify_signed_snapshot_envelope
from .atlas_hml_snapshot_publisher_candidate import _publish_in_review_directory
from .deploy_host_source import RuntimeContainer

_BLOCKS = (
    "SIGNED_PIPELINE_DISPOSABLE_ONLY",
    "NOT_HOST_ATTESTATION",
    "SEC_01_TO_10_PENDING",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)


class HMLSignedPipelineError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class HMLSignedPipelineResult:
    generation: int
    key_id: str
    signature_verified: bool
    continuity_persisted: bool
    socket_mode: int
    status: str = "blocked"
    prepare_eligible: bool = False
    can_execute: bool = False
    blocks: tuple[str, ...] = _BLOCKS


def _require_disposable(root: Path) -> None:
    if (
        type(root) is not type(Path("/"))
        or not root.is_absolute()
        or root == Path("/")
        or root.is_symlink()
        or not root.is_dir()
    ):
        raise HMLSignedPipelineError("HML_PIPELINE_ROOT_DENIED")
    marker = root / "DISPOSABLE_FIXTURE"
    if not marker.is_file():
        raise HMLSignedPipelineError("HML_PIPELINE_DISPOSABLE_MARKER_REQUIRED")


def run_disposable_signed_pipeline(
    *,
    fixture_root: Path,
    container: RuntimeContainer,
    generation: int = 1,
    observed_at: datetime | None = None,
    max_age_seconds: int = 300,
) -> HMLSignedPipelineResult:
    """Real UNIX socket path inside a disposable fixture; always status=blocked."""
    _require_disposable(fixture_root)
    if type(container) is not RuntimeContainer:
        raise HMLSignedPipelineError("HML_PIPELINE_CONTAINER_DENIED")
    if type(generation) is not int or generation < 1:
        raise HMLSignedPipelineError("HML_PIPELINE_GENERATION_DENIED")
    if type(max_age_seconds) is not int or max_age_seconds < 1:
        raise HMLSignedPipelineError("HML_PIPELINE_MAX_AGE_DENIED")
    now = observed_at or datetime.now(timezone.utc)
    if now.tzinfo is None or now.utcoffset() is None:
        raise HMLSignedPipelineError("HML_PIPELINE_TIME_DENIED")
    uid = os.getuid()
    gid = os.getgid()
    if uid <= 0:
        raise HMLSignedPipelineError("HML_PIPELINE_ROOT_DENIED")

    state_dir = fixture_root / "state"
    socket_dir = fixture_root / "socket"
    claim_dir = fixture_root / "claims"
    for path, mode in (
        (state_dir, 0o750),
        (socket_dir, 0o2750),
        (claim_dir, 0o750),
    ):
        path.mkdir(parents=True, exist_ok=True)
        os.chmod(path, mode)

    material = generate_ephemeral_keypair()
    keyring = build_keyring(active=((material.key_id, material.public_key),))
    signer = HMLLocalSigner(
        private_key=material.private_key,
        public_key=material.public_key,
        allowed_peer_uids=frozenset({uid}),
    )

    intent_preview = prepare_signing_intent(
        container, observed_at=now, generation=generation, key_id=material.key_id,
    )
    _publish_in_review_directory(
        claim_dir,
        raw=intent_preview.payload,
        owner_uid=uid,
        expected_gid=gid,
        now=now,
    )

    sock_path = socket_dir / "sign.sock"
    ready = threading.Event()
    errors: list[str] = []
    thread = start_background_signer_listen_fixture(
        socket_path=sock_path,
        owner_uid=uid,
        socket_gid=gid,
        signer=signer,
        now=now,
        expected_generation=generation,
        ready=ready,
        errors=errors,
    )
    if not ready.wait(timeout=3):
        raise HMLSignedPipelineError("HML_PIPELINE_SIGNER_START_TIMEOUT")
    if errors:
        raise HMLSignedPipelineError(errors[0])

    try:
        st = os.stat(sock_path, follow_symlinks=False)
        if not stat.S_ISSOCK(st.st_mode) or stat.S_IMODE(st.st_mode) != 0o660:
            raise HMLSignedPipelineError("HML_PIPELINE_SOCKET_MODE_DENIED")
        intent = build_nonroot_signing_intent(
            directory=claim_dir,
            owner_uid=uid,
            expected_gid=gid,
            generation=generation,
            key_id=material.key_id,
            now=now,
        )
        bridged = request_signature_via_nonroot_uds(
            intent,
            socket_path=sock_path,
            expected_socket_owner_uid=uid,
            expected_socket_gid=gid,
            expected_signer_uid=uid,
            keyring=keyring,
            now=now,
            disposable_same_uid_fixture=True,
        )
        verified = verify_signed_snapshot_envelope(
            bridged.envelope, now=now, keyring=keyring,
        )
        if not verified.signature_verified:
            raise HMLSignedPipelineError("HML_PIPELINE_VERIFY_FAILED")
        produced = verified.envelope.produced_at
        if isinstance(produced, str):
            produced = datetime.fromisoformat(produced.replace("Z", "+00:00"))
        age = now - produced
        if age > timedelta(seconds=max_age_seconds) or age < timedelta(0):
            raise HMLSignedPipelineError("HML_PIPELINE_SNAPSHOT_EXPIRED")

        store = HMLContinuityStore(state_dir, owner_uid=uid, expected_gid=gid)
        store.commit(HMLContinuityRecord(
            generation=generation,
            digest=verified.envelope.payload_sha256,
            observed_at=now,
            container_id=container.container_id,
            image_id=container.image_id,
            updated_at=now,
        ))
        loaded = store.load()
        if loaded is None or loaded.generation != generation:
            raise HMLSignedPipelineError("HML_PIPELINE_CONTINUITY_REGRESSION")
        assert_generation_floor(proposed=generation + 1, floor=loaded.generation)
        try:
            assert_generation_floor(proposed=generation, floor=loaded.generation)
        except Exception as exc:
            code = getattr(exc, "code", "")
            if code != "HML_RECOVERY_GENERATION_REGRESSION":
                raise HMLSignedPipelineError("HML_PIPELINE_FLOOR_UNEXPECTED") from exc
    except HMLSignedPipelineError:
        raise
    except Exception as exc:
        code = getattr(exc, "code", type(exc).__name__)
        raise HMLSignedPipelineError(str(code)) from None
    finally:
        thread.join(timeout=5)

    if errors:
        raise HMLSignedPipelineError(errors[0])

    return HMLSignedPipelineResult(
        generation=generation,
        key_id=material.key_id,
        signature_verified=True,
        continuity_persisted=True,
        socket_mode=0o660,
    )
