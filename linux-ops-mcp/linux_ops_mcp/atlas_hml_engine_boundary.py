"""ATLAS HML upstream Docker GET boundary, source-only and fail-closed.

No Docker socket, supervisor, listener, network client, daemon, HTTP/MCP
endpoint or privileged process is instantiated here. The upstream transport
is injected by an independently reviewed host process in a future phase.
This guard limits calls made *through it*; it does not sandbox malicious code
that can access Docker directly or attest its own supervisor.
"""
from __future__ import annotations

import httpx

from .deploy_host_source import (
    DockerReadOnlyInspect,
    HostSourceError,
    RuntimeContainer,
    RuntimeTarget,
)

HML_TARGET = RuntimeTarget(
    environment="hml",
    service_id="public-hub",
    host_id="srv-api-pilot",
    compose_project="delpi-hml",
    container_name="delpi-hml-public-hub",
)
_HML_URL = "http://docker.local/containers/delpi-hml-public-hub/json"
_ALLOWED_HEADERS = frozenset({
    b"host", b"accept", b"accept-encoding", b"connection", b"user-agent",
})
_MAX_REQUEST_HEADER_BYTES = 2048
_MAX_UPSTREAM_BYTES = 262_144


def _approved_request(request: httpx.Request) -> bool:
    """Exact HTTP method, URL, framing and headers, with no request body."""
    if (
        type(request) is not httpx.Request
        or request.method != "GET"
        or str(request.url) != _HML_URL
    ):
        return False
    try:
        headers = request.headers.raw
        if (
            not 1 <= len(headers) <= 8
            or sum(len(k) + len(v) for k, v in headers) > _MAX_REQUEST_HEADER_BYTES
        ):
            return False
        host_count = 0
        for key, value in headers:
            name = key.lower()
            if (
                name not in _ALLOWED_HEADERS
                or any(c < 32 or c == 127 for c in value)
                or len(value) > 256
            ):
                return False
            if name == b"host":
                host_count += 1
                if value != b"docker.local":
                    return False
        if host_count != 1:
            return False
        return request.content == b""
    except (ValueError, httpx.RequestNotRead, TypeError):
        return False


class HMLDockerGETTransport(httpx.AsyncBaseTransport):
    """No rewrite/redirect: exactly one Docker inspect GET may pass through."""

    __slots__ = ("_upstream",)

    def __init__(self, upstream: httpx.AsyncBaseTransport):
        if not isinstance(upstream, httpx.AsyncBaseTransport):
            raise HostSourceError("HML_ENGINE_TRANSPORT_UNAVAILABLE")
        self._upstream = upstream

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        if not _approved_request(request):
            raise HostSourceError("HML_ENGINE_REQUEST_DENIED")
        response = await self._upstream.handle_async_request(request)
        try:
            if (
                response.status_code != 200
                or response.headers.get("content-encoding", "identity").lower()
                not in ("", "identity")
            ):
                raise HostSourceError("HML_ENGINE_RESPONSE_DENIED")
            declared_size = response.headers.get("content-length")
            if declared_size is not None:
                if not declared_size.isdecimal() or int(declared_size) > _MAX_UPSTREAM_BYTES:
                    raise HostSourceError("HML_ENGINE_RESPONSE_DENIED")
            return response
        except (HostSourceError, ValueError):
            await response.aclose()
            raise HostSourceError("HML_ENGINE_RESPONSE_DENIED") from None

    async def aclose(self) -> None:
        await self._upstream.aclose()


class HMLDockerInspectOnly:
    """Typed source for the HML proxy; never accepts a production target.

    This wrapper is necessary, not sufficient, for safe access to the Engine.
    A privileged host process could bypass it: independent OS confinement,
    upstream policy, review, and HML authorization are mandatory.
    """

    __slots__ = ("_reader",)

    def __init__(self, *, upstream: httpx.AsyncBaseTransport):
        self._reader = DockerReadOnlyInspect(
            transport=HMLDockerGETTransport(upstream),
        )

    async def inspect(self, target: RuntimeTarget) -> RuntimeContainer:
        if type(target) is not RuntimeTarget or target != HML_TARGET:
            raise HostSourceError("HML_ENGINE_TARGET_DENIED")
        return await self._reader.inspect(HML_TARGET)
