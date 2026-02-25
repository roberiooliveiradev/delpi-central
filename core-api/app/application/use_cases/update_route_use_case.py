# app/application/use_cases/update_route_use_case.py

from dataclasses import dataclass
from typing import Dict, Any, List, Optional

from app.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class UpdateRouteResult:
    success: bool
    errors: List[Dict[str, Any]]


class UpdateRouteUseCase:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(self, route_id: str, patch: Dict[str, Any]) -> UpdateRouteResult:
        try:
            self._uow.admin_routes.update(route_id, patch)
            self._uow.commit()
            return UpdateRouteResult(True, [])
        except Exception as e:
            self._uow.rollback()
            return UpdateRouteResult(False, [{"code": "routes.update_failed", "message": str(e), "path": "_global"}])