# app/infrastructure/persistence/sqlalchemy/user_repository.py

from __future__ import annotations

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session

from app.domain.ports.user_repository_port import UserRepositoryPort, UserDTO
from app.infrastructure.db.models import User


class SqlAlchemyUserRepository(UserRepositoryPort):
    def __init__(self, session: Session):
        self.session = session

    # =========================
    # Helpers
    # =========================

    def _to_dto(self, row: User) -> UserDTO:
        return UserDTO(
            id=row.id,
            email=row.email,
            name=row.name,
            active=bool(getattr(row, "active", True)),
            is_superadmin=bool(getattr(row, "is_superadmin", False)),
            last_login_at=getattr(row, "last_login_at", None),
        )

    # =========================
    # Queries
    # =========================

    def get_by_email(self, email: str) -> Optional[UserDTO]:
        row = self.session.query(User).filter_by(email=email).first()
        return self._to_dto(row) if row else None

    def get_by_id(self, user_id: UUID) -> Optional[UserDTO]:
        row = self.session.get(User, user_id)
        return self._to_dto(row) if row else None

    def list_all(self) -> List[UserDTO]:
        rows = self.session.query(User).all()
        return [self._to_dto(r) for r in rows]

    # =========================
    # Commands
    # =========================

    def create(
        self,
        *,
        id: UUID,
        email: str,
        name: str,
        is_superadmin: bool = False,
    ) -> None:
        row = User(
            id=id,
            email=email,
            name=name,
            is_superadmin=is_superadmin,
        )

        # se o model tiver active, setamos True por padrão
        if hasattr(row, "active"):
            setattr(row, "active", True)

        self.session.add(row)

    def update_name(self, user_id: UUID, name: str) -> None:
        row = self.session.get(User, user_id)
        if row:
            row.name = name

    def set_active(self, user_id: UUID, active: bool) -> None:
        row = self.session.get(User, user_id)
        if row and hasattr(row, "active"):
            setattr(row, "active", active)

    def set_superadmin(self, user_id: UUID, is_superadmin: bool) -> None:
        row = self.session.get(User, user_id)
        if row and hasattr(row, "is_superadmin"):
            setattr(row, "is_superadmin", is_superadmin)

    def update_last_login(self, user_id: UUID, timestamp: datetime) -> None:
        row = self.session.get(User, user_id)
        if row and hasattr(row, "last_login_at"):
            setattr(row, "last_login_at", timestamp)

    def delete(self, user_id: UUID) -> None:
        row = self.session.get(User, user_id)
        if row:
            self.session.delete(row)

    # =========================
    # Paginated List
    # =========================

    def list_paginated(
        self,
        *,
        page: int,
        page_size: int,
        sort: str,
        direction: str,
    ) -> tuple[list[UserDTO], int]:

        query = self.session.query(User)

        # =========================
        # Sorting seguro
        # =========================

        sort_map = {
            "email": User.email,
            "name": User.name,
            "created_at": getattr(User, "created_at", User.email),
            "last_login_at": getattr(User, "last_login_at", User.email),
        }

        column = sort_map.get(sort, User.email)

        if direction.lower() == "desc":
            column = column.desc()

        query = query.order_by(column)

        # =========================
        # Total
        # =========================

        total = query.count()

        # =========================
        # Pagination
        # =========================

        offset = (page - 1) * page_size

        rows = (
            query
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return [self._to_dto(r) for r in rows], total
    
    def count_superadmins(self) -> int:
        return (
            self.session.query(User)
            .filter_by(is_superadmin=True)
            .count()
        )