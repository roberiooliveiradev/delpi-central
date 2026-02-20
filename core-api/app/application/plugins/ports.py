# app/application/plugins/ports.py

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class AppRepository(ABC):

    @abstractmethod
    def get_by_id(self, app_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def create(self, data: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def update_version(self, app_id: str, version: str) -> None:
        pass


class PermissionRepository(ABC):

    @abstractmethod
    def exists_by_code(self, code: str) -> bool:
        pass

    @abstractmethod
    def get_by_code(self, code: str):
        pass

    @abstractmethod
    def bulk_create(self, permissions: List[Dict[str, Any]]) -> None:
        pass


class RouteRepository(ABC):

    @abstractmethod
    def exists_by_path(self, path: str) -> bool:
        pass

    @abstractmethod
    def exists_by_path(self, path: str) -> bool:
        pass

    @abstractmethod
    def bulk_create(self, routes: List[Dict[str, Any]]) -> None:
        pass


class ManifestRepository(ABC):

    @abstractmethod
    def save(self, app_id: str, manifest: Dict[str, Any], checksum: str) -> None:
        pass


class AuditRepository(ABC):

    @abstractmethod
    def log(self, data: Dict[str, Any]) -> None:
        pass


class UnitOfWork(ABC):

    app_repo: AppRepository
    permission_repo: PermissionRepository
    route_repo: RouteRepository
    manifest_repo: ManifestRepository
    audit_repo: AuditRepository

    @abstractmethod
    def commit(self) -> None:
        pass

    @abstractmethod
    def rollback(self) -> None:
        pass