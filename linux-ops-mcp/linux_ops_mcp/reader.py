"""Strictly bounded read projections of the canonical IT Portal Linux observation.

No shell, SSH, Docker, filesystem scanning, SQL or arbitrary URLs live here.
An authenticated end-user bearer is sent ONLY to the configured internal
IT Portal API, which enforces its own IT Portal permissions.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse
from uuid import UUID

import httpx

SYSTEMD_ALLOWLIST = frozenset((
    "docker.service", "containerd.service", "ssh.service", "sshd.service",
    "cron.service", "crond.service", "nginx.service",
    "zabbix-agent.service", "zabbix-agent2.service",
))
SECTION_KEYS = frozenset(("identity", "os", "memory", "volumes", "nics", "systemd", "docker"))
SECTION_STATES = frozenset(("ok", "partial", "unavailable", "failed"))
OBSERVATION_STATES = frozenset(("available", "partial", "stale", "unavailable"))
SYSTEMD_STATES = frozenset(("active", "inactive", "failed", "activating", "deactivating", "reloading", "unknown"))
MAX_UPSTREAM_BYTES = 256_000


class ReadError(Exception):
    """Safe machine-readable error code; never include upstream body or secrets."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class Settings:
    upstream_base_url: str
    server_id: str
    timeout_seconds: float = 5.0

    @classmethod
    def from_environment(cls) -> "Settings":
        base = (os.getenv("LINUX_OPS_IT_PORTAL_URL") or "").rstrip("/")
        server_id = (os.getenv("LINUX_OPS_SERVER_ID") or "").strip()
        try:
            UUID(server_id)
        except (ValueError, AttributeError):
            raise ReadError("server_id_not_configured") from None
        parsed = urlparse(base)
        # Only the canonical in-cluster host, or the loopback gateway, are
        # acceptable. Never let an MCP argument choose an outbound endpoint.
        if (
            parsed.scheme != "http"
            or parsed.hostname not in {"it-portal-api", "127.0.0.1", "localhost"}
            or parsed.username or parsed.password
            or parsed.path not in {"", "/"} or parsed.query or parsed.fragment
            or parsed.port not in {None, 80, 8000}
        ):
            raise ReadError("upstream_not_configured")
        return cls(upstream_base_url=base, server_id=server_id)


def _nonnegative_number(value: object) -> int | None:
    if type(value) is not int or value < 0:
        return None
    return value


def _safe_status(value: object, allowed: frozenset[str], fallback: str) -> str:
    return value if isinstance(value, str) and value in allowed else fallback


def _limit_string(value: object, *, max_len: int = 40) -> str | None:
    return value[:max_len] if isinstance(value, str) and 0 < len(value) <= max_len else None


def validate_observation(data: object) -> dict[str, Any] | None:
    """Return ONLY a valid Linux observation, or None when no snapshot exists."""
    if data is None:
        return None
    if not isinstance(data, dict):
        raise ReadError("malformed_observation")
    if data.get("source") != "linux_host_collector" or str(data.get("schema_version")) != "1":
        raise ReadError("unexpected_observation_source")
    if not isinstance(data.get("summary"), dict) or not isinstance(data.get("sections_status"), dict):
        raise ReadError("malformed_observation")
    return data


def _metadata(obs: dict[str, Any] | None) -> dict[str, Any]:
    if not obs:
        return {"source": "it-portal-api", "observation_status": "unavailable", "observed_at": None}
    return {
        "source": "it-portal-linux-collector",
        "observation_status": _safe_status(obs.get("presentation_status"), OBSERVATION_STATES, "unavailable"),
        "observed_at": _limit_string(obs.get("observed_at"), max_len=40),
    }


def host_health(data: object) -> dict[str, Any]:
    obs = validate_observation(data)
    result = _metadata(obs)
    if obs is None:
        return result
    summary = obs["summary"]
    mem = summary.get("memory") if isinstance(summary.get("memory"), dict) else {}
    swap = summary.get("swap") if isinstance(summary.get("swap"), dict) else {}
    raw_vols = summary.get("volumes")
    volumes = []
    if isinstance(raw_vols, list):
        for volume in raw_vols[:30]:
            if not isinstance(volume, dict) or volume.get("mount_point") != "/":
                continue
            volumes.append({
                "mount_point": "/",
                "size_bytes": _nonnegative_number(volume.get("size_bytes")),
                "used_bytes": _nonnegative_number(volume.get("used_bytes")),
                "available_bytes": _nonnegative_number(volume.get("available_bytes")),
            })
            break
    sections = obs.get("sections_status", {})
    result.update({
        "cpu_logical": _nonnegative_number(summary.get("cpu_logical")),
        "memory": {
            "total_bytes": _nonnegative_number(mem.get("total_bytes")),
            "available_bytes": _nonnegative_number(mem.get("available_bytes")),
        },
        "swap": {
            "total_bytes": _nonnegative_number(swap.get("total_bytes")),
            "free_bytes": _nonnegative_number(swap.get("free_bytes")),
        },
        "root_volume": volumes[0] if volumes else None,
        "sections": {
            key: _safe_status(sections.get(key), SECTION_STATES, "unavailable")
            for key in sorted(SECTION_KEYS)
        },
    })
    return result


