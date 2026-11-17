"""ATLAS P2.2h.2ae-af: source-only, one-shot HML Docker inspect proxy.

No executable entrypoint, systemd unit, listener provisioning, Docker socket
opening, Keycloak client, MCP tool, HTTP route, DB access or deploy operation.
An independently reviewed supervisor must pre-bind the *fixed* UNIX socket,
own its root-controlled parent directory, and supply a separate Docker
read-only inspector. The proxy never binds or chmods a socket itself.

A valid local SO_PEERCRED UID proves only a kernel-observed connecting UID,
not the policy of the upstream Docker inspector, OS process attestation,
mTLS, backup, rollback, nonce consumption, or PREPARE/ACT permission.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import socket
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .deploy_host_source import RuntimeContainer, RuntimeTarget
from .atlas_hml_engine_boundary import HMLDockerInspectOnly, HML_TARGET
from .atlas_hml_uds_policy import (
    HMLUDSPolicyError, atlas_collector_identity, verify_socket_metadata,
)

_HML_PATH = Path("/run/atlas-hml-readonly/inspect.sock")
_DOCKER_RAW = (Path("/run/docker.sock"), Path("/var/run/docker.sock"))
# Single owner of the HML target across the upstream guard and UDS proxy.
_TARGET = HML_TARGET
_ALLOWED_REQUEST = "GET /containers/delpi-hml-public-hub/json HTTP/1.1"
_MAX_HEADERS = 2048
_MAX_JSON = 2048
_SHA = re.compile(r"sha256:[0-9a-f]{64}\Z")
_HEX = re.compile(r"[0-9a-f]{64}\Z")
_NO_BODY_HEADERS = frozenset({
    "authorization", "proxy-authorization", "content-length",
    "transfer-encoding", "expect", "upgrade",
})
_REASONS = {200: "OK", 400: "Bad Request", 403: "Forbidden",
            404: "Not Found", 405: "Method Not Allowed",
            502: "Bad Gateway"}


class HMLUnixProxyError(Exception):
    """Finite diagnostic codes, without socket paths or Docker data."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class BoundedRuntimeInspector(Protocol):
    async def inspect(self, target: RuntimeTarget) -> RuntimeContainer: ...


@dataclass(frozen=True, slots=True)
class SingleRequestProxyResult:
    """Single connection completed, not a certification of safe deployment."""

    status: str
    http_status: int
    request_accepted: bool
    raw_docker_socket_exposed: bool = False
    proxy_policy_independently_attested: bool = False
    host_identity_attested: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False


def _check_prebound_socket(
    listener: socket.socket, *, expected_path: Path, owner_uid: int,
    socket_gid: int | None = None,
) -> None:
    """Check the listening FD and shared UNIX pathname security policy."""
    if (
        type(listener) is not socket.socket
        or listener.family != socket.AF_UNIX
        or not isinstance(expected_path, Path)
        or not expected_path.is_absolute()
        or type(owner_uid) is not int or owner_uid < 0
    ):
        raise HMLUnixProxyError("HML_PROXY_LISTENER_UNTRUSTED")
    try:
        if (
            listener.getsockopt(socket.SOL_SOCKET, socket.SO_TYPE) != socket.SOCK_STREAM
            or listener.getsockopt(socket.SOL_SOCKET, socket.SO_ACCEPTCONN) != 1
            or listener.getsockname() != str(expected_path)
        ):
            raise HMLUnixProxyError("HML_PROXY_LISTENER_UNTRUSTED")
        verify_socket_metadata(
            path=expected_path, owner_uid=owner_uid, socket_gid=socket_gid,
        )
    except HMLUDSPolicyError as exc:
        raise HMLUnixProxyError(exc.code) from None
    except OSError:
        raise HMLUnixProxyError("HML_PROXY_LISTENER_UNTRUSTED") from None

def _peer_uid(client: socket.socket) -> int:
    try:
        # Linux-only, kernel-supplied {pid,uid,gid}; never trust HTTP headers.
        creds = client.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12)
        _, uid, _ = struct.unpack("3i", creds)
        return uid
    except (OSError, ValueError, struct.error):
        raise HMLUnixProxyError("HML_PEER_IDENTITY_UNAVAILABLE") from None


def _receive_get(client: socket.socket) -> int:
    """Receive one bounded HTTP request without body or pipelining."""
    raw = bytearray()
    try:
        while b"\r\n\r\n" not in raw and len(raw) <= _MAX_HEADERS:
            chunk = client.recv(min(512, _MAX_HEADERS + 1 - len(raw)))
            if not chunk:
                break
            raw.extend(chunk)
    except (OSError, TimeoutError):
        return 400
    if len(raw) > _MAX_HEADERS or b"\r\n\r\n" not in raw:
        return 400
    head, extra = bytes(raw).split(b"\r\n\r\n", 1)
    if extra or b"\x00" in head:
        return 400
    try:
        lines = head.decode("ascii").split("\r\n")
    except UnicodeDecodeError:
        return 400
    if lines[0] != _ALLOWED_REQUEST:
        if lines[0].startswith("GET "):
            return 404
        if lines[0].startswith(("POST ", "PUT ", "PATCH ", "DELETE ", "HEAD ", "OPTIONS ")):
            return 405
        return 400
    host_seen = 0
    for header in lines[1:]:
        if ":" not in header:
            return 400
        k, v = header.split(":", 1)
        name = k.lower()
        if (
            not k or k.strip() != k or not all(
                "a" <= c.lower() <= "z" or c.isdigit() or c == "-" for c in k
            )
            or name in _NO_BODY_HEADERS
            or "\r" in v or "\n" in v
        ):
            return 400
        if name == "host":
            host_seen += 1
            if v.strip() != "docker.local":
                return 400
    return 200 if host_seen == 1 else 400


