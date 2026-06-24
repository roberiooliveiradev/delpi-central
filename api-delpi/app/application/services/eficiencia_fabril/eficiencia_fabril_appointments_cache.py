from __future__ import annotations

from typing import Any

from app.application.dto.eficiencia_fabril.get_eficiencia_fabril_dashboard_request import (
    GetEficienciaFabrilDashboardRequest,
)
from app.composition.query_cache_composer import build_query_cache


def eficiencia_fabril_appointments_cache_key(
    request: GetEficienciaFabrilDashboardRequest,
    *,
    status_ok_only: bool,
) -> str:
    return "|".join(
        [
            "eficiencia-fabril-appointments",
            request.branch or "",
            str(request.date_start or ""),
            str(request.date_end or ""),
            request.op or "",
            request.employee or "",
            request.work_center or "",
            "ok1" if status_ok_only else "ok0",
        ]
    )


def get_cached_eficiencia_fabril_appointments(key: str) -> list[dict[str, Any]] | None:
    cached = build_query_cache().get(key)
    if isinstance(cached, dict):
        rows = cached.get("items")
        if isinstance(rows, list):
            return rows
    return None


def set_cached_eficiencia_fabril_appointments(
    key: str,
    items: list[dict[str, Any]],
) -> None:
    build_query_cache().set(key, {"items": items})
