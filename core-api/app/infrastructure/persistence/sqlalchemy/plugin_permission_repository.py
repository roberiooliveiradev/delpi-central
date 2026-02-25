# app/infrastructure/persistence/sqlalchemy/plugin_permission_repository.py

from __future__ import annotations

from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.domain.ports.plugin_permission_repository_port import PluginPermissionRepositoryPort
from app.infrastructure.db.models import Permission


class SqlAlchemyPluginPermissionRepository(PluginPermissionRepositoryPort):
    def __init__(self, session: Session):
        self.session = session

    def bulk_create(self, permissions: List[Dict[str, Any]]) -> None:
        """
        Espera cada permission:
          {
            "code": str,
            "name": str,
            "description": str | None,
            "module": str
          }
        """
        objs: List[Permission] = []
        for p in permissions:
            objs.append(
                Permission(
                    code=p["code"],
                    name=p["name"],  # obrigatório
                    description=p.get("description"),
                    module=p.get("module"),
                )
            )

        if objs:
            self.session.add_all(objs)

    def delete_by_module(self, module: str) -> None:
        self.session.query(Permission).filter_by(module=module).delete(synchronize_session=False)