# app/infrastructure/persistence/sqlalchemy/permission_repository.py

from typing import List, Tuple
from uuid import UUID
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from app.domain.ports.permission_repository_port import (
    PermissionRepositoryPort,
    PermissionDTO,
)

from app.infrastructure.db.models import Permission


class SqlAlchemyPermissionRepository(PermissionRepositoryPort):

    def __init__(self, session: Session):
        self.session = session

    # ==========================================================
    # LIST ALL (admin simple list)
    # ==========================================================

    def list_all(self) -> List[PermissionDTO]:
        rows = self.session.query(Permission).all()

        return [
            PermissionDTO(
                id=row.id,
                code=row.code,
                name=row.description or row.code,
                module=row.module,
            )
            for row in rows
        ]

    # ==========================================================
    # PAGINATED LIST (Admin Console)
    # ==========================================================

    def list_paginated(
        self,
        page: int,
        page_size: int,
        sort: str,
        direction: str,
    ) -> Tuple[List[PermissionDTO], int]:

        query = self.session.query(Permission)

        total = query.count()

        sort_column = getattr(Permission, sort, Permission.code)
        order = asc(sort_column) if direction == "asc" else desc(sort_column)

        rows = (
            query
            .order_by(order)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        items = [
            PermissionDTO(
                id=row.id,
                code=row.code,
                name=row.description or row.code,
                module=row.module,
            )
            for row in rows
        ]

        return items, total

    # ==========================================================
    # GET BY CODE
    # ==========================================================

    def get_by_code(self, code: str) -> PermissionDTO | None:
        row = (
            self.session
            .query(Permission)
            .filter(Permission.code == code)
            .first()
        )

        if not row:
            return None

        return PermissionDTO(
            id=row.id,
            code=row.code,
            name=row.description or row.code,
            module=row.module,
        )

    # ==========================================================
    # EXISTS
    # ==========================================================

    def exists_by_code(self, code: str) -> bool:
        return (
            self.session
            .query(Permission.id)
            .filter(Permission.code == code)
            .first()
            is not None
        )

    # ==========================================================
    # CREATE
    # ==========================================================

    def create(
        self,
        code: str,
        name: str,
        module: str,
        description: str | None,
    ) -> UUID:

        permission = Permission(
            code=code,
            description=description or name,
            module=module,
        )

        self.session.add(permission)
        self.session.flush()

        return permission.id

    # ==========================================================
    # DELETE
    # ==========================================================

    def delete(self, permission_id: UUID) -> None:
        (
            self.session
            .query(Permission)
            .filter(Permission.id == permission_id)
            .delete()
        )

    # ==========================================================
    # LIST BY MODULE
    # ==========================================================

    def list_by_module(self, module: str) -> List[PermissionDTO]:

        rows = (
            self.session
            .query(Permission)
            .filter(Permission.module == module)
            .all()
        )

        return [
            PermissionDTO(
                id=row.id,
                code=row.code,
                name=row.description or row.code,
                module=row.module,
            )
            for row in rows
        ]