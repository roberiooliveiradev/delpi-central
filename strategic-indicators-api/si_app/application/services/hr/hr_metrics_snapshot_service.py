from __future__ import annotations

from delpi_domain.hr_snapshot import HrBranchSnapshot, HrMetricsSnapshot
from si_app.application.use_cases.strategic_indicators.period_resolution import (
    ResolvedPeriod,
)
from si_app.infrastructure.gateways.delpi_hr_gateway import DelpiHrGateway


class HrMetricsSnapshotService:
    def __init__(
        self,
        *,
        hr_gateway: DelpiHrGateway,
    ) -> None:
        self._hr_gateway = hr_gateway
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

        snapshot = self._hr_gateway.get_snapshot(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
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

            snapshot = self._hr_gateway.get_snapshot(
                branch=branch,
                start_date=period.start_date,
                end_date=period.end_date,
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
