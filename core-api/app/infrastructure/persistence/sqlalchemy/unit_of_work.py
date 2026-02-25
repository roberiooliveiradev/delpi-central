# app/infrastructure/persistence/sqlalchemy/unit_of_work.py

from sqlalchemy.orm import Session

from app.extensions.db import db
from app.infrastructure.persistence.sqlalchemy.user_repository import SqlAlchemyUserRepository
from app.infrastructure.persistence.sqlalchemy.permission_query_repository import SqlAlchemyPermissionQueryRepository
from app.infrastructure.persistence.sqlalchemy.notification_repository import (
    SqlAlchemyNotificationRepository,
)

from app.infrastructure.persistence.sqlalchemy.app_query_repository import (
    SqlAlchemyAppQueryRepository,
)

from app.infrastructure.persistence.sqlalchemy.favorite_app_repository import (
    SqlAlchemyFavoriteAppRepository,
)

from app.infrastructure.persistence.sqlalchemy.role_repository import (
    SqlAlchemyRoleRepository,
)

from app.infrastructure.persistence.sqlalchemy.role_permission_repository import SqlAlchemyRolePermissionRepository

from app.infrastructure.persistence.sqlalchemy.rbac_query_repository import SqlAlchemyRbacQueryRepository

from app.infrastructure.persistence.sqlalchemy.group_role_repository import SqlAlchemyGroupRoleRepository

from app.infrastructure.persistence.sqlalchemy.user_role_repository import (
    SqlAlchemyUserRoleRepository,
)

from app.infrastructure.persistence.sqlalchemy.user_group_repository import SqlAlchemyUserGroupRepository

from app.infrastructure.persistence.sqlalchemy.admin_app_repository import (
    SqlAlchemyAdminAppRepository,
)

from app.infrastructure.persistence.sqlalchemy.plugin_repository import SqlAlchemyPluginRepository
from app.infrastructure.persistence.sqlalchemy.plugin_manifest_repository import SqlAlchemyPluginManifestRepository
from app.infrastructure.persistence.sqlalchemy.plugin_version_repository import SqlAlchemyPluginVersionRepository
from app.infrastructure.persistence.sqlalchemy.plugin_route_repository import SqlAlchemyPluginRouteRepository
from app.infrastructure.persistence.sqlalchemy.plugin_permission_repository import SqlAlchemyPluginPermissionRepository
from app.infrastructure.persistence.sqlalchemy.audit_repository import SqlAlchemyAuditRepository

from app.infrastructure.persistence.sqlalchemy.admin_route_repository import SqlAlchemyAdminRouteRepository


class SqlAlchemyUnitOfWork:
    def __init__(self):
        self.session: Session = db.session

        self.users = SqlAlchemyUserRepository(self.session)
        self.permission_queries = SqlAlchemyPermissionQueryRepository(self.session)
        
        self.notifications = SqlAlchemyNotificationRepository(self.session)

        self.app_queries = SqlAlchemyAppQueryRepository(self.session)
        self.favorite_apps = SqlAlchemyFavoriteAppRepository(self.session)

        self.roles = SqlAlchemyRoleRepository(self.session)

        self.role_permissions = SqlAlchemyRolePermissionRepository(self.session)
        self.rbac_queries = SqlAlchemyRbacQueryRepository(self.session)

        self.group_roles = SqlAlchemyGroupRoleRepository(self.session)

        self.user_roles = SqlAlchemyUserRoleRepository(self.session)

        self.user_groups = SqlAlchemyUserGroupRepository(self.session)
        
        self.admin_apps = SqlAlchemyAdminAppRepository(self.session)


        self.plugin_repo = SqlAlchemyPluginRepository(self.session)
        self.manifest_repo = SqlAlchemyPluginManifestRepository(self.session)
        self.version_repo = SqlAlchemyPluginVersionRepository(self.session)
        self.route_repo = SqlAlchemyPluginRouteRepository(self.session)
        self.permission_repo = SqlAlchemyPluginPermissionRepository(self.session)
        self.audit_repo = SqlAlchemyAuditRepository(self.session)
        
        self.admin_routes = SqlAlchemyAdminRouteRepository(self.session)

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()