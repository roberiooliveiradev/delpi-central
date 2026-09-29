from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol


class ProductionControlMesGatewayPort(Protocol):
    def get_monitoring(self, *, branch: str) -> dict[str, Any]: ...

    def get_timeline(self, run_id: str) -> dict[str, Any]: ...

    def get_work_center_timeline(
        self,
        *,
        branch: str,
        work_center: str,
        period_from: datetime,
        period_to: datetime | None,
    ) -> dict[str, Any]: ...

    def get_downtimes(
        self,
        *,
        branch: str,
        work_center: str | None,
        period_from: datetime | None,
        period_to: datetime | None,
        page: int,
        page_size: int,
    ) -> dict[str, Any]: ...
