"""GLPI #887: batched read-only SQL for weekly, consented app openings.

Only UI app-open events, not backend-only requests, routes or durations.
All queries are bounded by verified user IDs and a closed UTC interval.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.services.usage_tracking_consent_service import (
    USAGE_TRACKING_CONSENT_PURPOSE,
)
from app.infrastructure.db.models import App, AppUsageEvent, UsageSession, User, UserConsent
from app.infrastructure.persistence.sqlalchemy.app_usage_repository import (
    BACKEND_ONLY_APP_TYPE,
)


class SqlAlchemyOrganizationWeeklyUsageRepository:
    def __init__(self, session: Session):
        self.session = session

    def consented_active_user_ids(self, user_ids: set[UUID]) -> set[UUID]:
        if not user_ids:
            return set()
        rows = (
            self.session.query(UserConsent.user_id)
            .join(User, User.id == UserConsent.user_id)
            .filter(
                UserConsent.user_id.in_(user_ids),
                User.active.is_(True),
                UserConsent.purpose == USAGE_TRACKING_CONSENT_PURPOSE,
                UserConsent.granted.is_(True),
            )
            .all()
        )
        return {row[0] for row in rows}

    def app_opens(
        self,
        *,
        user_ids: set[UUID],
        since: datetime,
        until: datetime,
    ) -> list[dict]:
        if not user_ids:
            return []
        if since >= until:
            raise ValueError("Intervalo de apuração inválido.")

        rows = (
            self.session.query(
                AppUsageEvent.user_id,
                AppUsageEvent.app_id,
                App.name,
                func.count(AppUsageEvent.id).label("opens_count"),
            )
            .join(App, App.id == AppUsageEvent.app_id)
            .join(User, User.id == AppUsageEvent.user_id)
            .join(
                UserConsent,
                UserConsent.user_id == AppUsageEvent.user_id,
            )
            .filter(
                AppUsageEvent.user_id.in_(user_ids),
                AppUsageEvent.opened_at >= since,
                AppUsageEvent.opened_at < until,
                App.type != BACKEND_ONLY_APP_TYPE,
                User.active.is_(True),
                UserConsent.purpose == USAGE_TRACKING_CONSENT_PURPOSE,
                UserConsent.granted.is_(True),
            )
            .group_by(AppUsageEvent.user_id, AppUsageEvent.app_id, App.name)
            .order_by(AppUsageEvent.user_id, App.name, AppUsageEvent.app_id)
            .all()
        )
        return [
            {
                "userId": str(row.user_id),
                "appId": row.app_id,
                "appName": row.name,
                "count": int(row.opens_count or 0),
            }
            for row in rows
        ]


    def app_session_durations(
        self,
        *,
        user_ids: set[UUID],
        since: datetime,
        until: datetime,
    ) -> list[dict]:
        """Average duration of persisted UI-app sessions begun in the closed week.

        This is connection/session elapsed time, NOT active interaction time.
        Excludes portal presence (app_id=NULL), backend-only apps, inactive
        accounts and users without current usage_tracking consent.
        """
        if not user_ids:
            return []
        if since >= until:
            raise ValueError("Intervalo de apuração inválido.")

        rows = (
            self.session.query(
                UsageSession.user_id,
                UsageSession.app_id,
                func.count(UsageSession.id).label("session_count"),
                func.coalesce(
                    func.sum(UsageSession.duration_seconds), 0
                ).label("total_seconds"),
            )
            .join(App, App.id == UsageSession.app_id)
            .join(User, User.id == UsageSession.user_id)
            .join(UserConsent, UserConsent.user_id == UsageSession.user_id)
            .filter(
                UsageSession.user_id.in_(user_ids),
                UsageSession.app_id.isnot(None),
                UsageSession.started_at >= since,
                UsageSession.started_at < until,
                UsageSession.duration_seconds > 0,
                App.type != BACKEND_ONLY_APP_TYPE,
                User.active.is_(True),
                UserConsent.purpose == USAGE_TRACKING_CONSENT_PURPOSE,
                UserConsent.granted.is_(True),
            )
            .group_by(UsageSession.user_id, UsageSession.app_id)
            .all()
        )
        return [
            {
                "userId": str(row.user_id),
                "appId": row.app_id,
                "sessionCount": int(row.session_count or 0),
                "totalDurationSeconds": int(row.total_seconds or 0),
            }
            for row in rows
        ]
