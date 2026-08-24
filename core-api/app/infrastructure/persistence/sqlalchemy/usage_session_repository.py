# app/infrastructure/persistence/sqlalchemy/usage_session_repository.py

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.infrastructure.db.models import UsageSession


class SqlAlchemyUsageSessionRepository:
    def __init__(self, session: Session):
        self.session = session

    def record_session(
        self,
        *,
        user_id: UUID,
        app_id: str | None,
        route_path: str | None,
        started_at: datetime,
        ended_at: datetime,
        duration_seconds: int,
        source: str,
        socket_session_id: str | None = None,
    ) -> None:
        self.session.add(
            UsageSession(
                id=uuid4(),
                user_id=user_id,
                app_id=app_id,
                route_path=route_path,
                started_at=started_at,
                ended_at=ended_at,
                duration_seconds=duration_seconds,
                source=source,
                socket_session_id=socket_session_id,
            )
        )

    def delete_sessions_for_user(self, *, user_id: UUID) -> int:
        deleted = (
            self.session.query(UsageSession)
            .filter(UsageSession.user_id == user_id)
            .delete(synchronize_session=False)
        )
        return int(deleted or 0)

    def count_sessions_since(self, *, since: datetime) -> int:
        value = (
            self.session.query(UsageSession.id)
            .filter(UsageSession.started_at >= since)
            .count()
        )
        return int(value or 0)
