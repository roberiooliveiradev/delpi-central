# app/domain/ports/plugin_route_repository_port.py

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class PluginRouteRepositoryPort(ABC):

    @abstractmethod
    def bulk_create(self, routes: List[Dict[str, Any]]) -> None:
        ...

    @abstractmethod
    def delete_by_app(self, plugin_id: str) -> None:
        ...

    @abstractmethod
    def update_by_app_and_path(
        self,
        plugin_id: str,
        path: str,
        patch: Dict[str, Any],
    ) -> None:
        ...

    @abstractmethod
    def list_by_app(self, plugin_id: str):
        ...
    
    @abstractmethod
    def list_paths_by_app(self, plugin_id: str) -> set[str]:
        ...
    