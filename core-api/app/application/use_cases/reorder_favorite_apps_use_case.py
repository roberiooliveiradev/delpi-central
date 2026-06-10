# app/application/use_cases/reorder_favorite_apps_use_case.py

from typing import List

from app.application.unit_of_work import UnitOfWork


class ReorderFavoriteAppsUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, user_id: str, app_ids: List[str]):
        favorites = self.uow.favorites.list_user_favorites(user_id)
        favorite_ids = {fav["id"] for fav in favorites}

        if not app_ids:
            return {"ok": True}

        if len(app_ids) != len(set(app_ids)):
            raise ValueError("Lista de favoritos contém IDs duplicados")

        if set(app_ids) != favorite_ids:
            raise ValueError("Lista de favoritos inválida")

        self.uow.favorites.reorder(user_id, app_ids)

        return {"ok": True}
