"""Architecture B non-root signing bridge: CI fixture-only source library.

The root Docker producer NEVER holds a signing key or speaks to the signer.
After a bounded FD-checked handoff, a distinct non-root bridge can rebuild a
canonical HML intent and ask the signer over a peer-authenticated Unix socket.
This module is NOT a daemon, CLI or enabled ATLAS MCP data source. Same-host
root can forge an observation or impersonate processes: do not claim SEC gates.
"""
from __future__ import annotations

import base64
import json
import os
import socket
import stat
import struct
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .atlas_hml_b_external_signing_intent import (
    HMLExternalSigningError, HMLSigningIntent, seal_externally_signed_intent,
)
from .atlas_hml_b_snapshot_envelope import (
    HMLSnapshotEnvelopeError, build_unsigned_envelope_document, signing_message,
)
from .atlas_hml_b_snapshot_trust import HMLSnapshotTrustError, HMLTrustKeyring
from .atlas_hml_b_local_signer import encode_local_sign_request
from .atlas_hml_snapshot_file_reader import (
    HMLSnapshotFileError, _read_record_from_directory,
)

_MAX_RESPONSE = 4096
_RESPONSE_FIELDS = frozenset({
    "schema", "status", "key_id", "generation", "signature_b64",
    "prepare_eligible", "can_execute",
})
_BLOCKS = (
    "HML_BRIDGE_SOURCE_ONLY",
    "ROOT_PRODUCER_OBSERVATION_UNTRUSTED",
    "SAME_HOST_ROOT_CAN_IMPERSONATE_PEERS",
    "REAL_BRIDGE_PROCESS_NOT_ATTESTED",
    "SEC_01_TO_10_PENDING", "PREPARE_DISABLED", "ACT_DISABLED",
)


class HMLNonrootBridgeError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class HMLNonrootBridgeResult:
    envelope: bytes
    generation: int
    key_id: str
    status: str = "blocked"
    signer_peer_verified_in_fixture: bool = True
    host_isolation_attested: bool = False
    signer_key_custody_independent: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False
    blocks: tuple[str, ...] = _BLOCKS


def _require_nonroot_identity() -> int:
    try:
        real, effective, saved = os.getresuid()
        rgid, egid, sgid = os.getresgid()
    except (OSError, AttributeError):
        raise HMLNonrootBridgeError("HML_BRIDGE_IDENTITY_UNVERIFIABLE") from None
    if (
        not all(type(uid) is int for uid in (real, effective, saved, rgid, egid, sgid))
        or real <= 0 or (real, effective, saved) != (real, real, real)
        or rgid <= 0 or (rgid, egid, sgid) != (rgid, rgid, rgid)
    ):
        raise HMLNonrootBridgeError("HML_BRIDGE_NOT_UNPRIVILEGED")
    return effective


def build_nonroot_signing_intent(
    *, directory: Path, owner_uid: int, expected_gid: int,
    generation: int, key_id: str, now: datetime,
) -> HMLSigningIntent:
    """Read one fixed HML claim by checked FD, no Docker/socket/secret access.

    Directory and expected ownership are caller-injected for disposable CI.
    The future operational wrapper must fix these constants in reviewed code.
    """
    _require_nonroot_identity()
    if (
        type(directory) is not type(Path("/")) or not directory.is_absolute()
        or type(generation) is not int or generation < 1
        or type(key_id) is not str
        or type(now) is not datetime or now.tzinfo is None
        or now.utcoffset() is None
    ):
        raise HMLNonrootBridgeError("HML_BRIDGE_INPUT_DENIED")
    try:
        record = _read_record_from_directory(
            directory, owner_uid=owner_uid, expected_gid=expected_gid, now=now,
        )
        produced = datetime.fromisoformat(
            record.diagnostic.observed_at_untrusted.replace("Z", "+00:00"),
        )
        document = build_unsigned_envelope_document(
            record.raw, generation=generation, produced_at=produced,
            key_id=key_id,
        )
        signed = signing_message(
            generation=generation,
            produced_at=str(document["produced_at"]),
            payload_sha256=str(document["payload_sha256"]),
            key_id=key_id,
            payload=record.raw,
        )
    except (HMLSnapshotFileError, HMLSnapshotEnvelopeError, ValueError, TypeError):
        raise HMLNonrootBridgeError("HML_BRIDGE_CLAIM_UNTRUSTED") from None
    return HMLSigningIntent(
        payload=record.raw, generation=generation, produced_at=produced,
        key_id=key_id, signing_bytes=signed,
    )


