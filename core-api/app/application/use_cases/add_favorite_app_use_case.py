# app/application/use_cases/add_favorite_app_use_case.py

class AddFavoriteAppUseCase:

    def __init__(self, uow):
        self.uow = uow

    def execute(self, user_id: str, app_id: str):

        # valida app existente
        apps = self.uow.app_queries.list_active_apps_with_routes()
        if not any(a.id == app_id for a in apps):
            raise ValueError("App não encontrada")

        if self.uow.favorites.exists(user_id, app_id):
            return  # idempotente

        self.uow.favorites.add(user_id, app_id)
        self.uow.commit()