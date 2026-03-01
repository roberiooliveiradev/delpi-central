# app/application/unit_of_work.py

from typing import Protocol

# =========================
# Events
# =========================
from app.domain.events.admin_events import DomainEvent
from app.domain.ports.event_dispatcher_port import EventDispatcherPort
from app.domain.ports.cache_port import PermissionCachePort

# =========================
# User & RBAC Core
# =========================

from app.domain.ports.user_repository_port import UserRepositoryPort
from app.domain.ports.role_repository_port import RoleRepositoryPort
from app.domain.ports.group_repository_port import GroupRepositoryPort
from app.domain.ports.permission_repository_port import PermissionRepositoryPort

from app.domain.ports.user_role_repository_port import UserRoleRepositoryPort
from app.domain.ports.user_group_repository_port import UserGroupRepositoryPort
from app.domain.ports.group_role_repository_port import GroupRoleRepositoryPort
from app.domain.ports.role_permission_repository_port import RolePermissionRepositoryPort

from app.domain.ports.rbac_query_port import RbacQueryPort
from app.domain.ports.permission_query_port import PermissionQueryPort


# =========================
# Apps & Routes
# =========================

from app.domain.ports.app_query_port import AppQueryPort
from app.domain.ports.admin_route_repository_port import AdminRouteRepositoryPort
from app.domain.ports.admin_app_repository_port import AdminAppRepositoryPort
from app.domain.ports.route_query_port import RouteQueryPort


# =========================
# Plugin System
# =========================

from app.domain.ports.plugin_repository_port import PluginRepositoryPort
from app.domain.ports.plugin_manifest_repository_port import PluginManifestRepositoryPort
from app.domain.ports.plugin_version_repository_port import PluginVersionRepositoryPort
from app.domain.ports.plugin_route_repository_port import PluginRouteRepositoryPort
from app.domain.ports.plugin_permission_repository_port import PluginPermissionRepositoryPort

# =========================
# Misc
# =========================

from app.domain.ports.favorite_app_repository import FavoriteAppRepository
from app.domain.ports.notification_repository import NotificationRepository
from app.domain.ports.audit_repository_port import AuditRepositoryPort
from app.domain.ports.cache_port import PermissionCachePort
from app.domain.ports.event_dispatcher_port import EventDispatcherPort


class UnitOfWork(Protocol):

    # =========================
    # RBAC
    # =========================

    users: UserRepositoryPort
    roles: RoleRepositoryPort
    groups: GroupRepositoryPort
    permissions: PermissionRepositoryPort

    user_roles: UserRoleRepositoryPort
    user_groups: UserGroupRepositoryPort
    group_roles: GroupRoleRepositoryPort
    role_permissions: RolePermissionRepositoryPort

    rbac_queries: RbacQueryPort
    permission_queries: PermissionQueryPort

    # =========================
    # Apps & Routes
    # =========================

    app_queries: AppQueryPort
    admin_apps: AdminAppRepositoryPort
    admin_routes: AdminRouteRepositoryPort
    route_queries: RouteQueryPort

    # =========================
    # Plugin System
    # =========================

    plugins: PluginRepositoryPort
    plugin_manifests: PluginManifestRepositoryPort
    plugin_versions: PluginVersionRepositoryPort
    plugin_routes: PluginRouteRepositoryPort
    plugin_permissions: PluginPermissionRepositoryPort

    # =========================
    # Misc
    # =========================

    favorites: FavoriteAppRepository
    notifications: NotificationRepository
    audits: AuditRepositoryPort

    cache: PermissionCachePort
    events: EventDispatcherPort

    # =========================
    # Domain Events
    # =========================

    def collect_event(self, event: DomainEvent) -> None:
        ...

    # =========================
    # Transaction Control
    # =========================

    def commit(self) -> None:
        ...

    def rollback(self) -> None:
        ...