# app/application/use_cases/admin/get_app_usage_snapshot_use_case.py

from collections import defaultdict
from datetime import datetime, timedelta
from uuid import UUID

from app.application.unit_of_work import UnitOfWork
from app.infrastructure.app_usage.app_usage_live_store_provider import (
    get_app_usage_live_store,
    is_app_usage_enabled,
)
from app.infrastructure.db.models import App
from app.infrastructure.persistence.sqlalchemy.app_usage_repository import (
    BACKEND_ONLY_APP_TYPE,
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
                "trackableActive": 0,
                "backendOnlyActive": 0,
            }

        from flask import current_app

        ttl_seconds = int(current_app.config.get("APP_USAGE_TTL_SECONDS", 90))
        since = datetime.utcnow() - timedelta(days=max(1, history_days))

        live_store = get_app_usage_live_store()
        live_apps = live_store.list_live_apps()
        live_sessions = live_store.list_live_sessions()

        users_by_app: dict[str, set[str]] = defaultdict(set)
        for session in live_sessions:
            users_by_app[session.app_id].add(session.user_id)

        user_ids: list[UUID] = []
        for raw_id in {uid for ids in users_by_app.values() for uid in ids}:
            try:
                user_ids.append(UUID(str(raw_id)))
            except ValueError:
                continue

        users_by_id: dict[str, object] = {}
        if user_ids:
            for user in self.uow.users.get_by_ids(user_ids):
                users_by_id[str(user.id)] = user

        app_ids = [item.app_id for item in live_apps]
        app_names: dict[str, str] = {}
        if app_ids:
            rows = (
                self.uow.session.query(App.id, App.name)
                .filter(App.id.in_(app_ids))
                .all()
            )
            app_names = {row.id: row.name for row in rows}

        live = []
        for item in live_apps:
            active_users = []
            for user_id in sorted(users_by_app.get(item.app_id, set())):
                user = users_by_id.get(str(user_id))
                active_users.append(
                    {
                        "id": str(user_id),
                        "name": user.name if user else None,
                        "email": user.email if user else None,
                    }
                )

            live.append(
                {
                    "appId": item.app_id,
                    "appName": app_names.get(item.app_id, item.app_id),
                    "userCount": item.user_count,
                    "sessionCount": item.session_count,
                    "users": active_users,
                    "lastSeenAt": item.last_seen_at.isoformat() + "Z",
                }
            )

        top_used = self.repo.top_apps_by_unique_users(since=since, limit=5)
        ghost_apps = self.repo.ghost_active_apps(since=since)
        trackable_active = self.repo.count_trackable_active_apps()
        backend_only_active = int(
            self.uow.session.query(App.id)
            .filter(App.active.is_(True), App.type == BACKEND_ONLY_APP_TYPE)
            .count()
        )

        return {
            "enabled": True,
            "ttlSeconds": ttl_seconds,
            "inUseNow": len(live_apps),
            "live": live,
            "topUsed": top_used,
            "ghostApps": ghost_apps,
            "usedInPeriod": self.repo.count_distinct_apps_used(since=since),
            "trackableActive": trackable_active,
            "backendOnlyActive": backend_only_active,
        }
