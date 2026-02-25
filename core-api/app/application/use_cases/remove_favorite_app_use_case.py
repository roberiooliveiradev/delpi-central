# app/application/use_cases/remove_favorite_app_use_case.py

class RemoveFavoriteAppUseCase:

    def __init__(self, uow):
        self.uow = uow

    def execute(self, user_id: str, app_id: str):
        self.uow.favorite_apps.remove(user_id, app_id)
        self.uow.commit()