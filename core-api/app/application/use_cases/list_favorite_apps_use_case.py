# app/application/use_cases/list_favorite_apps_use_case.py

from typing import List, Dict
from app.application.unit_of_work import UnitOfWork


class ListFavoriteAppsUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, user_id: str) -> List[Dict]:
        return self.uow.favorites.list_user_favorites(user_id)