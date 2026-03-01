# app/application/use_cases/remove_favorite_app_use_case.py

from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent


class RemoveFavoriteAppUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, user_id: str, app_id: str):

        # 1️⃣ Regra de negócio
        self.uow.favorites.remove(user_id, app_id)

        # 2️⃣ Evento direcionado ao usuário
        self.uow.collect_event(
            AdminChangedEvent(
                entity="favorites",
                action="favorite_removed",
                payload={
                    "userId": user_id,
                    "appId": app_id,
                },
                target_user_id=user_id,
            )
        )

        return {"ok": True}