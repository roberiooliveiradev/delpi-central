from __future__ import annotations

from dataclasses import dataclass

from si_app.application.dto.commercial.commercial_target_request import CommercialTargetRequest
from si_app.application.dto.commercial.new_business_rol_pct_request import (
    NewBusinessRolPctRequest,
)
from si_app.application.dto.commercial.sales_conversion_rate_request import (
    SalesConversionRateRequest,
)
from si_app.application.dto.commercial.sales_order_otd_request import SalesOrderOtdRequest
from si_app.application.use_cases.commercial.get_new_business_rol_pct_use_case import (
    GetNewBusinessRolPctUseCase,
)
from si_app.application.use_cases.commercial.get_sales_order_otd_use_case import (
    GetSalesOrderOtdUseCase,
)
from si_app.application.use_cases.commercial.get_rol_target_pct_use_case import (
    GetRolTargetPctUseCase,
)
from si_app.application.use_cases.commercial.get_sales_conversion_rate_use_case import (
    GetSalesConversionRateUseCase,
)
from si_app.application.use_cases.strategic_indicators.period_resolution import (
    ResolvedPeriod,
)


MATRIX_BRANCH_CODE = "01"
BRANCH_BRANCH_CODE = "02"


@dataclass(frozen=True)
class CommercialMetricsSnapshot:
    start_date: str | None
    end_date: str | None
    matrix_rol_value: float | None
    branch_rol_value: float | None
    sales_conversion_rate_pct: float | None
    sales_order_otd_pct: float | None
    new_business_rol_pct: float | None
    requested_branch: str | None = None


class CommercialMetricsSnapshotService:
    def __init__(
        self,
        *,
        head_office_rol_target_use_case: GetRolTargetPctUseCase,
        branch_rol_target_use_case: GetRolTargetPctUseCase,
        sales_conversion_rate_use_case: GetSalesConversionRateUseCase,
        new_business_rol_pct_use_case: GetNewBusinessRolPctUseCase,
        sales_order_otd_use_case: GetSalesOrderOtdUseCase,
    ) -> None:
        self._head_office_rol_target_use_case = head_office_rol_target_use_case
        self._branch_rol_target_use_case = branch_rol_target_use_case
        self._sales_conversion_rate_use_case = sales_conversion_rate_use_case
        self._new_business_rol_pct_use_case = new_business_rol_pct_use_case
        self._sales_order_otd_use_case = sales_order_otd_use_case
        self._cache: dict[
            tuple[str | None, str | None, str | None],
            CommercialMetricsSnapshot,
        ] = {}

    def get_snapshot(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        branch: str | None = None,
    ) -> CommercialMetricsSnapshot:
        key = (start_date, end_date, branch)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        snapshot = self._build_snapshot(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )
        self._cache[key] = snapshot
        return snapshot

    def get_snapshot_series(
        self,
        *,
        periods: list[ResolvedPeriod],
        branch: str | None = None,
    ) -> dict[str, CommercialMetricsSnapshot]:
        result: dict[str, CommercialMetricsSnapshot] = {}

        for period in periods:
            key = (period.start_date, period.end_date, branch)
            cached = self._cache.get(key)
            if cached is not None:
                result[period.competence] = cached
                continue

            snapshot = self._build_snapshot(
                start_date=period.start_date,
                end_date=period.end_date,
                branch=branch,
            )
            self._cache[key] = snapshot
            result[period.competence] = snapshot

        return result

    def _build_snapshot(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        branch: str | None,
    ) -> CommercialMetricsSnapshot:
        matrix_rol_value = self._load_rol_value(
            use_case=self._head_office_rol_target_use_case,
            branch=MATRIX_BRANCH_CODE,
            start_date=start_date,
            end_date=end_date,
        )
        branch_rol_value = self._load_rol_value(
            use_case=self._branch_rol_target_use_case,
            branch=BRANCH_BRANCH_CODE,
            start_date=start_date,
            end_date=end_date,
        )

        sales_conversion_result = self._sales_conversion_rate_use_case.execute(
            SalesConversionRateRequest(
                branch=branch,
                start_date=start_date,
                end_date=end_date,
            )
        )
        new_business_rol_result = self._new_business_rol_pct_use_case.execute(
            NewBusinessRolPctRequest(
                branch=branch,
                start_date=start_date,
                end_date=end_date,
            )
        )
        sales_order_otd_result = self._sales_order_otd_use_case.execute(
            SalesOrderOtdRequest(
                branch=branch,
                start_date=start_date,
                end_date=end_date,
            )
        )

        sales_conversion_rate_pct = self._extract_number(
            sales_conversion_result,
            ["sales_conversion_rate_pct"],
        )
        new_business_rol_pct = self._extract_number(
            new_business_rol_result,
            ["new_business_rol_pct"],
        )
        sales_order_otd_pct = self._extract_number(
            sales_order_otd_result,
            ["sales_order_otd_pct"],
        )

        return CommercialMetricsSnapshot(
            start_date=start_date,
            end_date=end_date,
            matrix_rol_value=(
                round(matrix_rol_value, 2) if matrix_rol_value is not None else None
            ),
            branch_rol_value=(
                round(branch_rol_value, 2) if branch_rol_value is not None else None
            ),
            sales_conversion_rate_pct=(
                round(sales_conversion_rate_pct, 2)
                if sales_conversion_rate_pct is not None
                else None
            ),
            sales_order_otd_pct=(
                round(sales_order_otd_pct, 2)
                if sales_order_otd_pct is not None
                else None
            ),
            new_business_rol_pct=(
                round(new_business_rol_pct, 2)
                if new_business_rol_pct is not None
                else None
            ),
            requested_branch=branch,
        )

    def _load_rol_value(
        self,
        *,
        use_case: GetRolTargetPctUseCase,
        branch: str,
        start_date: str | None,
        end_date: str | None,
    ) -> float | None:
        result = use_case.execute(
            CommercialTargetRequest(
                branch=branch,
                start_date=start_date,
                end_date=end_date,
            )
        )
        return self._extract_number(result, ["rol"])

    def _extract_number(self, payload, candidate_keys: list[str]) -> float | None:
        if payload is None:
            return None

        if isinstance(payload, dict):
            for key in candidate_keys:
                value = payload.get(key)
                number = self._to_float(value)
                if number is not None:
                    return number

        return None

    def _to_float(self, value) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None