# app/domain/ports/favorite_app_repository.py

from typing import Protocol, List, Dict


class FavoriteAppRepository(Protocol):

    def list_user_favorites(self, user_id: str) -> List[Dict]:
        ...

    def exists(self, user_id: str, app_id: str) -> bool:
        ...

    def add(self, user_id: str, app_id: str) -> None:
        ...

    def remove(self, user_id: str, app_id: str) -> None:
        ...

    def delete_by_user_id(self, user_id: str) -> None:
        ...

    def reorder(self, user_id: str, app_ids: List[str]) -> None:
        ...