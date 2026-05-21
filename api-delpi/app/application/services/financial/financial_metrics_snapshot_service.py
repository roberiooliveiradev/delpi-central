from __future__ import annotations

from dataclasses import dataclass

from app.application.dto.financial.get_rol_request import GetRolRequest
from app.application.services.financial.financial_sheet_scope import (
    CONSOLIDATED_BRANCH_KEY,
    is_consolidated_sheet_row,
    normalize_sheet_branch,
)
from app.application.shared.period_resolution import (
    ResolvedPeriod,
)
from app.domain.ports.financial.financial_query_repository_port import (
    FinancialQueryRepositoryPort,
)
from app.infrastructure.persistence.google_sheets.financial.financial_ebitda_repository import (
    FinancialEbitdaRepository,
)
from app.infrastructure.persistence.google_sheets.financial.financial_fixed_cost_repository import (
    FinancialFixedCostRepository,
)
from app.infrastructure.persistence.google_sheets.financial.financial_receivables_repository import (
    FinancialReceivablesRepository,
)
from app.infrastructure.persistence.google_sheets.utils import Utils
from app.shared.utils.spreadsheet_date import spreadsheet_date_in_range


@dataclass(frozen=True)
class FinancialBranchSnapshot:
    branch: str
    rol_with_ipi: float
    ebitda_value: float
    fixed_cost_value: float
    pmr_days: float
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
        ebitda_repository: FinancialEbitdaRepository,
        fixed_cost_repository: FinancialFixedCostRepository,
        receivables_repository: FinancialReceivablesRepository,
        financial_query_repository: FinancialQueryRepositoryPort,
    ) -> None:
        self._ebitda_repository = ebitda_repository
        self._fixed_cost_repository = fixed_cost_repository
        self._receivables_repository = receivables_repository
        self._financial_query_repository = financial_query_repository
        self._utils = Utils()
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
            rows_override=None,
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

        if not periods:
            return result

        all_ebitda_rows = self._ebitda_repository.load_rows()
        all_fixed_cost_rows = self._fixed_cost_repository.load_rows()
        all_receivables_rows = self._receivables_repository.load_rows()

        for period in periods:
            key = (period.start_date, period.end_date, branch)
            cached = self._cache.get(key)
            if cached is not None:
                result[period.competence] = cached
                continue

            filtered_rows = {
                "ebitda_rows": self._filter_period_rows(
                    all_ebitda_rows,
                    start_date=period.start_date,
                    end_date=period.end_date,
                ),
                "fixed_cost_rows": self._filter_period_rows(
                    all_fixed_cost_rows,
                    start_date=period.start_date,
                    end_date=period.end_date,
                ),
                "receivables_rows": self._filter_period_rows(
                    all_receivables_rows,
                    start_date=period.start_date,
                    end_date=period.end_date,
                ),
            }

            snapshot = self._build_snapshot(
                start_date=period.start_date,
                end_date=period.end_date,
                branch=branch,
                rows_override=filtered_rows,
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
        rows_override: dict[str, list[dict]] | None,
    ) -> FinancialMetricsSnapshot:
        if rows_override is None:
            ebitda_rows = self._filter_period_rows(
                self._ebitda_repository.load_rows(),
                start_date=start_date,
                end_date=end_date,
            )
            fixed_cost_rows = self._filter_period_rows(
                self._fixed_cost_repository.load_rows(),
                start_date=start_date,
                end_date=end_date,
            )
            receivables_rows = self._filter_period_rows(
                self._receivables_repository.load_rows(),
                start_date=start_date,
                end_date=end_date,
            )
        else:
            ebitda_rows = rows_override.get("ebitda_rows", [])
            fixed_cost_rows = rows_override.get("fixed_cost_rows", [])
            receivables_rows = rows_override.get("receivables_rows", [])

        branch_codes = self._resolve_branch_codes(
            ebitda_rows=ebitda_rows,
            fixed_cost_rows=fixed_cost_rows,
            receivables_rows=receivables_rows,
            branch=branch,
        )

        snapshots: list[FinancialBranchSnapshot] = []
        rol_by_branch = self._fetch_rol_by_branch(
            branch_codes=branch_codes,
            start_date=start_date,
            end_date=end_date,
        )

        if branch is None:
            snapshots.append(
                self._build_scope_snapshot(
                    scope_key=CONSOLIDATED_BRANCH_KEY,
                    consolidated=True,
                    ebitda_rows=ebitda_rows,
                    fixed_cost_rows=fixed_cost_rows,
                    receivables_rows=receivables_rows,
                    rol_with_ipi=self._sum_rol(rol_by_branch),
                )
            )

        for branch_code in branch_codes:
            rol_payload = rol_by_branch.get(branch_code, {})
            rol_with_ipi = self._utils.to_float(rol_payload.get("rol_with_ipi")) or 0.0

            snapshots.append(
                self._build_scope_snapshot(
                    scope_key=branch_code,
                    consolidated=False,
                    ebitda_rows=ebitda_rows,
                    fixed_cost_rows=fixed_cost_rows,
                    receivables_rows=receivables_rows,
                    rol_with_ipi=rol_with_ipi,
                )
            )

        return FinancialMetricsSnapshot(
            start_date=start_date,
            end_date=end_date,
            branches=snapshots,
        )

    def _fetch_rol_by_branch(
        self,
        *,
        branch_codes: list[str],
        start_date: str | None,
        end_date: str | None,
    ) -> dict[str, dict]:
        result: dict[str, dict] = {}
        for branch_code in branch_codes:
            result[branch_code] = self._financial_query_repository.get_rol(
                GetRolRequest(
                    branch=branch_code,
                    start_date=start_date,
                    end_date=end_date,
                )
            )
        return result

    def _resolve_branch_codes(
        self,
        *,
        ebitda_rows: list[dict],
        fixed_cost_rows: list[dict],
        receivables_rows: list[dict],
        branch: str | None,
    ) -> list[str]:
        if branch:
            return [branch]

        branches: set[str] = set()

        for row in ebitda_rows + fixed_cost_rows + receivables_rows:
            branch_code = normalize_sheet_branch(row.get("filial"))
            if branch_code:
                branches.add(branch_code)

        return sorted(branches)

    def _build_scope_snapshot(
        self,
        *,
        scope_key: str,
        consolidated: bool,
        ebitda_rows: list[dict],
        fixed_cost_rows: list[dict],
        receivables_rows: list[dict],
        rol_with_ipi: float,
    ) -> FinancialBranchSnapshot:
        ebitda_pct = self._average_sheet_metric(
            rows=ebitda_rows,
            field_name="ebitida",
            consolidated=consolidated,
            branch=None if consolidated else scope_key,
        )
        fixed_cost_pct = self._average_sheet_metric(
            rows=fixed_cost_rows,
            field_name="custos_fixos",
            consolidated=consolidated,
            branch=None if consolidated else scope_key,
        )
        pmr_days = self._average_sheet_metric(
            rows=receivables_rows,
            field_name="prazo_medio_recebimento",
            consolidated=consolidated,
            branch=None if consolidated else scope_key,
        ) or 0.0

        return FinancialBranchSnapshot(
            branch=scope_key,
            rol_with_ipi=round(rol_with_ipi, 2),
            ebitda_value=round(ebitda_pct, 2) if ebitda_pct is not None else 0.0,
            fixed_cost_value=round(fixed_cost_pct, 2)
            if fixed_cost_pct is not None
            else 0.0,
            pmr_days=round(pmr_days, 2),
            ebitda_over_rol_pct=round(ebitda_pct, 2) if ebitda_pct is not None else None,
            fixed_cost_over_rol_pct=round(fixed_cost_pct, 2)
            if fixed_cost_pct is not None
            else None,
        )

    def _sum_rol(self, rol_by_branch: dict[str, dict]) -> float:
        total = 0.0
        for payload in rol_by_branch.values():
            total += self._utils.to_float(payload.get("rol_with_ipi")) or 0.0
        return total

    def _filter_period_rows(
        self,
        rows: list[dict],
        *,
        start_date: str | None,
        end_date: str | None,
    ) -> list[dict]:
        return [
            row
            for row in rows
            if spreadsheet_date_in_range(
                row.get("data"),
                start_date=start_date,
                end_date=end_date,
            )
        ]

    def _average_sheet_metric(
        self,
        *,
        rows: list[dict],
        field_name: str,
        consolidated: bool,
        branch: str | None,
    ) -> float | None:
        values: list[float] = []

        for row in rows:
            row_is_consolidated = is_consolidated_sheet_row(row.get("filial"))
            if consolidated and not row_is_consolidated:
                continue
            if not consolidated:
                row_branch = normalize_sheet_branch(row.get("filial"))
                if row_branch != branch:
                    continue

            number = row.get(field_name)
            if number is not None:
                values.append(float(number))

        if not values:
            return None

        return sum(values) / len(values)
