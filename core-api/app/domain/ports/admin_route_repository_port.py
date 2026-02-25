# admin_route_repository_port

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass(frozen=True)
class AdminRouteDTO:
    id: str
    app_id: str
    path: str
    label: Optional[str]
    icon: Optional[str]
    permission_code: Optional[str]
    order: int
    show_in_menu: bool
    active: bool


class AdminRouteRepositoryPort(ABC):

    @abstractmethod
    def list_by_app(self, app_id: str) -> List[AdminRouteDTO]:
        ...

    @abstractmethod
    def get(self, route_id: str) -> Optional[AdminRouteDTO]:
        ...

    @abstractmethod
    def create(self, data: Dict[str, Any]) -> AdminRouteDTO:
        ...

    @abstractmethod
    def update(self, route_id: str, patch: Dict[str, Any]) -> None:
        ...

    @abstractmethod
    def delete(self, route_id: str) -> None:
        ...

    @abstractmethod
    def bulk_delete(self, route_ids: List[str]) -> int:
        ...