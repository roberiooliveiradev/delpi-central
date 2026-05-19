# app/domain/ports/user_repository_port.py

from typing import Protocol, Optional, List
from dataclasses import dataclass
from uuid import UUID
from datetime import date, datetime


@dataclass(frozen=True)
class UserDTO:
    id: UUID
    email: str
    name: str
    active: bool
    is_superadmin: bool
    last_login_at: datetime | None
    birth_date: date | None = None


class UserRepositoryPort(Protocol):

    # =========================
    # Queries
    # =========================

    def get_by_id(self, user_id: UUID) -> Optional[UserDTO]:
        ...

    def get_by_ids(self, user_ids: list[UUID]) -> list[UserDTO]:
        ...

    def get_by_email(self, email: str) -> Optional[UserDTO]:
        ...

    def list_all(self) -> List[UserDTO]:
        ...

    def list_active_ids_with_birthday_on(self, *, month: int, day: int) -> List[str]:
        ...

    def set_birth_date(self, user_id: UUID, birth_date: date | None) -> None:
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

    def update_identity(self, user_id: UUID, *, name: str, email: str) -> None:
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
        q: str | None,
        page: int,
        page_size: int,
        sort: str,
        direction: str,
        is_superadmin: bool | None = None,
        role_id: UUID | None = None,
        group_id: UUID | None = None,
        online_filter: str | None = None,
        online_user_ids: list[UUID] | None = None,
    ) -> tuple[list[UserDTO], int]:
        ...

    def count_superadmins(self) -> int:
        ...