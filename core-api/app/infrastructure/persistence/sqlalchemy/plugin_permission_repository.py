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
                    name=p["name"],
                    description=p.get("description"),
                    module=p.get("module"),
                )
            )

        if objs:
            self.session.add_all(objs)

    def delete_by_module(self, module: str) -> None:
        self.session.query(Permission).filter_by(module=module).delete(
            synchronize_session=False
        )

    def list_by_module(self, module: str) -> List[Dict[str, Any]]:
        rows = (
            self.session.query(Permission)
            .filter_by(module=module)
            .order_by(Permission.code.asc())
            .all()
        )
        return [
            {
                "id": str(r.id),
                "code": r.code,
                "name": r.name,
                "description": r.description,
                "module": r.module,
            }
            for r in rows
        ]

    def sync_module(self, module: str, desired: List[Dict[str, Any]]) -> Dict[str, Any]:
        existing = (
            self.session.query(Permission)
            .filter_by(module=module)
            .all()
        )
        by_code = {str(row.code): row for row in existing if row.code}

        desired_by_code: Dict[str, Dict[str, Any]] = {}
        for item in desired:
            code = str(item.get("code") or "").strip()
            if not code:
                continue
            desired_by_code[code] = item

        kept = 0
        inserted = 0
        deleted = 0

        for code, row in list(by_code.items()):
            if code not in desired_by_code:
                self.session.delete(row)
                deleted += 1
                by_code.pop(code, None)

        self.session.flush()

        for code, item in desired_by_code.items():
            name = str(item.get("name") or code).strip() or code
            description = item.get("description")
            if code in by_code:
                row = by_code[code]
                row.name = name
                row.description = description
                row.module = module
                kept += 1
            else:
                self.session.add(
                    Permission(
                        code=code,
                        name=name,
                        description=description,
                        module=module,
                    )
                )
                inserted += 1

        self.session.flush()

        return {
            "kept": kept,
            "inserted": inserted,
            "deleted": deleted,
            "codes": sorted(desired_by_code.keys()),
        }
