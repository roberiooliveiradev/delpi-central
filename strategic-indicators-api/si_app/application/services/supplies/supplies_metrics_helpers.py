from __future__ import annotations

from datetime import date, datetime, timedelta


def build_cpv_payload(
    *,
    branch: str | None,
    start_date: str | None,
    end_date: str | None,
    cpv_raw: dict,
    rol_data: dict,
) -> dict:
    summary = cpv_raw.get("summary") or {}
    by_cfop = cpv_raw.get("by_cfop") or []
    by_tm = cpv_raw.get("by_tm") or []
    top_products = cpv_raw.get("top_products") or []
    top_documents = cpv_raw.get("top_documents") or []

    cpv_total = float(summary.get("cpv_total") or 0)
    rol_value = float(rol_data.get("rol") or 0)
    total_movements = int(summary.get("total_movements") or 0)
    total_quantity = float(summary.get("total_quantity") or 0)

    cpv_percentage = (cpv_total / rol_value * 100) if rol_value > 0 else 0
    average_cost_per_movement = (cpv_total / total_movements) if total_movements > 0 else 0
    average_cost_per_unit = (cpv_total / total_quantity) if total_quantity > 0 else 0

    return {
        "branch": branch or "consolidated",
        "start_date": summary.get("start_date") or cpv_raw.get("start_date") or start_date or "",
        "end_date": summary.get("end_date") or cpv_raw.get("end_date") or end_date or "",
        "summary": {
            "cpv_total": cpv_total,
            "rol": rol_value,
            "cpv_percentage": cpv_percentage,
            "total_movements": total_movements,
            "total_quantity": total_quantity,
            "average_cost_per_movement": average_cost_per_movement,
            "average_cost_per_unit": average_cost_per_unit,
        },
        "financial_context": {
            "gross_revenue": rol_data.get("gross_revenue", 0),
            "returns": rol_data.get("returns", 0),
            "discounts": rol_data.get("discounts", 0),
            "rol": rol_data.get("rol", 0),
            "ipi_separated": rol_data.get("ipi_separated", 0),
        },
        "by_cfop": by_cfop,
        "by_tm": by_tm,
        "top_products": top_products,
        "top_documents": top_documents,
    }


def build_otd_payload(
    *,
    branch: str | None,
    start_date: str | None,
    end_date: str | None,
    otd_raw: dict,
) -> dict:
    summary = otd_raw.get("summary") or {}
    monthly_breakdown = otd_raw.get("monthly_breakdown") or []
    top_late_suppliers = otd_raw.get("top_late_suppliers") or []
    late_deliveries = otd_raw.get("late_deliveries") or []

    total_lines = int(summary.get("total_lines") or 0)
    on_time_lines = int(summary.get("on_time_lines") or 0)
    late_lines = int(summary.get("late_lines") or 0)
    otd_percentage = float(summary.get("otd_percentage") or 0)

    late_percentage = round((late_lines * 100.0 / total_lines), 2) if total_lines > 0 else 0

    return {
        "branch": otd_raw.get("branch") or branch or "consolidated",
        "start_date": otd_raw.get("start_date") or start_date or "",
        "end_date": otd_raw.get("end_date") or end_date or "",
        "summary": {
            "total_lines": total_lines,
            "on_time_lines": on_time_lines,
            "late_lines": late_lines,
            "otd_percentage": otd_percentage,
            "late_percentage": late_percentage,
        },
        "monthly_breakdown": monthly_breakdown,
        "top_late_suppliers": top_late_suppliers,
        "late_deliveries": late_deliveries,
    }


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None

    value = str(value).strip()
    formats = (
        "%Y%m%d",
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
    )

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    raise ValueError(
        "Data inválida. Use formatos como YYYYMMDD, YYYY-MM-DD ou DD-MM-YYYY."
    )


def _uses_historical_estimation(
    *,
    start_date: str | None,
    end_date: str | None,
) -> bool:
    return bool(start_date or end_date)


def _resolve_stock_period(
    *,
    start_date: str | None,
    end_date: str | None,
) -> tuple[str, str] | None:
    if not _uses_historical_estimation(start_date=start_date, end_date=end_date):
        return None

    if not start_date or not end_date:
        raise ValueError(
            "Para consultar estoque em uma data passada, informe start_date e end_date."
        )

    start = _parse_date(start_date)
    end = _parse_date(end_date)

    if not start or not end:
        raise ValueError(
            "Para consultar estoque em uma data passada, informe start_date e end_date válidos."
        )

    if start > end:
        raise ValueError("start_date não pode ser maior que end_date.")

    period_start = start.strftime("%Y%m%d")
    period_end_exclusive = (end + timedelta(days=1)).strftime("%Y%m%d")
    return period_start, period_end_exclusive


