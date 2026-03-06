# app/domain/ports/role_repository_port.py

from typing import Protocol, List
from dataclasses import dataclass
from uuid import UUID


@dataclass
class RoleDTO:
    id: UUID
    name: str
    description: str | None


class RoleRepositoryPort(Protocol):

    def list_all(self) -> List[RoleDTO]:
        ...

    def get(self, role_id: UUID) -> RoleDTO | None:
        ...

    def exists_by_name(self, name: str) -> bool:
        ...

    def create(self, name: str, description: str | None) -> UUID:
        ...

    def update(self, role_id: UUID, name: str, description: str | None) -> None:
        ...

    def delete(self, role_id: UUID) -> None:
        ...
        
    def list_paginated(
        self,
        *,
        q: str | None,
        page: int,
        page_size: int,
        sort: str,
        direction: str
        ) -> tuple[list[RoleDTO], int]:
        ...