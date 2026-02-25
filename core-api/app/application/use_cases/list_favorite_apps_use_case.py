# app/application/use_cases/list_favorite_apps_use_case.py

from typing import List


class ListFavoriteAppsUseCase:

    def __init__(self, favorite_repo):
        self.favorite_repo = favorite_repo

    def execute(self, user_id: str) -> List[str]:
        return self.favorite_repo.list_user_favorites(user_id)