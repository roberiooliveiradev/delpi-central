# app/application/use_cases/create_app_route_use_case.py

from dataclasses import dataclass
from typing import Dict, Any, List, Optional

from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent


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

        # 1️⃣ Validação
        if not path or not str(path).startswith("/"):
            return CreateRouteResult(
                False,
                None,
                [{
                    "code": "routes.invalid_path",
                    "message": "path deve começar com '/'",
                    "path": "path"
                }]
            )

        # 2️⃣ Regra de negócio
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

        # 3️⃣ Evento administrativo (broadcast)
        self._uow.collect_event(
            AdminChangedEvent(
                entity="routes",
                action="route_created",
                payload={
                    "routeId": str(dto.id) if hasattr(dto, "id") else None,
                    "appId": app_id,
                },
                target_user_id=None,  # broadcast
            )
        )

        return CreateRouteResult(
            True,
            dto.__dict__,
            []
        )