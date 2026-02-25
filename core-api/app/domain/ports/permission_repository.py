# app/domain/ports/permission_repository.py

from typing import Protocol, Optional, List
from uuid import UUID
from app.infrastructure.db.models.permission import Permission


class PermissionRepository(Protocol):

    def get(self, permission_id: UUID) -> Optional[Permission]:
        ...

    def get_by_code(self, code: str) -> Optional[Permission]:
        ...

    def list(self) -> List[Permission]:
        ...

    def add(self, permission: Permission) -> None:
        ...

    def delete(self, permission_id: UUID) -> None:
        ...