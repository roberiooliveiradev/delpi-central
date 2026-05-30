# app/application/use_cases/admin/get_least_engaged_users_use_case.py

from __future__ import annotations

from datetime import datetime, timedelta

from app.application.services.app_authorization_service import AppAuthorizationService
from app.application.unit_of_work import UnitOfWork
from app.domain.services.permission_resolver import PermissionResolver
from app.infrastructure.persistence.sqlalchemy.app_usage_repository import (
    SqlAlchemyAppUsageRepository,
)


def _iso_z(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat() + "Z"


def _serialize_ref(item_id, name: str) -> dict:
    return {"id": str(item_id), "name": name}


class GetLeastEngagedUsersUseCase:

    DEFAULT_LIMIT = 15

    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.usage_repo = SqlAlchemyAppUsageRepository(uow.session)
        self._auth_service = AppAuthorizationService()

    def _collect_groups_and_roles(self, user_id, *, is_superadmin: bool) -> tuple[list[dict], list[dict]]:
        groups: list[dict] = []
        roles_by_id: dict[str, dict] = {}

        for role_id in self.uow.user_roles.list_role_ids(user_id):
            role = self.uow.roles.get(role_id)
            if role:
                roles_by_id[str(role.id)] = _serialize_ref(role.id, role.name)

        for group_id in self.uow.user_groups.list_group_ids(user_id):
            group = self.uow.groups.get(group_id)
            if not group:
                continue

            groups.append(_serialize_ref(group.id, group.name))

            for role_id in self.uow.group_roles.list_role_ids(group_id):
                role = self.uow.roles.get(role_id)
                if role:
                    roles_by_id[str(role.id)] = _serialize_ref(role.id, role.name)

        if is_superadmin:
            for role in self.uow.roles.list_all():
                roles_by_id[str(role.id)] = _serialize_ref(role.id, role.name)

        groups.sort(key=lambda item: item["name"].lower())
        roles = sorted(roles_by_id.values(), key=lambda item: item["name"].lower())
        return groups, roles

    def execute(self, *, history_days: int = 30, limit: int | None = None) -> dict:
        since = datetime.utcnow() - timedelta(days=max(1, history_days))
        max_items = limit if limit is not None else self.DEFAULT_LIMIT

        candidates = self.usage_repo.list_least_engaged_users(
            since=since,
            limit=max_items,
        )

        all_apps = self.uow.app_queries.list_active_apps_with_routes()
        resolver = PermissionResolver(self.uow.permission_queries, self.uow.cache)

        items: list[dict] = []
        for row in candidates:
            permissions = resolver.resolve(row["id"], row["is_superadmin"])
            authorized_apps = self._auth_service.filter_apps(
                all_apps,
                permissions,
                row["is_superadmin"],
            )
            available_apps = [
                {"id": app.id, "name": app.name}
                for app in authorized_apps
                if app.type != "backend-only"
            ]
            available_apps.sort(key=lambda item: item["name"].lower())
            available_groups, available_roles = self._collect_groups_and_roles(
                row["id"],
                is_superadmin=row["is_superadmin"],
            )

            items.append(
                {
                    "id": str(row["id"]),
                    "name": row["name"],
                    "email": row["email"],
                    "isSuperadmin": row["is_superadmin"],
                    "lastLoginAt": _iso_z(row["last_login_at"]),
                    "appsUsedInPeriod": row["apps_used"],
                    "totalOpensInPeriod": row["total_opens"],
                    "lastAppUsageAt": _iso_z(row["last_app_usage_at"]),
                    "availableAppsCount": len(available_apps),
                    "availableApps": available_apps,
                    "availableGroupsCount": len(available_groups),
                    "availableGroups": available_groups,
                    "availableRolesCount": len(available_roles),
                    "availableRoles": available_roles,
                }
            )

        return {
            "periodDays": max(1, history_days),
            "items": items,
        }
