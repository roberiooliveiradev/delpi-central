# app/application/use_cases/list_app_routes_use_case.py

from dataclasses import dataclass
from typing import List, Dict, Any

from app.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class ListAppRoutesResult:
    success: bool
    routes: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]


class ListAppRoutesUseCase:

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(self, app_id: str) -> ListAppRoutesResult:
        try:
            # Garantir que o app existe
            app = self._uow.admin_apps.get(app_id)
            if app is None:
                return ListAppRoutesResult(
                    success=False,
                    routes=[],
                    errors=[{
                        "code": "apps.not_found",
                        "message": "App not found",
                        "path": "app_id"
                    }],
                )

            routes = self._uow.admin_routes.list_by_app(app_id)

            return ListAppRoutesResult(
                success=True,
                routes=[r.__dict__ for r in routes],
                errors=[],
            )

        except Exception as e:
            return ListAppRoutesResult(
                success=False,
                routes=[],
                errors=[{
                    "code": "routes.list_failed",
                    "message": str(e),
                    "path": "_global"
                }],
            )