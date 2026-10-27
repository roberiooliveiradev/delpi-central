from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol


class MesMonitoringReadRepositoryPort(Protocol):
    def list_live_work_centers(self, *, branch: str) -> list[dict[str, Any]]: ...

    def get_run(self, run_id: str) -> dict[str, Any] | None: ...

    def list_timeline_facts(self, run_id: str) -> list[dict[str, Any]]: ...

    def list_timeline_facts_for_runs(
        self, run_ids: list[str]
    ) -> list[dict[str, Any]]: ...

    def list_work_center_timeline_facts(
        self,
        *,
        branch: str,
        work_center: str,
        period_from: datetime,
        period_to: datetime,
    ) -> list[dict[str, Any]]: ...

    def has_activity_in_period(
        self,
        *,
        branch: str,
        work_center: str,
        period_from: datetime,
        period_to: datetime,
    ) -> bool: ...

    def list_downtimes(
        self,
        *,
        branch: str,
        work_center: str | None,
        period_from: datetime | None,
        period_to: datetime | None,
        reason_code: str | None = None,
        source: str | None = None,
        classification: str | None = None,
        status: str | None = None,
        sort: str | None = None,
        downtime_id: str | None = None,
        page: int,
        page_size: int,
    ) -> tuple[list[dict[str, Any]], int]: ...

    def list_downtime_analytics_facts(
        self,
        *,
        branch: str,
        work_center: str | None,
        period_from: datetime,
        period_to: datetime,
        reason_code: str | None = None,
        source: str | None = None,
        classification: str | None = None,
        status: str | None = None,
        max_facts: int = 20000,
    ) -> dict[str, Any]: ...

    def list_downtime_export(
        self,
        *,
        branch: str,
        work_center: str | None,
        period_from: datetime | None,
        period_to: datetime | None,
        reason_code: str | None = None,
        source: str | None = None,
        classification: str | None = None,
        status: str | None = None,
        pendency: bool = False,
        max_facts: int,
    ) -> dict[str, Any]: ...

    def list_concluded_downtime_treatments(
        self,
        *,
        branch: str,
        period_from: datetime,
        period_to: datetime,
        max_items: int = 200,
    ) -> list[dict[str, Any]]: ...

    def count_downtime_occurrences(
        self,
        *,
        branch: str,
        work_center: str,
        reason_code: str,
        period_from: datetime,
        period_to: datetime,
    ) -> dict[str, int]: ...

    def count_open_downtime_treatments(
        self,
        *,
        branch: str,
        work_center: str | None,
        period_from: datetime,
        period_to: datetime,
    ) -> int: ...

    def list_work_center_observer_states(
        self, *, branch: str
    ) -> list[dict[str, Any]]: ...
