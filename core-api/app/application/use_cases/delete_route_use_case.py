# app/application/use_cases/delete_route_use_case.py

from dataclasses import dataclass
from typing import Dict, Any, List

from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent


@dataclass(frozen=True)
class DeleteRouteResult:
    success: bool
    errors: List[Dict[str, Any]]


class DeleteRouteUseCase:

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(self, route_id: str) -> DeleteRouteResult:

        # 1️⃣ Regra de negócio
        self._uow.admin_routes.delete(route_id)

        # 2️⃣ Evento administrativo (broadcast)
        self._uow.collect_event(
            AdminChangedEvent(
                entity="routes",
                action="route_deleted",
                payload={"routeId": route_id},
                target_user_id=None,  # broadcast
            )
        )

        return DeleteRouteResult(True, [])