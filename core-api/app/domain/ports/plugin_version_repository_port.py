# app/domain/ports/plugin_version_repository_port.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class PluginVersionRepositoryPort(ABC):

    @abstractmethod
    def exists(self, plugin_id: str, version: str) -> bool:
        ...

    @abstractmethod
    def create(self, data: Dict[str, Any]) -> None:
        ...

    @abstractmethod
    def list_versions(self, plugin_id: str) -> List[Dict[str, Any]]:
        ...

    @abstractmethod
    def get_version(self, plugin_id: str, version: str) -> Optional[Dict[str, Any]]:
        ...

    @abstractmethod
    def delete_by_app(self, plugin_id: str) -> None:
        ...