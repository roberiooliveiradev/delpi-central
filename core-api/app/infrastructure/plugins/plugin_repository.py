# app/infrastructure/plugins/plugin_repository.py

from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.infrastructure.db.models import (
    App,
    Permission,
    AppRoute,
    AppManifest,
    AuditLog,
    AppVersion
)


# ==========================================================
# App Repository
# ==========================================================

class SqlAlchemyAppRepository:

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, app_id: str) -> Optional[Dict[str, Any]]:
        app = self.session.get(App, app_id)
        if not app:
            return None

        return {
            "id": app.id,
            "version": app.version
        }

    def create(self, data: Dict[str, Any]) -> None:
        self.session.add(App(**data))

    def update_version(self, app_id: str, version: str) -> None:
        app = self.session.get(App, app_id)
        if app:
            app.version = version


# ==========================================================
# App Version Repository
# ==========================================================
class SqlAlchemyAppVersionRepository:

    def __init__(self, session):
        self.session = session

    def exists(self, app_id: str, version: str) -> bool:
        return (
            self.session.query(AppVersion)
            .filter_by(app_id=app_id, version=version)
            .first()
            is not None
        )

    def create(self, data: dict) -> AppVersion:
        """
        Esperado pelo RegisterPluginUseCase
        """
        app_version = AppVersion(
            app_id=data["app_id"],
            version=data["version"],
            manifest=data["manifest"],
            checksum=data["checksum"],
        )

        self.session.add(app_version)
        return app_version
    
# ==========================================================
# Permission Repository
# ==========================================================

class SqlAlchemyPermissionRepository:

    def __init__(self, session: Session):
        self.session = session

    def exists_by_code(self, code: str) -> bool:
        return (
            self.session.query(Permission)
            .filter_by(code=code)
            .first()
            is not None
        )

    def get_by_code(self, code: str) -> Optional[Permission]:
        return (
            self.session.query(Permission)
            .filter_by(code=code)
            .first()
        )

    def bulk_create(self, permissions: List[Dict[str, Any]]) -> None:
        """
        NÃO usar bulk_insert_mappings pois:
        - ignora validações
        - ignora defaults
        - ignora eventos
        - pode quebrar UUID default
        """

        objs = [
            Permission(
                code=p["code"],
                name=p["code"],  # obrigatório (nullable=False)
                description=p.get("description"),
                module=p.get("module"),
            )
            for p in permissions
        ]

        self.session.add_all(objs)


# ==========================================================
# Route Repository
# ==========================================================

class SqlAlchemyRouteRepository:

    def __init__(self, session: Session):
        self.session = session

    def exists_by_path(self, path: str) -> bool:
        return (
            self.session.query(AppRoute)
            .filter_by(path=path, active=True)
            .first()
            is not None
        )

    def bulk_create(self, routes: List[Dict[str, Any]]) -> None:
        """
        Espera routes no formato:
        {
            "app_id": str,
            "path": str,
            "label": str,
            "icon": str,
            "permission": str,   # permission CODE
            "order": int,
            "show_in_menu": bool
        }
        """

        objs = []

        for r in routes:

            permission = (
                self.session.query(Permission)
                .filter_by(code=r["permission"])
                .first()
            )

            objs.append(
                AppRoute(
                    app_id=r["app_id"],
                    path=r["path"],
                    label=r.get("label"),
                    icon=r.get("icon"),
                    permission_id=permission.id if permission else None,
                    order=r.get("order", 0),
                    show_in_menu=r.get("show_in_menu", True),
                    active=True,
                )
            )

        self.session.add_all(objs)

    def get_by_path(self, path: str) -> Optional[AppRoute]:
        return (
            self.session.query(AppRoute)
            .filter_by(path=path, active=True)
            .first()
        )
# ==========================================================
# Manifest Repository
# ==========================================================

class SqlAlchemyManifestRepository:

    def __init__(self, session: Session):
        self.session = session

    def save(self, app_id: str, manifest: Dict[str, Any], checksum: str) -> None:

        existing = self.session.get(AppManifest, app_id)

        if existing:
            existing.manifest = manifest
            existing.checksum = checksum
        else:
            self.session.add(
                AppManifest(
                    app_id=app_id,
                    manifest=manifest,
                    checksum=checksum,
                )
            )


# ==========================================================
# Audit Repository
# ==========================================================

class SqlAlchemyAuditRepository:

    def __init__(self, session: Session):
        self.session = session

    def log(self, data: Dict[str, Any]) -> None:

        self.session.add(
            AuditLog(
                user_id=data.get("user_id"),
                action=data.get("action"),
                entity_type=data.get("entity_type"),
                entity_id=data.get("entity_id"),
                payload=data.get("payload"),
                ip_address=data.get("ip_address"),
            )
        )