# app/domain/ports/user_repository_port.py

from typing import Protocol, Optional, List
from dataclasses import dataclass
from uuid import UUID
from datetime import datetime


@dataclass(frozen=True)
class UserDTO:
    id: UUID
    email: str
    name: str
    active: bool
    is_superadmin: bool
    last_login_at: datetime | None


class UserRepositoryPort(Protocol):

    # =========================
    # Queries
    # =========================

    def get_by_id(self, user_id: UUID) -> Optional[UserDTO]:
        ...

    def get_by_email(self, email: str) -> Optional[UserDTO]:
        ...

    def list_all(self) -> List[UserDTO]:
        ...


    # =========================
    # Commands
    # =========================

    def create(
        self,
        *,
        id: UUID,
        email: str,
        name: str,
        is_superadmin: bool = False,
    ) -> None:
        ...

    def update_name(self, user_id: UUID, name: str) -> None:
        ...

    def set_active(self, user_id: UUID, active: bool) -> None:
        ...

    def set_superadmin(self, user_id: UUID, is_superadmin: bool) -> None:
        ...

    def update_last_login(self, user_id: UUID, timestamp: datetime) -> None:
        ...

    def delete(self, user_id: UUID) -> None:
        ...

    def list_paginated(
        self,
        *,
        q:str | None,
        page: int,
        page_size: int,
        sort: str,
        direction: str
    ) -> tuple[list[UserDTO], int]:
        ...

    def count_superadmins(self) -> int:
        ...