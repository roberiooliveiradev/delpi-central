# app/domain/ports/favorite_repository.py

from typing import Protocol, List
from uuid import UUID
from app.infrastructure.db.models.user_favorite_app import UserFavoriteApp


class FavoriteRepository(Protocol):

    def list_by_user(self, user_id: UUID) -> List[UserFavoriteApp]:
        ...

    def add(self, favorite: UserFavoriteApp) -> None:
        ...

    def remove(self, user_id: UUID, app_id: str) -> None:
        ...