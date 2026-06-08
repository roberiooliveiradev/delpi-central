from __future__ import annotations

from dataclasses import dataclass

from si_app.application.use_cases.strategic_indicators.period_resolution import (
    ResolvedPeriod,
)
from si_app.application.services.financial.financial_sheet_scope import (
    CONSOLIDATED_BRANCH_KEY,
)
from si_app.infrastructure.gateways.delpi_financial_gateway import (
    DelpiFinancialGateway,
    DelpiFinancialSheetsGateway,
)


@dataclass(frozen=True)
class FinancialBranchSnapshot:
    branch: str
    rol: float
    ebitda_value: float
    fixed_cost_value: float
    pmr_days: float | None
    ebitda_over_rol_pct: float | None
    fixed_cost_over_rol_pct: float | None


@dataclass(frozen=True)
class FinancialMetricsSnapshot:
    start_date: str | None
    end_date: str | None
    branches: list[FinancialBranchSnapshot]


class FinancialMetricsSnapshotService:
    def __init__(
        self,
        *,
        financial_sheets_gateway: DelpiFinancialSheetsGateway,
        financial_gateway: DelpiFinancialGateway,
    ) -> None:
        self._financial_sheets_gateway = financial_sheets_gateway
        self._financial_gateway = financial_gateway
        self._cache: dict[
            tuple[str | None, str | None, str | None],
            FinancialMetricsSnapshot,
        ] = {}

    def get_snapshot(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        branch: str | None = None,
    ) -> FinancialMetricsSnapshot:
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
    ) -> dict[str, FinancialMetricsSnapshot]:
        result: dict[str, FinancialMetricsSnapshot] = {}

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

    def get_branch_snapshot(
        self,
        *,
        branch: str,
        start_date: str | None,
        end_date: str | None,
    ) -> FinancialBranchSnapshot | None:
        snapshot = self.get_snapshot(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )
        return snapshot.branches[0] if snapshot.branches else None

    def _build_snapshot(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        branch: str | None,
    ) -> FinancialMetricsSnapshot:
        ebitda_data = self._financial_sheets_gateway.get_ebitda_pct(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )
        fixed_cost_data = self._financial_sheets_gateway.get_fixed_cost_pct(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )
        pmr_data = self._financial_sheets_gateway.get_pmr(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )

        branch_codes = self._resolve_branch_codes(
            branch=branch,
            ebitda_data=ebitda_data,
            fixed_cost_data=fixed_cost_data,
            pmr_data=pmr_data,
        )

        rol_by_branch = self._financial_gateway.list_rol_by_branch(
            branches=branch_codes,
            start_date=start_date,
            end_date=end_date,
        )

        snapshots: list[FinancialBranchSnapshot] = []

        if branch is None:
            snapshots.append(
                self._build_consolidated_snapshot(
                    ebitda_data=ebitda_data,
                    fixed_cost_data=fixed_cost_data,
                    pmr_data=pmr_data,
                    rol=self._sum_rol(rol_by_branch),
                )
            )

        for branch_code in branch_codes:
            rol_payload = rol_by_branch.get(branch_code, {})
            snapshots.append(
                self._build_branch_snapshot(
                    branch_code=branch_code,
                    rol=self._rol_value(rol_payload),
                    ebitda_data=ebitda_data,
                    fixed_cost_data=fixed_cost_data,
                    pmr_data=pmr_data,
                    scoped_to_single_branch=branch is not None,
                )
            )

        return FinancialMetricsSnapshot(
            start_date=start_date,
            end_date=end_date,
            branches=snapshots,
        )

    def _build_consolidated_snapshot(
        self,
        *,
        ebitda_data: dict,
        fixed_cost_data: dict,
        pmr_data: dict,
        rol: float,
    ) -> FinancialBranchSnapshot:
        ebitda_pct = self._opt_float(ebitda_data.get("ebitda_over_rol_pct"))
        fixed_pct = self._opt_float(fixed_cost_data.get("fixed_cost_over_rol_pct"))
        pmr_days = self._opt_float(pmr_data.get("pmr_days"))

        return FinancialBranchSnapshot(
            branch=CONSOLIDATED_BRANCH_KEY,
            rol=round(rol, 2),
            ebitda_value=round(ebitda_pct, 2) if ebitda_pct is not None else 0.0,
            fixed_cost_value=round(fixed_pct, 2) if fixed_pct is not None else 0.0,
            pmr_days=round(pmr_days, 2) if pmr_days is not None else None,
            ebitda_over_rol_pct=ebitda_pct,
            fixed_cost_over_rol_pct=fixed_pct,
        )

    def _build_branch_snapshot(
        self,
        *,
        branch_code: str,
        rol: float,
        ebitda_data: dict,
        fixed_cost_data: dict,
        pmr_data: dict,
        scoped_to_single_branch: bool,
    ) -> FinancialBranchSnapshot:
        if scoped_to_single_branch:
            ebitda_pct = self._opt_float(ebitda_data.get("ebitda_over_rol_pct"))
            fixed_pct = self._opt_float(fixed_cost_data.get("fixed_cost_over_rol_pct"))
            pmr_days = self._opt_float(pmr_data.get("pmr_days"))
        else:
            ebitda_pct = self._branch_metric(
                ebitda_data.get("branches"),
                branch_code,
                "ebitda_over_rol_pct",
            )
            fixed_pct = self._branch_metric(
                fixed_cost_data.get("branches"),
                branch_code,
                "fixed_cost_over_rol_pct",
            )
            pmr_days = self._branch_metric(
                pmr_data.get("branches"),
                branch_code,
                "pmr_days",
            )

        return FinancialBranchSnapshot(
            branch=branch_code,
            rol=round(rol, 2),
            ebitda_value=round(ebitda_pct, 2) if ebitda_pct is not None else 0.0,
            fixed_cost_value=round(fixed_pct, 2) if fixed_pct is not None else 0.0,
            pmr_days=round(pmr_days, 2) if pmr_days is not None else None,
            ebitda_over_rol_pct=ebitda_pct,
            fixed_cost_over_rol_pct=fixed_pct,
        )

    def _resolve_branch_codes(
        self,
        *,
        branch: str | None,
        ebitda_data: dict,
        fixed_cost_data: dict,
        pmr_data: dict,
    ) -> list[str]:
        if branch:
            return [branch]

        branches: set[str] = set()
        for payload in (ebitda_data, fixed_cost_data, pmr_data):
            for item in payload.get("branches") or []:
                code = (item.get("branch") or "").strip()
                if code:
                    branches.add(code)

        return sorted(branches)

    def _branch_metric(
        self,
        branches: list[dict] | None,
        branch_code: str,
        field: str,
    ) -> float | None:
        for item in branches or []:
            if item.get("branch") == branch_code:
                return self._opt_float(item.get(field))
        return None

    def _sum_rol(self, rol_by_branch: dict[str, dict]) -> float:
        total = 0.0
        for payload in rol_by_branch.values():
            total += self._rol_value(payload)
        return total

    def _rol_value(self, payload: dict) -> float:
        value = self._opt_float(payload.get("rol"))
        if value is not None:
            return value
        return self._opt_float(payload.get("rol_with_ipi")) or 0.0

    def _opt_float(self, value: object) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