def build_stock_value_payload(
    *,
    branch: str | None,
    start_date: str | None,
    end_date: str | None,
    location: str | None,
    stock_raw: dict,
) -> dict:
    period = _resolve_stock_period(start_date=start_date, end_date=end_date)

    summary = stock_raw.get("summary") or {}
    by_branch = stock_raw.get("by_branch") or []
    by_location = stock_raw.get("by_location") or []
    top_products = stock_raw.get("top_products") or []

    total_stock_value = float(summary.get("total_stock_value") or 0)
    total_stock_quantity = float(summary.get("total_stock_quantity") or 0)

    average_unit_value = (
        total_stock_value / total_stock_quantity
        if total_stock_quantity > 0
        else 0
    )

    payload = {
        "branch": stock_raw.get("branch") or branch or "consolidated",
        "location": stock_raw.get("location") or location or "all",
        "summary": {
            "total_stock_value": total_stock_value,
            "total_stock_quantity": total_stock_quantity,
            "total_records": int(summary.get("total_records") or 0),
            "total_products": int(summary.get("total_products") or 0),
            "total_locations": int(summary.get("total_locations") or 0),
            "average_unit_value": average_unit_value,
        },
        "by_branch": by_branch,
        "by_location": by_location,
        "top_products": top_products,
    }

    if period:
        period_start, period_end_exclusive = period
        payload["estimation"] = {
            "enabled": True,
            "method": "sb9_last_closure_plus_sd3_movements",
            "start_date": period_start,
            "end_date_exclusive": period_end_exclusive,
            "note": (
                "Valor estimado a partir do último fechamento real em SB9010 "
                "somado às movimentações líquidas em SD3010 (entrada se D3_TM < '500', "
                "saída caso contrário). Não substitui fechamento oficial da SB9."
            ),
        }

    return payload


def _last_day_of_month(value: date) -> date:
    if value.month == 12:
        return date(value.year + 1, 1, 1) - timedelta(days=1)
    return date(value.year, value.month + 1, 1) - timedelta(days=1)


def _is_closed_month(start: date, end: date) -> bool:
    return (
        start.day == 1
        and end == _last_day_of_month(end)
        and start.year == end.year
        and start.month == end.month
    )


def _is_full_month_range(start: date, end: date) -> bool:
    current = date(start.year, start.month, 1)

    while current <= end:
        month_start = current
        month_end = _last_day_of_month(current)

        if month_start < start or month_end > end:
            return False

        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)

    return True


def _months_in_range(start: date, end: date) -> int:
    return ((end.year - start.year) * 12) + (end.month - start.month) + 1


def _days_in_range(start: date, end: date) -> int:
    return (end - start).days + 1


def _is_valid_idd_period(start: date, end: date) -> bool:
    return _is_closed_month(start, end) or _is_full_month_range(start, end)


def _resolve_cpv_average_monthly(
    cpv_total: float,
    start: date,
    end: date,
) -> tuple[float, str, int]:
    if _is_closed_month(start, end):
        return cpv_total, "closed_month", 1

    if _is_full_month_range(start, end):
        months = _months_in_range(start, end)
        average = cpv_total / months if months > 0 else 0
        return average, "full_month_range", months

    days = _days_in_range(start, end)
    average = (cpv_total / days) * 30 if days > 0 else 0
    return average, "partial_period_monthlyized", days


def _stock_summary_from_raw(stock_raw: dict) -> dict:
    summary = stock_raw.get("summary") or {}
    return {
        "branch": stock_raw.get("branch", ""),
        "location": stock_raw.get("location", ""),
        "total_stock_value": summary.get("total_stock_value", 0),
        "total_stock_quantity": summary.get("total_stock_quantity", 0),
        "total_records": summary.get("total_records", 0),
        "total_products": summary.get("total_products", 0),
        "total_locations": summary.get("total_locations", 0),
    }


def build_turnover_raw_from_cpv(
    *,
    cpv_raw: dict,
    start_date: str | None,
    end_date: str | None,
) -> dict:
    summary = cpv_raw.get("summary") or {}
    return {
        "start_date": cpv_raw.get("start_date") or start_date or "",
        "end_date": cpv_raw.get("end_date") or end_date or "",
        "cpv_context": {
            "cpv_total": summary.get("cpv_total", 0),
            "total_movements": summary.get("total_movements", 0),
            "total_quantity": summary.get("total_quantity", 0),
            "start_date": cpv_raw.get("start_date") or start_date or "",
            "end_date": cpv_raw.get("end_date") or end_date or "",
        },
    }


