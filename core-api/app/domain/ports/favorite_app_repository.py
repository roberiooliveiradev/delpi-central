# app/domain/ports/favorite_app_repository.py

from typing import Protocol, List


class FavoriteAppRepository(Protocol):

    def list_user_favorites(self, user_id: str) -> List[str]:
        ...

    def exists(self, user_id: str, app_id: str) -> bool:
        ...

    def add(self, user_id: str, app_id: str) -> None:
        ...

    def remove(self, user_id: str, app_id: str) -> None:
        ...