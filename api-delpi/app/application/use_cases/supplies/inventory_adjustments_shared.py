"""Validação compartilhada do período dos ajustes de inventário."""

from __future__ import annotations

from datetime import datetime, timedelta

from app.application.dto.supplies.inventory_adjustments_request import (
    InventoryAdjustmentsRequest,
)
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder

MAX_PERIOD_DAYS = 366


def resolve_required_period(
    request: InventoryAdjustmentsRequest,
) -> tuple[str, str, str]:
    """start/end obrigatórios, intervalo máximo de 366 dias.

    Retorna (start_yyyymmdd, end_yyyymmdd, end_exclusive_yyyymmdd)
    no formato Protheus.
    """
    if not request.start_date or not request.end_date:
        raise ValueError("Informe start_date e end_date para consultar ajustes.")

    start = QueryBuilder().convert_date_to_protheus(request.start_date)
    end = QueryBuilder().convert_date_to_protheus(request.end_date)
    if not start or not end:
        raise ValueError("Data inválida. Use YYYY-MM-DD ou DD/MM/YYYY.")
    if start > end:
        raise ValueError("start_date não pode ser maior que end_date.")

    parsed_start = datetime.strptime(start, "%Y%m%d")
    parsed_end = datetime.strptime(end, "%Y%m%d")
    if (parsed_end - parsed_start).days + 1 > MAX_PERIOD_DAYS:
        raise ValueError("O intervalo máximo é de 366 dias.")

    end_exclusive = (parsed_end + timedelta(days=1)).strftime("%Y%m%d")
    return start, end, end_exclusive
