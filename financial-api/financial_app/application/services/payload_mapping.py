from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from financial_app.domain.errors import InvalidPeriod


def unwrap_data(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    data = payload.get("data")
    if isinstance(data, dict):
        return data
    return payload


def as_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def as_opt_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def as_str(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def as_opt_str(value: Any) -> str | None:
    text = as_str(value)
    return text or None


def map_period(raw: Any) -> dict[str, Any]:
    source = raw if isinstance(raw, dict) else {}
    end_exclusive = as_opt_str(
        source.get("data_fim_exclusiva")
        or source.get("end_date_exclusive")
        or source.get("endDateExclusive")
    )
    end_inclusive_legacy = as_opt_str(
        source.get("data_fim") or source.get("end_date") or source.get("endDate")
    )
    end_inclusive = end_inclusive_legacy or _inclusive_end_from_exclusive(end_exclusive)
    return {
        "startDate": as_opt_str(
            source.get("data_inicio") or source.get("start_date") or source.get("startDate")
        ),
        "endDate": end_inclusive,
        "endDateExclusive": end_exclusive or end_inclusive_legacy,
        "label": as_opt_str(source.get("rotulo") or source.get("label")),
    }


def map_pagination(raw: Any, *, default_page_size: int = 20) -> dict[str, Any]:
    source = raw if isinstance(raw, dict) else {}
    total_items = as_int(
        source.get("total_items") if "total_items" in source else source.get("totalItems"),
        as_int(source.get("total"), 0),
    )
    return {
        "page": as_int(source.get("page"), 1),
        "pageSize": as_int(
            source.get("page_size") if "page_size" in source else source.get("pageSize"),
            default_page_size,
        ),
        "totalItems": total_items,
        "totalPages": as_int(
            source.get("total_pages") if "total_pages" in source else source.get("totalPages"),
            1,
        ),
        "hasNext": bool(
            source.get("has_next") if "has_next" in source else source.get("hasNext", False)
        ),
        "hasPrevious": bool(
            source.get("has_previous")
            if "has_previous" in source
            else source.get("hasPrevious", False)
        ),
        "isComplete": bool(
            source.get("is_complete") if "is_complete" in source else source.get("isComplete", True)
        ),
    }


def map_sort(raw: Any, *, default_by: str, default_dir: str) -> dict[str, str]:
    source = raw if isinstance(raw, dict) else {}
    return {
        "sortBy": as_str(source.get("sort_by") or source.get("sortBy")) or default_by,
        "sortDir": (as_str(source.get("sort_dir") or source.get("sortDir")) or default_dir).lower(),
    }


def validate_period_pair(start_date: str | None, end_date: str | None) -> tuple[str | None, str | None]:
    start = (start_date or "").strip() or None
    end = (end_date or "").strip() or None
    if (start is None) != (end is None):
        raise InvalidPeriod("Informe início e fim do período juntos.")
    if start and end and start > end:
        raise InvalidPeriod("A data inicial não pode ser posterior à data final.")
    return start, end


def _parse_iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value[:10])
    except ValueError as exc:
        raise InvalidPeriod("Informe datas válidas no formato AAAA-MM-DD.") from exc


def _inclusive_end_from_exclusive(end_exclusive: str | None) -> str | None:
    if not end_exclusive:
        return None
    parsed = _parse_iso_date(end_exclusive)
    return (parsed - timedelta(days=1)).isoformat()


def resolve_delinquency_gateway_period(
    start_date: str | None,
    end_date: str | None,
) -> tuple[str | None, str | None]:
    """
    Portal Financeiro: fim inclusivo na UI.
    api-delpi inadimplência: end_date exclusivo (MES_REFERENCIA < end).
    """
    start, end_inclusive = validate_period_pair(start_date, end_date)
    if not start or not end_inclusive:
        return None, None
    end_exclusive = (_parse_iso_date(end_inclusive) + timedelta(days=1)).isoformat()
    return start, end_exclusive


def clamp_page(page: int | None, default: int = 1) -> int:
    value = as_int(page, default)
    return value if value > 0 else default


def clamp_page_size(page_size: int | None, *, default: int, maximum: int) -> int:
    value = as_int(page_size, default)
    if value < 1:
        return default
    return min(value, maximum)


def clamp_limit(limit: int | None, *, default: int, maximum: int) -> int:
    if limit is None:
        return default
    value = as_int(limit, default)
    if value < 1:
        return default
    return min(value, maximum)


def shift_months(origin: date, months: int) -> date:
    month_index = origin.month - 1 + months
    year = origin.year + month_index // 12
    month = month_index % 12 + 1
    if month <= 0:
        month += 12
        year -= 1
    day = min(origin.day, _days_in_month(year, month))
    return date(year, month, day)


def _days_in_month(year: int, month: int) -> int:
    if month == 12:
        nxt = date(year + 1, 1, 1)
    else:
        nxt = date(year, month + 1, 1)
    return (nxt - date(year, month, 1)).days


def default_period(months: int) -> tuple[str, str]:
    end = date.today()
    start = shift_months(end, -abs(months))
    return start.isoformat(), end.isoformat()
