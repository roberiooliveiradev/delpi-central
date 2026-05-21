# app/infrastructure/persistence/sqlalchemy/admin_app_repository.py

from typing import List, Tuple
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from app.domain.ports.admin_app_repository_port import (
    AdminAppRepositoryPort,
    AdminAppDTO,
)
from app.infrastructure.db.models import App


def _to_admin_app_dto(row: App) -> AdminAppDTO:
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
        created_by_email=row.created_by_email,
        updated_by_user_id=str(row.updated_by_user_id) if row.updated_by_user_id else None,
        updated_by_email=row.updated_by_email,
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
    ) -> Tuple[List[AdminAppDTO], int]:

        query = self.session.query(App)

        # 🔍 busca
        if q:
            query = query.filter(App.name.ilike(f"%{q}%"))

        # 🔄 ordenação segura
        allowed_sort = {
            "name": App.name,
            "version": App.version,
            "active": App.active,
            "type": App.type,
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

        return (
            [_to_admin_app_dto(row) for row in rows],
            total,
        )

    def get(self, app_id: str) -> AdminAppDTO | None:
        row = self.session.get(App, app_id)
        if not row:
            return None

        return _to_admin_app_dto(row)

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