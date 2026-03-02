# app/application/use_cases/list_favorite_apps_use_case.py

from typing import List, Dict

from app.application.unit_of_work import UnitOfWork
from app.application.services.app_authorization_service import (
    AppAuthorizationService,
)


class ListFavoriteAppsUseCase:
    """
    Lista aplicações favoritas do usuário,
    garantindo que apenas apps autorizadas sejam retornadas.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self._auth_service = AppAuthorizationService()

    def execute(
        self,
        user_id: str,
        permissions: list[str],
        is_superadmin: bool,
    ) -> List[Dict]:

        with self.uow:

            favorites = self.uow.favorites.list_user_favorites(user_id)

            if not favorites:
                return []

            apps = self.uow.app_queries.list_active_apps_with_routes()

            authorized_ids = self._auth_service.filter_app_ids(
                apps=apps,
                permissions=permissions,
                is_superadmin=is_superadmin,
            )

            return [
                fav for fav in favorites
                if fav["id"] in authorized_ids
            ]