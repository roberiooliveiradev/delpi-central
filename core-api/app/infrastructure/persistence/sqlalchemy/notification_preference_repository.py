# app/infrastructure/persistence/sqlalchemy/notification_preference_repository.py

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.application.services.notification_catalog_service import NotificationCatalogService
from app.domain.ports.notification_preference_repository import NotificationPreferenceRepository
from app.infrastructure.db.models.user_notification_preference import UserNotificationPreference


class SqlAlchemyNotificationPreferenceRepository(NotificationPreferenceRepository):

    def __init__(self, session: Session):
        self.session = session

    def get_muted_categories(self, user_id: str) -> list[str]:
        row = self._get_row(user_id)
        if not row or not row.muted_categories:
            return []
        return list(row.muted_categories)

    def set_muted_categories(self, user_id: str, muted_categories: list[str]) -> None:
        row = self._get_row(user_id)
        if row:
            row.muted_categories = muted_categories
            row.updated_at = datetime.utcnow()
            return

        self.session.add(
            UserNotificationPreference(
                user_id=UUID(user_id),
                muted_categories=muted_categories,
            )
        )

    def is_category_muted(self, user_id: str, category: str) -> bool:
        normalized = (category or "").strip().lower()
        if normalized not in NotificationCatalogService.get().mutable_categories:
            return False
        return normalized in self.get_muted_categories(user_id)

    def filter_user_ids_accepting_category(self, user_ids: list[str], category: str) -> list[str]:
        normalized_category = (category or "").strip().lower()
        if normalized_category not in NotificationCatalogService.get().mutable_categories:
            return list(user_ids)

        if not user_ids:
            return []

        uuid_ids = [UUID(user_id) for user_id in user_ids]
        rows = (
            self.session.query(UserNotificationPreference)
            .filter(UserNotificationPreference.user_id.in_(uuid_ids))
            .all()
        )
        muted_by_user = {
            str(row.user_id): set(row.muted_categories or []) for row in rows
        }

        return [
            user_id
            for user_id in user_ids
            if normalized_category not in muted_by_user.get(user_id, set())
        ]

    def _get_row(self, user_id: str) -> UserNotificationPreference | None:
        return self.session.get(UserNotificationPreference, UUID(user_id))
