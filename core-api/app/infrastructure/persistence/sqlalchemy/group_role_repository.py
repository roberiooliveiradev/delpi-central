# app/infrastructure/persistence/sqlalchemy/group_role_repository.py

from typing import List, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.ports.group_role_repository_port import GroupRoleRepositoryPort
from app.infrastructure.db.models import group_roles


class SqlAlchemyGroupRoleRepository(GroupRoleRepositoryPort):

    def __init__(self, session: Session):
        self.session = session

    def list_role_ids(self, group_id: UUID) -> List[UUID]:
        rows = (
            self.session.query(group_roles.c.role_id)
            .filter(group_roles.c.group_id == group_id)
            .all()
        )

        return [rid for (rid,) in rows]

    def list_group_role_ids_by_role_ids(
        self,
        role_ids: List[UUID],
    ) -> List[Tuple[UUID, UUID]]:
        if not role_ids:
            return []

        rows = (
            self.session.query(
                group_roles.c.group_id,
                group_roles.c.role_id,
            )
            .filter(group_roles.c.role_id.in_(role_ids))
            .all()
        )

        return [(group_id, role_id) for group_id, role_id in rows]

    def replace_roles(self, group_id: UUID, role_ids: List[UUID]) -> None:
        unique_ids = sorted(set(role_ids))

        (
            self.session.query(group_roles)
            .filter(group_roles.c.group_id == group_id)
            .delete(synchronize_session=False)
        )

        for rid in unique_ids:
            self.session.execute(
                group_roles.insert().values(
                    group_id=group_id,
                    role_id=rid,
                )
            )

    def add_role(self, group_id: UUID, role_id: UUID) -> None:
        exists = (
            self.session.query(group_roles)
            .filter(
                group_roles.c.group_id == group_id,
                group_roles.c.role_id == role_id,
            )
            .first()
            is not None
        )

        if exists:
            return

        self.session.execute(
            group_roles.insert().values(
                group_id=group_id,
                role_id=role_id,
            )
        )

    def remove_role(self, group_id: UUID, role_id: UUID) -> None:
        (
            self.session.query(group_roles)
            .filter(
                group_roles.c.group_id == group_id,
                group_roles.c.role_id == role_id,
            )
            .delete(synchronize_session=False)
        )

    def delete_by_role_id(self, role_id: UUID) -> None:
        (
            self.session.query(group_roles)
            .filter(group_roles.c.role_id == role_id)
            .delete(synchronize_session=False)
        )

    def delete_by_group_id(self, group_id: UUID) -> None:
        (
            self.session.query(group_roles)
            .filter(group_roles.c.group_id == group_id)
            .delete(synchronize_session=False)
        )