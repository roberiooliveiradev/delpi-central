from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol


class MesMonitoringReadRepositoryPort(Protocol):
    def list_live_work_centers(self, *, branch: str) -> list[dict[str, Any]]: ...

    def get_run(self, run_id: str) -> dict[str, Any] | None: ...

    def list_timeline_facts(self, run_id: str) -> list[dict[str, Any]]: ...

    def list_downtimes(
        self,
        *,
        branch: str,
        work_center: str | None,
        period_from: datetime | None,
        period_to: datetime | None,
        page: int,
        page_size: int,
    ) -> tuple[list[dict[str, Any]], int]: ...
