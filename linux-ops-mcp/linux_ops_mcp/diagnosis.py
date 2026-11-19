"""Conservative health classification for IT Portal observations.

Separates collection freshness from host health. Never invents missing metrics.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from .reader import (
    OBSERVATION_STATES,
    SECTION_STATES,
    SYSTEMD_ALLOWLIST,
    SYSTEMD_STATES,
    ReadError,
    _limit_string,
    _nonnegative_number,
    _safe_status,
)

COLLECTION_STATUSES = frozenset(
    ("available", "partial", "stale", "unavailable", "failed_read")
)
HEALTH_STATUSES = frozenset(
    ("healthy", "attention", "critical", "unknown")
)
OVERALL_STATUSES = frozenset(
    ("healthy", "attention", "critical", "stale", "no_data", "partial", "unknown")
)

WINDOWS_SERVICE_RUNNING = frozenset(("running", "start_pending", "continue_pending"))
WINDOWS_SERVICE_STOPPED = frozenset(("stopped", "stop_pending", "paused", "pause_pending"))


def parse_observed_at(value: object) -> datetime | None:
    text = _limit_string(value, max_len=40)
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _ratio_percent(used: int | None, total: int | None) -> float | None:
    if used is None or total is None or total <= 0 or used < 0:
        return None
    return round((used / total) * 100.0, 2)


def _percent_from_available(total: int | None, available: int | None) -> float | None:
    if total is None or available is None or total <= 0 or available < 0:
        return None
    used = total - available
    if used < 0:
        return None
    return _ratio_percent(used, total)


def _coerce_percent(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str) and value.strip():
        try:
            number = float(value.strip())
        except ValueError:
            return None
    else:
        return None
    if number < 0 or number > 100:
        return None
    return round(number, 2)


def collection_status(
    observation: dict[str, Any] | None,
    *,
    now: datetime | None = None,
    stale_after_hours: float = 36.0,
) -> str:
    if observation is None:
        return "unavailable"
    presented = observation.get("presentation_status")
    if isinstance(presented, str) and presented in OBSERVATION_STATES:
        # Prefer IT Portal presentation when present; still recompute stale locally
        # so MCP thresholds remain explicit and testable.
        if presented == "unavailable":
            return "unavailable"
    observed_at = parse_observed_at(observation.get("observed_at"))
    clock = now or datetime.now(timezone.utc)
    if observed_at is None:
        return "unavailable"
    if clock - observed_at > timedelta(hours=max(1.0, float(stale_after_hours))):
        return "stale"
    status = observation.get("status")
    if status == "failed":
        return "unavailable"
    if status == "partial" or presented == "partial":
        return "partial"
    if presented == "available" or status in {"complete", "available", None}:
        return "available"
    return _safe_status(presented, OBSERVATION_STATES, "partial")


def _volume_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    raw = summary.get("volumes")
    if not isinstance(raw, list):
        return []
    rows: list[dict[str, Any]] = []
    for item in raw[:32]:
        if not isinstance(item, dict):
            continue
        mount = _limit_string(item.get("mount_point"), max_len=120)
        if not mount:
            continue
        size = _nonnegative_number(item.get("size_bytes"))
        used = _nonnegative_number(item.get("used_bytes"))
        available = _nonnegative_number(item.get("available_bytes"))
        used_percent = _coerce_percent(item.get("used_percent"))
        if used_percent is None:
            used_percent = _ratio_percent(used, size)
        if used_percent is None and size is not None and available is not None:
            used_percent = _percent_from_available(size, available)
        rows.append({
            "mount_point": mount,
            "size_bytes": size,
            "used_bytes": used,
            "available_bytes": available,
            "used_percent": used_percent,
        })
    return rows


def _linux_service_summary(summary: dict[str, Any]) -> dict[str, Any]:
    raw = summary.get("systemd_services")
    services: list[dict[str, Any]] = []
    if isinstance(raw, list):
        seen: set[str] = set()
        for item in raw[:100]:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            if not isinstance(name, str) or name not in SYSTEMD_ALLOWLIST or name in seen:
                continue
            seen.add(name)
            state = _safe_status(item.get("active_state"), SYSTEMD_STATES, "unknown")
            services.append({"name": name, "active_state": state})
    inactive = [s for s in services if s["active_state"] in {"inactive", "failed"}]
    return {
        "source": "observation_systemd_allowlist",
        "total_observed_allowlisted": len(services),
        "inactive_or_failed": len(inactive),
        "items": sorted(services, key=lambda row: row["name"]),
        "attention_items": inactive[:20],
    }


def _windows_observation_service_summary(summary: dict[str, Any]) -> dict[str, Any]:
    raw = summary.get("windows_services")
    services: list[dict[str, Any]] = []
    if isinstance(raw, list):
        for item in raw[:40]:
            if not isinstance(item, dict):
                continue
            name = _limit_string(item.get("name"), max_len=120)
            if not name:
                continue
            state = _limit_string(item.get("active_state"), max_len=40) or "unknown"
            services.append({"name": name, "active_state": state.lower()})
    stopped = [
        s for s in services
        if s["active_state"] in WINDOWS_SERVICE_STOPPED or s["active_state"] == "stopped"
    ]
    return {
        "source": "observation_windows_services",
        "total_observed": len(services),
        "stopped_or_paused": len(stopped),
        "items": services,
        "attention_items": stopped[:20],
    }


def _issue(
    severity: str,
    code: str,
    message: str,
    *,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {"severity": severity, "code": code, "message": message}
    if evidence:
        payload["evidence"] = evidence
    return payload


def analyze_observation(
    observation: dict[str, Any] | None,
    *,
    server: dict[str, Any] | None = None,
    now: datetime | None = None,
    stale_after_hours: float = 36.0,
    memory_attention_pct: float = 85.0,
    memory_critical_pct: float = 95.0,
    disk_attention_pct: float = 85.0,
    disk_critical_pct: float = 95.0,
    cpu_attention_pct: float = 85.0,
    cpu_critical_pct: float = 95.0,
) -> dict[str, Any]:
    """Project a sanitized health view for one server observation."""
    server = server or {}
    collected = collection_status(
        observation, now=now, stale_after_hours=stale_after_hours,
    )
    base = {
        "server_id": _limit_string(server.get("id"), max_len=36),
        "name": _limit_string(server.get("name"), max_len=120),
        "hostname": _limit_string(server.get("hostname"), max_len=253),
        "operating_system": _limit_string(server.get("operating_system"), max_len=120),
        "unit_code": _limit_string(server.get("unit_code"), max_len=40),
        "environment": _limit_string(server.get("environment"), max_len=40),
        "criticality": _limit_string(server.get("criticality"), max_len=40),
        "administrative_status": _limit_string(
            server.get("administrative_status"), max_len=40
        ),
        "archived": server.get("archived") is True,
        "collection_status": collected,
        "health_status": "unknown",
        "overall_status": "no_data" if collected == "unavailable" else collected,
        "source": "it-portal-api",
        "observation_source": None,
        "observed_at": None,
        "os": None,
        "cpu_logical": None,
        "cpu_usage_percent": None,
        "memory": None,
        "volumes": [],
        "uptime_seconds": None,
        "services_summary": None,
        "sections": {},
        "issues": [],
        "analyzed_at": (now or datetime.now(timezone.utc)).isoformat().replace("+00:00", "Z"),
    }
    if observation is None:
        base["issues"].append(_issue(
            "attention", "no_observation",
            "Nenhuma observacao automatica disponivel para este servidor.",
        ))
        return base

    source = observation.get("source")
    if source not in {"linux_host_collector", "windows_host_collector"}:
        raise ReadError("unexpected_observation_source")
    if str(observation.get("schema_version")) != "1":
        raise ReadError("unexpected_observation_source")
    summary = observation.get("summary")
    sections = observation.get("sections_status")
    if not isinstance(summary, dict) or not isinstance(sections, dict):
        raise ReadError("malformed_observation")

    base["observation_source"] = source
    base["observed_at"] = _limit_string(observation.get("observed_at"), max_len=40)
    base["source"] = (
        "it-portal-linux-collector" if source == "linux_host_collector"
        else "it-portal-windows-collector"
    )
    os_info = summary.get("os") if isinstance(summary.get("os"), dict) else {}
    base["os"] = {
        "name": _limit_string(os_info.get("name"), max_len=120),
        "version": _limit_string(os_info.get("version"), max_len=80),
    }
    base["cpu_logical"] = _nonnegative_number(summary.get("cpu_logical"))
    base["cpu_usage_percent"] = _coerce_percent(summary.get("cpu_usage_percent"))
    base["uptime_seconds"] = _nonnegative_number(summary.get("uptime_seconds"))

    mem = summary.get("memory") if isinstance(summary.get("memory"), dict) else {}
    total = _nonnegative_number(mem.get("total_bytes"))
    available = _nonnegative_number(mem.get("available_bytes"))
    used = _nonnegative_number(mem.get("used_bytes"))
    used_percent = _percent_from_available(total, available)
    if used_percent is None:
        used_percent = _ratio_percent(used, total)
    base["memory"] = {
        "total_bytes": total,
        "available_bytes": available,
        "used_bytes": used if used is not None else (
            (total - available) if total is not None and available is not None else None
        ),
        "used_percent": used_percent,
    }
    base["volumes"] = _volume_rows(summary)
    if source == "linux_host_collector":
        section_keys = ("identity", "os", "memory", "volumes", "nics", "systemd", "docker")
        base["services_summary"] = _linux_service_summary(summary)
    else:
        section_keys = ("identity", "os", "cpu", "memory", "volumes", "nics", "windows_services")
        base["services_summary"] = _windows_observation_service_summary(summary)
    base["sections"] = {
        key: _safe_status(sections.get(key), SECTION_STATES, "unavailable")
        for key in section_keys
    }

    issues: list[dict[str, Any]] = []
    if collected == "stale":
        issues.append(_issue(
            "attention", "observation_stale",
            "A ultima observacao ultrapassou a janela de atualizacao configurada.",
            evidence={"observed_at": base["observed_at"], "stale_after_hours": stale_after_hours},
        ))
    if collected == "partial":
        issues.append(_issue(
            "attention", "observation_partial",
            "A coleta esta parcial; indicadores ausentes nao foram inventados.",
        ))

    if used_percent is not None:
        if used_percent >= memory_critical_pct:
            issues.append(_issue(
                "critical", "memory_critical",
                "Utilizacao de memoria em faixa critica.",
                evidence={"used_percent": used_percent},
            ))
        elif used_percent >= memory_attention_pct:
            issues.append(_issue(
                "attention", "memory_attention",
                "Utilizacao de memoria elevada.",
                evidence={"used_percent": used_percent},
            ))

    cpu_pct = base["cpu_usage_percent"]
    if cpu_pct is not None:
        if cpu_pct >= cpu_critical_pct:
            issues.append(_issue(
                "critical", "cpu_critical",
                "Utilizacao de CPU em faixa critica.",
                evidence={"cpu_usage_percent": cpu_pct},
            ))
        elif cpu_pct >= cpu_attention_pct:
            issues.append(_issue(
                "attention", "cpu_attention",
                "Utilizacao de CPU elevada.",
                evidence={"cpu_usage_percent": cpu_pct},
            ))
    # Missing CPU percent is unknown, never treated as 0%.

    for volume in base["volumes"]:
        pct = volume.get("used_percent")
        if pct is None:
            continue
        if pct >= disk_critical_pct:
            issues.append(_issue(
                "critical", "volume_critical",
                "Volume com utilizacao critica.",
                evidence={"mount_point": volume["mount_point"], "used_percent": pct},
            ))
        elif pct >= disk_attention_pct:
            issues.append(_issue(
                "attention", "volume_attention",
                "Volume com utilizacao elevada.",
                evidence={"mount_point": volume["mount_point"], "used_percent": pct},
            ))

    services = base["services_summary"] or {}
    for item in services.get("attention_items") or []:
        severity = "critical" if item.get("active_state") == "failed" else "attention"
        issues.append(_issue(
            severity, "service_not_active",
            "Servico observado fora do estado ativo/running.",
            evidence=item,
        ))

    base["issues"] = issues
    severities = {issue["severity"] for issue in issues if issue["code"] not in {
        "observation_stale", "observation_partial", "no_observation",
    }}
    if "critical" in severities:
        health = "critical"
    elif "attention" in severities:
        health = "attention"
    elif collected in {"unavailable"}:
        health = "unknown"
    elif collected == "partial" and not _has_minimum_metrics(base):
        health = "unknown"
    elif collected in {"available", "partial", "stale"} and _has_minimum_metrics(base):
        health = "healthy"
    else:
        health = "unknown"
    base["health_status"] = health

    if collected == "unavailable":
        overall = "no_data"
    elif collected == "stale":
        overall = "stale" if health in {"healthy", "unknown"} else health
    elif collected == "partial" and health == "healthy":
        overall = "partial"
    elif health == "healthy":
        overall = "healthy"
    elif health in {"attention", "critical"}:
        overall = health
    else:
        overall = "partial" if collected == "partial" else "unknown"
    base["overall_status"] = overall
    return base


def _has_minimum_metrics(projection: dict[str, Any]) -> bool:
    memory = projection.get("memory") or {}
    has_memory = memory.get("total_bytes") is not None and (
        memory.get("available_bytes") is not None or memory.get("used_percent") is not None
    )
    has_cpu_count = projection.get("cpu_logical") is not None
    return bool(has_memory and has_cpu_count)


def classify_os_family(operating_system: str | None, observation_source: str | None = None) -> str | None:
    if observation_source == "windows_host_collector":
        return "windows"
    if observation_source == "linux_host_collector":
        return "linux"
    text = (operating_system or "").strip().lower()
    if not text:
        return None
    if "windows" in text:
        return "windows"
    if any(token in text for token in ("linux", "ubuntu", "debian", "centos", "rhel", "red hat", "suse", "rocky", "alma")):
        return "linux"
    return None
