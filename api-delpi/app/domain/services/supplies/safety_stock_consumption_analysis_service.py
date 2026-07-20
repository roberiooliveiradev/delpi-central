"""Cálculo de consumo médio e estoque de segurança sugerido (lead time BZ_PE)."""

from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Any

from app.domain.services.supplies.safety_stock_business_days_service import (
    SafetyStockBusinessDaysService,
)
from app.domain.services.supplies.safety_stock_classification_service import TOLERANCE

ANALYSIS_CALENDAR_DAYS = 365
ANNUAL_COMPARISON_YEARS = 3
CONSUMPTION_WAREHOUSE = "99"
CONSUMPTION_MOVEMENT_TYPE = "999"

STATUS_BELOW = "below_suggested"
STATUS_ABOVE = "above_suggested"
STATUS_ADEQUATE = "adequate"
STATUS_INCONSISTENT = "inconsistent_data"

ALLOWED_ANALYSIS_STATUSES = frozenset(
    {
        STATUS_BELOW,
        STATUS_ABOVE,
        STATUS_ADEQUATE,
        STATUS_INCONSISTENT,
    }
)

# Adequado quando |atual − sugerido| ≤ max(tolerância absoluta, 5% do sugerido).
ADEQUATE_RATIO = 0.05


class SafetyStockConsumptionAnalysisService:
    """Transforma agregados SD3 + SBZ em indicadores gerenciais."""

    @staticmethod
    def resolve_period(*, as_of: date | None = None) -> tuple[date, date, int]:
        end = as_of or date.today()
        start = end - timedelta(days=ANALYSIS_CALENDAR_DAYS - 1)
        business_days = SafetyStockBusinessDaysService.count_inclusive(start, end)
        return start, end, business_days

    @staticmethod
    def resolve_annual_comparison_period(
        *,
        as_of: date | None = None,
        years: int = ANNUAL_COMPARISON_YEARS,
    ) -> tuple[date, date, list[int]]:
        """Jan/1 do (ano atual − years + 1) até a data de referência."""
        end = as_of or date.today()
        span = max(int(years), 1)
        year_list = list(range(end.year - span + 1, end.year + 1))
        start = date(year_list[0], 1, 1)
        return start, end, year_list

    @staticmethod
    def filter_monthly_series_for_period(
        monthly: list[dict[str, Any]],
        *,
        period_start: date,
        period_end: date,
    ) -> list[dict[str, Any]]:
        start_key = period_start.strftime("%Y%m")
        end_key = period_end.strftime("%Y%m")
        return [
            point
            for point in monthly
            if start_key <= str(point.get("year_month") or "") <= end_key
        ]

    @classmethod
    def build_annual_comparison(
        cls,
        monthly: list[dict[str, Any]],
        *,
        years: list[int],
        period_start: date,
        period_end: date,
    ) -> dict[str, Any]:
        """Pivot mês × ano para gráfico sazonal (eixo X = Jan–Dez)."""
        month_labels = (
            "Jan",
            "Fev",
            "Mar",
            "Abr",
            "Mai",
            "Jun",
            "Jul",
            "Ago",
            "Set",
            "Out",
            "Nov",
            "Dez",
        )
        year_keys = [str(year) for year in years]
        by_year_month: dict[tuple[int, int], float] = {}
        for point in monthly:
            raw = str(point.get("year_month") or "").strip()
            if len(raw) != 6 or not raw.isdigit():
                continue
            year = int(raw[0:4])
            month = int(raw[4:6])
            if year not in years or month < 1 or month > 12:
                continue
            by_year_month[(year, month)] = float(point.get("consumption_quantity") or 0)

        items: list[dict[str, Any]] = []
        for month in range(1, 13):
            values_by_year: dict[str, float | None] = {}
            for year in years:
                month_date = date(year, month, 1)
                if month_date > period_end.replace(day=1):
                    values_by_year[str(year)] = None
                elif (year, month) in by_year_month:
                    values_by_year[str(year)] = by_year_month[(year, month)]
                elif month_date < period_start.replace(day=1):
                    values_by_year[str(year)] = None
                else:
                    values_by_year[str(year)] = 0.0
            items.append(
                {
                    "month": month,
                    "month_label": month_labels[month - 1],
                    "values_by_year": values_by_year,
                }
            )

        return {
            "years": year_keys,
            "items": items,
            "total": len(items),
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
        }

    @classmethod
    def average_daily_consumption(
        cls,
        *,
        period_consumption: float,
        period_business_days: int,
    ) -> float:
        days = int(period_business_days or 0)
        if days <= 0:
            return 0.0
        return float(period_consumption or 0) / days

    @classmethod
    def lead_time_business_days(
        cls,
        *,
        lead_time_calendar_days: float | int | None,
        as_of: date | None = None,
    ) -> int:
        calendar_days = int(float(lead_time_calendar_days or 0))
        if calendar_days <= 0:
            return 0
        return SafetyStockBusinessDaysService.count_in_calendar_span(
            calendar_days,
            start=as_of or date.today(),
        )

    @classmethod
    def suggested_safety_stock(
        cls,
        *,
        average_daily_consumption: float,
        lead_time_business_days: int,
    ) -> float:
        avg = float(average_daily_consumption or 0)
        days = int(lead_time_business_days or 0)
        if avg <= 0 or days <= 0:
            return 0.0
        return float(math.ceil(avg * days))

    @classmethod
    def coverage_business_days(
        cls,
        *,
        available_stock: float,
        average_daily_consumption: float,
    ) -> float | None:
        avg = float(average_daily_consumption or 0)
        if avg <= 0:
            return None
        return float(available_stock or 0) / avg

    @classmethod
    def classify_suggestion_status(
        cls,
        *,
        current_safety_stock: float,
        suggested_safety_stock: float,
        period_consumption: float,
        lead_time_calendar_days: float | int | None,
        average_daily_consumption: float,
    ) -> str:
        lead = float(lead_time_calendar_days or 0)
        if (
            float(period_consumption or 0) <= 0
            or float(average_daily_consumption or 0) <= 0
            or lead <= 0
            or float(suggested_safety_stock or 0) <= 0
        ):
            return STATUS_INCONSISTENT

        current = float(current_safety_stock or 0)
        suggested = float(suggested_safety_stock or 0)
        band = max(TOLERANCE, suggested * ADEQUATE_RATIO)
        if abs(current - suggested) <= band:
            return STATUS_ADEQUATE
        if current < suggested:
            return STATUS_BELOW
        return STATUS_ABOVE

    @classmethod
    def enrich_row(
        cls,
        row: dict[str, Any],
        *,
        period_start: date,
        period_end: date,
        period_business_days: int,
        as_of: date | None = None,
    ) -> dict[str, Any]:
        period_consumption = float(row.get("period_consumption") or 0)
        available_stock = float(
            row.get("available_stock")
            if row.get("available_stock") is not None
            else (
                float(row.get("primary_stock") or 0)
                + float(row.get("warehouse_98_stock") or 0)
                + float(row.get("warehouse_99_stock") or 0)
            )
        )
        current_safety = float(row.get("safety_stock") or 0)
        lead_time = float(row.get("lead_time_days") or 0)

        avg = cls.average_daily_consumption(
            period_consumption=period_consumption,
            period_business_days=period_business_days,
        )
        lead_business = cls.lead_time_business_days(
            lead_time_calendar_days=lead_time,
            as_of=as_of or period_end,
        )
        suggested = cls.suggested_safety_stock(
            average_daily_consumption=avg,
            lead_time_business_days=lead_business,
        )
        coverage = cls.coverage_business_days(
            available_stock=available_stock,
            average_daily_consumption=avg,
        )
        status = cls.classify_suggestion_status(
            current_safety_stock=current_safety,
            suggested_safety_stock=suggested,
            period_consumption=period_consumption,
            lead_time_calendar_days=lead_time,
            average_daily_consumption=avg,
        )
        difference = current_safety - suggested
        difference_percent = (
            (difference / suggested) * 100.0 if suggested > 0 else None
        )
        quality_warnings: list[str] = []
        if period_consumption <= 0:
            quality_warnings.append("period_consumption_not_positive")
        if lead_time <= 0:
            quality_warnings.append("lead_time_missing_or_zero")
        if avg <= 0:
            quality_warnings.append("average_consumption_not_positive")

        return {
            **row,
            "available_stock": available_stock,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "period_calendar_days": ANALYSIS_CALENDAR_DAYS,
            "period_business_days": period_business_days,
            "period_consumption": period_consumption,
            "average_daily_consumption": avg,
            "lead_time_days": lead_time,
            "lead_time_business_days": lead_business,
            "suggested_safety_stock": suggested,
            "difference_quantity": difference,
            "difference_percent": difference_percent,
            "coverage_business_days": coverage,
            "analysis_status": status,
            "quality_warnings": quality_warnings,
            "has_inconsistent_data": status == STATUS_INCONSISTENT,
            "consumption_warehouse": CONSUMPTION_WAREHOUSE,
            "consumption_movement_type": CONSUMPTION_MOVEMENT_TYPE,
        }

    @classmethod
    def build_summary(cls, items: list[dict[str, Any]]) -> dict[str, Any]:
        below = sum(1 for item in items if item.get("analysis_status") == STATUS_BELOW)
        above = sum(1 for item in items if item.get("analysis_status") == STATUS_ABOVE)
        adequate = sum(
            1 for item in items if item.get("analysis_status") == STATUS_ADEQUATE
        )
        inconsistent = sum(
            1 for item in items if item.get("analysis_status") == STATUS_INCONSISTENT
        )
        net_impact = sum(float(item.get("difference_quantity") or 0) for item in items)
        return {
            "analyzed_items": len(items),
            "below_suggested": below,
            "above_suggested": above,
            "adequate": adequate,
            "inconsistent_data": inconsistent,
            "net_difference_quantity": net_impact,
        }

    @classmethod
    def build_calculation_memory(cls, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "formula": (
                "suggested_safety_stock = ceil("
                "average_daily_consumption × lead_time_business_days)"
            ),
            "average_daily_consumption_formula": (
                "period_consumption ÷ period_business_days"
            ),
            "period_consumption": item.get("period_consumption"),
            "period_business_days": item.get("period_business_days"),
            "average_daily_consumption": item.get("average_daily_consumption"),
            "lead_time_days": item.get("lead_time_days"),
            "lead_time_business_days": item.get("lead_time_business_days"),
            "suggested_safety_stock": item.get("suggested_safety_stock"),
            "current_safety_stock": item.get("safety_stock"),
            "available_stock": item.get("available_stock"),
            "coverage_business_days": item.get("coverage_business_days"),
            "consumption_filters": {
                "warehouse": CONSUMPTION_WAREHOUSE,
                "movement_type": CONSUMPTION_MOVEMENT_TYPE,
                "requires_production_order": True,
                "signed_quantity": True,
            },
            "quality_warnings": list(item.get("quality_warnings") or []),
        }
