# app/domain/ports/group_role_repository_port.py

from typing import Protocol, List, Tuple
from uuid import UUID


class GroupRoleRepositoryPort(Protocol):

    def list_role_ids(self, group_id: UUID) -> List[UUID]:
        ...

    def list_group_role_ids_by_role_ids(
        self,
        role_ids: List[UUID],
    ) -> List[Tuple[UUID, UUID]]:
        ...

    def replace_roles(self, group_id: UUID, role_ids: List[UUID]) -> None:
        ...

    def add_role(self, group_id: UUID, role_id: UUID) -> None:
        ...

    def remove_role(self, group_id: UUID, role_id: UUID) -> None:
        ...

    def delete_by_role_id(self, role_id: UUID) -> None:
        ...

    def delete_by_group_id(self, group_id: UUID) -> None:
        ...