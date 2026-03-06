# app/domain/ports/user_group_repository_port.py

from typing import Protocol, List
from uuid import UUID


class UserGroupRepositoryPort(Protocol):
    def list_group_ids(self, user_id: UUID) -> List[UUID]:
        ...

    def replace_groups(self, user_id: UUID, group_ids: List[UUID]) -> None:
        ...

    def add_group(self, user_id: UUID, group_id: UUID) -> None:
        ...

    def remove_group(self, user_id: UUID, group_id: UUID) -> None:
        ...


    def delete_by_group_id(self, group_id: UUID) -> None:
        ...

    def delete_by_user_id(self, user_id: UUID) -> None:
        ...