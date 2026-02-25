# app/application/unit_of_work.py

from typing import Protocol
from sqlalchemy.orm import Session
from app.domain.ports.user_repository import UserRepository
from app.domain.ports.role_repository import RoleRepository
from app.domain.ports.permission_repository import PermissionRepository
from app.domain.ports.group_repository import GroupRepository
from app.domain.ports.app_repository import AppRepository
from app.domain.ports.route_repository import RouteRepository
from app.domain.ports.favorite_repository import FavoriteRepository
from app.domain.ports.notification_repository import NotificationRepository
from app.domain.ports.audit_repository import AuditRepository
from app.domain.ports.role_permission_repository_port import RolePermissionRepositoryPort
from app.domain.ports.rbac_query_port import RbacQueryPort
from app.domain.ports.group_role_repository_port import GroupRoleRepositoryPort
from app.domain.ports.user_role_repository_port import UserRoleRepositoryPort
from app.domain.ports.user_group_repository_port import UserGroupRepositoryPort
from app.domain.ports.admin_app_repository_port import AdminAppRepositoryPort

from app.domain.ports.plugin_repository_port import PluginRepositoryPort
from app.domain.ports.plugin_manifest_repository_port import PluginManifestRepositoryPort
from app.domain.ports.plugin_version_repository_port import PluginVersionRepositoryPort
from app.domain.ports.plugin_route_repository_port import PluginRouteRepositoryPort
from app.domain.ports.plugin_permission_repository_port import PluginPermissionRepositoryPort
from app.domain.ports.audit_repository_port import AuditRepositoryPort

from app.domain.ports.admin_route_repository_port import AdminRouteRepositoryPort

class UnitOfWork(Protocol):
    session: Session
    users: UserRepository
    roles: RoleRepository
    permissions: PermissionRepository
    groups: GroupRepository
    apps: AppRepository
    routes: RouteRepository
    favorites: FavoriteRepository
    notifications: NotificationRepository
    audits: AuditRepository
    role_permissions: RolePermissionRepositoryPort
    rbac_queries: RbacQueryPort
    group_roles: GroupRoleRepositoryPort
    user_roles: UserRoleRepositoryPort
    user_groups: UserGroupRepositoryPort
    admin_apps: AdminAppRepositoryPort
    
    plugin_repo: PluginRepositoryPort
    manifest_repo: PluginManifestRepositoryPort
    version_repo: PluginVersionRepositoryPort
    route_repo: PluginRouteRepositoryPort
    permission_repo: PluginPermissionRepositoryPort
    audit_repo: AuditRepositoryPort

    admin_routes: AdminRouteRepositoryPort

    def commit(self) -> None:
        ...

    def rollback(self) -> None:
        ...