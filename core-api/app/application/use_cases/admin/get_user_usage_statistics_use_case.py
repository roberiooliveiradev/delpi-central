# app/application/use_cases/admin/get_user_usage_statistics_use_case.py

from datetime import datetime
from uuid import UUID

from app.application.unit_of_work import UnitOfWork
from app.application.use_cases.admin.get_engagement_statistics_use_case import (
    ALLOWED_PERIOD_DAYS,
)
from app.domain.services.usage_tracking_consent_service import (
    user_has_usage_tracking_consent,
)
from app.infrastructure.app_usage.app_usage_live_store_provider import is_app_usage_enabled
from app.infrastructure.persistence.sqlalchemy.engagement_repository import (
    SqlAlchemyEngagementRepository,
)


class GetUserUsageStatisticsUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.repo = SqlAlchemyEngagementRepository(uow.session)

    def execute(self, *, user_id: UUID, period_days: int = 30) -> dict:
        if period_days not in ALLOWED_PERIOD_DAYS:
            raise ValueError("periodDays inválido")

        user = self.uow.users.get_by_id(user_id)
        if not user:
            raise LookupError("Usuário não encontrado.")

        consent_granted = user_has_usage_tracking_consent(self.uow, user_id)
        since = self.repo.window_since(period_days=period_days)

        user_payload = {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "active": user.active,
            "lastLoginAt": user.last_login_at.isoformat() + "Z"
            if user.last_login_at
            else None,
        }

        if not consent_granted:
            return self._build_payload(
                user=user_payload,
                period_days=period_days,
                consent_granted=False,
                summary=self._empty_summary(),
                activity={"opensSeries": [], "durationSeries": []},
                rankings={
                    "topAppsByOpens": [],
                    "topAppsByDuration": [],
                    "topRoutes": [],
                },
                coverage={
                    "trackingEnabled": is_app_usage_enabled(),
                    "sessionsRecorded": 0,
                    "eventsInPeriod": 0,
                },
            )

        summary = self.repo.user_usage_summary(user_id=user_id, since=since)

        return self._build_payload(
            user=user_payload,
            period_days=period_days,
            consent_granted=True,
            summary=summary,
            activity={
                "opensSeries": self.repo.user_opens_by_day(user_id=user_id, since=since),
                "durationSeries": self.repo.user_duration_by_day(
                    user_id=user_id,
                    since=since,
                ),
            },
            rankings={
                "topAppsByOpens": self.repo.user_apps_by_opens(
                    user_id=user_id,
                    since=since,
                ),
                "topAppsByDuration": self.repo.user_apps_by_duration(
                    user_id=user_id,
                    since=since,
                ),
                "topRoutes": self.repo.user_routes_by_opens(
                    user_id=user_id,
                    since=since,
                ),
            },
            coverage={
                "trackingEnabled": is_app_usage_enabled(),
                "sessionsRecorded": self.repo.user_count_sessions_since(
                    user_id=user_id,
                    since=since,
                ),
                "eventsInPeriod": self.repo.user_count_events_since(
                    user_id=user_id,
                    since=since,
                ),
            },
        )

    @staticmethod
    def _empty_summary() -> dict:
        return {
            "totalOpens": 0,
            "appsUsed": 0,
            "totalDurationSeconds": 0,
            "portalDurationSeconds": 0,
            "appDurationSeconds": 0,
            "avgSessionSeconds": 0,
            "lastAppUsageAt": None,
        }

    @staticmethod
    def _build_payload(
        *,
        user: dict,
        period_days: int,
        consent_granted: bool,
        summary: dict,
        activity: dict,
        rankings: dict,
        coverage: dict,
    ) -> dict:
        return {
            "generatedAt": datetime.utcnow().isoformat() + "Z",
            "periodDays": period_days,
            "user": user,
            "consent": {"granted": consent_granted},
            "summary": summary,
            "activity": activity,
            "rankings": rankings,
            "coverage": coverage,
        }
