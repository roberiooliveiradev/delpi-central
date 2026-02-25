# app/domain/ports/group_repository.py

from typing import Protocol, Optional, List
from uuid import UUID
from app.infrastructure.db.models.group import Group


class GroupRepository(Protocol):

    def get(self, group_id: UUID) -> Optional[Group]:
        ...

    def get_by_name(self, name: str) -> Optional[Group]:
        ...

    def list(self) -> List[Group]:
        ...

    def add(self, group: Group) -> None:
        ...

    def delete(self, group_id: UUID) -> None:
        ...