def _response(client: socket.socket, code: int, payload: dict[str, object]) -> None:
    body = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode()
    if len(body) > _MAX_JSON:
        code, body = 502, b'{"error":"HML_UPSTREAM_INVALID"}'
    head = (
        f"HTTP/1.1 {code} {_REASONS[code]}\r\n"
        "Content-Type: application/json\r\n"
        "Cache-Control: no-store\r\n"
        "Connection: close\r\n"
        f"Content-Length: {len(body)}\r\n"
        "\r\n"
    ).encode()
    try:
        client.sendall(head + body)
    except (OSError, TimeoutError):
        pass


def _sanitized_runtime(runtime: RuntimeContainer) -> dict[str, object]:
    if (
        type(runtime) is not RuntimeContainer
        or type(runtime.container_id) is not str
        or _HEX.fullmatch(runtime.container_id) is None
        or type(runtime.image_id) is not str
        or _SHA.fullmatch(runtime.image_id) is None
        or type(runtime.running) is not bool
        or type(runtime.healthy) is not bool
    ):
        raise HMLUnixProxyError("HML_UPSTREAM_INVALID")
    return {
        "Id": runtime.container_id,
        "Image": runtime.image_id,
        "Name": "/" + _TARGET.container_name,
        "Config": {"Labels": {
            "com.docker.compose.service": _TARGET.service_id,
            "com.docker.compose.project": _TARGET.compose_project,
        }},
        "State": {
            "Running": runtime.running,
            "Health": {
                "Status": "healthy" if runtime.healthy else "unhealthy",
            },
        },
    }


def serve_one_prebound(
    *,
    listener: socket.socket,
    allowed_collector_uid: int,
    inspector: BoundedRuntimeInspector,
    expected_path: Path = _HML_PATH,
    owner_uid: int = 0,
    socket_gid: int | None = None,
) -> SingleRequestProxyResult:
    """Serve exactly one approved GET, then stop without closing supervisor FD.

    A separately reviewed supervisor must supply the pre-bound socket,
    unprivileged collector UID and a tightly constrained Docker inspector.
    expected_path and owner_uid are test-only DI; no CLI/request accepts
    them and real use MUST keep fixed HML path and root-owned socket.
    """
    if (
        type(allowed_collector_uid) is not int or allowed_collector_uid <= 0
        or not callable(getattr(inspector, "inspect", None))
    ):
        raise HMLUnixProxyError("HML_PROXY_NOT_CONFIGURED")
    if expected_path == _HML_PATH:
        try:
            collector_uid, _ = atlas_collector_identity()
        except HMLUDSPolicyError as exc:
            raise HMLUnixProxyError(exc.code) from None
        if allowed_collector_uid != collector_uid:
            raise HMLUnixProxyError("HML_PROXY_IDENTITY_UNAVAILABLE")
        # The production UDS must not bypass the Engine GET-only guard by
        # supplying an arbitrary inspect() implementation. Test fixtures with
        # disposable non-production paths retain dependency injection.
        if type(inspector) is not HMLDockerInspectOnly:
            raise HMLUnixProxyError("HML_ENGINE_BOUNDARY_REQUIRED")
    _check_prebound_socket(
        listener, expected_path=expected_path, owner_uid=owner_uid,
        socket_gid=socket_gid,
    )
    client = None
    try:
        listener.settimeout(3.0)
        client, _ = listener.accept()
        client.settimeout(3.0)
        try:
            uid = _peer_uid(client)
        except HMLUnixProxyError:
            _response(client, 403, {"error": "HML_PEER_UNTRUSTED"})
            return SingleRequestProxyResult("blocked", 403, False)
        if uid != allowed_collector_uid:
            _response(client, 403, {"error": "HML_PEER_UNTRUSTED"})
            return SingleRequestProxyResult("blocked", 403, False)

        code = _receive_get(client)
        if code != 200:
            _response(client, code, {"error": "HML_REQUEST_DENIED"})
            return SingleRequestProxyResult("blocked", code, False)
        try:
            container = asyncio.run(asyncio.wait_for(inspector.inspect(_TARGET), timeout=4.0))
            payload = _sanitized_runtime(container)
        except Exception:
            _response(client, 502, {"error": "HML_INSPECT_UNAVAILABLE"})
            return SingleRequestProxyResult("blocked", 502, False)
        _response(client, 200, payload)
        return SingleRequestProxyResult("blocked", 200, True)
    except (OSError, TimeoutError):
        raise HMLUnixProxyError("HML_PROXY_UNAVAILABLE") from None
    finally:
        if client is not None:
            # Fail-closed rejected requests can still have unread input.
            # A bounded local drain after SHUT_WR avoids Linux resetting the
            # connection before the sanitized refusal can reach the client.
            # This never forwards data upstream and has a strict 16 KiB cap.
            try:
                client.shutdown(socket.SHUT_WR)
                client.settimeout(0.05)
                for _ in range(4):
                    try:
                        if not client.recv(4096):
                            break
                    except (OSError, TimeoutError):
                        break
            except OSError:
                pass
            finally:
                try:
                    client.close()
                except OSError:
                    pass
