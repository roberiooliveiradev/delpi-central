# app/application/use_cases/create_app_route_use_case.py

from dataclasses import dataclass
from typing import Dict, Any, List, Optional

from app.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class CreateRouteResult:
    success: bool
    route: Optional[Dict[str, Any]]
    errors: List[Dict[str, Any]]


class CreateAppRouteUseCase:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(
        self,
        app_id: str,
        *,
        path: str,
        label: str,
        icon: str,
        permission_code: Optional[str],
        order: int,
        show_in_menu: bool,
        active: bool = True,
    ) -> CreateRouteResult:
        if not path or not str(path).startswith("/"):
            return CreateRouteResult(False, None, [{"code": "routes.invalid_path", "message": "path deve começar com '/'", "path": "path"}])

        try:
            dto = self._uow.admin_routes.create({
                "app_id": app_id,
                "path": path,
                "label": label,
                "icon": icon,
                "permission_code": permission_code,
                "order": order,
                "show_in_menu": show_in_menu,
                "active": active,
            })
            self._uow.commit()
            return CreateRouteResult(True, dto.__dict__, [])
        except Exception as e:
            self._uow.rollback()
            return CreateRouteResult(False, None, [{"code": "routes.create_failed", "message": str(e), "path": "_global"}])