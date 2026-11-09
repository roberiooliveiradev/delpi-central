# app/application/use_cases/bulk_delete_routes_use_case.py

from dataclasses import dataclass
from typing import Dict, Any, List

from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent


@dataclass(frozen=True)
class BulkDeleteRoutesResult:
    success: bool
    deleted: int
    errors: List[Dict[str, Any]]


class BulkDeleteRoutesUseCase:

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(self, route_ids: List[str]) -> BulkDeleteRoutesResult:
        try:
            deleted = self._uow.admin_routes.bulk_delete(route_ids)
            self._uow.collect_event(
                AdminChangedEvent(
                    entity="routes",
                    action="routes_bulk_deleted",
                    payload={
                        "routeIds": route_ids,
                        "deleted": deleted,
                    },
                    target_user_id=None,
                )
            )
            return BulkDeleteRoutesResult(True, deleted, [])
        except Exception as exc:
            self._uow.rollback()
            return BulkDeleteRoutesResult(
                False,
                0,
                [{"code": "routes.bulk_delete_failed", "message": str(exc)}],
            )
