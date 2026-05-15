from __future__ import annotations

from dataclasses import dataclass

from si_app.application.dto.supplies.get_cpv_request import GetCPVRequest
from si_app.application.dto.supplies.get_inventory_turnover_request import (
    GetInventoryTurnoverRequest,
)
from si_app.application.dto.supplies.get_otd_request import GetOTDRequest
from si_app.application.dto.supplies.get_stock_value_request import GetStockValueRequest
from si_app.application.use_cases.strategic_indicators.period_resolution import (
    ResolvedPeriod,
)
from si_app.application.use_cases.supplies.get_cpv_use_case import GetCPVUseCase
from si_app.application.use_cases.supplies.get_inventory_turnover_use_case import (
    GetInventoryTurnoverUseCase,
)
from si_app.application.use_cases.supplies.get_otd_use_case import GetOTDUseCase
from si_app.application.use_cases.supplies.get_stock_value_use_case import (
    GetStockValueUseCase,
)


@dataclass(frozen=True)
class SuppliesMetricsSnapshot:
    branch: str | None
    start_date: str | None
    end_date: str | None
    cpv_pct: float
    inventory_turnover_months: float
    otd_pct: float
    stock_value: float


class SuppliesMetricsSnapshotService:
    def __init__(
        self,
        *,
        get_cpv_use_case: GetCPVUseCase,
        get_inventory_turnover_use_case: GetInventoryTurnoverUseCase,
        get_otd_use_case: GetOTDUseCase,
        get_stock_value_use_case: GetStockValueUseCase,
    ) -> None:
        self._get_cpv_use_case = get_cpv_use_case
        self._get_inventory_turnover_use_case = get_inventory_turnover_use_case
        self._get_otd_use_case = get_otd_use_case
        self._get_stock_value_use_case = get_stock_value_use_case
        self._cache: dict[
            tuple[str | None, str | None, str | None],
            SuppliesMetricsSnapshot,
        ] = {}

    def get_snapshot(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        branch: str | None = None,
    ) -> SuppliesMetricsSnapshot:
        key = (branch, start_date, end_date)
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
    ) -> dict[str, SuppliesMetricsSnapshot]:
        result: dict[str, SuppliesMetricsSnapshot] = {}

        for period in periods:
            key = (branch, period.start_date, period.end_date)
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
    ) -> SuppliesMetricsSnapshot:
        cpv_result = self._get_cpv_use_case.execute(
            GetCPVRequest(
                start_date=start_date,
                end_date=end_date,
                branch=branch,
            )
        )
        inventory_turnover_result = self._get_inventory_turnover_use_case.execute(
            GetInventoryTurnoverRequest(
                start_date=start_date,
                end_date=end_date,
                branch=branch,
                strict_idd_period=False,
            )
        )
        otd_result = self._get_otd_use_case.execute(
            GetOTDRequest(
                start_date=start_date,
                end_date=end_date,
                branch=branch,
            )
        )
        stock_value_result = self._get_stock_value_use_case.execute(
            GetStockValueRequest(
                branch=branch,
            )
        )

        cpv_payload = self._extract_payload(cpv_result)
        inventory_turnover_payload = self._extract_payload(inventory_turnover_result)
        otd_payload = self._extract_payload(otd_result)
        stock_value_payload = self._extract_payload(stock_value_result)

        cpv_data = self._extract_data(cpv_payload)
        inventory_turnover_data = self._extract_data(inventory_turnover_payload)
        otd_data = self._extract_data(otd_payload)
        stock_value_data = self._extract_data(stock_value_payload)

        cpv_summary = cpv_data.get("summary", {})
        inventory_turnover_summary = inventory_turnover_data.get("summary", {})
        otd_summary = otd_data.get("summary", {})
        stock_value_summary = stock_value_data.get("summary", {})

        return SuppliesMetricsSnapshot(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
            cpv_pct=self._to_float(cpv_summary.get("cpv_percentage")),
            inventory_turnover_months=self._to_float(
                inventory_turnover_summary.get("inventory_turnover_months")
            ),
            otd_pct=self._to_float(otd_summary.get("otd_percentage")),
            stock_value=self._to_float(stock_value_summary.get("total_stock_value")),
        )

    def _extract_payload(self, result):
        return result.to_dict() if hasattr(result, "to_dict") else result

    def _extract_data(self, payload: dict) -> dict:
        return payload.get("data", payload)

    def _to_float(self, value) -> float:
        if value is None:
            return 0.0
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0