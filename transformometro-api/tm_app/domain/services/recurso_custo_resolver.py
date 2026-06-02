from __future__ import annotations

from datetime import date
from typing import Optional


def _month_start(value: date) -> date:
    return date(value.year, value.month, 1)


def _parse_date(value: object) -> Optional[date]:
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    if len(text) >= 10:
        text = text[:10]
    try:
        parts = text.split("-")
        if len(parts) == 3:
            return date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (TypeError, ValueError):
        return None
    return None


def _covers_month(
    competencia_date: date,
    start_date: Optional[date],
    end_date: Optional[date],
) -> bool:
    month_value = _month_start(competencia_date)
    if start_date and month_value < _month_start(start_date):
        return False
    if end_date and month_value > _month_start(end_date):
        return False
    return True


def resolve_recurso_valor_mensal(
    resource: dict,
    custos: list[dict],
    competencia_date: date,
) -> float:
    """Retorna o valor mensal do recurso na competencia usando a tabela historica."""
    resource_id = str(resource.get("recurso_compartilhado_id") or "")
    eligible: list[dict] = []
    for row in custos:
        if row.get("deletado"):
            continue
        if str(row.get("recurso_compartilhado_id") or "") != resource_id:
            continue
        start = _parse_date(row.get("data_inicio_vigencia"))
        end = _parse_date(row.get("data_fim_vigencia"))
        if not start:
            continue
        if _covers_month(competencia_date, start, end):
            eligible.append(row)

    if not eligible:
        return 0.0

    eligible.sort(
        key=lambda item: _parse_date(item.get("data_inicio_vigencia")) or date.min,
        reverse=True,
    )
    try:
        return float(eligible[0].get("valor_mensal") or 0)
    except (TypeError, ValueError):
        return 0.0
