# app/application/use_cases/admin/get_engagement_statistics_use_case.py

from datetime import datetime

from app.application.unit_of_work import UnitOfWork
from app.infrastructure.app_usage.app_usage_live_store_provider import is_app_usage_enabled
from app.infrastructure.persistence.sqlalchemy.engagement_repository import (
    SqlAlchemyEngagementRepository,
)

ALLOWED_PERIOD_DAYS = frozenset({7, 30, 90})


class GetEngagementStatisticsUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.repo = SqlAlchemyEngagementRepository(uow.session)

    def execute(self, *, period_days: int = 30) -> dict:
        if period_days not in ALLOWED_PERIOD_DAYS:
            raise ValueError("periodDays inválido")

        since = self.repo.window_since(period_days=period_days)
        activity = self.repo.activity_counts(period_days=period_days)
        portal_percentiles = self.repo.duration_percentiles(since=since, portal_only=True)
        app_percentiles = self.repo.duration_percentiles(since=since, portal_only=False)
        coverage = self.repo.consent_coverage()

        return {
            "generatedAt": datetime.utcnow().isoformat() + "Z",
            "periodDays": period_days,
            "activity": {
                **activity,
                "activeUsersSeries": self.repo.active_users_by_day(since=since),
                "durationSeries": self.repo.duration_by_day(since=since),
            },
            "duration": {
                "avgPortalSeconds": round(
                    self.repo.avg_session_duration(since=since, portal_only=True)
                ),
                "avgAppSeconds": round(
                    self.repo.avg_session_duration(since=since, portal_only=False)
                ),
                "medianPortalSeconds": round(portal_percentiles["median"]),
                "p90AppSeconds": round(app_percentiles["p90"]),
            },
            "rankings": {
                "topAppsByOpens": self.repo.top_apps_by_opens(since=since),
                "topAppsByDuration": self.repo.top_apps_by_duration(since=since),
                "topAppsByUniqueUsers": self.repo.top_apps_by_unique_users(since=since),
                "topUsers": self.repo.top_users_by_activity(since=since),
                "topRoutes": self.repo.top_routes_by_opens(since=since),
            },
            "coverage": {
                "trackingEnabled": is_app_usage_enabled(),
                "consentRate": coverage["consentRate"],
                "consentedUsers": coverage["consentedUsers"],
                "activeUsers": coverage["activeUsers"],
                "sessionsRecorded": self.repo.count_sessions_since(since=since),
                "eventsInPeriod": self.repo.count_events_since(since=since),
            },
        }
