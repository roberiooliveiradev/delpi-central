# app/infrastructure/persistence/sqlalchemy/role_repository.py

from typing import List
from uuid import UUID
from sqlalchemy import asc, desc, or_
from sqlalchemy.orm import Session
from typing import Tuple

from app.domain.ports.role_repository_port import RoleRepositoryPort, RoleDTO
from app.infrastructure.db.models import Role


class SqlAlchemyRoleRepository(RoleRepositoryPort):

    def __init__(self, session: Session):
        self.session = session

    def list_all(self) -> List[RoleDTO]:
        rows = self.session.query(Role).all()
        return [
            RoleDTO(
                id=row.id,
                name=row.name,
                description=row.description,
            )
            for row in rows
        ]

    def get(self, role_id: UUID) -> RoleDTO | None:
        row = self.session.get(Role, role_id)
        if not row:
            return None
        return RoleDTO(
            id=row.id,
            name=row.name,
            description=row.description,
        )

    def exists_by_name(self, name: str) -> bool:
        return (
            self.session.query(Role)
            .filter_by(name=name)
            .first()
            is not None
        )

    def create(self, name: str, description: str | None) -> UUID:
        role = Role(
            name=name,
            description=description,
        )
        self.session.add(role)
        self.session.flush()
        return role.id

    def update(self, role_id: UUID, name: str, description: str | None) -> None:
        role = self.session.get(Role, role_id)
        if role:
            role.name = name
            role.description = description

    def delete(self, role_id: UUID) -> None:
        role = self.session.get(Role, role_id)
        if role:
            self.session.delete(role)

    # =========================
    # Paginated List
    # =========================
    def list_paginated(
        self,
        *,
        q: str | None,
        page: int,
        page_size: int,
        sort: str,
        direction: str,
    ) -> Tuple[List[RoleDTO], int]:

        # =========================
        # Segurança — whitelist
        # =========================
        sortable_fields = {
            "name": Role.name,
            "description": Role.description,
            "created_at": getattr(Role, "created_at", None),
        }

        sort_column = sortable_fields.get(sort, Role.name)

        order_clause = desc(sort_column) if direction.lower() == "desc" else asc(sort_column)

        query = self.session.query(Role)

        # =========================
        # Filtro de busca
        # =========================
        if q:
            search = f"%{q}%"
            query = query.filter(
                or_(
                    Role.name.ilike(search),
                    Role.description.ilike(search),
                )
            )

        # =========================
        # Total após filtro
        # =========================
        total = query.count()

        rows = (
            query
            .order_by(order_clause)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return (
            [
                RoleDTO(
                    id=row.id,
                    name=row.name,
                    description=row.description,
                )
                for row in rows
            ],
            total,
        )