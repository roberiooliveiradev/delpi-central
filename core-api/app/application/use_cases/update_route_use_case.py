# app/application/use_cases/update_route_use_case.py

from dataclasses import dataclass
from typing import Dict, Any, List

from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent


@dataclass(frozen=True)
class UpdateRouteResult:
    success: bool
    errors: List[Dict[str, Any]]


class UpdateRouteUseCase:

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(self, route_id: str, patch: Dict[str, Any]) -> UpdateRouteResult:

        # 1️⃣ Regra de negócio
        self._uow.admin_routes.update(route_id, patch)

        # 2️⃣ Evento global
        self._uow.collect_event(
            AdminChangedEvent(
                entity="routes",
                action="route_updated",
                payload={
                    "routeId": route_id,
                },
                target_user_id=None,  # broadcast
            )
        )

        return UpdateRouteResult(success=True, errors=[])