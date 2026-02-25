# app/domain/ports/plugin_manifest_repository_port.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class PluginManifestRepositoryPort(ABC):

    @abstractmethod
    def save(self, plugin_id: str, manifest: Dict[str, Any], checksum: str) -> None:
        ...

    @abstractmethod
    def get(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        ...

    @abstractmethod
    def list_all(self) -> List[Dict[str, Any]]:
        ...

    @abstractmethod
    def delete(self, plugin_id: str) -> None:
        ...