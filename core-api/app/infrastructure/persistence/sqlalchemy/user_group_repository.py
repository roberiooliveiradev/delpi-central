# app/infrastructure/persistence/sqlalchemy/user_group_repository.py

from typing import List
from uuid import UUID
from sqlalchemy.orm import Session

from app.domain.ports.user_group_repository_port import UserGroupRepositoryPort
from app.infrastructure.db.models import user_groups


class SqlAlchemyUserGroupRepository(UserGroupRepositoryPort):
    def __init__(self, session: Session):
        self.session = session

    def list_group_ids(self, user_id: UUID) -> List[UUID]:
        rows = (
            self.session.query(user_groups.c.group_id)
            .filter(user_groups.c.user_id == user_id)
            .all()
        )
        return [gid for (gid,) in rows]

    def replace_groups(self, user_id: UUID, group_ids: List[UUID]) -> None:
        unique_ids = sorted(set(group_ids))

        (
            self.session.query(user_groups)
            .filter(user_groups.c.user_id == user_id)
            .delete(synchronize_session=False)
        )

        for gid in unique_ids:
            self.session.execute(
                user_groups.insert().values(user_id=user_id, group_id=gid)
            )

    def add_group(self, user_id: UUID, group_id: UUID) -> None:
        exists = (
            self.session.query(user_groups)
            .filter(
                user_groups.c.user_id == user_id,
                user_groups.c.group_id == group_id,
            )
            .first()
            is not None
        )
        if exists:
            return

        self.session.execute(
            user_groups.insert().values(user_id=user_id, group_id=group_id)
        )

    def remove_group(self, user_id: UUID, group_id: UUID) -> None:
        (
            self.session.query(user_groups)
            .filter(
                user_groups.c.user_id == user_id,
                user_groups.c.group_id == group_id,
            )
            .delete(synchronize_session=False)
        )