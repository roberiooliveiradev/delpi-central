from __future__ import annotations

from dataclasses import dataclass

from si_app.application.dto.financial.get_rol_request import GetRolRequest
from si_app.application.dto.production.production_request import ProductionRequest
from si_app.application.use_cases.strategic_indicators.period_resolution import (
    ResolvedPeriod,
)
from si_app.domain.ports.financial.financial_query_repository_port import (
    FinancialQueryRepositoryPort,
)
from si_app.domain.ports.production.on_time_delivery_repository_port import (
    OnTimeDeliveryRepositoryPort,
)
from si_app.domain.ports.production.overall_equipment_effectiveness_repository_port import (
    OverallEquipmentEffectivenessRepositoryPort,
)
from si_app.infrastructure.gateways.delpi_production_gateway import (
    DelpiProductionSheetsGateway,
)
from si_app.shared.branch_filter import effective_query_branch


@dataclass(frozen=True)
class ProductionUnitMetricsSnapshot:
    branch: str | None
    start_date: str | None
    end_date: str | None
    rol: float
    average_direct_labor_cost: float
    average_production_cost: float
    average_depreciation_cost: float
    direct_labor_cost_pct: float | None
    production_cost_pct: float | None
    depreciation_pct: float | None
    oee_pct: float | None
    otd_pct: float | None


class ProductionMetricsSnapshotService:
    def __init__(
        self,
        *,
        production_sheets_gateway: DelpiProductionSheetsGateway,
        overall_equipment_effectiveness_repository: OverallEquipmentEffectivenessRepositoryPort,
        on_time_delivery_repository: OnTimeDeliveryRepositoryPort,
        financial_query_repository: FinancialQueryRepositoryPort,
    ) -> None:
        self._production_sheets_gateway = production_sheets_gateway
        self._overall_equipment_effectiveness_repository = (
            overall_equipment_effectiveness_repository
        )
        self._on_time_delivery_repository = on_time_delivery_repository
        self._financial_query_repository = financial_query_repository
        self._cache: dict[
            tuple[str | None, str | None, str | None],
            ProductionUnitMetricsSnapshot,
        ] = {}

    def get_unit_snapshot(
        self,
        *,
        branch: str,
        start_date: str | None,
        end_date: str | None,
    ) -> ProductionUnitMetricsSnapshot:
        effective_branch = effective_query_branch(branch)
        if not effective_branch:
            return self.get_consolidated_snapshot(
                start_date=start_date,
                end_date=end_date,
            )
        return self._build_snapshot(
            branch=effective_branch,
            start_date=start_date,
            end_date=end_date,
        )

    def get_snapshot_series(
        self,
        *,
        periods: list[ResolvedPeriod],
        branch: str | None = None,
    ) -> dict[str, ProductionUnitMetricsSnapshot]:
        result: dict[str, ProductionUnitMetricsSnapshot] = {}

        effective_branch = effective_query_branch(branch)

        for period in periods:
            key = (effective_branch, period.start_date, period.end_date)
            cached = self._cache.get(key)
            if cached is not None:
                result[period.competence] = cached
                continue

            if effective_branch:
                snapshot = self.get_unit_snapshot(
                    branch=effective_branch,
                    start_date=period.start_date,
                    end_date=period.end_date,
                )
            else:
                snapshot = self.get_consolidated_snapshot(
                    start_date=period.start_date,
                    end_date=period.end_date,
                )

            result[period.competence] = snapshot

        return result

    def get_consolidated_snapshot(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
    ) -> ProductionUnitMetricsSnapshot:
        return self._build_snapshot(
            branch=None,
            start_date=start_date,
            end_date=end_date,
        )

    def _build_snapshot(
        self,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> ProductionUnitMetricsSnapshot:
        effective_branch = effective_query_branch(branch)
        key = (effective_branch, start_date, end_date)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        production_request = ProductionRequest(
            branch=effective_branch,
            start_date=start_date,
            end_date=end_date,
        )
        rol_request = GetRolRequest(
            branch=effective_branch,
            start_date=start_date,
            end_date=end_date,
        )

        rol_payload = self._financial_query_repository.get_rol(rol_request)
        rol_value = self._rol_value(rol_payload)

        direct_labor_cost_pct = self._production_sheets_gateway.get_direct_labor_cost_pct(
            production_request
        )
        production_cost_pct = self._production_sheets_gateway.get_production_cost_pct(
            production_request
        )
        depreciation_pct = self._production_sheets_gateway.get_depreciation_pct(
            production_request
        )

        oee = self._overall_equipment_effectiveness_repository.get_overall_equipment_effectiveness(
            production_request
        )
        otd = self._on_time_delivery_repository.get_on_time_delivery(production_request)

        snapshot = ProductionUnitMetricsSnapshot(
            branch=effective_branch,
            start_date=start_date,
            end_date=end_date,
            rol=rol_value,
            average_direct_labor_cost=self._cost_from_pct(rol_value, direct_labor_cost_pct),
            average_production_cost=self._cost_from_pct(rol_value, production_cost_pct),
            average_depreciation_cost=self._cost_from_pct(rol_value, depreciation_pct),
            direct_labor_cost_pct=direct_labor_cost_pct,
            production_cost_pct=production_cost_pct,
            depreciation_pct=depreciation_pct,
            oee_pct=self._to_float(getattr(oee, "oee_pct", None)),
            otd_pct=self._to_float(getattr(otd, "on_time_delivery_pct", None)),
        )
        self._cache[key] = snapshot
        return snapshot

    def _cost_from_pct(self, rol: float, pct: float | None) -> float:
        if pct is None or not rol:
            return 0.0
        return rol * pct / 100

    def _rol_value(self, payload: dict) -> float:
        value = self._to_float(payload.get("rol"))
        if value is not None:
            return value
        return self._to_float(payload.get("rol_with_ipi")) or 0.0

    def _to_float(self, value) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
