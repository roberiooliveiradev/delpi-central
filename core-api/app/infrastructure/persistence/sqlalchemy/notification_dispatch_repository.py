# app/infrastructure/persistence/sqlalchemy/notification_dispatch_repository.py

import uuid
from datetime import datetime
from typing import List, Tuple
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.application.dto.list_notification_dispatches_filters import (
    ListNotificationDispatchesFilters,
)
from app.domain.notifications.notification_constants import ALLOWED_NOTIFICATION_CATEGORIES
from app.domain.ports.notification_dispatch_repository import (
    NotificationDispatchDTO,
    NotificationDispatchRepository,
)
from app.infrastructure.db.models.notification_dispatch import NotificationDispatch

ALLOWED_DISPATCH_STATUSES = frozenset({"pending", "processing", "completed", "failed"})


class SqlAlchemyNotificationDispatchRepository(NotificationDispatchRepository):

    def __init__(self, session: Session):
        self.session = session

    def create(self, dispatch: NotificationDispatchDTO) -> UUID:
        model = NotificationDispatch(
            id=uuid.uuid4(),
            created_by_user_id=UUID(dispatch.created_by_user_id)
            if dispatch.created_by_user_id
            else None,
            status=dispatch.status,
            scheduled_at=dispatch.scheduled_at,
            processed_at=dispatch.processed_at,
            broadcast=dispatch.broadcast,
            recipient_count=dispatch.recipient_count,
            created_count=dispatch.created_count,
            title=dispatch.title,
            category=dispatch.category,
            presentation=dispatch.presentation,
            template_id=dispatch.template_id,
            source_app=dispatch.source_app,
            payload=dispatch.payload,
            notification_ids=dispatch.notification_ids,
            error_message=dispatch.error_message,
        )
        self.session.add(model)
        return model.id

    def get(self, dispatch_id: UUID) -> NotificationDispatchDTO | None:
        row = self.session.get(NotificationDispatch, dispatch_id)
        if not row:
            return None
        return self._to_dto(row)

    def delete(self, dispatch_id: UUID) -> None:
        row = self.session.get(NotificationDispatch, dispatch_id)
        if row:
            self.session.delete(row)

    def update(self, dispatch: NotificationDispatchDTO) -> None:
        row = self.session.get(NotificationDispatch, dispatch.id)
        if not row:
            return

        row.status = dispatch.status
        row.scheduled_at = dispatch.scheduled_at
        row.processed_at = dispatch.processed_at
        row.broadcast = dispatch.broadcast
        row.recipient_count = dispatch.recipient_count
        row.created_count = dispatch.created_count
        row.title = dispatch.title
        row.category = dispatch.category
        row.presentation = dispatch.presentation
        row.template_id = dispatch.template_id
        row.source_app = dispatch.source_app
        row.payload = dispatch.payload
        row.notification_ids = dispatch.notification_ids
        row.error_message = dispatch.error_message

    def list_filtered(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        filters: ListNotificationDispatchesFilters | None = None,
    ) -> Tuple[List[NotificationDispatchDTO], int]:
        query = self.session.query(NotificationDispatch)
        query = self._apply_filters(query, filters)

        total = query.count()
        rows = (
            query.order_by(NotificationDispatch.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        return [self._to_dto(row) for row in rows], total

    @staticmethod
    def _apply_filters(query, filters: ListNotificationDispatchesFilters | None):
        if not filters:
            return query

        if filters.status:
            normalized_status = filters.status.strip().lower()
            if normalized_status in ALLOWED_DISPATCH_STATUSES:
                query = query.filter(
                    NotificationDispatch.status == normalized_status  # type: ignore[arg-type]
                )

        if filters.category:
            normalized_category = filters.category.strip().lower()
            if normalized_category in ALLOWED_NOTIFICATION_CATEGORIES:
                query = query.filter(NotificationDispatch.category == normalized_category)

        if filters.source_app:
            normalized_app = filters.source_app.strip().lower()
            if normalized_app:
                query = query.filter(
                    NotificationDispatch.source_app.ilike(normalized_app)  # type: ignore[attr-defined]
                )

        if filters.search:
            term = f"%{filters.search.strip()}%"
            if term != "%%":
                query = query.filter(
                    or_(
                        NotificationDispatch.title.ilike(term),  # type: ignore[attr-defined]
                        NotificationDispatch.template_id.ilike(term),  # type: ignore[attr-defined]
                    )
                )

        revoked_at = NotificationDispatch.payload["revokedAt"].as_string()
        if filters.revoked == "revoked":
            query = query.filter(revoked_at.isnot(None), revoked_at != "")
        elif filters.revoked == "active":
            query = query.filter(or_(revoked_at.is_(None), revoked_at == ""))

        if filters.date_from:
            query = query.filter(NotificationDispatch.created_at >= filters.date_from)
        if filters.date_to:
            query = query.filter(NotificationDispatch.created_at <= filters.date_to)

        return query

    def list_due_pending(self, *, limit: int = 20) -> List[NotificationDispatchDTO]:
        now = datetime.utcnow()
        rows = (
            self.session.query(NotificationDispatch)
            .filter(
                NotificationDispatch.status == "pending",
                or_(
                    NotificationDispatch.scheduled_at.is_(None),
                    NotificationDispatch.scheduled_at <= now,
                ),
            )
            .order_by(NotificationDispatch.scheduled_at.asc().nullsfirst())
            .limit(limit)
            .all()
        )
        return [self._to_dto(row) for row in rows]

    @staticmethod
    def _to_dto(row: NotificationDispatch) -> NotificationDispatchDTO:
        return NotificationDispatchDTO(
            id=row.id,
            created_by_user_id=str(row.created_by_user_id) if row.created_by_user_id else None,
            status=row.status,
            scheduled_at=row.scheduled_at,
            processed_at=row.processed_at,
            broadcast=row.broadcast,
            recipient_count=row.recipient_count,
            created_count=row.created_count,
            title=row.title,
            category=row.category,
            presentation=row.presentation,
            template_id=row.template_id,
            source_app=row.source_app,
            payload=row.payload or {},
            notification_ids=row.notification_ids,
            error_message=row.error_message,
            created_at=row.created_at,
        )
