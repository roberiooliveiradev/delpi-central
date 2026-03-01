# app/infrastructure/persistence/sqlalchemy/role_permission_repository.py

from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.ports.role_permission_repository_port import RolePermissionRepositoryPort
from app.infrastructure.db.models import Permission, role_permissions


class SqlAlchemyRolePermissionRepository(RolePermissionRepositoryPort):
    def __init__(self, session: Session):
        self.session = session

    def list_permission_codes(self, role_id: UUID) -> List[str]:
        rows = (
            self.session.query(Permission.code)
            .join(role_permissions, Permission.id == role_permissions.c.permission_id)
            .filter(role_permissions.c.role_id == role_id)
            .all()
        )
        return [code for (code,) in rows]

    def replace_permissions_by_codes(self, role_id: UUID, permission_codes: List[str]) -> None:
        # Normaliza
        codes = sorted({(c or "").strip() for c in permission_codes if (c or "").strip()})
        # Busca IDs existentes
        perm_rows = (
            self.session.query(Permission.id, Permission.code)
            .filter(Permission.code.in_(codes))
            .all()
        )
        found_codes = {code for (_id, code) in perm_rows}

        # Se algum code não existe, falha (melhor do que inserir "quebrado")
        missing = [c for c in codes if c not in found_codes]
        if missing:
            raise ValueError(f"Permissions não existem: {', '.join(missing)}")

        # Apaga vínculos atuais
        (
            self.session.query(role_permissions)
            .filter(role_permissions.c.role_id == role_id)
            .delete(synchronize_session=False)
        )

        # Insere vínculos novos
        for perm_id, _code in perm_rows:
            self.session.execute(
                role_permissions.insert().values(role_id=role_id, permission_id=perm_id)
            )

    def replace_permissions_by_ids(self, role_id: UUID, permission_ids: List[str]) -> None:
        # Normaliza UUIDs
        ids = {UUID(pid) for pid in permission_ids if pid}

        # Verifica se todas existem
        existing = {
            row.id for row in
            self.session.query(Permission.id)
            .filter(Permission.id.in_(ids))
            .all()
        }

        missing = ids - existing
        if missing:
            raise ValueError(f"Permissions não existem: {', '.join(str(m) for m in missing)}")

        # Remove vínculos atuais
        (
            self.session.query(role_permissions)
            .filter(role_permissions.c.role_id == role_id)
            .delete(synchronize_session=False)
        )

        # Insere novos vínculos
        for pid in existing:
            self.session.execute(
                role_permissions.insert().values(
                    role_id=role_id,
                    permission_id=pid
                )
            )

    def add_permission_by_code(self, role_id: UUID, permission_code: str) -> None:
        code = (permission_code or "").strip()
        if not code:
            raise ValueError("permission_code vazio")

        perm = self.session.query(Permission).filter_by(code=code).first()
        if not perm:
            raise ValueError(f"Permission não existe: {code}")

        # evita duplicar
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
            role_permissions.insert().values(role_id=role_id, permission_id=perm.id)
        )

    def add_permission_by_id(self, role_id: UUID, permission_id: str):
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

        if not exists:
            self.session.execute(
                role_permissions.insert().values(
                    role_id=role_id,
                    permission_id=pid
                )
            )

    def remove_permission_by_code(self, role_id: UUID, permission_code: str) -> None:
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

    def list_permission_ids(self, role_id: UUID):
        rows = (
            self.session.query(role_permissions.c.permission_id)
            .filter(role_permissions.c.role_id == role_id)
            .all()
        )
        return [pid for (pid,) in rows]