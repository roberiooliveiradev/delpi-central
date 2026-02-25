# app/domain/ports/plugin_permission_repository_port.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class PluginPermissionRepositoryPort(ABC):

    @abstractmethod
    def bulk_create(self, permissions: List[Dict[str, Any]]) -> None:
        ...

    @abstractmethod
    def delete_by_module(self, module: str) -> None:
        ...