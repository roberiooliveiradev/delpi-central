# app/domain/ports/user_repository.py

from typing import Protocol, Optional
from uuid import UUID
from app.infrastructure.db.models.user import User


class UserRepository(Protocol):

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        ...

    def get_by_email(self, email: str) -> Optional[User]:
        ...

    def add(self, user: User) -> None:
        ...

    def update(self, user: User) -> None:
        ...

    def delete(self, user_id: UUID) -> None:
        ...