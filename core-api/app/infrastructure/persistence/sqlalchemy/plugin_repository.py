# app/infrastructure/persistence/sqlalchemy/plugin_repository.py

from __future__ import annotations

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.domain.ports.plugin_repository_port import PluginRepositoryPort
from app.infrastructure.db.models import App
from app.infrastructure.persistence.app_audit import apply_app_audit


class SqlAlchemyPluginRepository(PluginRepositoryPort):
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, plugin_id: str) -> Optional[App]:
        return self.session.get(App, plugin_id)

    def create(
        self,
        data: Dict[str, Any],
        *,
        actor_user_id: str | None = None,
        actor_name: str | None = None,
    ) -> None:
        row = App(**data)
        apply_app_audit(
            row,
            user_id=actor_user_id,
            name=actor_name,
            on_create=True,
        )
        self.session.add(row)

    def update_version(
        self,
        plugin_id: str,
        version: str,
        *,
        actor_user_id: str | None = None,
        actor_name: str | None = None,
    ) -> None:
        row = self.session.get(App, plugin_id)
        if not row:
            raise ValueError("Plugin not found")
        row.version = version
        apply_app_audit(row, user_id=actor_user_id, name=actor_name)

    def update_metadata(
        self,
        plugin_id: str,
        *,
        name: str,
        description: Optional[str],
        icon: Optional[str],
        actor_user_id: str | None = None,
        actor_name: str | None = None,
    ) -> None:
        row = self.session.get(App, plugin_id)
        if not row:
            raise ValueError("Plugin not found")

        row.name = name
        row.description = description
        row.icon = icon
        apply_app_audit(row, user_id=actor_user_id, name=actor_name)

    def delete(self, plugin_id: str) -> None:
        row = self.session.get(App, plugin_id)
        if not row:
            raise ValueError("Plugin not found")
        self.session.delete(row)