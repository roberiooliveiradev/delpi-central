"""Disposable Architecture B chain helpers (source-only).

Prefer composing existing publisher/bridge/signer/presenter APIs in tests.
This module provides a bounded same-UID fixture helper that never opens Docker
unless the caller already supplies a RuntimeContainer. Always status=blocked.
"""
from __future__ import annotations

import os
import socket
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .atlas_hml_b_external_signing_intent import prepare_signing_intent
from .atlas_hml_b_key_lifecycle import generate_ephemeral_keypair
from .atlas_hml_b_lifecycle import HMLLifecycleSupervisor
from .atlas_hml_b_local_signer import HMLLocalSigner, _serve_one_local_sign_request
from .atlas_hml_b_nonroot_sign_bridge import (
    HMLNonrootBridgeError,
    build_nonroot_signing_intent,
    request_signature_via_nonroot_uds,
)
from .atlas_hml_b_signed_presenter import (
    HMLSignedPresenterError,
    present_verified_signed_envelope,
)
from .atlas_hml_b_snapshot_trust import build_keyring
from .atlas_hml_snapshot_publisher_candidate import (
    HMLSnapshotPublishError,
    _publish_in_review_directory,
)
from .deploy_host_source import RuntimeContainer

_BLOCKS = (
    "CHAIN_ORCHESTRATOR_SOURCE_ONLY",
    "DISPOSABLE_FIXTURE_NOT_HOST_ATTESTATION",
    "SEC_01_TO_10_PENDING",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)


class HMLChainOrchestratorError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class HMLChainResult:
    generation: int
    key_id: str
    envelope: bytes
    status: str = "blocked"
    signature_verified: bool = False
    bridge_used: bool = False
    signer_self_bound: bool = False
    authenticity_independent: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False
    blocks: tuple[str, ...] = _BLOCKS


def run_bridge_signed_chain_fixture(
    container: RuntimeContainer, *,
    claim_directory: Path,
    socket_directory: Path,
    owner_uid: int,
    expected_gid: int,
    socket_gid: int,
    generation: int,
    observed_at: datetime | None = None,
    disposable_same_uid_fixture: bool = True,
) -> HMLChainResult:
    """Same-UID disposable chain using an explicit pre-bound listener thread.

    The listener is created by the current non-root UID (not root-prebound by a
    distinct supervisor). Operational hosts must use signer-owned bind via
    atlas_hml_b_signer_listen instead of this fixture helper.
    """
    if (
        type(container) is not RuntimeContainer
        or type(claim_directory) is not type(Path("/"))
        or type(socket_directory) is not type(Path("/"))
        or not claim_directory.is_absolute()
        or not socket_directory.is_absolute()
        or type(generation) is not int
        or generation < 1
    ):
        raise HMLChainOrchestratorError("HML_CHAIN_INPUT_DENIED")
    now = observed_at or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise HMLChainOrchestratorError("HML_CHAIN_INPUT_DENIED")
    peer = os.getuid()
    if peer <= 0:
        raise HMLChainOrchestratorError("HML_CHAIN_ROOT_PEER_DENIED")
    material = generate_ephemeral_keypair()
    keyring = build_keyring(active=((material.key_id, material.public_key),))
    signer = HMLLocalSigner(
        private_key=material.private_key,
        public_key=material.public_key,
        allowed_peer_uids=frozenset({peer}),
    )
    try:
        intent_preview = prepare_signing_intent(
            container, observed_at=now, generation=generation, key_id=material.key_id,
        )
        _publish_in_review_directory(
            claim_directory, raw=intent_preview.payload,
            owner_uid=owner_uid, expected_gid=expected_gid, now=now,
        )
    except (HMLSnapshotPublishError, Exception) as exc:
        code = getattr(exc, "code", "HML_CHAIN_CLAIM_PUBLISH_DENIED")
        raise HMLChainOrchestratorError(code) from None

    socket_path = socket_directory / "sign.sock"
    if socket_path.exists():
        raise HMLChainOrchestratorError("HML_CHAIN_SOCKET_EXISTS")
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(socket_path))
    os.chmod(socket_path, 0o660)
    listener.listen(1)
    listener.settimeout(3.0)
    errors: list[str] = []

    def _serve() -> None:
        try:
            _serve_one_local_sign_request(
                listener=listener,
                signer=signer,
                expected_path=socket_path,
                now=now,
                expected_generation=generation,
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(str(getattr(exc, "code", type(exc).__name__)))
        finally:
            try:
                listener.close()
            except OSError:
                pass

    thread = threading.Thread(target=_serve, daemon=True)
    thread.start()
    try:
        intent = build_nonroot_signing_intent(
            directory=claim_directory,
            owner_uid=owner_uid,
            expected_gid=expected_gid,
            generation=generation,
            key_id=material.key_id,
            now=now,
        )
        bridged = request_signature_via_nonroot_uds(
            intent,
            socket_path=socket_path,
            expected_socket_owner_uid=owner_uid,
            expected_socket_gid=socket_gid,
            expected_signer_uid=peer,
            keyring=keyring,
            now=now,
            disposable_same_uid_fixture=disposable_same_uid_fixture,
        )
        presented = present_verified_signed_envelope(
            bridged.envelope,
            keyring=keyring,
            now=now,
            lifecycle=HMLLifecycleSupervisor(),
        )
    except (HMLNonrootBridgeError, HMLSignedPresenterError, OSError) as exc:
        code = getattr(exc, "code", "HML_CHAIN_BRIDGE_DENIED")
        raise HMLChainOrchestratorError(code) from None
    finally:
        thread.join(timeout=3.0)
        try:
            socket_path.unlink(missing_ok=True)
        except OSError:
            pass
    if errors:
        raise HMLChainOrchestratorError(errors[0])
    return HMLChainResult(
        generation=presented.generation,
        key_id=presented.key_id,
        envelope=bridged.envelope,
        signature_verified=presented.signature_verified,
        bridge_used=True,
        signer_self_bound=False,
    )
