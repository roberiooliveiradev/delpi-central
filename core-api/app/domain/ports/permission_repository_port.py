# app/domain/ports/permission_repository_port.py

from typing import Protocol, List, Tuple
from dataclasses import dataclass
from uuid import UUID


@dataclass
class PermissionDTO:
    id: UUID
    code: str
    name: str
    description: str | None
    module: str | None


class PermissionRepositoryPort(Protocol):

    def list_all(self) -> List[PermissionDTO]:
        ...

    def get_by_code(self, code: str) -> PermissionDTO | None:
        ...

    def exists_by_code(self, code: str) -> bool:
        ...

    def create(self, code: str, name: str, module: str, description: str | None) -> UUID:
        ...

    def delete(self, permission_id: UUID) -> None:
        ...

    def list_by_module(self, module: str) -> List[PermissionDTO]:
        ...
    
    def list_paginated(
        self,
        *,
        q: str | None,
        page: int,
        page_size: int,
        sort: str,
        direction: str,
    ) -> Tuple[List[PermissionDTO], int]:
            ...