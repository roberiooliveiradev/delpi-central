# app/infrastructure/persistence/sqlalchemy/admin_app_repository.py

from typing import List, Tuple
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from app.domain.ports.admin_app_repository_port import (
    AdminAppRepositoryPort,
    AdminAppDTO,
)
from app.infrastructure.db.models import App, User


def _load_user_names(session, rows: list[App]) -> dict[str, str]:
    user_ids: set = set()

    for row in rows:
        if row.created_by_user_id:
            user_ids.add(row.created_by_user_id)
        if row.updated_by_user_id:
            user_ids.add(row.updated_by_user_id)

    if not user_ids:
        return {}

    return {
        str(user.id): user.name
        for user in session.query(User).filter(User.id.in_(user_ids)).all()
    }


def _resolve_audit_name(
    stored_name: str | None,
    user_id,
    names_by_id: dict[str, str],
) -> str | None:
    if stored_name and stored_name.strip():
        return stored_name.strip()

    if user_id:
        return names_by_id.get(str(user_id))

    return None


def _to_admin_app_dto(row: App, names_by_id: dict[str, str]) -> AdminAppDTO:
    return AdminAppDTO(
        id=row.id,
        name=row.name,
        description=row.description,
        icon=row.icon,
        type=row.type,
        version=row.version,
        active=row.active,
        base_path=row.base_path,
        created_at=row.created_at,
        updated_at=row.updated_at,
        created_by_user_id=str(row.created_by_user_id) if row.created_by_user_id else None,
        created_by_name=_resolve_audit_name(
            row.created_by_name,
            row.created_by_user_id,
            names_by_id,
        ),
        updated_by_user_id=str(row.updated_by_user_id) if row.updated_by_user_id else None,
        updated_by_name=_resolve_audit_name(
            row.updated_by_name,
            row.updated_by_user_id,
            names_by_id,
        ),
    )


class SqlAlchemyAdminAppRepository(AdminAppRepositoryPort):

    def __init__(self, session: Session):
        self.session = session


    def list_paginated(
        self,
        page: int,
        page_size: int,
        q: str | None,
        sort: str,
        direction: str,
        created_from=None,
        created_to=None,
        updated_from=None,
        updated_to=None,
    ) -> Tuple[List[AdminAppDTO], int]:

        query = self.session.query(App)

        # 🔍 busca
        if q:
            query = query.filter(App.name.ilike(f"%{q}%"))

        if created_from is not None:
            query = query.filter(App.created_at >= created_from)
        if created_to is not None:
            query = query.filter(App.created_at <= created_to)
        if updated_from is not None:
            query = query.filter(App.updated_at >= updated_from)
        if updated_to is not None:
            query = query.filter(App.updated_at <= updated_to)

        # 🔄 ordenação segura
        allowed_sort = {
            "name": App.name,
            "version": App.version,
            "active": App.active,
            "type": App.type,
            "created_at": App.created_at,
            "updated_at": App.updated_at,
        }

        sort_column = allowed_sort.get(sort, App.name)
        order_func = asc if direction.lower() == "asc" else desc
        query = query.order_by(order_func(sort_column))

        total = query.count()

        rows = (
            query
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        names_by_id = _load_user_names(self.session, rows)

        return (
            [_to_admin_app_dto(row, names_by_id) for row in rows],
            total,
        )

    def get(self, app_id: str) -> AdminAppDTO | None:
        row = self.session.get(App, app_id)
        if not row:
            return None

        names_by_id = _load_user_names(self.session, [row])
        return _to_admin_app_dto(row, names_by_id)

    def update_metadata(self, app_id: str, name: str, description: str | None, icon: str | None) -> None:
        row = self.session.get(App, app_id)
        if not row:
            raise ValueError("App não encontrada")

        row.name = name
        row.description = description
        row.icon = icon

    def set_active(self, app_id: str, active: bool) -> None:
        row = self.session.get(App, app_id)
        if not row:
            raise ValueError("App não encontrada")

        row.active = active

    def delete(self, app_id: str) -> None:
        row = self.session.get(App, app_id)
        if not row:
            raise ValueError("App não encontrada")

        self.session.delete(row)