from __future__ import annotations

from dataclasses import dataclass

from si_app.application.services.strategic_indicators.period_resolution import (
    ResolvedPeriod,
)
from si_app.infrastructure.gateways.delpi_commercial_gateway import DelpiCommercialGateway
from si_app.infrastructure.gateways.delpi_financial_gateway import DelpiFinancialGateway


MATRIX_BRANCH_CODE = "01"
BRANCH_BRANCH_CODE = "02"
DEFAULT_HEAD_OFFICE_TARGET = 1.0
DEFAULT_BRANCH_TARGET = 1.0


@dataclass(frozen=True)
class CommercialMetricsSnapshot:
    start_date: str | None
    end_date: str | None
    matrix_rol_value: float | None
    branch_rol_value: float | None
    matrix_weg_rol_value: float | None
    branch_weg_rol_value: float | None
    matrix_new_business_rol_value: float | None
    branch_new_business_rol_value: float | None
    sales_conversion_rate_pct: float | None
    sales_order_otd_pct: float | None
    new_business_rol_pct: float | None
    requested_branch: str | None = None


class CommercialMetricsSnapshotService:
    def __init__(
        self,
        *,
        commercial_gateway: DelpiCommercialGateway,
        financial_gateway: DelpiFinancialGateway,
        head_office_target: float = DEFAULT_HEAD_OFFICE_TARGET,
        branch_target: float = DEFAULT_BRANCH_TARGET,
    ) -> None:
        self._commercial_gateway = commercial_gateway
        self._financial_gateway = financial_gateway
        self._head_office_target = head_office_target
        self._branch_target = branch_target
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
            branch=MATRIX_BRANCH_CODE,
            start_date=start_date,
            end_date=end_date,
        )
        branch_rol_value = self._load_rol_value(
            branch=BRANCH_BRANCH_CODE,
            start_date=start_date,
            end_date=end_date,
        )
        matrix_weg_rol_value, matrix_new_business_rol_value = (
            self._load_segment_rol_values(
                branch=MATRIX_BRANCH_CODE,
                start_date=start_date,
                end_date=end_date,
            )
        )
        branch_weg_rol_value, branch_new_business_rol_value = (
            self._load_segment_rol_values(
                branch=BRANCH_BRANCH_CODE,
                start_date=start_date,
                end_date=end_date,
            )
        )

        sales_conversion_result = self._commercial_gateway.get_sales_conversion_rate(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )
        new_business_rol_result = self._commercial_gateway.get_new_business_rol_pct(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )
        sales_order_otd_result = self._commercial_gateway.get_sales_order_otd(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
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
            matrix_weg_rol_value=(
                round(matrix_weg_rol_value, 2)
                if matrix_weg_rol_value is not None
                else None
            ),
            branch_weg_rol_value=(
                round(branch_weg_rol_value, 2)
                if branch_weg_rol_value is not None
                else None
            ),
            matrix_new_business_rol_value=(
                round(matrix_new_business_rol_value, 2)
                if matrix_new_business_rol_value is not None
                else None
            ),
            branch_new_business_rol_value=(
                round(branch_new_business_rol_value, 2)
                if branch_new_business_rol_value is not None
                else None
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
        branch: str,
        start_date: str | None,
        end_date: str | None,
    ) -> float | None:
        rol_result = self._financial_gateway.get_rol(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )
        return self._extract_number(rol_result, ["rol"])

    def _load_segment_rol_values(
        self,
        *,
        branch: str,
        start_date: str | None,
        end_date: str | None,
    ) -> tuple[float | None, float | None]:
        segment_result = self._commercial_gateway.get_new_business_rol_pct(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )
        weg_rol = self._extract_number(segment_result, ["weg_rol"])
        new_business_rol = self._extract_number(segment_result, ["new_business_rol"])
        return weg_rol, new_business_rol

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
