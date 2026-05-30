# app/application/services/usage_tracking_purge_service.py

from uuid import UUID

from app.application.unit_of_work import UnitOfWork
from app.infrastructure.app_usage.app_usage_live_store_provider import (
    get_app_usage_live_store,
    is_app_usage_enabled,
)
from app.infrastructure.persistence.sqlalchemy.app_usage_repository import (
    SqlAlchemyAppUsageRepository,
)
from app.infrastructure.presence.presence_store_provider import (
    get_user_presence_store,
    is_user_presence_enabled,
)


def purge_usage_tracking_data(uow: UnitOfWork, *, user_id: UUID) -> int:
    repo = SqlAlchemyAppUsageRepository(uow.session)
    deleted = repo.delete_events_for_user(user_id=user_id)

    user_key = str(user_id)
    if is_app_usage_enabled():
        clear_user = getattr(get_app_usage_live_store(), "clear_user", None)
        if callable(clear_user):
            clear_user(user_id=user_key)

    if is_user_presence_enabled():
        clear_user = getattr(get_user_presence_store(), "clear_user", None)
        if callable(clear_user):
            clear_user(user_id=user_key)

    return deleted
