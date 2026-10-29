"""Agregações de dashboard LMP — R09/R10/R11 (owner: Engineering API).

Portado de `api-delpi/.../list_lmp_dashboard_use_case.py`
(`_compute_summary`, `_build_charts`, filtro de status).

R09 (semântica sutil DIV-02 da spec): `% dentro do prazo` conta
`status != "Atrasado"` — Andamento e Retornada entram no numerador.
Comportamento vigente preservado; decisão de produto pendente não é
reinterpretada aqui.
"""

from __future__ import annotations

from typing import Any, Iterable, Protocol

from engineering_app.domain.lmp.business_rules import DASHBOARD_STATUS_VALUES
from engineering_app.domain.lmp.listing_semantics import LISTING_KIND_LMP

LEVEL_ORDER = ("Nível 1", "Nível 2", "Nível 3")


class EnrichedItem(Protocol):
    """Contrato mínimo que a agregação exige do item enriquecido."""

    listing_kind: str | None
    status: str
    lead_time_util: int | None
    nivel: str  # campo de contrato legado — PT mantido por paridade


def resolve_dashboard_status_filter(raw: str | None) -> str | None:
    """Filtro de status do dashboard — aliases do contrato legado."""
    if raw is None:
        return None

    normalized = str(raw).strip().lower()
    if normalized in ("", "todos", "all"):
        return None

    aliases = {
        "pontual": "Pontual",
        "atrasado": "Atrasado",
        "andamento": "Andamento",
        "retornada": "Retornada",
    }
    if normalized in aliases:
        return aliases[normalized]

    for value in DASHBOARD_STATUS_VALUES:
        if str(raw).strip() == value:
            return value

    raise ValueError(
        "status inválido. Valores aceitos: Todos, Pontual, Atrasado, Andamento ou Retornada."
    )


def filter_items_by_status(
    items: Iterable[EnrichedItem],
    status_filter: str | None,
) -> list[EnrichedItem]:
    if not status_filter:
        return list(items)
    return [item for item in items if item.status == status_filter]


def compute_summary(
    lmp_enriched: list[EnrichedItem],
    total_items: int,
) -> dict[str, Any]:
    """R09/R10 — KPIs do dashboard sobre itens LMP enriquecidos."""
    lead_items = [item for item in lmp_enriched if item.lead_time_util is not None]
    pontuais = len([item for item in lmp_enriched if item.status != "Atrasado"])
    total_lmps_for_kpi = len(lmp_enriched)

    percent_dentro_prazo = (
        (pontuais / total_lmps_for_kpi * 100) if total_lmps_for_kpi else 0
    )
    avg_lead_time = (
        sum(item.lead_time_util or 0 for item in lead_items) / len(lead_items)
        if lead_items
        else 0
    )

    return {
        "total_lmps": total_lmps_for_kpi,
        "total_items": total_items,
        "percent_dentro_prazo": round(percent_dentro_prazo, 2),
        "avg_lead_time": round(avg_lead_time, 2),
    }


def build_charts(items: list[EnrichedItem]) -> dict[str, Any]:
    """R11 — gráficos por nível/status/lead médio (contrato legado)."""
    level_data = [
        {"name": name, "value": sum(1 for item in items if item.nivel == name)}
        for name in LEVEL_ORDER
    ]
    status_data = [
        {"name": name, "value": sum(1 for item in items if item.status == name)}
        for name in DASHBOARD_STATUS_VALUES
    ]

    lead_by_level = []
    for nivel in LEVEL_ORDER:
        items_by_level = [
            item
            for item in items
            if item.nivel == nivel and item.lead_time_util is not None
        ]
        avg = (
            sum(item.lead_time_util or 0 for item in items_by_level)
            / len(items_by_level)
            if items_by_level
            else 0
        )
        lead_by_level.append({"nivel": nivel, "valor": round(avg, 2)})

    return {
        "levelData": level_data,
        "statusData": status_data,
        "leadByLevel": lead_by_level,
    }


def is_lmp(item: EnrichedItem) -> bool:
    return item.listing_kind == LISTING_KIND_LMP
