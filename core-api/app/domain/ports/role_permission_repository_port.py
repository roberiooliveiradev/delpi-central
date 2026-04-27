# app/domain/ports/role_permission_repository_port.py

from typing import Protocol, List
from uuid import UUID


class RolePermissionRepositoryPort(Protocol):
    def list_permission_codes(self, role_id: UUID) -> List[str]:
        ...

    def list_permission_ids(self, role_id: UUID) -> List[UUID]:
        ...

    def list_role_ids_by_permission_id(self, permission_id: UUID) -> List[UUID]:
        ...

    def replace_permissions_by_ids(
        self,
        role_id: UUID,
        permission_ids: List[str],
    ) -> None:
        """
        Substitui o conjunto de permissions do role pelo conjunto fornecido.
        Deve ser transacional sob o UoW.
        """
        ...

    def replace_permissions_by_codes(
        self,
        role_id: UUID,
        permission_codes: List[str],
    ) -> None:
        """
        Substitui o conjunto de permissions do role pelo conjunto fornecido.
        Deve ser transacional sob o UoW.
        """
        ...

    def add_permission_by_code(
        self,
        role_id: UUID,
        permission_code: str,
    ) -> None:
        ...

    def add_permission_by_id(
        self,
        role_id: UUID,
        permission_id: str,
    ) -> None:
        ...

    def remove_permission_by_code(
        self,
        role_id: UUID,
        permission_code: str,
    ) -> None:
        ...

    def delete_by_role_id(self, role_id: UUID) -> None:
        ...