"""Agregação de eficiência média por centro de trabalho (CT).

Espelha a regra do plugin eficiência-fabril:
- só STATUS_REGISTRO = OK (já filtrado na listagem quando status_ok_only);
- exclui outliers fora da faixa 0–199% das médias;
- média simples de EFICIENCIA_PERCENTUAL por CT;
- KPI do dashboard = média simples dessas médias (não média dos apontamentos).
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping, Sequence

from app.domain.production.production_efficiency_valid_range import (
    is_valid_production_efficiency_pct,
)

_PLACEHOLDER_WORK_CENTER = "—"


def aggregate_efficiency_by_work_center(
    items: Sequence[Mapping[str, Any]],
    *,
    status_registro_ok: str = "OK",
) -> list[dict[str, Any]]:
    """Agrupa apontamentos e devolve uma linha por CT (ordenada por nome)."""
    buckets: dict[str, list[float]] = defaultdict(list)

    for item in items:
        if str(item.get("status_registro") or "").strip() != status_registro_ok:
            continue
        work_center = str(item.get("centro_trabalho") or "").strip()
        if not work_center:
            continue
        efficiency = item.get("eficiencia_percentual")
        if not is_valid_production_efficiency_pct(efficiency):
            continue
        buckets[work_center].append(float(efficiency))

    rows: list[dict[str, Any]] = []
    for work_center in sorted(buckets.keys(), key=lambda value: value.casefold()):
        values = buckets[work_center]
        rows.append(
            {
                "work_center": work_center,
                "efficiency_pct": round(sum(values) / len(values), 2),
                "appointment_count": len(values),
            }
        )
    return rows


def average_efficiency_across_work_centers(
    rows: Sequence[Mapping[str, Any]],
) -> float | None:
    """Média simples das eficiências já agregadas por CT (KPI do dashboard)."""
    values: list[float] = []
    for row in rows:
        work_center = str(row.get("work_center") or "").strip()
        if not work_center or work_center == _PLACEHOLDER_WORK_CENTER:
            continue
        efficiency = row.get("efficiency_pct")
        if efficiency is None:
            continue
        try:
            values.append(float(efficiency))
        except (TypeError, ValueError):
            continue
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def headline_work_center_efficiency_pct(
    items: Sequence[Mapping[str, Any]],
    *,
    status_registro_ok: str = "OK",
) -> float | None:
    """KPI canônico: média das médias por CT a partir dos apontamentos."""
    return average_efficiency_across_work_centers(
        aggregate_efficiency_by_work_center(
            items,
            status_registro_ok=status_registro_ok,
        )
    )
