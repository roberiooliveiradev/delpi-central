# app/infrastructure/persistence/sqlalchemy/admin_app_repository.py

from typing import List
from sqlalchemy.orm import Session

from app.domain.ports.admin_app_repository_port import (
    AdminAppRepositoryPort,
    AdminAppDTO,
)
from app.infrastructure.db.models import App


class SqlAlchemyAdminAppRepository(AdminAppRepositoryPort):

    def __init__(self, session: Session):
        self.session = session

    def list_all(self) -> List[AdminAppDTO]:
        rows = self.session.query(App).all()

        return [
            AdminAppDTO(
                id=row.id,
                name=row.name,
                description=row.description,
                icon=row.icon,
                type=row.type,
                version=row.version,
                active=row.active,
            )
            for row in rows
        ]

    def get(self, app_id: str) -> AdminAppDTO | None:
        row = self.session.get(App, app_id)
        if not row:
            return None

        return AdminAppDTO(
            id=row.id,
            name=row.name,
            description=row.description,
            icon=row.icon,
            type=row.type,
            version=row.version,
            active=row.active,
        )

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