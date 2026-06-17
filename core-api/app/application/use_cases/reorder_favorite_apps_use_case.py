# app/application/use_cases/reorder_favorite_apps_use_case.py

from typing import List, Set

from app.application.unit_of_work import UnitOfWork
from app.application.services.app_authorization_service import (
    AppAuthorizationService,
)


class ReorderFavoriteAppsUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self._auth_service = AppAuthorizationService()

    def execute(
        self,
        user_id: str,
        app_ids: List[str],
        permissions: list[str],
        is_superadmin: bool,
    ):
        favorites = self.uow.favorites.list_user_favorites(user_id)
        all_ordered_ids = [fav["id"] for fav in favorites]
        favorite_ids = set(all_ordered_ids)

        if not app_ids:
            return {"ok": True}

        if len(app_ids) != len(set(app_ids)):
            raise ValueError("Lista de favoritos contém IDs duplicados")

        authorized_ids = self._authorized_favorite_ids(
            favorites=favorites,
            permissions=permissions,
            is_superadmin=is_superadmin,
        )

        if set(app_ids) != authorized_ids:
            raise ValueError("Lista de favoritos inválida")

        hidden_ids = favorite_ids - authorized_ids
        merged_ids = (
            app_ids
            if not hidden_ids
            else self._merge_reorder_with_hidden(
                all_ordered_ids=all_ordered_ids,
                authorized_ids=authorized_ids,
                new_authorized_order=app_ids,
            )
        )

        self.uow.favorites.reorder(user_id, merged_ids)

        return {"ok": True}

    def _authorized_favorite_ids(
        self,
        favorites: list[dict],
        permissions: list[str],
        is_superadmin: bool,
    ) -> Set[str]:
        apps = self.uow.app_queries.list_active_apps_with_routes()
        authorized_app_ids = self._auth_service.filter_app_ids(
            apps=apps,
            permissions=permissions,
            is_superadmin=is_superadmin,
        )
        return {fav["id"] for fav in favorites if fav["id"] in authorized_app_ids}

    @staticmethod
    def _merge_reorder_with_hidden(
        all_ordered_ids: List[str],
        authorized_ids: Set[str],
        new_authorized_order: List[str],
    ) -> List[str]:
        queue = list(new_authorized_order)
        merged: List[str] = []

        for fav_id in all_ordered_ids:
            if fav_id in authorized_ids:
                merged.append(queue.pop(0))
            else:
                merged.append(fav_id)

        return merged
