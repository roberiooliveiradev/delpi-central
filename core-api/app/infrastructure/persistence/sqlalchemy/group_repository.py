# app/infrastructure/persistence/sqlalchemy/group_repository.py

from typing import List, Tuple, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import asc, desc, or_

from app.domain.ports.group_repository_port import GroupRepositoryPort, GroupDTO
from app.infrastructure.db.models import Group


class SqlAlchemyGroupRepository(GroupRepositoryPort):

    def __init__(self, session: Session):
        self.session = session

    def _to_dto(self, row: Group) -> GroupDTO:
        return GroupDTO(
            id=row.id,
            name=row.name,
            description=row.description,
        )

    # =========================
    # Queries
    # =========================

    def get(self, group_id: UUID) -> Optional[GroupDTO]:
        row = self.session.get(Group, group_id)
        return self._to_dto(row) if row else None

    def list_all(self) -> List[GroupDTO]:
        rows = self.session.query(Group).all()
        return [self._to_dto(r) for r in rows]

    def list_paginated(
        self,
        *,
        q: str | None,
        page: int,
        page_size: int,
        sort: str,
        direction: str,
    ) -> Tuple[List[GroupDTO], int]:

        sortable_fields = {
            "name": Group.name,
            "description": Group.description,
            "created_at": getattr(Group, "created_at", None),
        }

        sort_column = sortable_fields.get(sort, Group.name)
        order_clause = desc(sort_column) if direction == "desc" else asc(sort_column)

        query = self.session.query(Group)

        if q:
            search = f"%{q}%"
            query = query.filter(
                or_(
                    Group.name.ilike(search),
                    Group.description.ilike(search),
                )
            )

        total = query.count()

        rows = (
            query
            .order_by(order_clause)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return [self._to_dto(r) for r in rows], total

    # =========================
    # Commands
    # =========================

    def create(self, name: str, description: str | None) -> UUID:
        group = Group(name=name, description=description)
        self.session.add(group)
        self.session.flush()
        return group.id

    def update(self, group_id: UUID, name: str, description: str | None) -> None:
        group = self.session.get(Group, group_id)
        if group:
            group.name = name
            group.description = description

    def delete(self, group_id: UUID) -> None:
        group = self.session.get(Group, group_id)
        if group:
            self.session.delete(group)
            