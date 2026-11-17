"""Architecture B: non-privileged, snapshot-only HML presenter CANDIDATE.

This module implements one request on a supervisor-PREBOUND AF_UNIX listener.
It does NOT bind a socket, start a process/service, open the Docker Engine,
access a network API, authenticate a producer, authorize PREPARE/ACT, or wire
itself into MCP. It is for an independently reviewed, disposable design test.

The presenter's readable JSON remains an UNTRUSTED claim with status=blocked.
A successfully parsed root-owned snapshot is never origin attestation. An
operational unit must separately prove it has no inherited Docker descriptors,
aliases, socket permissions or network access. No executable entrypoint.
"""
from __future__ import annotations

import json
import os
import re
import socket
import stat
import struct
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .atlas_hml_snapshot_candidate import SnapshotDiagnostic
from .atlas_hml_snapshot_file_reader import (
    HMLSnapshotFileError,
    read_fixed_hml_snapshot,
)
from .atlas_hml_uds_policy import (
    HMLUDSPolicyError,
    atlas_collector_identity,
    verify_socket_metadata,
)

_FIXED_SOCKET = Path("/run/atlas-hml-readonly/inspect.sock")
_GET = b"GET /v1/hml/public-hub/snapshot HTTP/1.1\r\n"
_HOST = b"Host: atlas-hml.local\r\n"
_REQUESTS = frozenset((
    _GET + _HOST + b"\r\n",
    _GET + _HOST + b"Connection: close\r\n\r\n",
))
_MAX_REQUEST = 512
_MAX_BODY = 1024
_HEX = re.compile(r"[0-9a-f]{64}\Z")
_SHA = re.compile(r"sha256:[0-9a-f]{64}\Z")
_REASON = {
    200: "OK", 400: "Bad Request", 403: "Forbidden",
    404: "Not Found", 405: "Method Not Allowed",
    502: "Bad Gateway", 503: "Service Unavailable",
}


