from __future__ import annotations

from typing import Any
from uuid import UUID

from app.application.services.app_authorization_service import AppAuthorizationService
from app.application.unit_of_work import UnitOfWork
from app.domain.services.permission_resolver import PermissionResolver


class GetMyAccessProfileUseCase:
    """Perfil de acesso do usuário: papéis, permissões por papel e apps liberados."""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self._app_auth = AppAuthorizationService()

    def execute(self, user_id: UUID, *, is_superadmin: bool) -> dict[str, Any]:
        roles_by_id: dict[str, dict[str, Any]] = {}
        groups_detail: list[dict[str, Any]] = []

        for role_id in self.uow.user_roles.list_role_ids(user_id):
            self._merge_role(
                roles_by_id,
                role_id=role_id,
                source={"type": "direct"},
            )

        for group_id in self.uow.user_groups.list_group_ids(user_id):
            group = self.uow.groups.get(group_id)
            if not group:
                continue

            group_role_names: list[str] = []
            for role_id in self.uow.group_roles.list_role_ids(group_id):
                role = self.uow.roles.get(role_id)
                if role:
                    group_role_names.append(role.name)
                self._merge_role(
                    roles_by_id,
                    role_id=role_id,
                    source={"type": "group", "groupName": group.name},
                )

            groups_detail.append(
                {
                    "id": str(group.id),
                    "name": group.name,
                    "description": group.description,
                    "roles": sorted(set(group_role_names)),
                }
            )

        all_apps = self.uow.app_queries.list_active_apps_with_routes()

        for entry in roles_by_id.values():
            permission_rows = self.uow.permission_queries.list_permissions_by_role_id(
                UUID(entry["id"])
            )
            permission_codes = sorted({row.code for row in permission_rows})
            entry["permissions"] = [
                {
                    "code": row.code,
                    "name": row.name,
                    "description": row.description,
                    "module": row.module,
                }
                for row in sorted(permission_rows, key=lambda item: item.code)
            ]
            entry["apps"] = self._serialize_apps(
                self._app_auth.filter_apps(all_apps, permission_codes, False)
            )

        resolver = PermissionResolver(self.uow.permission_queries, self.uow.cache)
        effective_permissions = resolver.resolve(user_id, is_superadmin)
        effective_apps = self._serialize_apps(
            self._app_auth.filter_apps(all_apps, effective_permissions, is_superadmin)
        )

        roles = sorted(roles_by_id.values(), key=lambda item: str(item.get("name") or ""))

        return {
            "isSuperadmin": is_superadmin,
            "roles": roles,
            "groups": groups_detail,
            "effectivePermissions": effective_permissions,
            "effectiveApps": effective_apps,
        }

    def _merge_role(
        self,
        roles_by_id: dict[str, dict[str, Any]],
        *,
        role_id: UUID,
        source: dict[str, str],
    ) -> None:
        role = self.uow.roles.get(role_id)
        if not role:
            return

        key = str(role.id)
        entry = roles_by_id.get(key)
        if not entry:
            entry = {
                "id": key,
                "name": role.name,
                "description": role.description,
                "sources": [],
                "permissions": [],
                "apps": [],
            }
            roles_by_id[key] = entry

        sources = entry["sources"]
        if not any(
            existing.get("type") == source.get("type")
            and existing.get("groupName") == source.get("groupName")
            for existing in sources
        ):
            sources.append(source)

    @staticmethod
    def _serialize_apps(apps) -> list[dict[str, Any]]:
        serialized: list[dict[str, Any]] = []

        for app in apps:
            serialized.append(
                {
                    "id": app.id,
                    "name": app.name,
                    "basePath": app.base_path,
                    "icon": app.icon,
                    "type": app.type,
                    "routes": [
                        {
                            "path": route.path,
                            "label": route.label,
                            "permission": route.permission_code,
                            "showInMenu": route.show_in_menu,
                        }
                        for route in app.routes
                    ],
                }
            )

        return serialized
