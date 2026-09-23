from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol


class LineFeederPickPlanRepositoryPort(Protocol):
    """Listas de coleta do alimentador — persistência do que ele decidiu buscar."""

    def create_plan(
        self,
        *,
        branch: str,
        cutoff_at: datetime,
        work_center: str | None,
        created_by: str | None,
        items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        ...

    def get_plan(self, *, plan_id: str, branch: str) -> dict[str, Any] | None:
        ...

    def list_plans(
        self,
        *,
        branch: str,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        ...

    def update_item_status(
        self,
        *,
        plan_id: str,
        item_id: str,
        branch: str,
        status: str,
        updated_by: str | None,
    ) -> dict[str, Any] | None:
        ...

    def close_plan(
        self,
        *,
        plan_id: str,
        branch: str,
        updated_by: str | None,
    ) -> dict[str, Any] | None:
        ...
