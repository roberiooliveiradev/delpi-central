"""Fontes TV do GR Diário (GLPI #1598): período e granularidade configuráveis.

A API mantém as três operações originais. start_date/end_date permitem que o
filtro de período relativo do TV Dashboard (dateRangePreset) seja resolvido no
gateway, enquanto granularity=day|week|month|year controla os agrupamentos
temporais. O ranking de itens consolida por filial/produto, compensando
falta/sobra entre armazéns (GLPI #1615) dentro do período escolhido.
Os KPIs de divergência bruta continuam distintos do saldo líquido de itens.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.application.dto.supplies.inventory_adjustments_request import (
    InventoryAdjustmentsRequest,
)
from app.composition.supplies_composer import (
    build_get_inventory_adjustments_summary_use_case,
)
from app.infrastructure.persistence.totvs.supplies_repositories.inventory_adjustments_tv_repository import (
    InventoryAdjustmentsTvRepository,
)

_CENT = Decimal("0.01")
try:
    _BRAZIL_TZ = ZoneInfo("America/Sao_Paulo")
except ZoneInfoNotFoundError:
    _BRAZIL_TZ = timezone(timedelta(hours=-3))
_MINIMUM_DATE = date(2023, 1, 1)
_MAX_DAYS = 366
_GRANULARITIES = frozenset({"day", "week", "month", "year"})
_MEASURE_KEYS = ("gross_value", "net_value", "shortage_value", "surplus_value")
_COUNT_KEYS = ("adjustment_count", "shortage_count", "surplus_count")
_VALUATION_NOTE = (
    "Valores operacionais do custo atual D3_CUSTO1. O recálculo de custo "
    "médio no Protheus pode alterar números históricos; o fechamento "
    "mensal R07 utiliza apuração as-of e requer comparação própria."
)


def _round_money(value: Any) -> float:
    return float(Decimal(str(value or 0)).quantize(_CENT, rounding=ROUND_HALF_UP))


def _reference_date(as_of: str | None) -> date:
    today = datetime.now(_BRAZIL_TZ).date()
    if not as_of:
        return today
    try:
        parsed = date.fromisoformat(as_of)
    except (TypeError, ValueError) as exc:
        raise ValueError("as_of deve estar no formato YYYY-MM-DD.") from exc
    if parsed < _MINIMUM_DATE or parsed > today:
        raise ValueError("A referência deve estar entre 2023-01-01 e hoje.")
    return parsed


def _filters(branch: str | None, warehouse: str | None) -> tuple[str | None, str | None]:
    raw = (branch or "all").strip().lower()
    if raw not in {"all", "01", "02", ""}:
        raise ValueError("branch deve ser all, 01 ou 02.")
    branch_code = raw if raw in {"01", "02"} else None
    warehouse_code = (warehouse or "").strip() or None
    if warehouse_code is not None and (len(warehouse_code) > 10 or not warehouse_code.isalnum()):
        raise ValueError("Armazém inválido.")
    return branch_code, warehouse_code


def _bucket_start(day: date, granularity: str) -> date:
    if granularity == "day":
        return day
    if granularity == "week":
        return day - timedelta(days=day.weekday())
    if granularity == "month":
        return date(day.year, day.month, 1)
    if granularity == "year":
        return date(day.year, 1, 1)
    raise ValueError("Granularidade inválida: use day, week, month ou year.")


@dataclass(frozen=True)
class InventoryTvPeriod:
    reference: date
    start: date
    end: date
    granularity: str
    custom: bool


def _selected_period(
    *,
    granularity: str,
    as_of: str | None,
    start_date: str | None,
    end_date: str | None,
    default_window: str,
) -> InventoryTvPeriod:
    """Valida recorte; o gateway TV traduz presets para start_date/end_date.

    Fim futuro de um preset _full é limitado a hoje/referência, para não
    incluir lançamentos com data futura como se já tivessem ocorrido.
    """
    if granularity not in _GRANULARITIES:
        raise ValueError("Granularidade inválida: use day, week, month ou year.")
    if bool(start_date) != bool(end_date):
        raise ValueError("Informe start_date e end_date juntos.")
    today = _reference_date(None)

    if start_date:
        try:
            start = date.fromisoformat(start_date)
            requested_end = date.fromisoformat(end_date or "")
        except (TypeError, ValueError) as exc:
            raise ValueError("Datas devem estar no formato YYYY-MM-DD.") from exc
        if start < _MINIMUM_DATE or start > today:
            raise ValueError("Data inicial fora do período permitido.")
        if requested_end < start:
            raise ValueError("end_date não pode ser anterior a start_date.")
        if (requested_end - start).days >= _MAX_DAYS:
            raise ValueError("O período consultado pode ter no máximo 366 dias.")
        reference = _reference_date(as_of) if as_of else min(requested_end, today)
        effective_end = min(requested_end, reference)
        if effective_end < start:
            raise ValueError("O período está depois da data de referência.")
        return InventoryTvPeriod(reference, start, effective_end, granularity, True)

    reference = _reference_date(as_of)
    basis = granularity if default_window == "granularity" else default_window
    start = max(_bucket_start(reference, basis), _MINIMUM_DATE)
    return InventoryTvPeriod(reference, start, reference, granularity, False)


def _bucket_key(day: date, granularity: str) -> str:
    if granularity == "month":
        return day.strftime("%Y-%m")
    if granularity == "year":
        return str(day.year)
    return day.isoformat()


def _bucket_range(period: InventoryTvPeriod) -> list[str]:
    """Intervalos completos, com pontos vazios para gráficos sem lacunas."""
    result = []
    current = _bucket_start(period.start, period.granularity)
    while current <= period.end:
        result.append(_bucket_key(current, period.granularity))
        if period.granularity == "day":
            current += timedelta(days=1)
        elif period.granularity == "week":
            current += timedelta(days=7)
        elif period.granularity == "month":
            current = (
                date(current.year + 1, 1, 1) if current.month == 12
                else date(current.year, current.month + 1, 1)
            )
        else:
            current = date(current.year + 1, 1, 1)
    return result


def _point(periodo: str, values: dict[str, Any]) -> dict[str, Any]:
    return {
        "periodo": periodo,
        "month": periodo if len(periodo) == 7 else None,
        "gross_value_brl": _round_money(values.get("gross_value")),
        "net_value_brl": _round_money(values.get("net_value")),
        "shortage_value_brl": _round_money(values.get("shortage_value")),
        "surplus_value_brl": _round_money(values.get("surplus_value")),
        "adjustment_count": int(values.get("adjustment_count") or 0),
        "shortage_count": int(values.get("shortage_count") or 0),
        "surplus_count": int(values.get("surplus_count") or 0),
    }


class InventoryAdjustmentsTvService:
    """Contrato de TV: bases e classificação herdadas do Suprimentos."""

    def __init__(self, *, summary_use_case=None, weekly_repository=None):
        self._summary = summary_use_case or build_get_inventory_adjustments_summary_use_case()
        self._weekly = weekly_repository or InventoryAdjustmentsTvRepository()

    def _query_summary(
        self, *, start: date, end: date, branch: str | None,
        warehouse: str | None,
    ) -> dict[str, Any]:
        return self._summary.execute(
            InventoryAdjustmentsRequest(
                start_date=start.isoformat(),
                end_date=end.isoformat(),
                branch=branch,
                warehouse=warehouse,
            )
        )

    def _year_data(
        self, *, reference: date, branch: str | None, warehouse: str | None,
    ) -> dict[str, Any]:
        return self._query_summary(
            start=date(reference.year, 1, 1),
            end=reference,
            branch=branch,
            warehouse=warehouse,
        )

    def summary(
        self, *, as_of: str | None = None, branch: str | None = None,
        warehouse: str | None = None, granularity: str = "month",
        start_date: str | None = None, end_date: str | None = None,
    ) -> dict[str, Any]:
        period = _selected_period(
            granularity=granularity, as_of=as_of, start_date=start_date,
            end_date=end_date, default_window="granularity",
        )
        branch_code, warehouse_code = _filters(branch, warehouse)
        year_data = self._year_data(
            reference=period.reference, branch=branch_code, warehouse=warehouse_code,
        )
        year = year_data.get("summary") or {}
        month = next(
            (row for row in year_data.get("by_month") or []
             if row.get("month") == period.reference.strftime("%Y-%m")),
            {},
        )
        if period.start == date(period.reference.year, 1, 1) and period.end == period.reference:
            selected = year
        elif (
            period.start == date(period.reference.year, period.reference.month, 1)
            and period.end == period.reference
        ):
            selected = month
        else:
            selected = self._query_summary(
                start=period.start, end=period.end,
                branch=branch_code, warehouse=warehouse_code,
            ).get("summary") or {}
        payload: dict[str, Any] = {
            "source": "supplies_inventory_adjustments_sd3",
            "as_of": period.reference.isoformat(),
            "year": period.reference.year,
            "month": period.reference.strftime("%Y-%m"),
            "branch": branch_code or "all",
            "warehouse": warehouse_code,
            "year_start": date(period.reference.year, 1, 1).isoformat(),
            "month_start": date(period.reference.year, period.reference.month, 1).isoformat(),
            "period_start": period.start.isoformat(),
            "period_end": period.end.isoformat(),
            "granularity": granularity,
            "valuation_note": _VALUATION_NOTE,
            "divergence_definition": "gross_shortages_plus_surpluses",
        }
        for key in _MEASURE_KEYS:
            for prefix, row in (("year", year), ("month", month), ("period", selected)):
                payload[f"{prefix}_{key}_brl"] = _round_money(row.get(key))
        for key in _COUNT_KEYS:
            for prefix, row in (("year", year), ("month", month), ("period", selected)):
                payload[f"{prefix}_{key}"] = int(row.get(key) or 0)
        for prefix in ("year", "month", "period"):
            payload[f"{prefix}_divergence_brl"] = payload[f"{prefix}_gross_value_brl"]
        return payload

    def monthly_series(
        self, *, as_of: str | None = None, branch: str | None = None,
        warehouse: str | None = None, granularity: str = "month",
        start_date: str | None = None, end_date: str | None = None,
    ) -> dict[str, Any]:
        period = _selected_period(
            granularity=granularity, as_of=as_of, start_date=start_date,
            end_date=end_date, default_window="year",
        )
        branch_code, warehouse_code = _filters(branch, warehouse)
        if granularity in {"month", "year"}:
            data = self._query_summary(
                start=period.start, end=period.end,
                branch=branch_code, warehouse=warehouse_code,
            )
            monthly = {str(row.get("month") or ""): row for row in data.get("by_month") or []}
            if granularity == "month":
                buckets = monthly
            else:
                buckets: dict[str, dict[str, Any]] = {}
                for month, row in monthly.items():
                    key = month[:4]
                    target = buckets.setdefault(key, {})
                    for value_key in (*_MEASURE_KEYS, *_COUNT_KEYS):
                        target[value_key] = Decimal(str(target.get(value_key) or 0)) + Decimal(
                            str(row.get(value_key) or 0)
                        )
        else:
            # Dia e semana não podem ser inferidos de um resumo mensal.
            raw = self._weekly.fetch_granular_series(
                date_start=period.start.strftime("%Y%m%d"),
                date_end_exclusive=(period.end + timedelta(days=1)).strftime("%Y%m%d"),
                branch=branch_code,
                warehouse=warehouse_code,
                granularity=granularity,
            )
            buckets = {}
            for row in raw:
                bucket = row.get("bucket") or ""
                if granularity == "day" and len(bucket) == 8:
                    key = f"{bucket[:4]}-{bucket[4:6]}-{bucket[6:8]}"
                elif granularity == "week" and len(bucket) == 8:
                    key = f"{bucket[:4]}-{bucket[4:6]}-{bucket[6:8]}"
                else:
                    continue
                buckets[key] = row
        return {
            "source": "supplies_inventory_adjustments_sd3",
            "as_of": period.reference.isoformat(),
            "branch": branch_code or "all",
            "warehouse": warehouse_code,
            "period_start": period.start.isoformat(),
            "period_end": period.end.isoformat(),
            "granularity": granularity,
            "divergence_definition": "gross_shortages_plus_surpluses",
            "items": [_point(key, buckets.get(key) or {}) for key in _bucket_range(period)],
            "valuation_note": _VALUATION_NOTE,
        }

    def weekly_items(
        self, *, as_of: str | None = None, branch: str | None = None,
        warehouse: str | None = None, top_limit: int = 10,
        granularity: str = "week", start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        period = _selected_period(
            granularity=granularity, as_of=as_of, start_date=start_date,
            end_date=end_date, default_window="granularity",
        )
        branch_code, warehouse_code = _filters(branch, warehouse)
        result = self._weekly.fetch_weekly_product_divergences(
            date_start=period.start.strftime("%Y%m%d"),
            date_end_exclusive=(period.end + timedelta(days=1)).strftime("%Y%m%d"),
            branch=branch_code,
            warehouse=warehouse_code,
            top_limit=top_limit,
        )
        return {
            "source": "supplies_inventory_adjustments_sd3",
            "as_of": period.reference.isoformat(),
            "branch": branch_code or "all",
            "warehouse": warehouse_code,
            # Um produto por filial, com compensação física e financeira.
            "granularity": granularity,
            "item_grain": "branch_product",
            "period_start": period.start.isoformat(),
            "period_end": period.end.isoformat(),
            "week_start": period.start.isoformat() if granularity == "week" else None,
            "week_end": period.end.isoformat() if granularity == "week" else None,
            "scope": "selected_period",
            "valuation_note": _VALUATION_NOTE,
            **result,
        }
