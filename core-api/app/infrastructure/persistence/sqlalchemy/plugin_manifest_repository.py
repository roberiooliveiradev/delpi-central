# app/infrastructure/persistence/sqlalchemy/plugin_manifest_repository.py

from __future__ import annotations

from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.domain.ports.plugin_manifest_repository_port import PluginManifestRepositoryPort
from app.infrastructure.db.models import AppManifest


class SqlAlchemyPluginManifestRepository(PluginManifestRepositoryPort):
    def __init__(self, session: Session):
        self.session = session

    def save(self, plugin_id: str, manifest: Dict[str, Any], checksum: str) -> None:
        row = self.session.get(AppManifest, plugin_id)
        if row:
            row.manifest = manifest
            row.checksum = checksum
            return

        self.session.add(
            AppManifest(
                app_id=plugin_id,
                manifest=manifest,
                checksum=checksum,
            )
        )

    def get(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        row = self.session.get(AppManifest, plugin_id)
        if not row:
            return None
        # retorna somente o manifesto (o controller pode precisar só disso)
        return row.manifest

    def list_all(self) -> List[Dict[str, Any]]:
        rows = self.session.query(AppManifest).all()
        return [{"app_id": str(r.app_id), "manifest": r.manifest} for r in rows]

    def delete(self, plugin_id: str) -> None:
        self.session.query(AppManifest).filter_by(app_id=plugin_id).delete(synchronize_session=False)