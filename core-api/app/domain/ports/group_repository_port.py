# app/domain/ports/group_repository_port.py

from typing import Protocol, List
from dataclasses import dataclass
from uuid import UUID


@dataclass
class GroupDTO:
    id: UUID
    name: str
    description: str | None


class GroupRepositoryPort(Protocol):

    def list_all(self) -> List[GroupDTO]:
        ...

    def exists_by_name(self, name: str) -> bool:
        ...

    def create(self, name: str, description: str | None) -> UUID:
        ...

    def delete(self, group_id: UUID) -> None:
        ...