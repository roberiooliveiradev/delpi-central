# app/infrastructure/persistence/sqlalchemy/app_usage_repository.py

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.infrastructure.db.models import App, AppUsageEvent


class SqlAlchemyAppUsageRepository:
    def __init__(self, session: Session):
        self.session = session

    def has_recent_open(
        self,
        *,
        user_id: UUID,
        app_id: str,
        since: datetime,
    ) -> bool:
        exists = (
            self.session.query(AppUsageEvent.id)
            .filter(
                AppUsageEvent.user_id == user_id,
                AppUsageEvent.app_id == app_id,
                AppUsageEvent.opened_at >= since,
            )
            .first()
        )
        return exists is not None

    def record_open(
        self,
        *,
        user_id: UUID,
        app_id: str,
        route_path: str | None,
        opened_at: datetime,
    ) -> None:
        self.session.add(
            AppUsageEvent(
                id=uuid4(),
                user_id=user_id,
                app_id=app_id,
                route_path=route_path,
                opened_at=opened_at,
            )
        )

    def top_apps_by_unique_users(
        self,
        *,
        since: datetime,
        limit: int = 5,
    ) -> list[dict]:
        rows = (
            self.session.query(
                AppUsageEvent.app_id,
                App.name,
                func.count(func.distinct(AppUsageEvent.user_id)).label("user_count"),
            )
            .join(App, App.id == AppUsageEvent.app_id)
            .filter(AppUsageEvent.opened_at >= since)
            .group_by(AppUsageEvent.app_id, App.name)
            .order_by(func.count(func.distinct(AppUsageEvent.user_id)).desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": row.app_id,
                "name": row.name,
                "count": int(row.user_count),
            }
            for row in rows
        ]

    def ghost_active_apps(self, *, since: datetime) -> list[dict]:
        used_rows = (
            self.session.query(AppUsageEvent.app_id)
            .filter(AppUsageEvent.opened_at >= since)
            .distinct()
            .all()
        )
        used_ids = [row[0] for row in used_rows]

        query = self.session.query(App.id, App.name).filter(App.active.is_(True))

        if used_ids:
            query = query.filter(~App.id.in_(used_ids))

        rows = query.order_by(App.name.asc()).all()
        return [{"id": row.id, "name": row.name} for row in rows]

    def count_distinct_apps_used(self, *, since: datetime) -> int:
        value = (
            self.session.query(func.count(func.distinct(AppUsageEvent.app_id)))
            .filter(AppUsageEvent.opened_at >= since)
            .scalar()
        )
        return int(value or 0)
