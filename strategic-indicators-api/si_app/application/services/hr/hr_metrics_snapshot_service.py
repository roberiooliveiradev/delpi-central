from __future__ import annotations

from dataclasses import dataclass

from si_app.application.use_cases.strategic_indicators.period_resolution import (
    ResolvedPeriod,
)
from si_app.infrastructure.persistence.portal_rh.hr_repositories.hr_metrics_repository import (
    HrMetricsRepository,
)


@dataclass(frozen=True)
class HrBranchSnapshot:
    branch_code: str
    absenteeism_pct: float | None
    turnover_pct: float | None
    training_hours_per_collaborator: float | None
    active_pdi_count: float | None = None
    active_pdi_pct: float | None = None
    performance_reviews_completion_pct: float | None = None
    internal_satisfaction_pct: float | None = None


@dataclass(frozen=True)
class HrMetricsSnapshot:
    start_date: str | None
    end_date: str | None
    branches: list[HrBranchSnapshot]
    internal_satisfaction_pct: float | None = None
    active_pdi_count: float | None = None
    active_pdi_pct: float | None = None
    performance_reviews_completion_pct: float | None = None


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

        snapshot = self._build_snapshot(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            internal_satisfaction_override=None,
        )
        self._cache[key] = snapshot
        return snapshot

    def get_snapshot_series(
        self,
        *,
        periods: list[ResolvedPeriod],
        branch: str | None = None,
    ) -> dict[str, HrMetricsSnapshot]:
        result: dict[str, HrMetricsSnapshot] = {}

        if not periods:
            return result

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
                internal_satisfaction_override=None,
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
    ) -> HrBranchSnapshot | None:
        snapshot = self.get_snapshot(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )
        return snapshot.branches[0] if snapshot.branches else None

    def get_active_pdi_count(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        branch: str | None = None,
    ) -> dict:
        branches = self._resolve_branches(branch=branch)
        branch_rows: list[dict] = []

        for branch_code in branches:
            raw = self._repository.get_active_pdi_snapshot(
                branch_code=branch_code,
                start_date=start_date,
                end_date=end_date,
            )
            count = self._to_float(raw.get("active_pdis"))
            branch_rows.append(
                {
                    "branch_code": branch_code,
                    "active_pdi_count": round(count, 2) if count is not None else None,
                    "total_pdis": self._to_float(raw.get("total_pdis")),
                    "active_pdi_pct": self._to_float(raw.get("active_pdi_pct")),
                }
            )

        counts = [
            row["active_pdi_count"]
            for row in branch_rows
            if row["active_pdi_count"] is not None
        ]

        return {
            "start_date": start_date,
            "end_date": end_date,
            "active_pdi_count": round(sum(counts), 2) if counts else None,
            "branches": branch_rows,
        }

    def get_performance_reviews_completion(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        branch: str | None = None,
    ) -> dict:
        branches = self._resolve_branches(branch=branch)
        branch_rows: list[dict] = []

        for branch_code in branches:
            raw = self._repository.get_performance_reviews_completion_snapshot(
                branch_code=branch_code,
                start_date=start_date,
                end_date=end_date,
            )
            completion_pct = self._to_float(raw.get("value"))
            branch_rows.append(
                {
                    "branch_code": branch_code,
                    "completion_pct": round(completion_pct, 2)
                    if completion_pct is not None
                    else None,
                    "total_reviews": self._to_float(raw.get("total_reviews")),
                    "completed_reviews": self._to_float(raw.get("completed_reviews")),
                }
            )

        completion_values = [
            row["completion_pct"]
            for row in branch_rows
            if row["completion_pct"] is not None
        ]
        completion_pct = (
            sum(completion_values) / len(completion_values)
            if completion_values
            else None
        )

        return {
            "start_date": start_date,
            "end_date": end_date,
            "completion_pct": round(completion_pct, 2) if completion_pct is not None else None,
            "branches": branch_rows,
        }

    def _build_snapshot(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        branch: str | None,
        internal_satisfaction_override: float | None,
    ) -> HrMetricsSnapshot:
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
            active_pdi_raw = self._repository.get_active_pdi_snapshot(
                branch_code=branch_code,
                start_date=start_date,
                end_date=end_date,
            )
            performance_reviews_raw = (
                self._repository.get_performance_reviews_completion_snapshot(
                    branch_code=branch_code,
                    start_date=start_date,
                    end_date=end_date,
                )
            )
            satisfaction_raw = self._repository.get_internal_satisfaction_snapshot(
                branch_code=branch_code,
                start_date=start_date,
                end_date=end_date,
            )
            internal_satisfaction_branch = self._to_float(satisfaction_raw.get("value"))

            total_absence_hours = self._to_float(absenteeism_raw.get("total_absence_hours")) or 0.0
            expected_hours = self._to_float(absenteeism_raw.get("expected_hours")) or 0.0
            absenteeism_pct = (
                (total_absence_hours / expected_hours) * 100
                if expected_hours > 0
                else None
            )

            terminations_count = self._to_float(turnover_raw.get("terminations_count")) or 0.0
            active_count = self._to_float(turnover_raw.get("active_count")) or 0.0
            turnover_pct = (
                (terminations_count / active_count) * 100
                if active_count > 0
                else None
            )

            total_training_hours = self._to_float(training_raw.get("total_training_hours")) or 0.0
            total_participations = self._to_float(training_raw.get("total_participations")) or 0.0
            training_hours_per_collaborator = (
                total_training_hours / total_participations
                if total_participations > 0
                else None
            )
            active_pdi_count = self._to_float(active_pdi_raw.get("active_pdis"))
            active_pdi_pct = self._to_float(active_pdi_raw.get("active_pdi_pct"))
            performance_reviews_completion_pct = self._to_float(
                performance_reviews_raw.get("value")
            )

            branch_snapshots.append(
                HrBranchSnapshot(
                    branch_code=branch_code,
                    absenteeism_pct=round(absenteeism_pct, 2) if absenteeism_pct is not None else None,
                    turnover_pct=round(turnover_pct, 2) if turnover_pct is not None else None,
                    training_hours_per_collaborator=round(training_hours_per_collaborator, 2)
                    if training_hours_per_collaborator is not None
                    else None,
                    active_pdi_count=round(active_pdi_count, 2)
                    if active_pdi_count is not None
                    else None,
                    active_pdi_pct=round(active_pdi_pct, 2)
                    if active_pdi_pct is not None
                    else None,
                    performance_reviews_completion_pct=round(
                        performance_reviews_completion_pct,
                        2,
                    )
                    if performance_reviews_completion_pct is not None
                    else None,
                    internal_satisfaction_pct=round(internal_satisfaction_branch, 2)
                    if internal_satisfaction_branch is not None
                    else None,
                )
            )

        active_pdi_counts = [
            item.active_pdi_count
            for item in branch_snapshots
            if item.active_pdi_count is not None
        ]
        active_pdi_count = sum(active_pdi_counts) if active_pdi_counts else None

        active_pdi_pct_values = [
            item.active_pdi_pct
            for item in branch_snapshots
            if item.active_pdi_pct is not None
        ]
        active_pdi_pct = (
            sum(active_pdi_pct_values) / len(active_pdi_pct_values)
            if active_pdi_pct_values
            else None
        )

        performance_review_values = [
            item.performance_reviews_completion_pct
            for item in branch_snapshots
            if item.performance_reviews_completion_pct is not None
        ]
        performance_reviews_completion_pct = (
            sum(performance_review_values) / len(performance_review_values)
            if performance_review_values
            else None
        )

        satisfaction_values = [
            item.internal_satisfaction_pct
            for item in branch_snapshots
            if item.internal_satisfaction_pct is not None
        ]
        if internal_satisfaction_override is not None:
            internal_satisfaction_pct = internal_satisfaction_override
        elif satisfaction_values:
            internal_satisfaction_pct = sum(satisfaction_values) / len(satisfaction_values)
        else:
            internal_satisfaction_pct = None

        return HrMetricsSnapshot(
            start_date=start_date,
            end_date=end_date,
            branches=branch_snapshots,
            internal_satisfaction_pct=round(internal_satisfaction_pct, 2)
            if internal_satisfaction_pct is not None
            else None,
            active_pdi_count=round(active_pdi_count, 2)
            if active_pdi_count is not None
            else None,
            active_pdi_pct=round(active_pdi_pct, 2)
            if active_pdi_pct is not None
            else None,
            performance_reviews_completion_pct=round(
                performance_reviews_completion_pct,
                2,
            )
            if performance_reviews_completion_pct is not None
            else None,
        )

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