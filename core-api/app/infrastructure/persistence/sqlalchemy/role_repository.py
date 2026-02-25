# app/infrastructure/persistence/sqlalchemy/role_repository.py

from typing import List
from uuid import UUID
from sqlalchemy.orm import Session

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