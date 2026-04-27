# app/domain/ports/user_role_repository_port.py

from typing import Protocol, List
from uuid import UUID


class UserRoleRepositoryPort(Protocol):

    def list_role_ids(self, user_id: UUID) -> List[UUID]:
        ...

    def list_user_ids_by_role_id(self, role_id: UUID) -> List[UUID]:
        ...

    def replace_roles(self, user_id: UUID, role_ids: List[UUID]) -> None:
        ...

    def add_role(self, user_id: UUID, role_id: UUID) -> None:
        ...

    def remove_role(self, user_id: UUID, role_id: UUID) -> None:
        ...

    def delete_by_role_id(self, role_id: UUID) -> None:
        ...

    def delete_by_user_id(self, user_id: UUID) -> None:
        ...