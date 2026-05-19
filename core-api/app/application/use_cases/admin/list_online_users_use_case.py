# app/application/use_cases/admin/list_online_users_use_case.py

from uuid import UUID

from app.application.unit_of_work import UnitOfWork
from app.domain.ports.user_presence_store_port import UserPresenceStorePort
from app.infrastructure.presence.presence_store_provider import get_user_presence_store


class ListOnlineUsersUseCase:

    def __init__(
        self,
        uow: UnitOfWork,
        presence_store: UserPresenceStorePort | None = None,
    ):
        self.uow = uow
        self.presence_store = presence_store or get_user_presence_store()

    def execute(self) -> dict:
        summaries = self.presence_store.list_online()
        if not summaries:
            return {"items": [], "total": 0}

        user_ids: list[UUID] = []
        for summary in summaries:
            try:
                user_ids.append(UUID(str(summary.user_id)))
            except ValueError:
                continue

        users = self.uow.users.get_by_ids(user_ids)
        users_by_id = {str(user.id): user for user in users}

        items = []
        for summary in summaries:
            user = users_by_id.get(str(summary.user_id))
            items.append(
                {
                    "userId": str(summary.user_id),
                    "name": user.name if user else None,
                    "email": user.email if user else None,
                    "active": user.active if user else None,
                    "connectionCount": summary.connection_count,
                    "connectedAt": summary.connected_at.isoformat() + "Z",
                    "lastSeenAt": summary.last_seen_at.isoformat() + "Z",
                }
            )

        return {"items": items, "total": len(items)}
