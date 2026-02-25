# app/domain/ports/role_repository.py

from typing import Protocol, Optional, List
from uuid import UUID
from app.infrastructure.db.models.role import Role


class RoleRepository(Protocol):

    def get(self, role_id: UUID) -> Optional[Role]:
        ...

    def get_by_name(self, name: str) -> Optional[Role]:
        ...

    def list(self) -> List[Role]:
        ...

    def add(self, role: Role) -> None:
        ...

    def delete(self, role_id: UUID) -> None:
        ...