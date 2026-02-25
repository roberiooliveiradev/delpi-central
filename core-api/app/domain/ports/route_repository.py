# app/domain/ports/route_repository.py

from typing import Protocol, List
from app.infrastructure.db.models.app_route import AppRoute


class RouteRepository(Protocol):

    def list_active_by_app(self, app_id: str) -> List[AppRoute]:
        ...