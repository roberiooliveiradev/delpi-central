# app/infrastructure/persistence/sqlalchemy/engagement_repository.py

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.infrastructure.db.models import App, AppUsageEvent, UsageSession, User, UserConsent
from app.infrastructure.persistence.sqlalchemy.app_usage_repository import (
    BACKEND_ONLY_APP_TYPE,
)
from app.domain.services.usage_tracking_consent_service import (
    USAGE_TRACKING_CONSENT_PURPOSE,
)


class SqlAlchemyEngagementRepository:
    def __init__(self, session: Session):
        self.session = session

    def count_events_since(self, *, since: datetime) -> int:
        value = (
            self.session.query(func.count(AppUsageEvent.id))
            .filter(AppUsageEvent.opened_at >= since)
            .scalar()
        )
        return int(value or 0)

    def count_distinct_active_users(self, *, since: datetime) -> int:
        value = (
            self.session.query(func.count(func.distinct(AppUsageEvent.user_id)))
            .filter(AppUsageEvent.opened_at >= since)
            .scalar()
        )
        return int(value or 0)

    def active_users_by_day(self, *, since: datetime) -> list[dict]:
        day_expr = func.date(AppUsageEvent.opened_at)
        rows = (
            self.session.query(
                day_expr.label("day"),
                func.count(func.distinct(AppUsageEvent.user_id)).label("active_users"),
            )
            .filter(AppUsageEvent.opened_at >= since)
            .group_by(day_expr)
            .order_by(day_expr.asc())
            .all()
        )
        return [
            {
                "date": row.day.isoformat() if hasattr(row.day, "isoformat") else str(row.day),
                "activeUsers": int(row.active_users or 0),
            }
            for row in rows
        ]

    def duration_by_day(self, *, since: datetime) -> list[dict]:
        """Tempo médio por usuário único em cada dia (soma ÷ distinct users)."""
        day_expr = func.date(UsageSession.started_at)
        rows = (
            self.session.query(
                day_expr.label("day"),
                func.coalesce(func.sum(UsageSession.duration_seconds), 0).label(
                    "total_seconds"
                ),
                func.count(func.distinct(UsageSession.user_id)).label("unique_users"),
            )
            .filter(UsageSession.started_at >= since)
            .group_by(day_expr)
            .order_by(day_expr.asc())
            .all()
        )
        series: list[dict] = []
        for row in rows:
            unique_users = int(row.unique_users or 0)
            total_seconds = int(row.total_seconds or 0)
            avg_seconds = (
                int(round(total_seconds / unique_users)) if unique_users > 0 else 0
            )
            series.append(
                {
                    "date": row.day.isoformat()
                    if hasattr(row.day, "isoformat")
                    else str(row.day),
                    "avgSecondsPerUser": avg_seconds,
                }
            )
        return series

    def top_apps_by_opens(self, *, since: datetime, limit: int = 8) -> list[dict]:
        rows = (
            self.session.query(
                AppUsageEvent.app_id,
                App.name,
                func.count(AppUsageEvent.id).label("open_count"),
            )
            .join(App, App.id == AppUsageEvent.app_id)
            .filter(
                AppUsageEvent.opened_at >= since,
                App.type != BACKEND_ONLY_APP_TYPE,
            )
            .group_by(AppUsageEvent.app_id, App.name)
            .order_by(func.count(AppUsageEvent.id).desc())
            .limit(limit)
            .all()
        )
        return [
            {"id": row.app_id, "name": row.name, "count": int(row.open_count or 0)}
            for row in rows
        ]

    def top_apps_by_unique_users(self, *, since: datetime, limit: int = 8) -> list[dict]:
        rows = (
            self.session.query(
                AppUsageEvent.app_id,
                App.name,
                func.count(func.distinct(AppUsageEvent.user_id)).label("user_count"),
            )
            .join(App, App.id == AppUsageEvent.app_id)
            .filter(
                AppUsageEvent.opened_at >= since,
                App.type != BACKEND_ONLY_APP_TYPE,
            )
            .group_by(AppUsageEvent.app_id, App.name)
            .order_by(func.count(func.distinct(AppUsageEvent.user_id)).desc())
            .limit(limit)
            .all()
        )
        return [
            {"id": row.app_id, "name": row.name, "count": int(row.user_count or 0)}
            for row in rows
        ]

    def top_apps_by_duration(self, *, since: datetime, limit: int = 8) -> list[dict]:
        rows = (
            self.session.query(
                UsageSession.app_id,
                App.name,
                func.coalesce(func.sum(UsageSession.duration_seconds), 0).label(
                    "total_seconds"
                ),
            )
            .join(App, App.id == UsageSession.app_id)
            .filter(
                UsageSession.started_at >= since,
                UsageSession.app_id.isnot(None),
                App.type != BACKEND_ONLY_APP_TYPE,
            )
            .group_by(UsageSession.app_id, App.name)
            .order_by(func.sum(UsageSession.duration_seconds).desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": row.app_id,
                "name": row.name,
                "count": int(row.total_seconds or 0),
            }
            for row in rows
        ]

    def top_users_by_activity(self, *, since: datetime, limit: int = 10) -> list[dict]:
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

        duration_subq = (
            self.session.query(
                UsageSession.user_id.label("user_id"),
                func.coalesce(func.sum(UsageSession.duration_seconds), 0).label(
                    "total_duration_seconds"
                ),
            )
            .filter(UsageSession.started_at >= since)
            .group_by(UsageSession.user_id)
            .subquery()
        )

        rows = (
            self.session.query(
                User.id,
                User.name,
                User.email,
                func.coalesce(usage_subq.c.apps_used, 0).label("apps_used"),
                func.coalesce(usage_subq.c.total_opens, 0).label("total_opens"),
                func.coalesce(duration_subq.c.total_duration_seconds, 0).label(
                    "total_duration_seconds"
                ),
                usage_subq.c.last_app_usage_at,
            )
            .outerjoin(usage_subq, User.id == usage_subq.c.user_id)
            .outerjoin(duration_subq, User.id == duration_subq.c.user_id)
            .filter(User.active.is_(True))
            .order_by(
                func.coalesce(usage_subq.c.total_opens, 0).desc(),
                func.coalesce(duration_subq.c.total_duration_seconds, 0).desc(),
                User.name.asc(),
            )
            .limit(max(1, limit))
            .all()
        )

        result: list[dict] = []
        for row in rows:
            if int(row.total_opens or 0) <= 0 and int(row.total_duration_seconds or 0) <= 0:
                continue
            last_usage = row.last_app_usage_at
            result.append(
                {
                    "id": str(row.id),
                    "name": row.name,
                    "email": row.email,
                    "appsUsed": int(row.apps_used or 0),
                    "totalOpens": int(row.total_opens or 0),
                    "totalDurationSeconds": int(row.total_duration_seconds or 0),
                    "lastAppUsageAt": last_usage.isoformat() + "Z"
                    if last_usage
                    else None,
                }
            )
        return result

    def top_routes_by_opens(self, *, since: datetime, limit: int = 8) -> list[dict]:
        rows = (
            self.session.query(
                AppUsageEvent.route_path,
                func.count(AppUsageEvent.id).label("open_count"),
            )
            .filter(
                AppUsageEvent.opened_at >= since,
                AppUsageEvent.route_path.isnot(None),
                AppUsageEvent.route_path != "",
            )
            .group_by(AppUsageEvent.route_path)
            .order_by(func.count(AppUsageEvent.id).desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": row.route_path,
                "name": row.route_path,
                "count": int(row.open_count or 0),
            }
            for row in rows
        ]

    def avg_session_duration(self, *, since: datetime, portal_only: bool) -> float:
        query = self.session.query(
            func.avg(UsageSession.duration_seconds)
        ).filter(UsageSession.started_at >= since)

        if portal_only:
            query = query.filter(UsageSession.app_id.is_(None))
        else:
            query = query.filter(UsageSession.app_id.isnot(None))

        value = query.scalar()
        return float(value or 0)

    def duration_percentiles(
        self,
        *,
        since: datetime,
        portal_only: bool,
    ) -> dict[str, float]:
        query = self.session.query(UsageSession.duration_seconds).filter(
            UsageSession.started_at >= since
        )
        if portal_only:
            query = query.filter(UsageSession.app_id.is_(None))
        else:
            query = query.filter(UsageSession.app_id.isnot(None))

        values = sorted(int(row[0]) for row in query.all() if row[0] is not None)
        if not values:
            return {"median": 0.0, "p90": 0.0}

        def percentile(data: list[int], pct: float) -> float:
            if not data:
                return 0.0
            index = max(0, min(len(data) - 1, int(round((pct / 100) * (len(data) - 1)))))
            return float(data[index])

        return {
            "median": percentile(values, 50),
            "p90": percentile(values, 90),
        }

    def consent_coverage(self) -> dict:
        active_users = (
            self.session.query(func.count(User.id))
            .filter(User.active.is_(True))
            .scalar()
        )
        active_users = int(active_users or 0)

        consented_users = (
            self.session.query(func.count(func.distinct(UserConsent.user_id)))
            .join(User, User.id == UserConsent.user_id)
            .filter(
                User.active.is_(True),
                UserConsent.purpose == USAGE_TRACKING_CONSENT_PURPOSE,
                UserConsent.granted.is_(True),
            )
            .scalar()
        )
        consented_users = int(consented_users or 0)

        rate = round((consented_users / active_users) * 100) if active_users > 0 else 0
        return {
            "activeUsers": active_users,
            "consentedUsers": consented_users,
            "consentRate": rate,
        }

    def count_sessions_since(self, *, since: datetime) -> int:
        value = (
            self.session.query(func.count(UsageSession.id))
            .filter(UsageSession.started_at >= since)
            .scalar()
        )
        return int(value or 0)

    @staticmethod
    def compute_stickiness(*, dau: int, mau: int) -> float:
        if mau <= 0:
            return 0.0
        return round((dau / mau) * 100, 1)

    @staticmethod
    def window_since(*, period_days: int) -> datetime:
        return datetime.utcnow() - timedelta(days=period_days)

    def activity_counts(self, *, period_days: int) -> dict:
        now = datetime.utcnow()
        dau = self.count_distinct_active_users(since=now - timedelta(days=1))
        wau = self.count_distinct_active_users(since=now - timedelta(days=7))
        mau = self.count_distinct_active_users(
            since=now - timedelta(days=min(period_days, 30))
        )
        return {
            "dau": dau,
            "wau": wau,
            "mau": mau,
            "stickiness": self.compute_stickiness(dau=dau, mau=mau),
        }

    def user_count_events_since(self, *, user_id: UUID, since: datetime) -> int:
        value = (
            self.session.query(func.count(AppUsageEvent.id))
            .filter(
                AppUsageEvent.user_id == user_id,
                AppUsageEvent.opened_at >= since,
            )
            .scalar()
        )
        return int(value or 0)

    def user_count_sessions_since(self, *, user_id: UUID, since: datetime) -> int:
        value = (
            self.session.query(func.count(UsageSession.id))
            .filter(
                UsageSession.user_id == user_id,
                UsageSession.started_at >= since,
            )
            .scalar()
        )
        return int(value or 0)

    def user_usage_summary(self, *, user_id: UUID, since: datetime) -> dict:
        total_opens = self.user_count_events_since(user_id=user_id, since=since)

        apps_used = (
            self.session.query(func.count(func.distinct(AppUsageEvent.app_id)))
            .filter(
                AppUsageEvent.user_id == user_id,
                AppUsageEvent.opened_at >= since,
            )
            .scalar()
        )

        portal_duration = (
            self.session.query(
                func.coalesce(func.sum(UsageSession.duration_seconds), 0)
            )
            .filter(
                UsageSession.user_id == user_id,
                UsageSession.started_at >= since,
                UsageSession.app_id.is_(None),
            )
            .scalar()
        )

        app_duration = (
            self.session.query(
                func.coalesce(func.sum(UsageSession.duration_seconds), 0)
            )
            .filter(
                UsageSession.user_id == user_id,
                UsageSession.started_at >= since,
                UsageSession.app_id.isnot(None),
            )
            .scalar()
        )

        avg_session = (
            self.session.query(func.avg(UsageSession.duration_seconds))
            .filter(
                UsageSession.user_id == user_id,
                UsageSession.started_at >= since,
            )
            .scalar()
        )

        last_app_usage_at = (
            self.session.query(func.max(AppUsageEvent.opened_at))
            .filter(
                AppUsageEvent.user_id == user_id,
                AppUsageEvent.opened_at >= since,
            )
            .scalar()
        )

        portal_seconds = int(portal_duration or 0)
        app_seconds = int(app_duration or 0)

        return {
            "totalOpens": total_opens,
            "appsUsed": int(apps_used or 0),
            "totalDurationSeconds": portal_seconds + app_seconds,
            "portalDurationSeconds": portal_seconds,
            "appDurationSeconds": app_seconds,
            "avgSessionSeconds": round(float(avg_session or 0)),
            "lastAppUsageAt": last_app_usage_at.isoformat() + "Z"
            if last_app_usage_at
            else None,
        }

    def user_opens_by_day(self, *, user_id: UUID, since: datetime) -> list[dict]:
        day_expr = func.date(AppUsageEvent.opened_at)
        rows = (
            self.session.query(
                day_expr.label("day"),
                func.count(AppUsageEvent.id).label("open_count"),
            )
            .filter(
                AppUsageEvent.user_id == user_id,
                AppUsageEvent.opened_at >= since,
            )
            .group_by(day_expr)
            .order_by(day_expr.asc())
            .all()
        )
        return [
            {
                "date": row.day.isoformat() if hasattr(row.day, "isoformat") else str(row.day),
                "opens": int(row.open_count or 0),
            }
            for row in rows
        ]

    def user_duration_by_day(self, *, user_id: UUID, since: datetime) -> list[dict]:
        day_expr = func.date(UsageSession.started_at)
        rows = (
            self.session.query(
                day_expr.label("day"),
                func.coalesce(func.sum(UsageSession.duration_seconds), 0).label(
                    "total_seconds"
                ),
            )
            .filter(
                UsageSession.user_id == user_id,
                UsageSession.started_at >= since,
            )
            .group_by(day_expr)
            .order_by(day_expr.asc())
            .all()
        )
        return [
            {
                "date": row.day.isoformat() if hasattr(row.day, "isoformat") else str(row.day),
                "totalSeconds": int(row.total_seconds or 0),
            }
            for row in rows
        ]

    def user_apps_by_opens(
        self,
        *,
        user_id: UUID,
        since: datetime,
        limit: int = 8,
    ) -> list[dict]:
        rows = (
            self.session.query(
                AppUsageEvent.app_id,
                App.name,
                func.count(AppUsageEvent.id).label("open_count"),
            )
            .join(App, App.id == AppUsageEvent.app_id)
            .filter(
                AppUsageEvent.user_id == user_id,
                AppUsageEvent.opened_at >= since,
                App.type != BACKEND_ONLY_APP_TYPE,
            )
            .group_by(AppUsageEvent.app_id, App.name)
            .order_by(func.count(AppUsageEvent.id).desc())
            .limit(limit)
            .all()
        )
        return [
            {"id": row.app_id, "name": row.name, "count": int(row.open_count or 0)}
            for row in rows
        ]

    def user_apps_by_duration(
        self,
        *,
        user_id: UUID,
        since: datetime,
        limit: int = 8,
    ) -> list[dict]:
        rows = (
            self.session.query(
                UsageSession.app_id,
                App.name,
                func.coalesce(func.sum(UsageSession.duration_seconds), 0).label(
                    "total_seconds"
                ),
            )
            .join(App, App.id == UsageSession.app_id)
            .filter(
                UsageSession.user_id == user_id,
                UsageSession.started_at >= since,
                UsageSession.app_id.isnot(None),
                App.type != BACKEND_ONLY_APP_TYPE,
            )
            .group_by(UsageSession.app_id, App.name)
            .order_by(func.sum(UsageSession.duration_seconds).desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": row.app_id,
                "name": row.name,
                "count": int(row.total_seconds or 0),
            }
            for row in rows
        ]

    def user_routes_by_opens(
        self,
        *,
        user_id: UUID,
        since: datetime,
        limit: int = 8,
    ) -> list[dict]:
        rows = (
            self.session.query(
                AppUsageEvent.route_path,
                func.count(AppUsageEvent.id).label("open_count"),
            )
            .filter(
                AppUsageEvent.user_id == user_id,
                AppUsageEvent.opened_at >= since,
                AppUsageEvent.route_path.isnot(None),
                AppUsageEvent.route_path != "",
            )
            .group_by(AppUsageEvent.route_path)
            .order_by(func.count(AppUsageEvent.id).desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": row.route_path,
                "name": row.route_path,
                "count": int(row.open_count or 0),
            }
            for row in rows
        ]
