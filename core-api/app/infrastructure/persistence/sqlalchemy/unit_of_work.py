# app/infrastructure/persistence/sqlalchemy/unit_of_work.py

from sqlalchemy.orm import Session

from app.extensions.db import db

from app.infrastructure.cache.rbac_permission_cache_adapter import RbacCachePermissionCacheAdapter

from app.infrastructure.persistence.sqlalchemy.user_repository import SqlAlchemyUserRepository
from app.infrastructure.persistence.sqlalchemy.permission_repository import SqlAlchemyPermissionRepository
from app.infrastructure.persistence.sqlalchemy.permission_query_repository import SqlAlchemyPermissionQueryRepository
from app.infrastructure.persistence.sqlalchemy.notification_repository import SqlAlchemyNotificationRepository
from app.infrastructure.persistence.sqlalchemy.app_query_repository import SqlAlchemyAppQueryRepository
from app.infrastructure.persistence.sqlalchemy.favorite_app_repository import SqlAlchemyFavoriteAppRepository
from app.infrastructure.persistence.sqlalchemy.role_repository import SqlAlchemyRoleRepository
from app.infrastructure.persistence.sqlalchemy.role_permission_repository import SqlAlchemyRolePermissionRepository
from app.infrastructure.persistence.sqlalchemy.rbac_query_repository import SqlAlchemyRbacQueryRepository
from app.infrastructure.persistence.sqlalchemy.group_role_repository import SqlAlchemyGroupRoleRepository
from app.infrastructure.persistence.sqlalchemy.user_role_repository import SqlAlchemyUserRoleRepository
from app.infrastructure.persistence.sqlalchemy.group_repository import SqlAlchemyGroupRepository
from app.infrastructure.persistence.sqlalchemy.user_group_repository import SqlAlchemyUserGroupRepository
from app.infrastructure.persistence.sqlalchemy.admin_app_repository import SqlAlchemyAdminAppRepository
from app.infrastructure.persistence.sqlalchemy.admin_route_repository import SqlAlchemyAdminRouteRepository

from app.infrastructure.persistence.sqlalchemy.plugin_repository import SqlAlchemyPluginRepository
from app.infrastructure.persistence.sqlalchemy.plugin_manifest_repository import SqlAlchemyPluginManifestRepository
from app.infrastructure.persistence.sqlalchemy.plugin_version_repository import SqlAlchemyPluginVersionRepository
from app.infrastructure.persistence.sqlalchemy.plugin_route_repository import SqlAlchemyPluginRouteRepository
from app.infrastructure.persistence.sqlalchemy.plugin_permission_repository import SqlAlchemyPluginPermissionRepository

from app.infrastructure.persistence.sqlalchemy.audit_repository import SqlAlchemyAuditRepository
from app.infrastructure.persistence.sqlalchemy.route_query_repository import (
    SqlAlchemyRouteQueryRepository,
)

class SqlAlchemyUnitOfWork:
    def __init__(self):
        self.session: Session = db.session

        # =========================
        # RBAC
        # =========================
        self.users = SqlAlchemyUserRepository(self.session)
        self.roles = SqlAlchemyRoleRepository(self.session)
        self.permissions = SqlAlchemyPermissionRepository(self.session)
        self.cache = RbacCachePermissionCacheAdapter()
        self.role_permissions = SqlAlchemyRolePermissionRepository(self.session)

        self.user_roles = SqlAlchemyUserRoleRepository(self.session)

        self.groups = SqlAlchemyGroupRepository(self.session)
        self.user_groups = SqlAlchemyUserGroupRepository(self.session)
        self.group_roles = SqlAlchemyGroupRoleRepository(self.session)

        self.rbac_queries = SqlAlchemyRbacQueryRepository(self.session)
        self.permission_queries = SqlAlchemyPermissionQueryRepository(self.session)

        # =========================
        # Notifications
        # =========================
        self.notifications = SqlAlchemyNotificationRepository(self.session)

        # =========================
        # Apps & Routes
        # =========================
        self.app_queries = SqlAlchemyAppQueryRepository(self.session)
        self.admin_apps = SqlAlchemyAdminAppRepository(self.session)
        self.admin_routes = SqlAlchemyAdminRouteRepository(self.session)

        # =========================
        # Favorites
        # =========================
        self.favorites = SqlAlchemyFavoriteAppRepository(self.session)

        # =========================
        # Plugins (novo naming)
        # =========================
        self.plugins = SqlAlchemyPluginRepository(self.session)
        self.plugin_manifests = SqlAlchemyPluginManifestRepository(self.session)
        self.plugin_versions = SqlAlchemyPluginVersionRepository(self.session)
        self.plugin_routes = SqlAlchemyPluginRouteRepository(self.session)
        self.plugin_permissions = SqlAlchemyPluginPermissionRepository(self.session)

        # =========================
        # Usuario
        # =========================
        self.route_queries = SqlAlchemyRouteQueryRepository(self.session)

        # =========================
        # Audits
        # =========================
        self.audits = SqlAlchemyAuditRepository(self.session)

        # ======================================================
        # Aliases (compatibilidade com código antigo)
        # ======================================================
        self.favorite_apps = self.favorites

        self.plugin_repo = self.plugins
        self.manifest_repo = self.plugin_manifests
        self.version_repo = self.plugin_versions
        self.route_repo = self.plugin_routes
        self.permission_repo = self.plugin_permissions

        self.audit_repo = self.audits

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()

    # =========================
    # Context manager support
    # =========================

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc:
            self.rollback()
        else:
            self.commit()