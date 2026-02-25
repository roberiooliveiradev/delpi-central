# app/infrastructure/persistence/sqlalchemy/rbac_query_repository.py

from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.ports.rbac_query_port import RbacQueryPort
from app.infrastructure.db.models import user_roles, group_roles, user_groups


class SqlAlchemyRbacQueryRepository(RbacQueryPort):
    def __init__(self, session: Session):
        self.session = session

    def list_user_ids_by_role(self, role_id: UUID) -> List[str]:
        rows = (
            self.session.query(user_roles.c.user_id)
            .filter(user_roles.c.role_id == role_id)
            .all()
        )
        # user_id é UUID no banco; devolve str
        return [str(uid) for (uid,) in rows]

    def list_user_ids_by_group_role(self, role_id: UUID) -> List[str]:
        # user_groups (user_id, group_id)
        # group_roles (group_id, role_id)
        rows = (
            self.session.query(user_groups.c.user_id)
            .join(group_roles, user_groups.c.group_id == group_roles.c.group_id)
            .filter(group_roles.c.role_id == role_id)
            .all()
        )
        return [str(uid) for (uid,) in rows]
    
    def list_user_ids_by_group(self, group_id: UUID) -> List[str]:
        from app.infrastructure.db.models import user_groups

        rows = (
            self.session.query(user_groups.c.user_id)
            .filter(user_groups.c.group_id == group_id)
            .all()
        )

        return [str(uid) for (uid,) in rows]