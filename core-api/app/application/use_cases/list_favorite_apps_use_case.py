# app/application/use_cases/list_favorite_apps_use_case.py

from typing import List
from app.application.unit_of_work import UnitOfWork

class ListFavoriteAppsUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow


    def execute(self, user_id: str) -> List[str]:
        return self.favorite_repo.list_user_favorites(user_id)