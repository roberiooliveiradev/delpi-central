"""Strictly bounded read projections of the canonical IT Portal observations.

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
OBSERVATION_SOURCES = frozenset(("linux_host_collector", "windows_host_collector"))
WINDOWS_HOST_SERVICE_STATES = frozenset((
    "running", "stopped", "start_pending", "stop_pending",
    "continue_pending", "pause_pending", "paused", "unknown",
))


class ReadError(Exception):
    """Safe machine-readable error code; never include upstream body or secrets."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _env_float(name: str, default: float, *, minimum: float, maximum: float) -> float:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    return max(minimum, min(maximum, value))


def _env_int(name: str, default: int, *, minimum: int, maximum: int) -> int:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(minimum, min(maximum, value))


@dataclass(frozen=True)
class Settings:
    upstream_base_url: str
    server_id: str | None = None
    timeout_seconds: float = 5.0
    stale_after_hours: float = 36.0
    infra_concurrency: int = 8
    infra_max_servers: int = 500
    memory_attention_pct: float = 85.0
    memory_critical_pct: float = 95.0
    disk_attention_pct: float = 85.0
    disk_critical_pct: float = 95.0
    cpu_attention_pct: float = 85.0
    cpu_critical_pct: float = 95.0

    @classmethod
    def from_environment(cls, *, require_legacy_server_id: bool = False) -> "Settings":
        base = (os.getenv("LINUX_OPS_IT_PORTAL_URL") or "").rstrip("/")
        server_raw = (os.getenv("LINUX_OPS_SERVER_ID") or "").strip()
        server_id: str | None = None
        if server_raw:
            try:
                server_id = str(UUID(server_raw))
            except (ValueError, AttributeError):
                raise ReadError("server_id_not_configured") from None
        elif require_legacy_server_id:
            raise ReadError("server_id_not_configured")
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
        return cls(
            upstream_base_url=base,
            server_id=server_id,
            stale_after_hours=_env_float(
                "LINUX_OPS_STALE_AFTER_HOURS", 36.0, minimum=1.0, maximum=24 * 30,
            ),
            infra_concurrency=_env_int(
                "LINUX_OPS_INFRA_CONCURRENCY", 8, minimum=1, maximum=20,
            ),
            infra_max_servers=_env_int(
                "LINUX_OPS_INFRA_MAX_SERVERS", 500, minimum=1, maximum=2000,
            ),
            memory_attention_pct=_env_float(
                "LINUX_OPS_MEMORY_ATTENTION_PCT", 85.0, minimum=1.0, maximum=100.0,
            ),
            memory_critical_pct=_env_float(
                "LINUX_OPS_MEMORY_CRITICAL_PCT", 95.0, minimum=1.0, maximum=100.0,
            ),
            disk_attention_pct=_env_float(
                "LINUX_OPS_DISK_ATTENTION_PCT", 85.0, minimum=1.0, maximum=100.0,
            ),
            disk_critical_pct=_env_float(
                "LINUX_OPS_DISK_CRITICAL_PCT", 95.0, minimum=1.0, maximum=100.0,
            ),
            cpu_attention_pct=_env_float(
                "LINUX_OPS_CPU_ATTENTION_PCT", 85.0, minimum=1.0, maximum=100.0,
            ),
            cpu_critical_pct=_env_float(
                "LINUX_OPS_CPU_CRITICAL_PCT", 95.0, minimum=1.0, maximum=100.0,
            ),
        )


def require_uuid(value: object, *, code: str = "invalid_server_id") -> str:
    try:
        return str(UUID(str(value).strip()))
    except (ValueError, AttributeError, TypeError):
        raise ReadError(code) from None


def _nonnegative_number(value: object) -> int | None:
    if type(value) is not int or value < 0:
        return None
    return value


def _safe_status(value: object, allowed: frozenset[str], fallback: str) -> str:
    return value if isinstance(value, str) and value in allowed else fallback


def _limit_string(value: object, *, max_len: int = 40) -> str | None:
    return value[:max_len] if isinstance(value, str) and 0 < len(value) <= max_len else None


def validate_observation(data: object) -> dict[str, Any] | None:
    """Return ONLY a valid Linux observation, or None when no snapshot exists.

    Legacy READ tools remain Linux-only for backward compatibility.
    """
    if data is None:
        return None
    if not isinstance(data, dict):
        raise ReadError("malformed_observation")
    if data.get("source") != "linux_host_collector" or str(data.get("schema_version")) != "1":
        raise ReadError("unexpected_observation_source")
    if not isinstance(data.get("summary"), dict) or not isinstance(data.get("sections_status"), dict):
        raise ReadError("malformed_observation")
    return data


def validate_any_observation(data: object) -> dict[str, Any] | None:
    """Accept Linux or Windows collector observations for multiserver tools."""
    if data is None:
        return None
    if not isinstance(data, dict):
        raise ReadError("malformed_observation")
    if data.get("source") not in OBSERVATION_SOURCES or str(data.get("schema_version")) != "1":
        raise ReadError("unexpected_observation_source")
    if not isinstance(data.get("summary"), dict) or not isinstance(data.get("sections_status"), dict):
        raise ReadError("malformed_observation")
    return data


