from __future__ import annotations

from dataclasses import dataclass

from app.infrastructure.persistence.portal_rh.hr_repositories.hr_metrics_repository import (
    HrMetricsRepository,
)


@dataclass(frozen=True)
class HrBranchSnapshot:
    branch_code: str
    absenteeism_pct: float
    turnover_pct: float
    training_hours_per_collaborator: float


@dataclass(frozen=True)
class HrMetricsSnapshot:
    start_date: str | None
    end_date: str | None
    branches: list[HrBranchSnapshot]
    internal_satisfaction_pct: float | None = None
    active_pdi_pct: float | None = None


class HrMetricsSnapshotService:
    def __init__(
        self,
        *,
        repository: HrMetricsRepository,
    ) -> None:
        self._repository = repository
        self._cache: dict[tuple[str | None, str | None, str | None], HrMetricsSnapshot] = {}

    def get_snapshot(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        branch: str | None = None,
    ) -> HrMetricsSnapshot:
        key = (start_date, end_date, branch)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        branches = self._resolve_branches(branch=branch)
        branch_snapshots: list[HrBranchSnapshot] = []

        for branch_code in branches:
            absenteeism_raw = self._repository.get_absenteeism_snapshot(
                branch_code=branch_code,
                start_date=start_date,
                end_date=end_date,
            )
            turnover_raw = self._repository.get_turnover_snapshot(
                branch_code=branch_code,
                start_date=start_date,
                end_date=end_date,
            )
            training_raw = self._repository.get_training_hours_snapshot(
                branch_code=branch_code,
                start_date=start_date,
                end_date=end_date,
            )

            total_absence_hours = self._to_float(absenteeism_raw.get("total_absence_hours")) or 0.0
            expected_hours = self._to_float(absenteeism_raw.get("expected_hours")) or 0.0
            absenteeism_pct = (
                (total_absence_hours / expected_hours) * 100
                if expected_hours > 0
                else 0.0
            )

            terminations_count = self._to_float(turnover_raw.get("terminations_count")) or 0.0
            active_count = self._to_float(turnover_raw.get("active_count")) or 0.0
            turnover_pct = (
                (terminations_count / active_count) * 100
                if active_count > 0
                else 0.0
            )

            total_training_hours = self._to_float(training_raw.get("total_training_hours")) or 0.0
            total_participations = self._to_float(training_raw.get("total_participations")) or 0.0
            training_hours_per_collaborator = (
                total_training_hours / total_participations
                if total_participations > 0
                else 0.0
            )

            branch_snapshots.append(
                HrBranchSnapshot(
                    branch_code=branch_code,
                    absenteeism_pct=round(absenteeism_pct, 2),
                    turnover_pct=round(turnover_pct, 2),
                    training_hours_per_collaborator=round(training_hours_per_collaborator, 2),
                )
            )

        snapshot = HrMetricsSnapshot(
            start_date=start_date,
            end_date=end_date,
            branches=branch_snapshots,
            internal_satisfaction_pct=None,
            active_pdi_pct=None,
        )
        self._cache[key] = snapshot
        return snapshot

    def get_branch_snapshot(
        self,
        *,
        branch: str,
        start_date: str | None,
        end_date: str | None,
    ) -> HrBranchSnapshot | None:
        snapshot = self.get_snapshot(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )
        return snapshot.branches[0] if snapshot.branches else None

    def _resolve_branches(self, *, branch: str | None) -> list[str]:
        if branch:
            return [branch]
        return self._repository.list_active_branches()

    def _to_float(self, value) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None