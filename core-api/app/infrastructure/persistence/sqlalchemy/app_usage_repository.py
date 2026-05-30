# app/infrastructure/persistence/sqlalchemy/app_usage_repository.py

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.infrastructure.db.models import App, AppUsageEvent

BACKEND_ONLY_APP_TYPE = "backend-only"


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
        caller_app_id: str | None = None,
    ) -> None:
        self.session.add(
            AppUsageEvent(
                id=uuid4(),
                user_id=user_id,
                app_id=app_id,
                route_path=route_path,
                caller_app_id=caller_app_id,
                opened_at=opened_at,
            )
        )

    def delete_events_for_user(self, *, user_id: UUID) -> int:
        deleted = (
            self.session.query(AppUsageEvent)
            .filter(AppUsageEvent.user_id == user_id)
            .delete(synchronize_session=False)
        )
        return int(deleted or 0)

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
        """Apps com UI ativas sem evento de uso no período (exclui backend-only)."""
        used_rows = (
            self.session.query(AppUsageEvent.app_id)
            .filter(AppUsageEvent.opened_at >= since)
            .distinct()
            .all()
        )
        used_ids = [row[0] for row in used_rows]

        query = self.session.query(App.id, App.name).filter(
            App.active.is_(True),
            App.type != BACKEND_ONLY_APP_TYPE,
        )

        if used_ids:
            query = query.filter(~App.id.in_(used_ids))

        rows = query.order_by(App.name.asc()).all()
        return [{"id": row.id, "name": row.name} for row in rows]

    def count_trackable_active_apps(self) -> int:
        """Apps ativas com interface no portal (microfrontend/iframe)."""
        value = (
            self.session.query(func.count(App.id))
            .filter(
                App.active.is_(True),
                App.type != BACKEND_ONLY_APP_TYPE,
            )
            .scalar()
        )
        return int(value or 0)

    def count_distinct_apps_used(self, *, since: datetime) -> int:
        value = (
            self.session.query(func.count(func.distinct(AppUsageEvent.app_id)))
            .filter(AppUsageEvent.opened_at >= since)
            .scalar()
        )
        return int(value or 0)

    def list_least_engaged_users(
        self,
        *,
        since: datetime,
        limit: int = 15,
    ) -> list[dict]:
        from app.infrastructure.db.models import User

        usage_subq = (
            self.session.query(
                AppUsageEvent.user_id.label("user_id"),
                func.count(func.distinct(AppUsageEvent.app_id)).label("apps_used"),
                func.count(AppUsageEvent.id).label("total_opens"),
                func.max(AppUsageEvent.opened_at).label("last_app_usage_at"),
            )
            .filter(AppUsageEvent.opened_at >= since)
            .group_by(AppUsageEvent.user_id)
            .subquery()
        )

        rows = (
            self.session.query(
                User.id,
                User.name,
                User.email,
                User.last_login_at,
                User.is_superadmin,
                func.coalesce(usage_subq.c.apps_used, 0).label("apps_used"),
                func.coalesce(usage_subq.c.total_opens, 0).label("total_opens"),
                usage_subq.c.last_app_usage_at,
            )
            .outerjoin(usage_subq, User.id == usage_subq.c.user_id)
            .filter(User.active.is_(True))
            .order_by(
                func.coalesce(usage_subq.c.apps_used, 0).asc(),
                func.coalesce(usage_subq.c.total_opens, 0).asc(),
                User.last_login_at.asc().nullsfirst(),
                User.name.asc(),
            )
            .limit(max(1, limit))
            .all()
        )

        result: list[dict] = []
        for row in rows:
            last_app_usage = row.last_app_usage_at
            last_login = row.last_login_at
            result.append(
                {
                    "id": row.id,
                    "name": row.name,
                    "email": row.email,
                    "is_superadmin": bool(row.is_superadmin),
                    "apps_used": int(row.apps_used or 0),
                    "total_opens": int(row.total_opens or 0),
                    "last_app_usage_at": last_app_usage,
                    "last_login_at": last_login,
                }
            )
        return result
