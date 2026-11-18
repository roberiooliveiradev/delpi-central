"""Local Ed25519 signer candidate for ATLAS HML on srv-api (source-only).

Validates ATLAS signing intents only — never an unrestricted signing API.
Private key is loaded from a fixture path or injected for tests; never returned
to the producer. Same-host root can still read the key; this module does not
claim independent cryptographic custody. No systemd/MCP/CLI entrypoint.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import socket
import struct
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from .atlas_hml_b_external_signing_intent import (
    HMLExternalSigningError,
    HMLSigningIntent,
    review_signing_intent_for_external_signer,
)
from .atlas_hml_b_key_lifecycle import (
    HMLKeyLifecycleError,
    load_private_key_file,
)
from .atlas_hml_b_continuity_store import (
    HMLContinuityRecord,
    HMLContinuityStore,
    HMLContinuityStoreError,
)
from .atlas_hml_snapshot_candidate import review_untrusted_snapshot, SnapshotContractError
from .atlas_hml_b_snapshot_trust import key_id_for_public_key

_MAX_REQUEST = 8192
_MAX_INFLIGHT = 1
_MAX_HISTORY = 64
_SCHEMA_REQ = "atlas.hml.local-sign-request.v1"
_SCHEMA_RESP = "atlas.hml.local-sign-response.v1"
_BLOCKS = (
    "LOCAL_SIGNER_SAME_HOST_AS_ROOT_PRODUCER",
    "PRIVATE_KEY_NEVER_RETURNED_TO_CALLER",
    "NOT_AN_UNRESTRICTED_SIGNING_API",
    "SEC_01_TO_10_PENDING",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)


class HMLLocalSignerError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class HMLLocalSignResult:
    signature: bytes
    key_id: str
    generation: int
    status: str = "blocked"
    authenticity_independent: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False
    blocks: tuple[str, ...] = _BLOCKS


class HMLLocalSigner:
    """In-process local signer with generation anti-replay and peer allowlist."""

    def __init__(
        self, *,
        private_key: bytes,
        public_key: bytes,
        allowed_peer_uids: frozenset[int],
        checkpoint_store: HMLContinuityStore | None = None,
        disposable_genesis: bool = False,
    ) -> None:
        if type(private_key) is not bytes or len(private_key) != 32:
            raise HMLLocalSignerError("HML_LOCAL_SIGNER_KEY_INVALID")
        if type(public_key) is not bytes or len(public_key) != 32:
            raise HMLLocalSignerError("HML_LOCAL_SIGNER_KEY_INVALID")
        if type(allowed_peer_uids) is not frozenset or not allowed_peer_uids:
            raise HMLLocalSignerError("HML_LOCAL_SIGNER_PEER_POLICY_INVALID")
        if any(type(uid) is not int or uid <= 0 for uid in allowed_peer_uids):
            raise HMLLocalSignerError("HML_LOCAL_SIGNER_PEER_POLICY_INVALID")
        if (
            (checkpoint_store is not None and type(checkpoint_store) is not HMLContinuityStore)
            or type(disposable_genesis) is not bool
            or (disposable_genesis and checkpoint_store is None)
        ):
            raise HMLLocalSignerError("HML_LOCAL_SIGNER_CHECKPOINT_INPUT_INVALID")
        key_id = key_id_for_public_key(public_key)
        # Verify keypair consistency without exposing private material.
        derived = Ed25519PrivateKey.from_private_bytes(private_key).public_key()
        if derived.public_bytes_raw() != public_key:
            raise HMLLocalSignerError("HML_LOCAL_SIGNER_KEY_MISMATCH")
        self._private = private_key
        self._public = public_key
        self._key_id = key_id
        self._allowed_peers = allowed_peer_uids
        self._lock = threading.Lock()
        self._inflight = 0
        self._fault: str | None = None
        self._seen_digests: list[bytes] = []
        self._last_generation: int | None = None
        self._checkpoint_store = checkpoint_store
        if checkpoint_store is not None:
            try:
                last = checkpoint_store.load()
            except HMLContinuityStoreError:
                raise HMLLocalSignerError("HML_LOCAL_SIGNER_CHECKPOINT_UNTRUSTED") from None
            if last is None:
                # First boot is never indistinguishable from a lost/rolled-back
                # file in an operational context. Only disposable fixtures may
                # explicitly start at generation 1; operational genesis requires
                # a separate, authenticated owner bootstrap and change record.
                if not disposable_genesis:
                    raise HMLLocalSignerError("HML_LOCAL_SIGNER_BOOTSTRAP_REVIEW_REQUIRED")
            else:
                self._last_generation = last.generation

    @classmethod
    def from_key_file(
        cls, path: Path, *, public_key: bytes,
        owner_uid: int, expected_gid: int,
        allowed_peer_uids: frozenset[int],
        checkpoint_store: HMLContinuityStore | None = None,
        disposable_genesis: bool = False,
    ) -> "HMLLocalSigner":
        try:
            private = load_private_key_file(
                path, owner_uid=owner_uid, expected_gid=expected_gid,
            )
        except HMLKeyLifecycleError as exc:
            raise HMLLocalSignerError(exc.code) from None
        return cls(
            private_key=private, public_key=public_key,
            allowed_peer_uids=allowed_peer_uids,
            checkpoint_store=checkpoint_store,
            disposable_genesis=disposable_genesis,
        )

    @property
    def key_id(self) -> str:
        return self._key_id

    @property
    def halted(self) -> bool:
        return self._fault is not None

    def _halt(self, code: str) -> None:
        if self._fault is None:
            self._fault = code
        raise HMLLocalSignerError(self._fault)

    def sign_intent(
        self,
        intent: HMLSigningIntent, *,
        now: datetime,
        peer_uid: int,
        expected_generation: int,
    ) -> HMLLocalSignResult:
        """Sign only a reviewed ATLAS HML intent for an allowed peer UID."""
        if self._fault is not None:
            raise HMLLocalSignerError(self._fault)
        if type(peer_uid) is not int or peer_uid not in self._allowed_peers:
            raise HMLLocalSignerError("HML_LOCAL_SIGNER_PEER_DENIED")
        if type(intent) is not HMLSigningIntent:
            raise HMLLocalSignerError("HML_LOCAL_SIGNER_REQUEST_DENIED")
        if intent.key_id != self._key_id:
            raise HMLLocalSignerError("HML_LOCAL_SIGNER_KEY_ID_DENIED")
        try:
            reviewed = review_signing_intent_for_external_signer(
                intent, now=now, expected_generation=expected_generation,
            )
        except HMLExternalSigningError as exc:
            raise HMLLocalSignerError(exc.code) from None
        digest = hashlib.sha256(reviewed.signing_bytes).digest()
        with self._lock:
            if self._fault is not None:
                raise HMLLocalSignerError(self._fault)
            if self._inflight >= _MAX_INFLIGHT:
                raise HMLLocalSignerError("HML_LOCAL_SIGNER_BACKPRESSURE")
            if digest in self._seen_digests:
                self._halt("HML_LOCAL_SIGNER_REPLAY")
            if (
                self._last_generation is not None
                and reviewed.generation <= self._last_generation
            ):
                self._halt("HML_LOCAL_SIGNER_GENERATION_REGRESSION")
            if (
                self._last_generation is not None
                and reviewed.generation != self._last_generation + 1
            ):
                self._halt("HML_LOCAL_SIGNER_GENERATION_GAP")
            if self._last_generation is None and reviewed.generation != 1:
                # First sign in this process must start at generation 1 unless
                # an explicit warm-start API is added later.
                self._halt("HML_LOCAL_SIGNER_GENERATION_GAP")
            self._inflight += 1
        try:
            signature = Ed25519PrivateKey.from_private_bytes(self._private).sign(
                reviewed.signing_bytes,
            )
            if self._checkpoint_store is not None:
                # Reserve the issuance in an atomic + fsynced, FD-checked state
                # BEFORE disclosing the signature to any peer. A crash after
                # this reservation creates a gap that requires manual
                # reconciliation, never a silent counter reset.
                claim = review_untrusted_snapshot(reviewed.payload, now=now)
                self._checkpoint_store.commit(HMLContinuityRecord(
                    generation=reviewed.generation,
                    digest=hashlib.sha256(reviewed.signing_bytes).hexdigest(),
                    observed_at=reviewed.produced_at,
                    container_id=claim.container_id,
                    image_id=claim.image_id,
                    updated_at=now,
                ))
        except (HMLContinuityStoreError, SnapshotContractError):
            self._halt("HML_LOCAL_SIGNER_CHECKPOINT_UNTRUSTED")
        except (ValueError, TypeError):
            self._halt("HML_LOCAL_SIGNER_CRYPTO_FAILED")
        finally:
            with self._lock:
                self._inflight = max(0, self._inflight - 1)
        with self._lock:
            self._seen_digests.append(digest)
            if len(self._seen_digests) > _MAX_HISTORY:
                self._seen_digests.pop(0)
            self._last_generation = reviewed.generation
        return HMLLocalSignResult(
            signature=signature,
            key_id=self._key_id,
            generation=reviewed.generation,
        )

    def refuse_arbitrary_bytes(self, raw: bytes) -> None:
        """Explicit denial for non-intent payloads (generic signing API)."""
        raise HMLLocalSignerError("HML_LOCAL_SIGNER_NOT_GENERIC_API")


def _peer_uid(connection: socket.socket) -> int:
    try:
        packed = connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12)
        _, uid, _ = struct.unpack("3i", packed)
        if type(uid) is not int or uid <= 0:
            raise ValueError("uid")
        return uid
    except (OSError, AttributeError, struct.error, ValueError):
        raise HMLLocalSignerError("HML_LOCAL_SIGNER_PEER_UNVERIFIABLE") from None


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    out: dict[str, object] = {}
    for key, value in pairs:
        if key in out:
            raise HMLLocalSignerError("HML_LOCAL_SIGNER_REQUEST_DENIED")
        out[key] = value
    return out


def intent_from_local_request(raw: bytes) -> HMLSigningIntent:
    """Parse a bounded JSON sign request into an HMLSigningIntent."""
    if type(raw) is not bytes or not 1 <= len(raw) <= _MAX_REQUEST or b"\x00" in raw:
        raise HMLLocalSignerError("HML_LOCAL_SIGNER_REQUEST_DENIED")
    try:
        document = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique)
    except (ValueError, UnicodeError, TypeError):
        raise HMLLocalSignerError("HML_LOCAL_SIGNER_REQUEST_DENIED") from None
    fields = {
        "schema", "generation", "produced_at", "key_id",
        "payload_b64", "signing_bytes_b64",
    }
    if type(document) is not dict or set(document) != fields:
        raise HMLLocalSignerError("HML_LOCAL_SIGNER_REQUEST_DENIED")
    if document["schema"] != _SCHEMA_REQ:
        raise HMLLocalSignerError("HML_LOCAL_SIGNER_REQUEST_DENIED")
    try:
        payload = base64.b64decode(document["payload_b64"], validate=True)
        signing_bytes = base64.b64decode(document["signing_bytes_b64"], validate=True)
        produced = datetime.fromisoformat(
            str(document["produced_at"]).replace("Z", "+00:00"),
        )
        generation = document["generation"]
        key_id = document["key_id"]
    except (ValueError, TypeError, KeyError):
        raise HMLLocalSignerError("HML_LOCAL_SIGNER_REQUEST_DENIED") from None
    if (
        type(generation) is not int or type(key_id) is not str
        or produced.tzinfo is None
    ):
        raise HMLLocalSignerError("HML_LOCAL_SIGNER_REQUEST_DENIED")
    return HMLSigningIntent(
        payload=payload,
        generation=generation,
        produced_at=produced.astimezone(timezone.utc),
        key_id=key_id,
        signing_bytes=signing_bytes,
    )


def encode_local_sign_request(intent: HMLSigningIntent) -> bytes:
    document = {
        "schema": _SCHEMA_REQ,
        "generation": intent.generation,
        "produced_at": intent.produced_at.astimezone(timezone.utc)
        .isoformat().replace("+00:00", "Z"),
        "key_id": intent.key_id,
        "payload_b64": base64.b64encode(intent.payload).decode("ascii"),
        "signing_bytes_b64": base64.b64encode(intent.signing_bytes).decode("ascii"),
    }
    return json.dumps(
        document, separators=(",", ":"), sort_keys=True, ensure_ascii=True,
    ).encode("ascii")


def encode_local_sign_response(result: HMLLocalSignResult) -> bytes:
    document = {
        "schema": _SCHEMA_RESP,
        "status": "blocked",
        "key_id": result.key_id,
        "generation": result.generation,
        "signature_b64": base64.b64encode(result.signature).decode("ascii"),
        "prepare_eligible": False,
        "can_execute": False,
    }
    return json.dumps(
        document, separators=(",", ":"), sort_keys=True, ensure_ascii=True,
    ).encode("ascii")


def encode_local_sign_error(code: str) -> bytes:
    document = {
        "schema": _SCHEMA_RESP,
        "status": "blocked",
        "error": code if type(code) is str else "HML_LOCAL_SIGNER_INTERNAL",
        "prepare_eligible": False,
        "can_execute": False,
    }
    return json.dumps(
        document, separators=(",", ":"), sort_keys=True, ensure_ascii=True,
    ).encode("ascii")


def _serve_one_local_sign_request(
    *,
    listener: socket.socket,
    signer: HMLLocalSigner,
    expected_path: Path,
    now: datetime,
    expected_generation: int,
) -> HMLLocalSignResult | None:
    """Handle one AF_UNIX sign request on a disposable prebound listener."""
    if (
        type(listener) is not socket.socket
        or type(signer) is not HMLLocalSigner
        or type(expected_path) is not type(Path("/"))
        or not expected_path.is_absolute()
    ):
        raise HMLLocalSignerError("HML_LOCAL_SIGNER_LISTENER_INVALID")
    try:
        if (
            listener.family != socket.AF_UNIX
            or listener.getsockopt(socket.SOL_SOCKET, socket.SO_TYPE) != socket.SOCK_STREAM
            or listener.getsockopt(socket.SOL_SOCKET, socket.SO_ACCEPTCONN) != 1
            or listener.getsockname() != str(expected_path)
        ):
            raise HMLLocalSignerError("HML_LOCAL_SIGNER_LISTENER_INVALID")
    except (OSError, ValueError, TypeError):
        raise HMLLocalSignerError("HML_LOCAL_SIGNER_LISTENER_INVALID") from None
    connection = None
    try:
        listener.settimeout(3.0)
        connection, _ = listener.accept()
        connection.settimeout(3.0)
        peer = _peer_uid(connection)
        received = bytearray()
        while len(received) <= _MAX_REQUEST:
            chunk = connection.recv(min(512, _MAX_REQUEST + 1 - len(received)))
            if not chunk:
                break
            received.extend(chunk)
            if len(received) > _MAX_REQUEST:
                raise HMLLocalSignerError("HML_LOCAL_SIGNER_REQUEST_DENIED")
        intent = intent_from_local_request(bytes(received))
        result = signer.sign_intent(
            intent, now=now, peer_uid=peer,
            expected_generation=expected_generation,
        )
        connection.sendall(encode_local_sign_response(result))
        return result
    except HMLLocalSignerError as exc:
        if connection is not None:
            try:
                connection.sendall(encode_local_sign_error(exc.code))
            except OSError:
                pass
        raise
    finally:
        if connection is not None:
            try:
                connection.close()
            except OSError:
                pass
