from __future__ import annotations

from typing import Any, Mapping, Optional

SAVINGS_TYPES = frozenset({"tempo", "material", "financeiro", "qualitativo", "misto"})

# Projeção anual = diária × dias úteis (constante Delpi).
# Distinto da validade do kaizen (1 ano corrido desde a implantação).
ANNUAL_BUSINESS_DAYS = 253
# Base de conversão: dias corridos ativos → dias úteis equivalentes.
CALENDAR_DAYS_PER_YEAR = 365


def business_days_equivalent(calendar_days: int) -> float:
    """Converte dias corridos ativos em dias úteis equivalentes (constante Delpi).

    Assim um ano de validade (365 dias corridos) rende exatamente
    ``ANNUAL_BUSINESS_DAYS`` no ganho do período — alinhado a ``annual_savings``.
    """
    if calendar_days <= 0:
        return 0.0
    return calendar_days * ANNUAL_BUSINESS_DAYS / CALENDAR_DAYS_PER_YEAR


def amount_for_active_calendar_days(daily: float, calendar_days: int) -> float:
    """``daily × dias úteis equivalentes`` arredondado em 2 casas."""
    return round(daily * business_days_equivalent(calendar_days), 2)


def _to_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def infer_savings_type(
    explicit_type: Optional[str],
    *,
    seconds_per_occurrence: Optional[float] = None,
    occurrences_per_day: Optional[float] = None,
    hourly_cost: Optional[float] = None,
    quantity_saved_per_day: Optional[float] = None,
    unit_material_cost: Optional[float] = None,
    fixed_daily_savings: Optional[float] = None,
) -> str:
    normalized = (explicit_type or "").strip().lower()
    if normalized in SAVINGS_TYPES:
        return normalized

    has_time = all(
        value is not None and value > 0
        for value in (seconds_per_occurrence, occurrences_per_day, hourly_cost)
    )
    has_material = all(
        value is not None and value > 0
        for value in (quantity_saved_per_day, unit_material_cost)
    )
    has_financial = fixed_daily_savings is not None and fixed_daily_savings > 0

    parts = sum([has_time, has_material, has_financial])
    if parts > 1:
        return "misto"
    if has_time:
        return "tempo"
    if has_material:
        return "material"
    if has_financial:
        return "financeiro"
    return "qualitativo"


def _time_daily_savings(
    seconds_per_occurrence: Optional[float],
    occurrences_per_day: Optional[float],
    hourly_cost: Optional[float],
) -> Optional[float]:
    if (
        seconds_per_occurrence is None
        or occurrences_per_day is None
        or hourly_cost is None
    ):
        return None
    hours_saved = (seconds_per_occurrence * occurrences_per_day) / 3600
    return round(hours_saved * hourly_cost, 2)


def _material_daily_savings(
    quantity_saved_per_day: Optional[float],
    unit_material_cost: Optional[float],
) -> Optional[float]:
    if quantity_saved_per_day is None or unit_material_cost is None:
        return None
    return round(quantity_saved_per_day * unit_material_cost, 2)


def calculate_daily_savings(fields: Mapping[str, Any]) -> Optional[float]:
    savings_type = infer_savings_type(
        fields.get("savings_type"),
        seconds_per_occurrence=_to_float(fields.get("seconds_per_occurrence")),
        occurrences_per_day=_to_float(fields.get("occurrences_per_day")),
        hourly_cost=_to_float(fields.get("hourly_cost")),
        quantity_saved_per_day=_to_float(fields.get("quantity_saved_per_day")),
        unit_material_cost=_to_float(fields.get("unit_material_cost")),
        fixed_daily_savings=_to_float(fields.get("fixed_daily_savings")),
    )

    if savings_type == "qualitativo":
        return None

    time_part = _time_daily_savings(
        _to_float(fields.get("seconds_per_occurrence")),
        _to_float(fields.get("occurrences_per_day")),
        _to_float(fields.get("hourly_cost")),
    )
    material_part = _material_daily_savings(
        _to_float(fields.get("quantity_saved_per_day")),
        _to_float(fields.get("unit_material_cost")),
    )
    financial_part = _to_float(fields.get("fixed_daily_savings"))

    if savings_type == "tempo":
        return time_part
    if savings_type == "material":
        return material_part
    if savings_type == "financeiro":
        return round(financial_part, 2) if financial_part is not None else None
    if savings_type == "misto":
        total = 0.0
        has_value = False
        for part in (time_part, material_part, financial_part):
            if part is not None:
                total += part
                has_value = True
        return round(total, 2) if has_value else None

    return None


def calculate_annual_savings(daily_savings: Optional[float]) -> Optional[float]:
    """Projeção anual em dias úteis — não usar 365 (ano corrido = só validade)."""
    if daily_savings is None:
        return None
    return round(daily_savings * ANNUAL_BUSINESS_DAYS, 2)


def resolve_realized_daily_savings(
    fields: Mapping[str, Any],
    *,
    calculated_daily: Optional[float] = None,
) -> Optional[float]:
    """Economia realizada/dia: medida informada ou, se ausente, estimativa calculada."""
    explicit = _to_float(fields.get("realized_daily_savings"))
    if explicit is not None:
        return round(explicit, 2)
    daily = (
        calculated_daily
        if calculated_daily is not None
        else _to_float(fields.get("daily_savings"))
    )
    if daily is None:
        daily = calculate_daily_savings(fields)
    return round(daily, 2) if daily is not None else None


def resolve_realized_annual_savings(
    fields: Mapping[str, Any],
    *,
    calculated_daily: Optional[float] = None,
) -> Optional[float]:
    realized_daily = resolve_realized_daily_savings(
        fields, calculated_daily=calculated_daily
    )
    return calculate_annual_savings(realized_daily)


def hours_saved_per_day(
    seconds_per_occurrence: Optional[float],
    occurrences_per_day: Optional[float],
) -> Optional[float]:
    if seconds_per_occurrence is None or occurrences_per_day is None:
        return None
    return round((seconds_per_occurrence * occurrences_per_day) / 3600, 4)


def enrich_savings_fields(fields: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(fields)
    enriched["savings_type"] = infer_savings_type(
        enriched.get("savings_type"),
        seconds_per_occurrence=_to_float(enriched.get("seconds_per_occurrence")),
        occurrences_per_day=_to_float(enriched.get("occurrences_per_day")),
        hourly_cost=_to_float(enriched.get("hourly_cost")),
        quantity_saved_per_day=_to_float(enriched.get("quantity_saved_per_day")),
        unit_material_cost=_to_float(enriched.get("unit_material_cost")),
        fixed_daily_savings=_to_float(enriched.get("fixed_daily_savings")),
    )
    daily = calculate_daily_savings(enriched)
    enriched["daily_savings"] = daily
    enriched["annual_savings"] = calculate_annual_savings(daily)
    enriched["hours_saved_per_day"] = hours_saved_per_day(
        _to_float(enriched.get("seconds_per_occurrence")),
        _to_float(enriched.get("occurrences_per_day")),
    )

    realized_daily = resolve_realized_daily_savings(enriched, calculated_daily=daily)
    enriched["realized_daily_savings"] = realized_daily
    enriched["realized_annual_savings"] = resolve_realized_annual_savings(
        enriched, calculated_daily=realized_daily
    )
    return enriched
