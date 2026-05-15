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
from si_app.domain.ports.production.depreciation_repository_port import (
    DepreciationRepositoryPort,
)
from si_app.domain.ports.production.direct_labor_repository_port import (
    DirectLaborRepositoryPort,
)
from si_app.domain.ports.production.on_time_delivery_repository_port import (
    OnTimeDeliveryRepositoryPort,
)
from si_app.domain.ports.production.overall_equipment_effectiveness_repository_port import (
    OverallEquipmentEffectivenessRepositoryPort,
)
from si_app.domain.ports.production.production_cost_repository_port import (
    ProductionCostRepositoryPort,
)


@dataclass(frozen=True)
class ProductionUnitMetricsSnapshot:
    branch: str | None
    start_date: str | None
    end_date: str | None
    rol_with_ipi: float
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
        direct_labor_repository: DirectLaborRepositoryPort,
        production_cost_repository: ProductionCostRepositoryPort,
        depreciation_repository: DepreciationRepositoryPort,
        overall_equipment_effectiveness_repository: OverallEquipmentEffectivenessRepositoryPort,
        on_time_delivery_repository: OnTimeDeliveryRepositoryPort,
        financial_query_repository: FinancialQueryRepositoryPort,
    ) -> None:
        self._direct_labor_repository = direct_labor_repository
        self._production_cost_repository = production_cost_repository
        self._depreciation_repository = depreciation_repository
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
        return self._build_snapshot(
            branch=branch,
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

        for period in periods:
            key = (branch, period.start_date, period.end_date)
            cached = self._cache.get(key)
            if cached is not None:
                result[period.competence] = cached
                continue

            if branch:
                snapshot = self.get_unit_snapshot(
                    branch=branch,
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
        key = (None, start_date, end_date)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        production_request = ProductionRequest(
            branch=None,
            start_date=start_date,
            end_date=end_date,
        )

        direct_labor_items = self._direct_labor_repository.get_direct_labor_cost(
            production_request
        )
        production_cost_items = self._production_cost_repository.get_production_cost(
            production_request
        )
        depreciation_items = self._depreciation_repository.get_depreciation_cost(
            production_request
        )

        oee_rows = self._overall_equipment_effectiveness_repository.list_overall_equipment_effectiveness_by_branch(
            production_request
        )
        otd_rows = self._on_time_delivery_repository.list_on_time_delivery_by_branch(
            production_request
        )

        sheet_branches = self._resolve_branches_from_items(
            direct_labor_items,
            production_cost_items,
            depreciation_items,
        )
        totvs_branches = self._resolve_branches_from_rows(
            oee_rows,
            otd_rows,
        )

        branches = self._merge_branches(sheet_branches, totvs_branches)

        if not branches:
            snapshot = ProductionUnitMetricsSnapshot(
                branch=None,
                start_date=start_date,
                end_date=end_date,
                rol_with_ipi=0.0,
                average_direct_labor_cost=0.0,
                average_production_cost=0.0,
                average_depreciation_cost=0.0,
                direct_labor_cost_pct=None,
                production_cost_pct=None,
                depreciation_pct=None,
                oee_pct=None,
                otd_pct=None,
            )
            self._cache[key] = snapshot
            return snapshot

        branch_snapshots = [
            self.get_unit_snapshot(
                branch=branch_code,
                start_date=start_date,
                end_date=end_date,
            )
            for branch_code in branches
        ]

        snapshot = ProductionUnitMetricsSnapshot(
            branch=None,
            start_date=start_date,
            end_date=end_date,
            rol_with_ipi=sum(item.rol_with_ipi for item in branch_snapshots),
            average_direct_labor_cost=self._average_cost(
                [item.average_direct_labor_cost for item in branch_snapshots]
            ),
            average_production_cost=self._average_cost(
                [item.average_production_cost for item in branch_snapshots]
            ),
            average_depreciation_cost=self._average_cost(
                [item.average_depreciation_cost for item in branch_snapshots]
            ),
            direct_labor_cost_pct=self._average_optional_pct(
                [item.direct_labor_cost_pct for item in branch_snapshots]
            ),
            production_cost_pct=self._average_optional_pct(
                [item.production_cost_pct for item in branch_snapshots]
            ),
            depreciation_pct=self._average_optional_pct(
                [item.depreciation_pct for item in branch_snapshots]
            ),
            oee_pct=self._average_optional_pct(
                [item.oee_pct for item in branch_snapshots]
            ),
            otd_pct=self._average_optional_pct(
                [item.otd_pct for item in branch_snapshots]
            ),
        )
        self._cache[key] = snapshot
        return snapshot

    def _build_snapshot(
        self,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> ProductionUnitMetricsSnapshot:
        key = (branch, start_date, end_date)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        production_request = ProductionRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )
        rol_request = GetRolRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )

        rol_payload = self._financial_query_repository.get_rol(rol_request)
        rol_with_ipi = self._to_float(rol_payload.get("rol_with_ipi")) or 0.0

        direct_labor_items = self._direct_labor_repository.get_direct_labor_cost(
            production_request
        )
        production_cost_items = self._production_cost_repository.get_production_cost(
            production_request
        )
        depreciation_items = self._depreciation_repository.get_depreciation_cost(
            production_request
        )

        average_direct_labor_cost = self._average_cost(
            [item.cost for item in direct_labor_items if item.cost is not None]
        )
        average_production_cost = self._average_cost(
            [item.cost for item in production_cost_items if item.cost is not None]
        )
        average_depreciation_cost = self._average_cost(
            [item.cost for item in depreciation_items if item.cost is not None]
        )

        oee = self._overall_equipment_effectiveness_repository.get_overall_equipment_effectiveness(
            production_request
        )
        otd = self._on_time_delivery_repository.get_on_time_delivery(production_request)

        snapshot = ProductionUnitMetricsSnapshot(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
            rol_with_ipi=rol_with_ipi,
            average_direct_labor_cost=average_direct_labor_cost,
            average_production_cost=average_production_cost,
            average_depreciation_cost=average_depreciation_cost,
            direct_labor_cost_pct=self._calculate_pct(
                numerator=average_direct_labor_cost,
                denominator=rol_with_ipi,
            ),
            production_cost_pct=self._calculate_pct(
                numerator=average_production_cost,
                denominator=rol_with_ipi,
            ),
            depreciation_pct=self._calculate_pct(
                numerator=average_depreciation_cost,
                denominator=rol_with_ipi,
            ),
            oee_pct=self._to_float(getattr(oee, "oee_pct", None)),
            otd_pct=self._to_float(getattr(otd, "on_time_delivery_pct", None)),
        )
        self._cache[key] = snapshot
        return snapshot

    def _resolve_branches_from_items(self, *collections) -> list[str]:
        branches = set()

        for collection in collections:
            for item in collection:
                branch = getattr(item, "branch", None)
                if branch is None:
                    continue

                normalized_branch = str(branch).strip()
                if normalized_branch:
                    branches.add(normalized_branch)

        return sorted(branches)

    def _resolve_branches_from_rows(self, *collections) -> list[str]:
        branches = set()

        for collection in collections:
            for row in collection:
                branch = row.get("branch")
                if branch is None:
                    continue

                normalized_branch = str(branch).strip()
                if normalized_branch:
                    branches.add(normalized_branch)

        return sorted(branches)

    def _merge_branches(self, *collections: list[str]) -> list[str]:
        branches = set()

        for collection in collections:
            for branch in collection:
                normalized_branch = str(branch).strip()
                if normalized_branch:
                    branches.add(normalized_branch)

        return sorted(branches)

    def _average_cost(self, values: list[float]) -> float:
        if not values:
            return 0.0
        return sum(values) / len(values)

    def _average_optional_pct(self, values: list[float | None]) -> float | None:
        if not values:
            return None

        if any(value is None for value in values):
            return None

        return sum(values) / len(values)

    def _calculate_pct(
        self,
        *,
        numerator: float,
        denominator: float,
    ) -> float | None:
        if not denominator:
            return None
        return (numerator / denominator) * 100

    def _to_float(self, value) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None