# app/domain/ports/group_role_repository_port.py

from typing import Protocol, List
from uuid import UUID


class GroupRoleRepositoryPort(Protocol):

    def list_role_ids(self, group_id: UUID) -> List[UUID]:
        ...

    def replace_roles(self, group_id: UUID, role_ids: List[UUID]) -> None:
        ...

    def add_role(self, group_id: UUID, role_id: UUID) -> None:
        ...

    def remove_role(self, group_id: UUID, role_id: UUID) -> None:
        ...