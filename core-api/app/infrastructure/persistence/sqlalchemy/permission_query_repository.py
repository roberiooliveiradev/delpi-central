# app/infrastructure/persistence/sqlalchemy/permission_query_repository.py

from typing import List, Tuple
from uuid import UUID
from sqlalchemy.orm import Session

from app.domain.ports.permission_query_port import PermissionQueryPort

from app.infrastructure.db.models import (
    Permission,
    Role,
    Group,
    User,
    UserPermission,
    role_permissions,
    group_roles,
    user_roles,
    user_groups,
)


class SqlAlchemyPermissionQueryRepository(PermissionQueryPort):

    def __init__(self, session: Session):
        self.session = session

    # ---------------------------------------------------------
    # All permissions (superadmin case)
    # ---------------------------------------------------------

    def list_all_permission_codes(self) -> List[str]:
        return [
            code for (code,) in self.session.query(Permission.code).all()
        ]

    # ---------------------------------------------------------
    # Direct role permissions
    # ---------------------------------------------------------

    def list_direct_role_permissions(self, user_id: UUID) -> List[str]:
        rows = (
            self.session.query(Permission.code)
            .join(role_permissions, Permission.id == role_permissions.c.permission_id)
            .join(Role, Role.id == role_permissions.c.role_id)
            .join(user_roles, Role.id == user_roles.c.role_id)
            .filter(user_roles.c.user_id == user_id)
            .all()
        )

        return [code for (code,) in rows]

    # ---------------------------------------------------------
    # Group role permissions
    # ---------------------------------------------------------

    def list_group_role_permissions(self, user_id: UUID) -> List[str]:
        rows = (
            self.session.query(Permission.code)
            .join(role_permissions, Permission.id == role_permissions.c.permission_id)
            .join(Role, Role.id == role_permissions.c.role_id)
            .join(group_roles, Role.id == group_roles.c.role_id)
            .join(Group, Group.id == group_roles.c.group_id)
            .join(user_groups, Group.id == user_groups.c.group_id)
            .filter(user_groups.c.user_id == user_id)
            .all()
        )

        return [code for (code,) in rows]

    def list_direct_role_permissions_excluding_roles(
        self, user_id: UUID, exclude_role_ids: set[UUID]
    ) -> List[str]:
        query = (
            self.session.query(Permission.code)
            .join(role_permissions, Permission.id == role_permissions.c.permission_id)
            .join(Role, Role.id == role_permissions.c.role_id)
            .join(user_roles, Role.id == user_roles.c.role_id)
            .filter(user_roles.c.user_id == user_id)
        )
        if exclude_role_ids:
            query = query.filter(Role.id.notin_(exclude_role_ids))
        return [code for (code,) in query.all()]

    def list_group_role_permissions_excluding_groups(
        self, user_id: UUID, exclude_group_ids: set[UUID]
    ) -> List[str]:
        query = (
            self.session.query(Permission.code)
            .join(role_permissions, Permission.id == role_permissions.c.permission_id)
            .join(Role, Role.id == role_permissions.c.role_id)
            .join(group_roles, Role.id == group_roles.c.role_id)
            .join(Group, Group.id == group_roles.c.group_id)
            .join(user_groups, Group.id == user_groups.c.group_id)
            .filter(user_groups.c.user_id == user_id)
        )
        if exclude_group_ids:
            query = query.filter(Group.id.notin_(exclude_group_ids))
        return [code for (code,) in query.all()]

    def list_group_role_permissions_excluding_roles(
        self, user_id: UUID, exclude_role_ids: set[UUID]
    ) -> List[str]:
        query = (
            self.session.query(Permission.code)
            .join(role_permissions, Permission.id == role_permissions.c.permission_id)
            .join(Role, Role.id == role_permissions.c.role_id)
            .join(group_roles, Role.id == group_roles.c.role_id)
            .join(Group, Group.id == group_roles.c.group_id)
            .join(user_groups, Group.id == user_groups.c.group_id)
            .filter(user_groups.c.user_id == user_id)
        )
        if exclude_role_ids:
            query = query.filter(Role.id.notin_(exclude_role_ids))
        return [code for (code,) in query.all()]

    def list_group_role_permissions_excluding_roles_for_group(
        self,
        user_id: UUID,
        group_id: UUID,
        exclude_role_ids: set[UUID],
    ) -> List[str]:
        query = (
            self.session.query(Permission.code)
            .join(role_permissions, Permission.id == role_permissions.c.permission_id)
            .join(Role, Role.id == role_permissions.c.role_id)
            .join(group_roles, Role.id == group_roles.c.role_id)
            .join(Group, Group.id == group_roles.c.group_id)
            .join(user_groups, Group.id == user_groups.c.group_id)
            .filter(
                user_groups.c.user_id == user_id,
                Group.id == group_id,
            )
        )
        if exclude_role_ids:
            query = query.filter(Role.id.notin_(exclude_role_ids))
        return [code for (code,) in query.all()]

    def list_permission_codes_granted_by_role_for_user(
        self, user_id: UUID, role_id: UUID
    ) -> List[str]:
        direct = (
            self.session.query(Permission.code)
            .join(role_permissions, Permission.id == role_permissions.c.permission_id)
            .join(user_roles, user_roles.c.role_id == role_permissions.c.role_id)
            .filter(
                user_roles.c.user_id == user_id,
                role_permissions.c.role_id == role_id,
            )
            .all()
        )
        via_group = (
            self.session.query(Permission.code)
            .join(role_permissions, Permission.id == role_permissions.c.permission_id)
            .join(group_roles, group_roles.c.role_id == role_permissions.c.role_id)
            .join(user_groups, user_groups.c.group_id == group_roles.c.group_id)
            .filter(
                user_groups.c.user_id == user_id,
                role_permissions.c.role_id == role_id,
            )
            .all()
        )
        codes = {code for (code,) in direct} | {code for (code,) in via_group}
        return sorted(codes)

    # ---------------------------------------------------------
    # User overrides
    # ---------------------------------------------------------

    def list_user_overrides(self, user_id: UUID) -> List[Tuple[str, bool]]:
        rows = (
            self.session.query(Permission.code, UserPermission.granted)
            .join(Permission, Permission.id == UserPermission.permission_id)
            .filter(UserPermission.user_id == user_id)
            .all()
        )

        return [(code, granted) for code, granted in rows]
    
    # ---------------------------------------------------------
    # Permissions by role_id (Admin Console)
    # ---------------------------------------------------------

    def list_permissions_by_role_id(self, role_id: UUID):

        rows = (
            self.session.query(Permission)
            .join(role_permissions, Permission.id == role_permissions.c.permission_id)
            .filter(role_permissions.c.role_id == role_id)
            .all()
        )

        return rows

    def list_permissions_by_codes(self, codes: List[str]) -> List:
        normalized = sorted({(code or "").strip() for code in codes if (code or "").strip()})
        if not normalized:
            return []

        rows = (
            self.session.query(Permission)
            .filter(Permission.code.in_(normalized))
            .all()
        )

        return rows