def _cpv_context_from_turnover_raw(turnover_raw: dict) -> dict:
    cpv_ctx = turnover_raw.get("cpv_context") or {}
    return {
        "cpv_total": cpv_ctx.get("cpv_total", 0),
        "total_movements": cpv_ctx.get("total_movements", 0),
        "total_quantity": cpv_ctx.get("total_quantity", 0),
        "start_date": turnover_raw.get("start_date", ""),
        "end_date": turnover_raw.get("end_date", ""),
    }


def build_inventory_turnover_payload(
    *,
    branch: str | None,
    start_date: str | None,
    end_date: str | None,
    location: str | None,
    turnover_raw: dict,
    stock_raw: dict,
    strict_idd_period: bool = False,
) -> dict:
    stock_context = _stock_summary_from_raw(stock_raw)
    cpv_context = _cpv_context_from_turnover_raw(turnover_raw)

    total_stock_value = float(stock_context.get("total_stock_value") or 0)
    total_stock_quantity = float(stock_context.get("total_stock_quantity") or 0)
    cpv_total = float(cpv_context.get("cpv_total") or 0)

    start_raw = cpv_context.get("start_date") or start_date
    end_raw = cpv_context.get("end_date") or end_date

    start_date_parsed = _parse_date(start_raw)
    end_date_parsed = _parse_date(end_raw)

    if not start_date_parsed or not end_date_parsed:
        raise ValueError("start_date e end_date são obrigatórios para calcular giro de estoque.")

    if start_date_parsed > end_date_parsed:
        raise ValueError("start_date não pode ser maior que end_date.")

    idd_period_valid = _is_valid_idd_period(start_date_parsed, end_date_parsed)

    if strict_idd_period and not idd_period_valid:
        raise ValueError(
            "Período inválido para o IDD. Use mês fechado ou intervalo composto apenas por meses completos."
        )

    cpv_average_monthly, calculation_mode, period_reference = _resolve_cpv_average_monthly(
        cpv_total=cpv_total,
        start=start_date_parsed,
        end=end_date_parsed,
    )

    inventory_turnover_months = (
        total_stock_value / cpv_average_monthly
        if cpv_average_monthly > 0 else 0
    )

    inventory_turnover_times = (
        cpv_total / total_stock_value
        if total_stock_value > 0 else 0
    )

    average_unit_value = (
        total_stock_value / total_stock_quantity
        if total_stock_quantity > 0 else 0
    )

    payload = {
        "branch": stock_context.get("branch") or branch or "consolidated",
        "location": stock_context.get("location") or location or "all",
        "start_date": start_date_parsed.strftime("%Y%m%d"),
        "end_date": end_date_parsed.strftime("%Y%m%d"),
        "summary": {
            "inventory_turnover_months": inventory_turnover_months,
            "inventory_turnover_times": inventory_turnover_times,
            "total_stock_value": total_stock_value,
            "cpv_total": cpv_total,
            "cpv_average_monthly": cpv_average_monthly,
        },
        "calculation_context": {
            "calculation_mode": calculation_mode,
            "idd_period_valid": idd_period_valid,
            "strict_idd_period": strict_idd_period,
            "period_reference": period_reference,
        },
        "stock_context": {
            "total_stock_value": total_stock_value,
            "total_stock_quantity": total_stock_quantity,
            "total_records": int(stock_context.get("total_records") or 0),
            "total_products": int(stock_context.get("total_products") or 0),
            "total_locations": int(stock_context.get("total_locations") or 0),
            "average_unit_value": average_unit_value,
        },
        "cpv_context": {
            "cpv_total": cpv_total,
            "total_movements": int(cpv_context.get("total_movements") or 0),
            "total_quantity": float(cpv_context.get("total_quantity") or 0),
            "cpv_average_monthly": cpv_average_monthly,
        },
    }

    if _uses_historical_estimation(start_date=start_date, end_date=end_date):
        payload["stock_estimation"] = {
            "enabled": True,
            "method": "sb9_last_closure_plus_sd3_movements",
            "start_date": start_date_parsed.strftime("%Y%m%d"),
            "end_date_exclusive": (end_date_parsed + timedelta(days=1)).strftime("%Y%m%d"),
            "note": (
                "Estoque estimado pelo mesmo método de /supplies/stock-value "
                "(SB9010 + SD3010)."
            ),
        }

    return payload
