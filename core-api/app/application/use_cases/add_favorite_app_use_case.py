# app/application/use_cases/add_favorite_app_use_case.py

from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent


class AddFavoriteAppUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, user_id: str, app_id: str):

        # 1️⃣ Valida app existente
        apps = self.uow.app_queries.list_active_apps_with_routes()
        if not any(a.id == app_id for a in apps):
            raise ValueError("App não encontrada")

        # 2️⃣ Idempotência
        if self.uow.favorites.exists(user_id, app_id):
            return {"ok": True}

        # 3️⃣ Regra de negócio
        self.uow.favorites.add(user_id, app_id)

        # 4️⃣ Evento direcionado ao usuário
        self.uow.collect_event(
            AdminChangedEvent(
                entity="favorites",
                action="favorite_added",
                payload={
                    "appId": app_id,
                },
                target_user_id=user_id,
            )
        )

        return {"ok": True}