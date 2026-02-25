# app/infrastructure/persistence/sqlalchemy/plugin_repository.py

from __future__ import annotations

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.domain.ports.plugin_repository_port import PluginRepositoryPort
from app.infrastructure.db.models import App


class SqlAlchemyPluginRepository(PluginRepositoryPort):
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        row = self.session.get(App, plugin_id)
        if not row:
            return None

        return {
            "id": str(row.id),
            "name": row.name,
            "description": row.description,
            "icon": row.icon,
            "type": getattr(row, "type", None),
            "version": row.version,
            "active": bool(getattr(row, "active", True)),
        }

    def create(self, data: Dict[str, Any]) -> None:
        # Espera os campos do model App
        self.session.add(App(**data))

    def update_version(self, plugin_id: str, version: str) -> None:
        row = self.session.get(App, plugin_id)
        if not row:
            raise ValueError("Plugin not found")
        row.version = version

    def update_metadata(
        self,
        plugin_id: str,
        *,
        name: str,
        description: Optional[str],
        icon: Optional[str],
    ) -> None:
        row = self.session.get(App, plugin_id)
        if not row:
            raise ValueError("Plugin not found")

        row.name = name
        row.description = description
        row.icon = icon

    def delete(self, plugin_id: str) -> None:
        row = self.session.get(App, plugin_id)
        if not row:
            raise ValueError("Plugin not found")
        self.session.delete(row)