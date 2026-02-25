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

    def commit(self) -> None:
        ...

    def rollback(self) -> None:
        ...