# app/application/use_cases/bulk_delete_routes_use_case.py

from dataclasses import dataclass
from typing import Dict, Any, List

from app.application.unit_of_work import UnitOfWork


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
            self._uow.commit()
            return BulkDeleteRoutesResult(True, deleted, [])
        except Exception as e:
            self._uow.rollback()
            return BulkDeleteRoutesResult(False, 0, [{"code": "routes.bulk_delete_failed", "message": str(e), "path": "_global"}])