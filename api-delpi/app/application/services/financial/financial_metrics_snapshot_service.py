from __future__ import annotations

from dataclasses import dataclass

from app.application.dto.financial.get_rol_request import GetRolRequest
from app.domain.ports.financial.financial_query_repository_port import (
    FinancialQueryRepositoryPort,
)
from app.infrastructure.persistence.google_sheets.financial.financial_metrics_repository import (
    FinancialMetricsRepository,
)
from app.shared.utils.spreadsheet_date import spreadsheet_date_in_range


@dataclass(frozen=True)
class FinancialBranchSnapshot:
    branch: str
    rol_with_ipi: float
    ebitda_value: float
    fixed_cost_value: float
    pmr_days: float
    ebitda_over_rol_pct: float
    fixed_cost_over_rol_pct: float


@dataclass(frozen=True)
class FinancialMetricsSnapshot:
    start_date: str | None
    end_date: str | None
    branches: list[FinancialBranchSnapshot]


class FinancialMetricsSnapshotService:
    def __init__(
        self,
        *,
        sheets_repository: FinancialMetricsRepository,
        financial_query_repository: FinancialQueryRepositoryPort,
    ) -> None:
        self._sheets_repository = sheets_repository
        self._financial_query_repository = financial_query_repository
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

        ebitda_rows = self._filter_period_rows(
            self._sheets_repository.load_ebitda_rows(),
            start_date=start_date,
            end_date=end_date,
        )
        fixed_cost_rows = self._filter_period_rows(
            self._sheets_repository.load_fixed_cost_rows(),
            start_date=start_date,
            end_date=end_date,
        )
        receivables_rows = self._filter_period_rows(
            self._sheets_repository.load_receivables_rows(),
            start_date=start_date,
            end_date=end_date,
        )

        branches = self._resolve_branches(
            ebitda_rows=ebitda_rows,
            fixed_cost_rows=fixed_cost_rows,
            receivables_rows=receivables_rows,
            branch=branch,
        )

        snapshots: list[FinancialBranchSnapshot] = []

        for branch_code in branches:
            rol_payload = self._financial_query_repository.get_rol(
                GetRolRequest(
                    branch=branch_code,
                    start_date=start_date,
                    end_date=end_date,
                )
            )
            rol_with_ipi = self._to_float(rol_payload.get("rol_with_ipi")) or 0.0

            ebitda_value = self._average_numeric_field(
                rows=ebitda_rows,
                branch=branch_code,
                field_name="ebitida",
            )

            fixed_cost_value = self._average_numeric_field(
                rows=fixed_cost_rows,
                branch=branch_code,
                field_name="custos_fixos",
            )

            pmr_days = self._average_numeric_field(
                rows=receivables_rows,
                branch=branch_code,
                field_name="prazo_medio_recebimento",
            )

            ebitda_over_rol_pct = self._calculate_ratio_pct(
                numerator=ebitda_value,
                denominator=rol_with_ipi,
            )
            fixed_cost_over_rol_pct = self._calculate_ratio_pct(
                numerator=fixed_cost_value,
                denominator=rol_with_ipi,
            )

            snapshots.append(
                FinancialBranchSnapshot(
                    branch=branch_code,
                    rol_with_ipi=rol_with_ipi,
                    ebitda_value=round(ebitda_value, 2),
                    fixed_cost_value=round(fixed_cost_value, 2),
                    pmr_days=round(pmr_days, 2),
                    ebitda_over_rol_pct=ebitda_over_rol_pct,
                    fixed_cost_over_rol_pct=fixed_cost_over_rol_pct,
                )
            )

        snapshot = FinancialMetricsSnapshot(
            start_date=start_date,
            end_date=end_date,
            branches=snapshots,
        )
        self._cache[key] = snapshot
        return snapshot

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

    def _resolve_branches(
        self,
        *,
        ebitda_rows: list[dict],
        fixed_cost_rows: list[dict],
        receivables_rows: list[dict],
        branch: str | None,
    ) -> list[str]:
        if branch:
            return [branch]

        branches = set()

        for row in ebitda_rows + fixed_cost_rows + receivables_rows:
            branch_code = self._normalize_branch(row.get("filial"))
            if branch_code:
                branches.add(branch_code)

        return sorted(branches)

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

    def _average_numeric_field(
        self,
        *,
        rows: list[dict],
        branch: str,
        field_name: str,
    ) -> float:
        values: list[float] = []

        for row in rows:
            row_branch = self._normalize_branch(row.get("filial"))
            if row_branch != branch:
                continue

            number = self._to_float(row.get(field_name))
            if number is not None:
                values.append(number)

        if not values:
            return 0.0

        return sum(values) / len(values)

    def _calculate_ratio_pct(
        self,
        *,
        numerator: float,
        denominator: float,
    ) -> float:
        if not denominator:
            return 0.0
        return round((numerator / denominator) * 100, 2)

    def _normalize_branch(self, value) -> str | None:
        if value is None:
            return None
        raw = str(value).strip()
        return raw or None

    def _to_float(self, value) -> float | None:
        if value is None:
            return None

        if isinstance(value, (int, float)):
            return float(value)

        raw = str(value).strip()
        if not raw:
            return None

        raw = raw.replace("R$", "").replace("%", "").replace(" ", "")

        if "," in raw and "." in raw:
            raw = raw.replace(".", "").replace(",", ".")
        elif "," in raw:
            raw = raw.replace(",", ".")

        try:
            return float(raw)
        except ValueError:
            return None