def _allowed_services(obs: dict[str, Any] | None) -> list[dict[str, Any]]:
    if obs is None:
        return []
    raw = obs["summary"].get("systemd_services")
    if not isinstance(raw, list):
        return []
    found = set()
    results = []
    for item in raw[:100]:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if not isinstance(name, str) or name not in SYSTEMD_ALLOWLIST or name in found:
            continue
        found.add(name)
        results.append({
            "name": name,
            "active_state": _safe_status(item.get("active_state"), SYSTEMD_STATES, "unknown"),
        })
    return sorted(results, key=lambda row: row["name"])


def managed_services(data: object) -> dict[str, Any]:
    obs = validate_observation(data)
    result = _metadata(obs)
    docker = obs["summary"].get("docker_summary") if obs else None
    docker = docker if isinstance(docker, dict) else {}
    result.update({
        "systemd_services": _allowed_services(obs),
        "docker": {
            "available": docker.get("available") is True,
            "containers_running": _nonnegative_number(docker.get("containers_running")),
            "containers_total": _nonnegative_number(docker.get("containers_total")),
            "note": "aggregate_only_no_docker_socket",
        },
    })
    return result


def service_health(data: object, name: str) -> dict[str, Any]:
    # This is an enumeration of pre-approved systemd units, not a shell-like
    # free-form service identifier. Docker container-level health is not
    # exposed by the existing Linux collector contract.
    if name not in SYSTEMD_ALLOWLIST:
        raise ReadError("service_not_allowlisted")
    obs = validate_observation(data)
    result = _metadata(obs)
    match = next((item for item in _allowed_services(obs) if item["name"] == name), None)
    result.update({
        "service": name,
        "active_state": match["active_state"] if match else "unknown",
        "health": "active" if match and match["active_state"] == "active"
        else "unknown" if not match else "not_active",
    })
    return result


def deployment_revision(data: object) -> dict[str, Any]:
    # An IT Portal observation does not contain Git revision in its v1
    # contract. The MCP must never confuse GitHub HEAD with deployed SHA.
    obs = validate_observation(data)
    return {
        **_metadata(obs),
        "revision": None,
        "status": "not_available",
        "reason": "no_authoritative_deployed_revision_source",
    }


class ItPortalReader:
    """Access only the configured, typed, existing IT Portal read endpoint."""

    def __init__(self, settings: Settings | None = None, *, transport: httpx.AsyncBaseTransport | None = None):
        self.settings = settings or Settings.from_environment()
        self.transport = transport

    async def latest(self, authorization: str) -> dict[str, Any] | None:
        if not authorization.startswith("Bearer ") or len(authorization) < 12:
            raise ReadError("unauthorized")
        url = (
            f"{self.settings.upstream_base_url}/servers/"
            f"{self.settings.server_id}/observations/latest"
        )
        try:
            async with httpx.AsyncClient(
                timeout=self.settings.timeout_seconds,
                trust_env=False,
                follow_redirects=False,
                transport=self.transport,
            ) as client:
                response = await client.get(
                    url,
                    headers={"Authorization": authorization, "Accept": "application/json"},
                )
        except httpx.RequestError:
            raise ReadError("upstream_unavailable") from None
        if response.status_code in (401, 403):
            raise ReadError("upstream_authorization_denied")
        if response.status_code == 404:
            raise ReadError("server_not_found")
        if response.status_code != 200:
            raise ReadError("upstream_unavailable")
        if len(response.content) > MAX_UPSTREAM_BYTES:
            raise ReadError("upstream_response_too_large")
        try:
            payload = response.json()
        except ValueError:
            raise ReadError("malformed_upstream_response") from None
        if not isinstance(payload, dict) or "data" not in payload:
            raise ReadError("malformed_upstream_response")
        return validate_observation(payload["data"])
