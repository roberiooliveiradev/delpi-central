"""Projeções estáveis para o painel de TV do GR Diário (GLPI #1598).

Usa o mesmo caso de uso e o mesmo repository canônicos da consulta
/supplies/inventory-adjustments/summary. Não troca falta por sobra nem faz
netting para determinar a divergência; o líquido é medida adicional.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from zoneinfo import ZoneInfo

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
_BRAZIL_TZ = ZoneInfo("America/Sao_Paulo")
_MINIMUM_DATE = date(2023, 1, 1)
_MEASURE_KEYS = (
    "gross_value",
    "net_value",
    "shortage_value",
    "surplus_value",
)
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


class InventoryAdjustmentsTvService:
    """Contratos exclusivos para TV; nenhum novo critério fiscal/contábil."""

    def __init__(self, *, summary_use_case=None, weekly_repository=None):
        self._summary = summary_use_case or build_get_inventory_adjustments_summary_use_case()
        self._weekly = weekly_repository or InventoryAdjustmentsTvRepository()

    def _year_data(
        self, *, reference: date, branch: str | None, warehouse: str | None
    ) -> dict[str, Any]:
        return self._summary.execute(
            InventoryAdjustmentsRequest(
                start_date=date(reference.year, 1, 1).isoformat(),
                end_date=reference.isoformat(),
                branch=branch,
                warehouse=warehouse,
            )
        )

    @staticmethod
    def _months(result: dict[str, Any], reference: date) -> list[dict[str, Any]]:
        existing = {
            str(item.get("month")): item for item in result.get("by_month") or []
        }
        months = []
        for month in range(1, reference.month + 1):
            name = f"{reference.year:04d}-{month:02d}"
            values = existing.get(name) or {}
            months.append({
                "periodo": name,
                "month": name,
                "gross_value_brl": _round_money(values.get("gross_value")),
                "net_value_brl": _round_money(values.get("net_value")),
                "shortage_value_brl": _round_money(values.get("shortage_value")),
                "surplus_value_brl": _round_money(values.get("surplus_value")),
                "adjustment_count": int(values.get("adjustment_count") or 0),
                "shortage_count": int(values.get("shortage_count") or 0),
                "surplus_count": int(values.get("surplus_count") or 0),
            })
        return months

    def summary(
        self, *, as_of: str | None = None, branch: str | None = None,
        warehouse: str | None = None,
    ) -> dict[str, Any]:
        reference = _reference_date(as_of)
        branch_code, warehouse_code = _filters(branch, warehouse)
        data = self._year_data(
            reference=reference, branch=branch_code, warehouse=warehouse_code,
        )
        year = data.get("summary") or {}
        month = next(
            (item for item in data.get("by_month") or []
             if item.get("month") == reference.strftime("%Y-%m")),
            {},
        )
        payload: dict[str, Any] = {
            "source": "supplies_inventory_adjustments_sd3",
            "as_of": reference.isoformat(),
            "year": reference.year,
            "month": reference.strftime("%Y-%m"),
            "branch": branch_code or "all",
            "warehouse": warehouse_code,
            "year_start": date(reference.year, 1, 1).isoformat(),
            "month_start": date(reference.year, reference.month, 1).isoformat(),
            "valuation_note": _VALUATION_NOTE,
            "divergence_definition": "gross_shortages_plus_surpluses",
        }
        for src in _MEASURE_KEYS:
            payload[f"year_{src}_brl"] = _round_money(year.get(src))
            payload[f"month_{src}_brl"] = _round_money(month.get(src))
        for src in _COUNT_KEYS:
            payload[f"year_{src}"] = int(year.get(src) or 0)
            payload[f"month_{src}"] = int(month.get(src) or 0)
        # Alias explícito para o KPI solicitado: valor absoluto (falta + sobra).
        payload["year_divergence_brl"] = payload["year_gross_value_brl"]
        payload["month_divergence_brl"] = payload["month_gross_value_brl"]
        return payload

    def monthly_series(
        self, *, as_of: str | None = None, branch: str | None = None,
        warehouse: str | None = None,
    ) -> dict[str, Any]:
        reference = _reference_date(as_of)
        branch_code, warehouse_code = _filters(branch, warehouse)
        data = self._year_data(
            reference=reference, branch=branch_code, warehouse=warehouse_code,
        )
        return {
            "source": "supplies_inventory_adjustments_sd3",
            "as_of": reference.isoformat(),
            "branch": branch_code or "all",
            "warehouse": warehouse_code,
            "granularity": "month",
            "divergence_definition": "gross_shortages_plus_surpluses",
            "items": self._months(data, reference),
            "valuation_note": _VALUATION_NOTE,
        }

    def weekly_items(
        self, *, as_of: str | None = None, branch: str | None = None,
        warehouse: str | None = None, top_limit: int = 10,
    ) -> dict[str, Any]:
        reference = _reference_date(as_of)
        branch_code, warehouse_code = _filters(branch, warehouse)
        monday = reference - timedelta(days=reference.weekday())
        end_exclusive = reference + timedelta(days=1)
        result = self._weekly.fetch_weekly_product_divergences(
            date_start=monday.strftime("%Y%m%d"),
            date_end_exclusive=end_exclusive.strftime("%Y%m%d"),
            branch=branch_code,
            warehouse=warehouse_code,
            top_limit=top_limit,
        )
        return {
            "source": "supplies_inventory_adjustments_sd3",
            "as_of": reference.isoformat(),
            "branch": branch_code or "all",
            "warehouse": warehouse_code,
            "granularity": "branch_product_warehouse_nature",
            "week_start": monday.isoformat(),
            "week_end": reference.isoformat(),
            "scope": "current_iso_week_monday_to_reference",
            "valuation_note": _VALUATION_NOTE,
            **result,
        }
