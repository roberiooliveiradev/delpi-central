# app/infrastructure/persistence/sqlalchemy/user_role_repository.py

from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.ports.user_role_repository_port import UserRoleRepositoryPort
from app.infrastructure.db.models import user_roles


class SqlAlchemyUserRoleRepository(UserRoleRepositoryPort):

    def __init__(self, session: Session):
        self.session = session

    def list_role_ids(self, user_id: UUID) -> List[UUID]:
        rows = (
            self.session.query(user_roles.c.role_id)
            .filter(user_roles.c.user_id == user_id)
            .all()
        )
        return [rid for (rid,) in rows]

    def list_user_ids_by_role_id(self, role_id: UUID) -> List[UUID]:
        rows = (
            self.session.query(user_roles.c.user_id)
            .filter(user_roles.c.role_id == role_id)
            .all()
        )
        return [uid for (uid,) in rows]

    def replace_roles(self, user_id: UUID, role_ids: List[UUID]) -> None:
        unique_ids = sorted(set(role_ids))

        (
            self.session.query(user_roles)
            .filter(user_roles.c.user_id == user_id)
            .delete(synchronize_session=False)
        )

        for rid in unique_ids:
            self.session.execute(
                user_roles.insert().values(user_id=user_id, role_id=rid)
            )

    def add_role(self, user_id: UUID, role_id: UUID) -> None:
        exists = (
            self.session.query(user_roles)
            .filter(
                user_roles.c.user_id == user_id,
                user_roles.c.role_id == role_id,
            )
            .first()
            is not None
        )

        if exists:
            return

        self.session.execute(
            user_roles.insert().values(user_id=user_id, role_id=role_id)
        )

    def remove_role(self, user_id: UUID, role_id: UUID) -> None:
        (
            self.session.query(user_roles)
            .filter(
                user_roles.c.user_id == user_id,
                user_roles.c.role_id == role_id,
            )
            .delete(synchronize_session=False)
        )

    def delete_by_role_id(self, role_id: UUID) -> None:
        (
            self.session.query(user_roles)
            .filter(user_roles.c.role_id == role_id)
            .delete(synchronize_session=False)
        )

    def delete_by_user_id(self, user_id: UUID) -> None:
        (
            self.session.query(user_roles)
            .filter(user_roles.c.user_id == user_id)
            .delete(synchronize_session=False)
        )