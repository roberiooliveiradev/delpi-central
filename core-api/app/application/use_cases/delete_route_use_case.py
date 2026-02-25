# app/application/use_cases/delete_route_use_case.py

from dataclasses import dataclass
from typing import Dict, Any, List

from app.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class DeleteRouteResult:
    success: bool
    errors: List[Dict[str, Any]]


class DeleteRouteUseCase:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(self, route_id: str) -> DeleteRouteResult:
        try:
            self._uow.admin_routes.delete(route_id)
            self._uow.commit()
            return DeleteRouteResult(True, [])
        except Exception as e:
            self._uow.rollback()
            return DeleteRouteResult(False, [{"code": "routes.delete_failed", "message": str(e), "path": "_global"}])