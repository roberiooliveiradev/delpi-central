# app/infrastructure/plugins/unit_of_work.py

from app.extensions.db import db
from app.application.plugins.ports import UnitOfWork
from app.infrastructure.plugins.plugin_repository import (
    SqlAlchemyAppRepository,
    SqlAlchemyPermissionRepository,
    SqlAlchemyRouteRepository,
    SqlAlchemyManifestRepository,
    SqlAlchemyAuditRepository,
    SqlAlchemyAppVersionRepository 
)


class SqlAlchemyUnitOfWork(UnitOfWork):

    def __init__(self, session=None):
        self.session = session or db.session

        self.app_repo = SqlAlchemyAppRepository(self.session)
        self.permission_repo = SqlAlchemyPermissionRepository(self.session)
        self.route_repo = SqlAlchemyRouteRepository(self.session)
        self.manifest_repo = SqlAlchemyManifestRepository(self.session)
        self.audit_repo = SqlAlchemyAuditRepository(self.session)

        self.app_version_repo = SqlAlchemyAppVersionRepository(self.session)

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()