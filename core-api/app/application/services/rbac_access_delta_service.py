# app/application/services/rbac_access_delta_service.py

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from app.application.services.app_authorization_service import AppAuthorizationService
from app.domain.ports.app_query_port import AppDTO, RouteDTO
from app.domain.services.permission_resolver import PermissionResolver

SYSTEM_PERMISSION_MODULE = "system"


@dataclass(frozen=True)
class SystemPermissionGain:
    code: str
    name: str


@dataclass(frozen=True)
class AccessGain:
    new_apps: list[AppDTO] = field(default_factory=list)
    new_routes: list[tuple[AppDTO, RouteDTO]] = field(default_factory=list)
    new_permission_codes: list[str] = field(default_factory=list)
    new_system_permissions: list[SystemPermissionGain] = field(default_factory=list)

    @property
    def has_gain(self) -> bool:
        """Apps, rotas novas ou permissões do módulo system."""
        return bool(self.new_apps or self.new_routes or self.new_system_permissions)


class RbacAccessDeltaService:
    """
    Calcula o que o usuário ganhou com uma mudança RBAC, comparando o estado
    atual com o estado anterior (sem as permissões/papéis recém-adicionados).

    Evita notificar quando o usuário já tinha acesso ao app ou à rota.
    """

    def __init__(self, permission_queries, cache, app_queries):
        self._permission_queries = permission_queries
        self._cache = cache
        self._app_queries = app_queries
        self._auth_service = AppAuthorizationService()

    def compute_gain(
        self,
        user_id: UUID,
        is_superadmin: bool,
        *,
        previous_codes: list[str],
    ) -> AccessGain:
        resolver = PermissionResolver(self._permission_queries, self._cache)
        full_codes = set(resolver.resolve(user_id, is_superadmin))
        prev_codes = set(previous_codes)

        new_permission_codes = sorted(full_codes - prev_codes)
        if not new_permission_codes:
            return AccessGain()

        new_system_permissions = self._resolve_new_system_permissions(new_permission_codes)

        apps = self._app_queries.list_active_apps_with_routes()
        if not apps:
            return AccessGain(
                new_permission_codes=new_permission_codes,
                new_system_permissions=new_system_permissions,
            )

        current_apps = self._auth_service.filter_apps(
            apps, sorted(full_codes), is_superadmin
        )
        previous_apps = self._auth_service.filter_apps(
            apps, sorted(prev_codes), is_superadmin
        )

        previous_app_ids = {app.id for app in previous_apps}
        previous_route_keys = {
            (app.id, route.path)
            for app in previous_apps
            for route in app.routes
        }

        new_apps = [app for app in current_apps if app.id not in previous_app_ids]

        new_routes: list[tuple[AppDTO, RouteDTO]] = []
        new_perm_set = set(new_permission_codes)

        for app in current_apps:
            for route in app.routes:
                if not route.permission_code:
                    continue
                if route.permission_code not in new_perm_set:
                    continue
                key = (app.id, route.path)
                if key in previous_route_keys:
                    continue
                new_routes.append((app, route))

        return AccessGain(
            new_apps=new_apps,
            new_routes=new_routes,
            new_permission_codes=new_permission_codes,
            new_system_permissions=new_system_permissions,
        )

    def _resolve_new_system_permissions(
        self, new_permission_codes: list[str]
    ) -> list[SystemPermissionGain]:
        rows = self._permission_queries.list_permissions_by_codes(new_permission_codes)
        gains: list[SystemPermissionGain] = []
        seen: set[str] = set()

        for row in rows:
            module = (getattr(row, "module", None) or "").strip().lower()
            if module != SYSTEM_PERMISSION_MODULE:
                continue
            code = (getattr(row, "code", None) or "").strip()
            if not code or code in seen:
                continue
            seen.add(code)
            name = (getattr(row, "name", None) or "").strip() or code
            gains.append(SystemPermissionGain(code=code, name=name))

        return sorted(gains, key=lambda item: item.name.casefold())

    def previous_codes_excluding_user_roles(
        self,
        user_id: UUID,
        is_superadmin: bool,
        exclude_role_ids: set[UUID],
    ) -> list[str]:
        return self._resolve_custom(
            user_id,
            is_superadmin,
            exclude_direct_role_ids=exclude_role_ids,
            exclude_group_role_ids=exclude_role_ids,
        )

    def previous_codes_excluding_group_roles(
        self,
        user_id: UUID,
        is_superadmin: bool,
        group_id: UUID,
        exclude_role_ids: set[UUID],
    ) -> list[str]:
        return self._resolve_custom(
            user_id,
            is_superadmin,
            exclude_group_id=group_id,
            exclude_group_role_ids=exclude_role_ids,
        )

    def previous_codes_excluding_groups(
        self,
        user_id: UUID,
        is_superadmin: bool,
        exclude_group_ids: set[UUID],
    ) -> list[str]:
        return self._resolve_custom(
            user_id,
            is_superadmin,
            exclude_group_ids=exclude_group_ids,
        )

    def previous_codes_after_role_permission_change(
        self,
        user_id: UUID,
        is_superadmin: bool,
        role_id: UUID,
        added_permission_codes: set[str],
    ) -> list[str]:
        resolver = PermissionResolver(self._permission_queries, self._cache)
        full = set(resolver.resolve(user_id, is_superadmin))
        role_codes = set(
            self._permission_queries.list_permission_codes_granted_by_role_for_user(
                user_id, role_id
            )
        )
        if not role_codes:
            return sorted(full - added_permission_codes)

        retained_from_role = role_codes - added_permission_codes
        return sorted((full - role_codes) | retained_from_role)

    def _resolve_custom(
        self,
        user_id: UUID,
        is_superadmin: bool,
        *,
        exclude_direct_role_ids: set[UUID] | None = None,
        exclude_group_role_ids: set[UUID] | None = None,
        exclude_group_ids: set[UUID] | None = None,
        exclude_group_id: UUID | None = None,
    ) -> list[str]:
        if is_superadmin:
            return []

        exclude_direct_role_ids = exclude_direct_role_ids or set()
        exclude_group_role_ids = exclude_group_role_ids or set()
        exclude_group_ids = exclude_group_ids or set()

        direct = set(
            self._permission_queries.list_direct_role_permissions_excluding_roles(
                user_id, exclude_direct_role_ids
            )
        )

        if exclude_group_id is not None:
            group = set(
                self._permission_queries.list_group_role_permissions_excluding_roles_for_group(
                    user_id, exclude_group_id, exclude_group_role_ids
                )
            )
            other_groups = set(
                self._permission_queries.list_group_role_permissions_excluding_groups(
                    user_id, {exclude_group_id}
                )
            )
            effective = direct | group | other_groups
        else:
            if exclude_group_role_ids:
                group = set(
                    self._permission_queries.list_group_role_permissions_excluding_roles(
                        user_id, exclude_group_role_ids
                    )
                )
            else:
                group = set(
                    self._permission_queries.list_group_role_permissions_excluding_groups(
                        user_id, exclude_group_ids
                    )
                )
            effective = direct | group

        overrides = self._permission_queries.list_user_overrides(user_id)
        for code, granted in overrides:
            if granted:
                effective.add(code)
            else:
                effective.discard(code)

        return sorted(effective)
