"""P2.2d: narrowly scoped, read-only Docker inspection for an OFFLINE host signer.

This adapter must run outside the ChatGPT-facing MCP process. Possession of a
Docker socket is high privilege EVEN if this Python module only issues GET.
Production use requires a separately reviewed, read-only engine proxy and a
pilot target allowlist. No socket is mounted or opened by importing this file.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Protocol

import httpx

_CONTAINER = re.compile(r"[a-z0-9][a-z0-9_.-]{1,100}\Z")
_HEX = re.compile(r"[a-f0-9]{64}\Z")
_IMAGE = re.compile(r"sha256:[a-f0-9]{64}\Z")
_MAX_BYTES = 262_144


class HostSourceError(Exception):
    """Safe, predetermined error codes; never expose inspect output."""
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class RuntimeTarget:
    environment: str
    service_id: str
    host_id: str
    compose_project: str
    container_name: str


@dataclass(frozen=True)
class RuntimeContainer:
    container_id: str
    image_id: str
    running: bool
    healthy: bool


class RuntimeInspector(Protocol):
    async def inspect(self, target: RuntimeTarget) -> RuntimeContainer: ...


def validate_target(target: RuntimeTarget) -> bool:
    if not isinstance(target, RuntimeTarget):
        return False
    return (
        type(target.environment) is str and target.environment in ("hml", "prod")
        and type(target.service_id) is str and bool(_CONTAINER.fullmatch(target.service_id))
        and type(target.host_id) is str and bool(_CONTAINER.fullmatch(target.host_id))
        and type(target.compose_project) is str and bool(_CONTAINER.fullmatch(target.compose_project))
        and type(target.container_name) is str and bool(_CONTAINER.fullmatch(target.container_name))
    )


class DockerReadOnlyInspect:
    """GET inspect for one fixed container. No POST, exec, volume or listing API.

    Injected transport is solely for isolated tests. In a future HML signer,
    a reviewed read-only socket proxy must be supplied outside the MCP service.
    Passing raw Docker socket to a container would grant host-equivalent power.
    """
    def __init__(self, *, transport: httpx.AsyncBaseTransport):
        if transport is None:
            raise HostSourceError("INSPECT_TRANSPORT_NOT_CONFIGURED")
        self._transport = transport

    async def inspect(self, target: RuntimeTarget) -> RuntimeContainer:
        if not validate_target(target):
            raise HostSourceError("INSPECT_TARGET_INVALID")
        # Names were validated against a strict allowlist pattern; never user URLs.
        url = f"http://docker.local/containers/{target.container_name}/json"
        try:
            async with httpx.AsyncClient(
                transport=self._transport, timeout=3.0, trust_env=False,
                follow_redirects=False,
            ) as client:
                async with client.stream("GET", url) as response:
                    if response.status_code != 200:
                        raise HostSourceError("INSPECT_UNAVAILABLE")
                    data = bytearray()
                    async for chunk in response.aiter_bytes():
                        data.extend(chunk)
                        if len(data) > _MAX_BYTES:
                            raise HostSourceError("INSPECT_TOO_LARGE")
            doc = json.loads(data)
        except HostSourceError:
            raise
        except (httpx.HTTPError, ValueError, UnicodeError):
            raise HostSourceError("INSPECT_UNAVAILABLE") from None
        if type(doc) is not dict:
            raise HostSourceError("INSPECT_INVALID")
        config, state = doc.get("Config"), doc.get("State")
        if type(config) is not dict or type(state) is not dict:
            raise HostSourceError("INSPECT_INVALID")
        labels = config.get("Labels")
        if type(labels) is not dict:
            raise HostSourceError("INSPECT_INVALID")
        # Prevent a different service within the same host from being attested.
        if (labels.get("com.docker.compose.service") != target.service_id
                or labels.get("com.docker.compose.project") != target.compose_project
                or doc.get("Name") != "/" + target.container_name):
            raise HostSourceError("INSPECT_TARGET_MISMATCH")
        container_id, image_id = doc.get("Id"), doc.get("Image")
        if (type(container_id) is not str or not _HEX.fullmatch(container_id)
                or type(image_id) is not str or not _IMAGE.fullmatch(image_id)):
            raise HostSourceError("INSPECT_IMAGE_INVALID")
        if type(state.get("Running")) is not bool:
            raise HostSourceError("INSPECT_STATE_INVALID")
        health = state.get("Health")
        healthy = type(health) is dict and health.get("Status") == "healthy"
        return RuntimeContainer(container_id, image_id, state["Running"], healthy)
