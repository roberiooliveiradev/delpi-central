# app/infrastructure/persistence/sqlalchemy/role_permission_repository.py

from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.ports.role_permission_repository_port import (
    RolePermissionRepositoryPort,
)
from app.infrastructure.db.models import Permission, role_permissions


class SqlAlchemyRolePermissionRepository(RolePermissionRepositoryPort):
    def __init__(self, session: Session):
        self.session = session

    def list_permission_codes(self, role_id: UUID) -> List[str]:
        rows = (
            self.session.query(Permission.code)
            .join(
                role_permissions,
                Permission.id == role_permissions.c.permission_id,
            )
            .filter(role_permissions.c.role_id == role_id)
            .all()
        )

        return [code for (code,) in rows]

    def list_permission_ids(self, role_id: UUID) -> List[UUID]:
        rows = (
            self.session.query(role_permissions.c.permission_id)
            .filter(role_permissions.c.role_id == role_id)
            .all()
        )

        return [pid for (pid,) in rows]

    def list_role_ids_by_permission_id(self, permission_id: UUID) -> List[UUID]:
        rows = (
            self.session.query(role_permissions.c.role_id)
            .filter(role_permissions.c.permission_id == permission_id)
            .all()
        )

        return [rid for (rid,) in rows]

    def replace_permissions_by_codes(
        self,
        role_id: UUID,
        permission_codes: List[str],
    ) -> None:
        codes = sorted({
            (code or "").strip()
            for code in permission_codes
            if (code or "").strip()
        })

        perm_rows = (
            self.session.query(Permission.id, Permission.code)
            .filter(Permission.code.in_(codes))
            .all()
        )

        found_codes = {code for (_id, code) in perm_rows}
        missing = [code for code in codes if code not in found_codes]

        if missing:
            raise ValueError(f"Permissions não existem: {', '.join(missing)}")

        (
            self.session.query(role_permissions)
            .filter(role_permissions.c.role_id == role_id)
            .delete(synchronize_session=False)
        )

        for perm_id, _code in perm_rows:
            self.session.execute(
                role_permissions.insert().values(
                    role_id=role_id,
                    permission_id=perm_id,
                )
            )

    def replace_permissions_by_ids(
        self,
        role_id: UUID,
        permission_ids: List[str],
    ) -> None:
        ids = {UUID(pid) for pid in permission_ids if pid}

        existing = {
            row.id for row in
            self.session.query(Permission.id)
            .filter(Permission.id.in_(ids))
            .all()
        }

        missing = ids - existing

        if missing:
            raise ValueError(
                f"Permissions não existem: {', '.join(str(m) for m in missing)}"
            )

        (
            self.session.query(role_permissions)
            .filter(role_permissions.c.role_id == role_id)
            .delete(synchronize_session=False)
        )

        for pid in existing:
            self.session.execute(
                role_permissions.insert().values(
                    role_id=role_id,
                    permission_id=pid,
                )
            )

    def add_permission_by_code(
        self,
        role_id: UUID,
        permission_code: str,
    ) -> None:
        code = (permission_code or "").strip()

        if not code:
            raise ValueError("permission_code vazio")

        perm = self.session.query(Permission).filter_by(code=code).first()

        if not perm:
            raise ValueError(f"Permission não existe: {code}")

        exists = (
            self.session.query(role_permissions)
            .filter(
                role_permissions.c.role_id == role_id,
                role_permissions.c.permission_id == perm.id,
            )
            .first()
            is not None
        )

        if exists:
            return

        self.session.execute(
            role_permissions.insert().values(
                role_id=role_id,
                permission_id=perm.id,
            )
        )

    def add_permission_by_id(self, role_id: UUID, permission_id: str) -> None:
        pid = UUID(permission_id)

        exists = (
            self.session.query(role_permissions)
            .filter(
                role_permissions.c.role_id == role_id,
                role_permissions.c.permission_id == pid,
            )
            .first()
            is not None
        )

        if exists:
            return

        self.session.execute(
            role_permissions.insert().values(
                role_id=role_id,
                permission_id=pid,
            )
        )

    def remove_permission_by_code(
        self,
        role_id: UUID,
        permission_code: str,
    ) -> None:
        code = (permission_code or "").strip()

        if not code:
            return

        perm = self.session.query(Permission).filter_by(code=code).first()

        if not perm:
            return

        (
            self.session.query(role_permissions)
            .filter(
                role_permissions.c.role_id == role_id,
                role_permissions.c.permission_id == perm.id,
            )
            .delete(synchronize_session=False)
        )

    def delete_by_role_id(self, role_id: UUID) -> None:
        (
            self.session.query(role_permissions)
            .filter(role_permissions.c.role_id == role_id)
            .delete(synchronize_session=False)
        )