class HMLSnapshotPresenterError(Exception):
    """Only predefined public error codes; never reflect host paths/data."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class HMLSnapshotPresentationResult:
    status: str
    http_status: int
    request_accepted: bool
    snapshot_read: bool
    docker_access_attested: bool = False
    snapshot_origin_attested: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False


def _check_listener(
    listener: socket.socket, *, expected_path: Path,
    owner_uid: int, socket_gid: int | None,
) -> None:
    if (
        type(listener) is not socket.socket
        or listener.family != socket.AF_UNIX
        or type(expected_path) is not Path
        or not expected_path.is_absolute()
        or type(owner_uid) is not int or owner_uid < 0
        or (socket_gid is not None and (type(socket_gid) is not int or socket_gid < 0))
    ):
        raise HMLSnapshotPresenterError("HML_PRESENTER_LISTENER_UNTRUSTED")
    try:
        if (
            listener.getsockopt(socket.SOL_SOCKET, socket.SO_TYPE) != socket.SOCK_STREAM
            or listener.getsockopt(socket.SOL_SOCKET, socket.SO_ACCEPTCONN) != 1
            or listener.getsockname() != str(expected_path)
        ):
            raise HMLSnapshotPresenterError("HML_PRESENTER_LISTENER_UNTRUSTED")
        verify_socket_metadata(
            path=expected_path, owner_uid=owner_uid, socket_gid=socket_gid,
        )
    except HMLUDSPolicyError:
        raise HMLSnapshotPresenterError("HML_PRESENTER_LISTENER_UNTRUSTED") from None
    except (OSError, ValueError, TypeError):
        raise HMLSnapshotPresenterError("HML_PRESENTER_LISTENER_UNTRUSTED") from None


def _peer_uid(connection: socket.socket) -> int:
    try:
        packed = connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12)
        _, uid, _ = struct.unpack("3i", packed)
        return uid
    except (OSError, AttributeError, struct.error, ValueError):
        raise HMLSnapshotPresenterError("HML_PRESENTER_PEER_UNVERIFIABLE") from None


def _validate_request(connection: socket.socket) -> int:
    received = bytearray()
    try:
        while b"\r\n\r\n" not in received and len(received) <= _MAX_REQUEST:
            chunk = connection.recv(min(256, _MAX_REQUEST + 1 - len(received)))
            if not chunk:
                break
            received.extend(chunk)
    except (OSError, TimeoutError):
        return 400
    if len(received) > _MAX_REQUEST or b"\r\n\r\n" not in received:
        return 400
    raw = bytes(received)
    if raw in _REQUESTS:
        return 200
    if raw.startswith(_GET):
        return 400
    if raw.startswith(b"GET "):
        return 404
    if raw.startswith((b"POST ", b"PUT ", b"PATCH ", b"DELETE ", b"HEAD ", b"OPTIONS ")):
        return 405
    return 400


def _http_json(connection: socket.socket, code: int, payload: dict[str, object]) -> None:
    raw = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("ascii")
    if len(raw) > _MAX_BODY:
        code, raw = 502, b'{"error":"HML_PRESENTER_OUTPUT_UNAVAILABLE"}'
    header = (
        f"HTTP/1.1 {code} {_REASON[code]}\r\n"
        "Content-Type: application/json\r\n"
        "Cache-Control: no-store\r\n"
        "Connection: close\r\n"
        "X-Content-Type-Options: nosniff\r\n"
        f"Content-Length: {len(raw)}\r\n"
        "\r\n"
    ).encode("ascii")
    try:
        connection.sendall(header + raw)
    except (OSError, TimeoutError):
        pass


def _presentation(snapshot: SnapshotDiagnostic) -> dict[str, object]:
    # Harden even against an injected/monkeypatched reader. This is still
    # not a statement that the process or upstream snapshot is trusted.
    if (
        type(snapshot) is not SnapshotDiagnostic
        or snapshot.status != "blocked"
        or snapshot.environment != "hml"
        or snapshot.service_id != "public-hub"
        or type(snapshot.running) is not bool
        or type(snapshot.healthy) is not bool
        or type(snapshot.container_id) is not str
        or not _HEX.fullmatch(snapshot.container_id)
        or type(snapshot.image_id) is not str
        or not _SHA.fullmatch(snapshot.image_id)
        or type(snapshot.observed_at_untrusted) is not str
        or not 1 <= len(snapshot.observed_at_untrusted) <= 40
        or not snapshot.observed_at_untrusted.isascii()
        or type(snapshot.blocks) is not tuple
        or not {"PREPARE_DISABLED", "ACT_DISABLED", "SNAPSHOT_ORIGIN_NOT_INDEPENDENTLY_ATTESTED"}.issubset(snapshot.blocks)
        or any(type(value) is not bool or value for value in (
            snapshot.snapshot_origin_attested,
            snapshot.docker_access_boundary_attested,
            snapshot.proxy_policy_independently_attested,
            snapshot.host_identity_attested,
            snapshot.checkout_integrity_attested,
            snapshot.challenge_consumed,
            snapshot.prepare_eligible,
            snapshot.can_execute,
        ))
    ):
        raise HMLSnapshotPresenterError("HML_PRESENTER_SNAPSHOT_UNTRUSTED")
    return {
        "schema": "atlas.hml.presentation.v1",
        "environment": "hml",
        "service_id": "public-hub",
        "status": "blocked",
        "running_untrusted": snapshot.running,
        "healthy_untrusted": snapshot.healthy,
        "observed_at_untrusted": snapshot.observed_at_untrusted,
        "snapshot_origin_attested": False,
        "docker_access_boundary_attested": False,
        "prepare_eligible": False,
        "can_execute": False,
    }


def _serve_one_prebound_snapshot_review(
    *, listener: socket.socket,
    reader: Callable[..., SnapshotDiagnostic] = read_fixed_hml_snapshot,
    allowed_uid: int,
    expected_path: Path = _FIXED_SOCKET,
    owner_uid: int = 0,
    socket_gid: int | None = None,
) -> HMLSnapshotPresentationResult:
    """Handle one peer-authenticated request on a disposable prebound listener.

    Override injection is for isolated test fixtures ONLY. This function has
    no executable entrypoint and is not imported by MCP or a service.
    The real fixed-path invocation enforces the fixed snapshot reader,
    uid/gid policy, and root ownership, but is STILL not host attestation.
    """
    if (
        type(allowed_uid) is not int or allowed_uid <= 0
        or not callable(reader)
    ):
        raise HMLSnapshotPresenterError("HML_PRESENTER_NOT_CONFIGURED")
    if expected_path == _FIXED_SOCKET:
        try:
            expected_uid, _ = atlas_collector_identity()
        except HMLUDSPolicyError:
            raise HMLSnapshotPresenterError("HML_PRESENTER_IDENTITY_UNVERIFIABLE") from None
        if (
            owner_uid != 0 or socket_gid is not None
            or allowed_uid != expected_uid
            or reader is not read_fixed_hml_snapshot
        ):
            raise HMLSnapshotPresenterError("HML_PRESENTER_POLICY_UNVERIFIABLE")

    _check_listener(
        listener, expected_path=expected_path,
        owner_uid=owner_uid, socket_gid=socket_gid,
    )
    connection = None
    try:
        listener.settimeout(3.0)
        connection, _ = listener.accept()
        connection.settimeout(3.0)
        try:
            uid = _peer_uid(connection)
        except HMLSnapshotPresenterError:
            _http_json(connection, 403, {"error": "HML_PRESENTER_PEER_DENIED"})
            return HMLSnapshotPresentationResult("blocked", 403, False, False)
        if uid != allowed_uid:
            _http_json(connection, 403, {"error": "HML_PRESENTER_PEER_DENIED"})
            return HMLSnapshotPresentationResult("blocked", 403, False, False)
        code = _validate_request(connection)
        if code != 200:
            _http_json(connection, code, {"error": "HML_PRESENTER_REQUEST_DENIED"})
            return HMLSnapshotPresentationResult("blocked", code, False, False)

        try:
            observed = reader(now=datetime.now(timezone.utc))
            result = _presentation(observed)
        except (HMLSnapshotFileError, HMLSnapshotPresenterError):
            _http_json(connection, 503, {"error": "HML_PRESENTER_SNAPSHOT_UNAVAILABLE"})
            return HMLSnapshotPresentationResult("blocked", 503, True, False)
        except Exception:
            _http_json(connection, 503, {"error": "HML_PRESENTER_SNAPSHOT_UNAVAILABLE"})
            return HMLSnapshotPresentationResult("blocked", 503, True, False)
        _http_json(connection, 200, result)
        return HMLSnapshotPresentationResult("blocked", 200, True, True)
    except (OSError, TimeoutError):
        raise HMLSnapshotPresenterError("HML_PRESENTER_IO_UNAVAILABLE") from None
    finally:
        if connection is not None:
            # Avoid close() resetting short rejected responses when the peer
            # sent more bytes than permitted. All draining is bounded.
            try:
                connection.shutdown(socket.SHUT_WR)
                connection.settimeout(0.05)
                for _ in range(4):
                    try:
                        if not connection.recv(4096):
                            break
                    except (OSError, TimeoutError):
                        break
            except OSError:
                pass
            finally:
                connection.close()
