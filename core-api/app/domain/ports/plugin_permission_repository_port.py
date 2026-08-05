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

    @abstractmethod
    def list_by_module(self, module: str) -> List[Dict[str, Any]]:
        """
        Retorna permissões do módulo como dicts:
          { "id": str, "code": str, "name": str, "description": str | None, "module": str | None }
        """
        ...

    @abstractmethod
    def sync_module(self, module: str, desired: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Reconcilia permissions do módulo por `code` (identidade estável).

        - codes que permanecem: UPDATE name/description; UUID preservado (grants intactos)
        - codes novos: INSERT
        - codes removidos: DELETE (CASCADE remove só esses grants)

        Cada item em desired:
          { "code": str, "name": str, "description": str | None }
        O campo module é forçado para o argumento `module`.

        Retorna resumo: { "kept": int, "inserted": int, "deleted": int, "codes": [...] }
        """
        ...
