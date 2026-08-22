from __future__ import annotations

from datetime import date, datetime
from typing import Any

from financial_app.domain.errors import InvalidPeriod
from financial_app.domain.services.payload_reader import as_optional_text


def parse_iso_date(value: str, *, field_name: str) -> date:
    normalized = str(value or "").strip()
    if not normalized:
        raise InvalidPeriod(f"{field_name} inválida. Use o formato AAAA-MM-DD.")
    try:
        if len(normalized) == 8 and normalized.isdigit():
            return datetime.strptime(normalized, "%Y%m%d").date()
        return datetime.strptime(normalized[:10], "%Y-%m-%d").date()
    except ValueError as exc:
        raise InvalidPeriod(f"{field_name} inválida. Use o formato AAAA-MM-DD.") from exc


def add_months(value: date, months: int) -> date:
    year = value.year + (value.month - 1 + months) // 12
    month = (value.month - 1 + months) % 12 + 1
    return date(year, month, 1)


def normalize_optional_period(
    start_date: str | None, end_date: str | None
) -> tuple[str | None, str | None]:
    """Período opcional: ou os dois lados, ou nenhum (a api-delpi aplica o padrão)."""
    start = as_optional_text(start_date)
    end = as_optional_text(end_date)
    if (start is None) ^ (end is None):
        raise InvalidPeriod(
            "Informe início e fim juntos, ou omita ambos para usar os últimos 12 meses."
        )
    if start is None or end is None:
        return None, None
    if parse_iso_date(start, field_name="startDate") >= parse_iso_date(
        end, field_name="endDate"
    ):
        raise InvalidPeriod("A data inicial deve ser anterior ao limite final.")
    return start, end


def resolve_required_period(
    start_date: str | None,
    end_date: str | None,
    *,
    default_months: int = 12,
    today: date | None = None,
) -> tuple[str, str]:
    """Período obrigatório na origem — aplica o padrão quando o caller omite."""
    start = as_optional_text(start_date)
    end = as_optional_text(end_date)
    if start is None and end is None:
        reference = today or date.today()
        current_month = date(reference.year, reference.month, 1)
        return add_months(current_month, -(default_months - 1)).isoformat(), reference.isoformat()
    if start is None or end is None:
        raise InvalidPeriod("Informe início e fim juntos.")
    if parse_iso_date(start, field_name="startDate") > parse_iso_date(
        end, field_name="endDate"
    ):
        raise InvalidPeriod("A data inicial deve ser anterior ou igual à data final.")
    return start, end


def current_month_bounds(today: date | None = None) -> tuple[str, str]:
    reference = today or date.today()
    return date(reference.year, reference.month, 1).isoformat(), reference.isoformat()


def last_completed_months_bounds(months: int = 12, today: date | None = None) -> tuple[str, str]:
    """Janela usada pela inadimplência: N meses completos até o mês anterior."""
    reference = today or date.today()
    end_exclusive = date(reference.year, reference.month, 1)
    return add_months(end_exclusive, -months).isoformat(), end_exclusive.isoformat()


def map_period(raw: Any) -> dict[str, str | None]:
    """Converte o ``periodo`` da api-delpi para o contrato camelCase do BFF."""
    source = raw if isinstance(raw, dict) else {}
    return {
        "startDate": as_optional_text(source.get("data_inicio")),
        "endDate": as_optional_text(source.get("data_fim")),
        "endDateExclusive": as_optional_text(source.get("data_fim_exclusiva")),
        "label": as_optional_text(source.get("rotulo")),
    }
