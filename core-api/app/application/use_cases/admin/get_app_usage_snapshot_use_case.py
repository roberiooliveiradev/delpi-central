# app/application/use_cases/admin/get_app_usage_snapshot_use_case.py

from datetime import datetime, timedelta

from app.application.unit_of_work import UnitOfWork
from app.infrastructure.app_usage.app_usage_live_store_provider import (
    get_app_usage_live_store,
    is_app_usage_enabled,
)
from app.infrastructure.db.models import App
from app.infrastructure.persistence.sqlalchemy.app_usage_repository import (
    SqlAlchemyAppUsageRepository,
)


class GetAppUsageSnapshotUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.repo = SqlAlchemyAppUsageRepository(uow.session)

    def execute(self, *, history_days: int = 30) -> dict:
        if not is_app_usage_enabled():
            return {
                "enabled": False,
                "ttlSeconds": 0,
                "inUseNow": 0,
                "live": [],
                "topUsed": [],
                "ghostApps": [],
                "usedInPeriod": 0,
            }

        from flask import current_app

        ttl_seconds = int(current_app.config.get("APP_USAGE_TTL_SECONDS", 90))
        since = datetime.utcnow() - timedelta(days=max(1, history_days))

        live_store = get_app_usage_live_store()
        live_apps = live_store.list_live_apps()

        app_ids = [item.app_id for item in live_apps]
        app_names: dict[str, str] = {}
        if app_ids:
            rows = (
                self.uow.session.query(App.id, App.name)
                .filter(App.id.in_(app_ids))
                .all()
            )
            app_names = {row.id: row.name for row in rows}

        live = [
            {
                "appId": item.app_id,
                "appName": app_names.get(item.app_id, item.app_id),
                "userCount": item.user_count,
                "sessionCount": item.session_count,
                "lastSeenAt": item.last_seen_at.isoformat() + "Z",
            }
            for item in live_apps
        ]

        top_used = self.repo.top_apps_by_unique_users(since=since, limit=5)
        ghost_apps = self.repo.ghost_active_apps(since=since)

        return {
            "enabled": True,
            "ttlSeconds": ttl_seconds,
            "inUseNow": len(live_apps),
            "live": live,
            "topUsed": top_used,
            "ghostApps": ghost_apps,
            "usedInPeriod": self.repo.count_distinct_apps_used(since=since),
        }