def _no_duplicate(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise HMLNonrootBridgeError("HML_BRIDGE_RESPONSE_INVALID")
        result[key] = value
    return result


def _no_constant(_: str) -> object:
    raise HMLNonrootBridgeError("HML_BRIDGE_RESPONSE_INVALID")


def _decode_response(raw: bytes, intent: HMLSigningIntent) -> bytes:
    if type(raw) is not bytes or not 1 <= len(raw) <= _MAX_RESPONSE or b"\x00" in raw:
        raise HMLNonrootBridgeError("HML_BRIDGE_RESPONSE_INVALID")
    try:
        document = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_no_duplicate,
            parse_constant=_no_constant,
        )
        if (
            type(document) is not dict or set(document) != _RESPONSE_FIELDS
            or document["schema"] != "atlas.hml.local-sign-response.v1"
            or document["status"] != "blocked"
            or document["prepare_eligible"] is not False
            or document["can_execute"] is not False
            or document["key_id"] != intent.key_id
            or type(document["generation"]) is not int
            or document["generation"] != intent.generation
            or type(document["signature_b64"]) is not str
        ):
            raise HMLNonrootBridgeError("HML_BRIDGE_RESPONSE_INVALID")
        sig = base64.b64decode(document["signature_b64"], validate=True)
        if len(sig) != 64:
            raise HMLNonrootBridgeError("HML_BRIDGE_RESPONSE_INVALID")
        return sig
    except HMLNonrootBridgeError:
        raise
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise HMLNonrootBridgeError("HML_BRIDGE_RESPONSE_INVALID") from None


def request_signature_via_nonroot_uds(
    intent: HMLSigningIntent, *, socket_path: Path,
    expected_socket_owner_uid: int, expected_socket_gid: int,
    expected_signer_uid: int, keyring: HMLTrustKeyring,
    now: datetime, disposable_same_uid_fixture: bool = False,
) -> HMLNonrootBridgeResult:
    """Authenticate peer UID in disposable UDS; never dispatch generic signing.

    Exact path is injected for CI only. Production needs a fixed reviewed path,
    real process/FD review and change-control. Never accepts root signer UID.
    """
    bridge_uid = _require_nonroot_identity()
    if (
        type(intent) is not HMLSigningIntent
        or type(socket_path) is not type(Path("/"))
        or not socket_path.is_absolute()
        or socket_path.name != "sign.sock"
        or type(expected_socket_owner_uid) is not int
        or expected_socket_owner_uid < 0
        or type(expected_socket_gid) is not int or expected_socket_gid < 0
        or type(expected_signer_uid) is not int or expected_signer_uid <= 0
        or type(disposable_same_uid_fixture) is not bool
        or (
            bridge_uid == expected_signer_uid
            and not disposable_same_uid_fixture
        )
        or type(keyring) is not HMLTrustKeyring
        or type(now) is not datetime or now.tzinfo is None
        or now.utcoffset() is None
    ):
        raise HMLNonrootBridgeError("HML_BRIDGE_POLICY_DENIED")
    connection = None
    try:
        before = os.stat(socket_path, follow_symlinks=False)
        if (
            not stat.S_ISSOCK(before.st_mode)
            or before.st_uid != expected_socket_owner_uid
            or before.st_gid != expected_socket_gid
            or stat.S_IMODE(before.st_mode) != 0o660
        ):
            raise HMLNonrootBridgeError("HML_BRIDGE_SOCKET_UNTRUSTED")
        connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        connection.settimeout(3.0)
        connection.connect(str(socket_path))
        packed = connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12)
        _, remote_uid, _ = struct.unpack("3i", packed)
        if remote_uid != expected_signer_uid:
            raise HMLNonrootBridgeError("HML_BRIDGE_SIGNER_PEER_DENIED")
        after = os.stat(socket_path, follow_symlinks=False)
        if (
            (before.st_dev, before.st_ino, before.st_mode, before.st_uid, before.st_gid)
            != (after.st_dev, after.st_ino, after.st_mode, after.st_uid, after.st_gid)
        ):
            raise HMLNonrootBridgeError("HML_BRIDGE_SOCKET_UNTRUSTED")
        encoded = encode_local_sign_request(intent)
        if len(encoded) > 8192:
            raise HMLNonrootBridgeError("HML_BRIDGE_INPUT_DENIED")
        connection.sendall(encoded)
        connection.shutdown(socket.SHUT_WR)
        chunks = bytearray()
        while len(chunks) <= _MAX_RESPONSE:
            data = connection.recv(min(1024, _MAX_RESPONSE + 1 - len(chunks)))
            if not data:
                break
            chunks.extend(data)
        signature = _decode_response(bytes(chunks), intent)
        verified = seal_externally_signed_intent(
            intent, signature=signature, keyring=keyring, now=now,
        )
    except HMLNonrootBridgeError:
        raise
    except (OSError, ValueError, TypeError, struct.error, HMLExternalSigningError,
            HMLSnapshotTrustError):
        raise HMLNonrootBridgeError("HML_BRIDGE_TRANSPORT_DENIED") from None
    finally:
        if connection is not None:
            connection.close()
    return HMLNonrootBridgeResult(
        envelope=verified.envelope, generation=intent.generation,
        key_id=intent.key_id,
    )
