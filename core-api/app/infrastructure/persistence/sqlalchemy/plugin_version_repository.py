# app/infrastructure/persistence/sqlalchemy/plugin_version_repository.py

from __future__ import annotations

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.domain.ports.plugin_version_repository_port import PluginVersionRepositoryPort
from app.infrastructure.db.models import AppVersion


class SqlAlchemyPluginVersionRepository(PluginVersionRepositoryPort):
    def __init__(self, session: Session):
        self.session = session

    def exists(self, plugin_id: str, version: str) -> bool:
        return (
            self.session.query(AppVersion)
            .filter_by(app_id=plugin_id, version=version)
            .first()
            is not None
        )

    def create(self, data: Dict[str, Any]) -> None:
        """
        Espera:
          data = {
            "app_id": str,
            "version": str,
            "manifest": dict,
            "checksum": str
          }
        """
        row = AppVersion(
            app_id=data["app_id"],
            version=data["version"],
            manifest=data["manifest"],
            checksum=data["checksum"],
        )
        self.session.add(row)

    def list_versions(self, plugin_id: str) -> List[Dict[str, Any]]:
        rows = (
            self.session.query(AppVersion)
            .filter_by(app_id=plugin_id)
            .order_by(AppVersion.created_at.desc())
            .all()
        )
        return [
            {
                "version": r.version,
                "checksum": r.checksum,
                "created_at": r.created_at.isoformat() if getattr(r, "created_at", None) else None,
            }
            for r in rows
        ]

    def get_version(self, plugin_id: str, version: str) -> Optional[Dict[str, Any]]:
        row = (
            self.session.query(AppVersion)
            .filter_by(app_id=plugin_id, version=version)
            .first()
        )
        if not row:
            return None

        return {
            "version": row.version,
            "checksum": row.checksum,
            "created_at": row.created_at.isoformat() if getattr(row, "created_at", None) else None,
            "manifest": row.manifest,
        }

    def delete_by_app(self, plugin_id: str) -> None:
        self.session.query(AppVersion).filter_by(app_id=plugin_id).delete(synchronize_session=False)