def _metadata(obs: dict[str, Any] | None) -> dict[str, Any]:
    if not obs:
        return {"source": "it-portal-api", "observation_status": "unavailable", "observed_at": None}
    source = (
        "it-portal-linux-collector" if obs.get("source") == "linux_host_collector"
        else "it-portal-windows-collector" if obs.get("source") == "windows_host_collector"
        else "it-portal-api"
    )
    return {
        "source": source,
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


def project_server_inventory_row(raw: object) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    server_id = raw.get("id")
    try:
        normalized_id = str(UUID(str(server_id)))
    except (ValueError, AttributeError, TypeError):
        return None
    hostname = _limit_string(raw.get("hostname"), max_len=253)
    name = _limit_string(raw.get("name"), max_len=120)
    if not hostname or not name:
        return None
    return {
        "id": normalized_id,
        "name": name,
        "hostname": hostname,
        "operating_system": _limit_string(raw.get("operating_system"), max_len=120),
        "unit_code": _limit_string(raw.get("unit_code"), max_len=40),
        "environment": _limit_string(raw.get("environment"), max_len=40),
        "criticality": _limit_string(raw.get("criticality"), max_len=40),
        "administrative_status": _limit_string(raw.get("administrative_status"), max_len=40),
        "archived": raw.get("archived") is True,
    }


# IT Portal host-service contract (domain/host_services.py + V006):
# name/service_key <= 200, display_name <= 240. Reject oversize; never truncate.
_WINDOWS_HOST_SERVICE_NAME_MAX = 200
_WINDOWS_HOST_SERVICE_KEY_MAX = 200
_WINDOWS_HOST_SERVICE_DISPLAY_NAME_MAX = 240


def project_windows_host_service(raw: object) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    name = _limit_string(raw.get("name"), max_len=_WINDOWS_HOST_SERVICE_NAME_MAX)
    service_key = _limit_string(raw.get("service_key"), max_len=_WINDOWS_HOST_SERVICE_KEY_MAX)
    if not name or not service_key:
        return None
    state = _limit_string(raw.get("state"), max_len=40) or "unknown"
    criticality = raw.get("criticality")
    if criticality not in {"normal", "high", "critical"}:
        criticality = "normal"
    return {
        "service_key": service_key,
        "name": name,
        "display_name": _limit_string(
            raw.get("display_name"), max_len=_WINDOWS_HOST_SERVICE_DISPLAY_NAME_MAX,
        ),
        "state": state.lower() if isinstance(state, str) else "unknown",
        "start_mode": _limit_string(raw.get("start_mode"), max_len=40),
        "can_stop": raw.get("can_stop") is True,
        "control_allowed": raw.get("control_allowed") is True,
        "is_favorite": raw.get("is_favorite") is True,
        "criticality": criticality,
        "is_present": raw.get("is_present") is not False,
        "observed_at": _limit_string(raw.get("observed_at"), max_len=40),
    }


class ItPortalReader:
    """Access only the configured, typed, existing IT Portal read endpoints."""

    def __init__(self, settings: Settings | None = None, *, transport: httpx.AsyncBaseTransport | None = None):
        self.settings = settings or Settings.from_environment()
        self.transport = transport

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            timeout=self.settings.timeout_seconds,
            trust_env=False,
            follow_redirects=False,
            transport=self.transport,
        )

    async def _get_json(
        self,
        authorization: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        allow_null_data: bool = False,
    ) -> Any:
        if not authorization.startswith("Bearer ") or len(authorization) < 12:
            raise ReadError("unauthorized")
        if not path.startswith("/"):
            raise ReadError("upstream_not_configured")
        url = f"{self.settings.upstream_base_url}{path}"
        try:
            async with self._client() as client:
                response = await client.get(
                    url,
                    params=params,
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
        data = payload["data"]
        if data is None and allow_null_data:
            return None
        return data

    async def latest(self, authorization: str) -> dict[str, Any] | None:
        if not self.settings.server_id:
            raise ReadError("server_id_not_configured")
        return await self.latest_for(authorization, self.settings.server_id, linux_only=True)

    async def latest_for(
        self,
        authorization: str,
        server_id: str,
        *,
        linux_only: bool = False,
    ) -> dict[str, Any] | None:
        normalized = require_uuid(server_id)
        data = await self._get_json(
            authorization,
            f"/servers/{normalized}/observations/latest",
            allow_null_data=True,
        )
        observation = (
            validate_observation(data) if linux_only else validate_any_observation(data)
        )
        # The upstream must return the same registered server ID that we
        # requested. Never leak observations for a different asset.
        if observation is not None and str(observation.get("server_id")) != normalized:
            raise ReadError("unexpected_observation_server")
        return observation

    async def get_server(self, authorization: str, server_id: str) -> dict[str, Any]:
        normalized = require_uuid(server_id)
        data = await self._get_json(authorization, f"/servers/{normalized}")
        projected = project_server_inventory_row(data)
        if projected is None:
            raise ReadError("malformed_upstream_response")
        return projected

    async def list_servers_page(
        self,
        authorization: str,
        *,
        q: str | None = None,
        unit_code: str | None = None,
        environment: str | None = None,
        criticality: str | None = None,
        archived: str = "active",
        page: int = 1,
        page_size: int = 25,
    ) -> dict[str, Any]:
        if archived not in {"active", "archived", "all"}:
            raise ReadError("invalid_archived_filter")
        page = max(1, min(int(page), 10_000))
        page_size = max(1, min(int(page_size), 100))
        params: dict[str, Any] = {
            "archived": archived,
            "page": page,
            "page_size": page_size,
            "sort": "name",
            "direction": "asc",
        }
        if q:
            params["q"] = q[:120]
        if unit_code:
            params["unit_code"] = unit_code[:40]
        if environment:
            params["environment"] = environment[:40]
        if criticality:
            params["criticality"] = criticality[:40]
        data = await self._get_json(authorization, "/servers", params=params)
        if not isinstance(data, dict):
            raise ReadError("malformed_upstream_response")
        raw_items = data.get("items")
        if not isinstance(raw_items, list):
            raise ReadError("malformed_upstream_response")
        items = [row for row in (project_server_inventory_row(item) for item in raw_items) if row]
        total = data.get("total")
        if type(total) is not int or total < 0:
            total = len(items)
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def list_host_services(
        self,
        authorization: str,
        server_id: str,
        *,
        q: str | None = None,
        state: str | None = None,
        present: str = "yes",
        favorites_only: bool = False,
        page: int = 1,
        page_size: int = 25,
    ) -> dict[str, Any]:
        normalized = require_uuid(server_id)
        if present not in {"yes", "no", "all"}:
            raise ReadError("invalid_present_filter")
        page = max(1, min(int(page), 10_000))
        page_size = max(1, min(int(page_size), 100))
        params: dict[str, Any] = {
            "present": present,
            "favorites_only": "true" if favorites_only else "false",
            "page": page,
            "page_size": page_size,
        }
        if q:
            params["q"] = q[:120]
        if state:
            params["state"] = state[:40]
        data = await self._get_json(
            authorization, f"/servers/{normalized}/host-services", params=params,
        )
        if not isinstance(data, dict) or not isinstance(data.get("items"), list):
            raise ReadError("malformed_upstream_response")
        items = [
            row for row in (project_windows_host_service(item) for item in data["items"])
            if row
        ]
        total = data.get("total")
        if type(total) is not int or total < 0:
            total = len(items)
        return {
            "server_id": normalized,
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "favorites_count": (
                data.get("favorites_count")
                if type(data.get("favorites_count")) is int else None
            ),
        }

    async def windows_services_health(self, authorization: str) -> dict[str, Any]:
        data = await self._get_json(authorization, "/dashboard/windows-services-health")
        if not isinstance(data, dict):
            raise ReadError("malformed_upstream_response")
        issues_raw = data.get("issues") if isinstance(data.get("issues"), list) else []
        issues = []
        for item in issues_raw[:100]:
            if not isinstance(item, dict):
                continue
            try:
                server_id = str(UUID(str(item.get("server_id"))))
            except (ValueError, AttributeError, TypeError):
                continue
            issues.append({
                "server_id": server_id,
                "server_name": _limit_string(item.get("server_name"), max_len=120),
                # Dashboard aliases hs.display_name AS service_name (V006: key 200, display 240).
                "service_key": _limit_string(
                    item.get("service_key"), max_len=_WINDOWS_HOST_SERVICE_KEY_MAX,
                ),
                "service_name": _limit_string(
                    item.get("service_name"), max_len=_WINDOWS_HOST_SERVICE_DISPLAY_NAME_MAX,
                ),
                "criticality": item.get("criticality") if item.get("criticality") in {"high", "critical"} else None,
                "state": _limit_string(item.get("state"), max_len=40),
                "status": item.get("status") if item.get("status") in {"stopped", "attention", "unverified"} else None,
                "reason": _limit_string(item.get("reason"), max_len=160),
            })
        return {
            "generated_at": _limit_string(data.get("generated_at"), max_len=40),
            "total": _nonnegative_number(data.get("total")),
            "running": _nonnegative_number(data.get("running")),
            "stopped": _nonnegative_number(data.get("stopped")),
            "attention": _nonnegative_number(data.get("attention")),
            "unverified": _nonnegative_number(data.get("unverified")),
            "health_percent": (
                data.get("health_percent")
                if type(data.get("health_percent")) in (int, float) else None
            ),
            "issues_total": _nonnegative_number(data.get("issues_total")),
            "issues": issues,
            "source": "it-portal-windows-services-health",
        }
