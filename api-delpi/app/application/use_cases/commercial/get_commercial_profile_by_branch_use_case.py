"""Commercial profile by branch — long-form radar/table of four existing KPIs.

Reuses GetSalesOrderOtdUseCase, GetSalesConversionRateUseCase,
GetNewBusinessRolPctUseCase and GetCommercialRolSummaryUseCase (+ SI goal
enrichment for rol_target_pct). Does not reimplement formulas or SQL.
"""

from __future__ import annotations

from typing import Any, Optional, Sequence

from app.application.dto.commercial.get_commercial_profile_by_branch_request import (
    GetCommercialProfileByBranchRequest,
)
from app.application.dto.commercial.new_business_rol_pct_request import (
    NewBusinessRolPctRequest,
)
from app.application.dto.commercial.sales_conversion_rate_request import (
    SalesConversionRateRequest,
)
from app.application.dto.commercial.sales_order_otd_request import SalesOrderOtdRequest
from app.application.services.strategic_indicators import (
    dashboard_goal_source_keys as goal_keys,
)
from app.application.services.strategic_indicators.dashboard_goals_service import (
    DashboardGoalsService,
    get_dashboard_goals_service,
)
from app.application.shared.numeric_parsing import to_optional_float
from app.application.use_cases.commercial.get_commercial_rol_summary_use_case import (
    GetCommercialRolSummaryUseCase,
)
from app.application.use_cases.commercial.get_new_business_rol_pct_use_case import (
    GetNewBusinessRolPctUseCase,
)
from app.application.use_cases.commercial.get_sales_conversion_rate_use_case import (
    GetSalesConversionRateUseCase,
)
from app.application.use_cases.commercial.get_sales_order_otd_use_case import (
    GetSalesOrderOtdUseCase,
)
from app.domain.totvs.protheus_branches import (
    PROTHEUS_BRANCH_CODES,
    branch_short_label,
    normalize_branch_code,
    optional_concrete_branch,
)

METRIC_OTD = "otd"
METRIC_CONVERSION = "conversion"
METRIC_NEW_BUSINESS = "new_business"
METRIC_ROL_ATTAINMENT = "rol_attainment"

METRIC_ORDER: tuple[str, ...] = (
    METRIC_OTD,
    METRIC_CONVERSION,
    METRIC_NEW_BUSINESS,
    METRIC_ROL_ATTAINMENT,
)

METRIC_LABELS: dict[str, str] = {
    METRIC_OTD: "OTD",
    METRIC_CONVERSION: "Conversão",
    METRIC_NEW_BUSINESS: "Novos negócios",
    METRIC_ROL_ATTAINMENT: "Atingimento ROL",
}


def _to_iso_date(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    raw = str(value).strip()
    if len(raw) == 8 and raw.isdigit():
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
    return raw


class GetCommercialProfileByBranchUseCase:
    def __init__(
        self,
        *,
        sales_order_otd_use_case: GetSalesOrderOtdUseCase,
        sales_conversion_rate_use_case: GetSalesConversionRateUseCase,
        new_business_rol_pct_use_case: GetNewBusinessRolPctUseCase,
        commercial_rol_summary_use_case: GetCommercialRolSummaryUseCase,
        dashboard_goals_service: DashboardGoalsService | None = None,
    ) -> None:
        self._otd = sales_order_otd_use_case
        self._conversion = sales_conversion_rate_use_case
        self._new_business = new_business_rol_pct_use_case
        self._rol_summary = commercial_rol_summary_use_case
        self._goals = dashboard_goals_service

    def execute(self, request: GetCommercialProfileByBranchRequest) -> dict[str, Any]:
        start_iso = _to_iso_date(request.start_date)
        end_iso = _to_iso_date(request.end_date)
        branches = self._resolve_branches(request.branch)

        items: list[dict[str, Any]] = []
        for branch in branches:
            values = self._metric_values_for_branch(
                branch=branch,
                start_date=start_iso,
                end_date=end_iso,
                customer_segment=request.customer_segment,
                customer_codes=request.customer_codes,
            )
            label = branch_short_label(branch)
            for metric in METRIC_ORDER:
                items.append(
                    {
                        "branch": branch,
                        "branch_label": label,
                        "metric": metric,
                        "metric_label": METRIC_LABELS[metric],
                        "value_pct": values[metric],
                    }
                )

        return {
            "start_date": start_iso or request.start_date,
            "end_date": end_iso or request.end_date,
            "items": items,
            "summary": {
                "items_count": len(items),
                "branches_count": len(branches),
            },
        }

    @staticmethod
    def _resolve_branches(branch: Optional[str]) -> tuple[str, ...]:
        concrete = optional_concrete_branch(branch)
        if concrete is None:
            return PROTHEUS_BRANCH_CODES
        return (normalize_branch_code(concrete),)

    def _metric_values_for_branch(
        self,
        *,
        branch: str,
        start_date: Optional[str],
        end_date: Optional[str],
        customer_segment: Optional[str],
        customer_codes: Optional[list[str]],
    ) -> dict[str, Optional[float]]:
        otd = self._otd.execute(
            SalesOrderOtdRequest(
                branch=branch,
                start_date=start_date,
                end_date=end_date,
                customer_segment=customer_segment,
                customer_codes=customer_codes,
            )
        )
        conversion = self._conversion.execute(
            SalesConversionRateRequest(
                branch=branch,
                start_date=start_date,
                end_date=end_date,
                customer_segment=customer_segment,
                customer_codes=customer_codes,
            )
        )
        new_business = self._new_business.execute(
            NewBusinessRolPctRequest(
                branch=branch,
                start_date=start_date,
                end_date=end_date,
                customer_segment=customer_segment,
                customer_codes=customer_codes,
            )
        )
        rol_payload = self._rol_summary.execute(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
            customer_segment=customer_segment,
            customer_codes=customer_codes,
        )
        enriched_rol = self._attach_rol_goal(
            rol_payload,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )

        return {
            METRIC_OTD: to_optional_float(otd.get("sales_order_otd_pct")),
            METRIC_CONVERSION: to_optional_float(
                conversion.get("sales_conversion_rate_pct")
            ),
            METRIC_NEW_BUSINESS: to_optional_float(
                new_business.get("new_business_rol_pct")
            ),
            METRIC_ROL_ATTAINMENT: to_optional_float(
                enriched_rol.get("rol_target_pct")
            ),
        }

    def _attach_rol_goal(
        self,
        payload: dict[str, Any],
        *,
        start_date: Optional[str],
        end_date: Optional[str],
        branch: str,
    ) -> dict[str, Any]:
        """Same SI enrichment as get_commercial_rol_summary (rol_target_pct)."""
        service = self._goals or get_dashboard_goals_service()
        try:
            return service.attach_goal_fields(
                payload,
                source_key=goal_keys.COMMERCIAL_ROL,
                start_date=start_date,
                end_date=end_date,
                branch=branch,
                recompute_target_pct_from="rol",
            )
        except Exception:
            return payload


def profile_value_for_metric(
    items: Sequence[dict[str, Any]],
    *,
    branch: str,
    metric: str,
) -> Optional[float]:
    """Test helper — extract value_pct from long-form items."""
    for row in items:
        if row.get("branch") == branch and row.get("metric") == metric:
            return to_optional_float(row.get("value_pct"))
    return None
