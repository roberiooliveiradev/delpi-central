"""Indicador de saúde dos serviços Windows prioritários na tela inicial.

Somente os favoritos de criticidade Alta/Crítica entram no denominador.
Sem coleta confiável não significa serviço executando nem parado.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timedelta, timezone
from typing import Any

STALE_AFTER_MINUTES = 15  # Três ciclos do inventário SCM (5 min).
FUTURE_TOLERANCE_MINUTES = 5
MAX_VISIBLE_ISSUES = 12

_STATE_ORDER = {"stopped": 0, "attention": 1, "unverified": 2}


def _assess(row: Mapping[str, Any], now: datetime) -> tuple[str, str]:
    observed = row.get("collected_at")
    if observed is None or observed.tzinfo is None:
        return "unverified", "Sem coleta válida"
    if observed < now - timedelta(minutes=STALE_AFTER_MINUTES):
        return "unverified", "Coleta atrasada"
    if observed > now + timedelta(minutes=FUTURE_TOLERANCE_MINUTES):
        return "unverified", "Horário da coleta inconsistente"
    if not row["is_present"]:
        return "attention", "Não encontrado na última coleta"
    state = str(row["state"]).lower()
    if state == "running":
        return "running", "Em execução"
    if state == "stopped":
        return "stopped", "Parado"
    if state == "paused":
        return "attention", "Pausado"
    return "attention", "Em transição ou estado desconhecido"


def _percent(running: int, total: int) -> int | None:
    # Truncar evita arredondar 99,9% para um falso "100% saudável".
    return (100 * running // total) if total else None


def summarize_windows_services_health(
    rows: Iterable[Mapping[str, Any]], *, now: datetime | None = None,
) -> dict:
    now = now or datetime.now(timezone.utc)
    counts = {"running": 0, "stopped": 0, "attention": 0, "unverified": 0}
    servers: dict[str, dict] = {}
    issues: list[dict] = []
    total = 0

    for row in rows:
        total += 1
        category, reason = _assess(row, now)
        counts[category] += 1
        server_id = str(row["server_id"])
        server = servers.setdefault(server_id, {
            "server_id": server_id,
            "server_name": row["server_name"],
            "hostname": row["hostname"],
            "last_collected_at": row.get("collected_at"),
            "total": 0,
            "running": 0,
            "stopped": 0,
            "attention": 0,
            "unverified": 0,
        })
        server["total"] += 1
        server[category] += 1

        if category != "running":
            issues.append({
                "server_id": server_id,
                "server_name": row["server_name"],
                "service_key": row["service_key"],
                "service_name": row["service_name"],
                "criticality": row["criticality"],
                "state": str(row["state"]).lower(),
                "status": category,
                "reason": reason,
            })

    server_rows = sorted(servers.values(), key=lambda item: item["hostname"].casefold())
    for server in server_rows:
        server["health_percent"] = _percent(server["running"], server["total"])

    issues.sort(key=lambda item: (
        0 if item["criticality"] == "critical" else 1,
        _STATE_ORDER[item["status"]],
        item["server_name"].casefold(),
        item["service_name"].casefold(),
    ))

    return {
        "generated_at": now,
        "stale_after_minutes": STALE_AFTER_MINUTES,
        "total": total,
        **counts,
        "health_percent": _percent(counts["running"], total),
        "servers": server_rows,
        "issues_total": len(issues),
        "issues": issues[:MAX_VISIBLE_ISSUES],
    }
