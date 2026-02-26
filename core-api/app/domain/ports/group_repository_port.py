# app/domain/ports/group_repository_port.py
from typing import Protocol, Optional, List, Tuple
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class GroupDTO:
    id: UUID
    name: str
    description: str | None


class GroupRepositoryPort(Protocol):

    def get(self, group_id: UUID) -> Optional[GroupDTO]:
        ...

    def list_all(self) -> List[GroupDTO]:
        ...

    def list_paginated(
        self,
        *,
        page: int,
        page_size: int,
        sort: str,
        direction: str,
    ) -> Tuple[List[GroupDTO], int]:
        ...

    def create(self, name: str, description: str | None) -> UUID:
        ...

    def update(self, group_id: UUID, name: str, description: str | None) -> None:
        ...

    def delete(self, group_id: UUID) -> None:
        ...