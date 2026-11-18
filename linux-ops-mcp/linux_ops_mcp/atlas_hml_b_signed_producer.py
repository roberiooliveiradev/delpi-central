"""Signed one-shot handoff helper for architecture B (source-only fixtures).

Composes the existing HML claim builder with Ed25519 envelope sealing and the
atomic publisher. Private keys are caller-injected and never read from disk by
this module. A successful publish is NOT independent authenticity: root with
key access on the same host remains host-equivalent. No MCP/CLI/systemd entry.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .atlas_hml_b_snapshot_trust import (
    HMLSnapshotTrustError,
    sign_snapshot_envelope,
)
from .atlas_hml_snapshot_publisher_candidate import (
    HMLSnapshotPublishError,
    _publish_in_review_directory,
    build_hml_snapshot_claim,
)
from .deploy_host_source import RuntimeContainer

# Signed envelopes exceed the bare inspect JSON size; publish path still uses
# the publisher's max for the *file* content which must be raised carefully.
# We keep envelopes in a sibling filename reviewed only by trust/continuity.


class HMLSignedProducerError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class HMLSignedProducerReceipt:
    status: str = "blocked"
    generation: int = 0
    envelope_bytes: int = 0
    snapshot_origin_attested: bool = False
    authenticity_independent: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False


_ENVELOPE_NAME = "inspect-snapshot.envelope.v1.json"
_MAX_ENVELOPE_FILE = 8192


def build_signed_hml_envelope(
    container: RuntimeContainer, *,
    observed_at: datetime,
    generation: int,
    private_key: bytes,
    public_key: bytes,
) -> bytes:
    """Build claim + signed envelope bytes without writing to disk."""
    if type(container) is not RuntimeContainer:
        raise HMLSignedProducerError("HML_SIGNED_PRODUCER_INPUT_INVALID")
    if (
        type(generation) is not int or generation < 1
        or type(private_key) is not bytes or type(public_key) is not bytes
    ):
        raise HMLSignedProducerError("HML_SIGNED_PRODUCER_INPUT_INVALID")
    try:
        payload = build_hml_snapshot_claim(container, observed_at=observed_at)
        return sign_snapshot_envelope(
            payload,
            generation=generation,
            produced_at=observed_at,
            private_key=private_key,
            public_key=public_key,
        )
    except (HMLSnapshotPublishError, HMLSnapshotTrustError):
        raise HMLSignedProducerError("HML_SIGNED_PRODUCER_BUILD_FAILED") from None


def _publish_envelope_bytes(
    directory: Path, *, raw: bytes, owner_uid: int, expected_gid: int,
) -> None:
    """Atomic write for envelope sibling file inside a disposable directory."""
    import os
    import secrets
    import stat

    if (
        type(directory) is not type(Path("/")) or not directory.is_absolute()
        or type(raw) is not bytes or not 1 <= len(raw) <= _MAX_ENVELOPE_FILE
        or type(owner_uid) is not int or owner_uid < 0
        or type(expected_gid) is not int or expected_gid < 0
    ):
        raise HMLSignedProducerError("HML_SIGNED_PRODUCER_PUBLISH_INVALID")
    directory_fd = -1
    staged_fd = -1
    staged_name: str | None = None
    try:
        directory_fd = os.open(
            directory,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
        )
        parent = os.fstat(directory_fd)
        if (
            not stat.S_ISDIR(parent.st_mode)
            or parent.st_uid != owner_uid
            or parent.st_gid != expected_gid
            or stat.S_IMODE(parent.st_mode) != 0o750
        ):
            raise HMLSignedProducerError("HML_SIGNED_PRODUCER_DIR_UNSAFE")
        staged_name = ".atlas-hml-env-stage-" + secrets.token_hex(8)
        staged_fd = os.open(
            staged_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
            0o600,
            dir_fd=directory_fd,
        )
        if os.fstat(staged_fd).st_gid != expected_gid:
            os.fchown(staged_fd, owner_uid, expected_gid)
        os.fchmod(staged_fd, 0o640)
        offset = 0
        while offset < len(raw):
            written = os.write(staged_fd, raw[offset:])
            if written <= 0:
                raise HMLSignedProducerError("HML_SIGNED_PRODUCER_WRITE_FAILED")
            offset += written
        os.fsync(staged_fd)
        os.replace(
            staged_name, _ENVELOPE_NAME,
            src_dir_fd=directory_fd, dst_dir_fd=directory_fd,
        )
        staged_name = None
        os.fsync(directory_fd)
    except HMLSignedProducerError:
        raise
    except (OSError, ValueError, TypeError):
        raise HMLSignedProducerError("HML_SIGNED_PRODUCER_PUBLISH_FAILED") from None
    finally:
        if staged_fd >= 0:
            os.close(staged_fd)
        if staged_name is not None and directory_fd >= 0:
            try:
                os.unlink(staged_name, dir_fd=directory_fd)
            except OSError:
                pass
        if directory_fd >= 0:
            os.close(directory_fd)


def publish_signed_hml_bundle(
    container: RuntimeContainer, *,
    directory: Path,
    owner_uid: int,
    expected_gid: int,
    observed_at: datetime,
    generation: int,
    private_key: bytes,
    public_key: bytes,
) -> HMLSignedProducerReceipt:
    """Publish bare claim (existing path) + signed envelope sibling in tmp dirs."""
    try:
        claim = build_hml_snapshot_claim(container, observed_at=observed_at)
        envelope = sign_snapshot_envelope(
            claim,
            generation=generation,
            produced_at=observed_at,
            private_key=private_key,
            public_key=public_key,
        )
        _publish_in_review_directory(
            directory, raw=claim, owner_uid=owner_uid,
            expected_gid=expected_gid, now=observed_at,
        )
        _publish_envelope_bytes(
            directory, raw=envelope, owner_uid=owner_uid, expected_gid=expected_gid,
        )
    except (HMLSnapshotPublishError, HMLSnapshotTrustError, HMLSignedProducerError):
        raise HMLSignedProducerError("HML_SIGNED_PRODUCER_PUBLISH_FAILED") from None
    return HMLSignedProducerReceipt(
        generation=generation,
        envelope_bytes=len(envelope),
    )
