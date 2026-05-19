# app/infrastructure/persistence/sqlalchemy/admin_statistics_repository.py

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func, exists, select
from sqlalchemy.orm import Session

from app.infrastructure.db.models import (
    App,
    AppRoute,
    Group,
    Permission,
    Role,
    User,
    group_roles,
    role_permissions,
    user_groups,
    user_roles,
)


class SqlAlchemyAdminStatisticsRepository:

    def __init__(self, session: Session):
        self.session = session

    def get_snapshot(self) -> dict:
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        users_total = self._count(User)
        users_active = self._count(User, User.active.is_(True))

        apps_total = self._count(App)
        apps_active = self._count(App, App.active.is_(True))
        routes_total = self._count(AppRoute)
        routes_active = self._count(AppRoute, AppRoute.active.is_(True))

        roles_total = self._count(Role)
        roles_system = self._count(Role, Role.system_role.is_(True))
        groups_total = self._count(Group)
        groups_active = self._count(Group, Group.active.is_(True))

        return {
            "users": {
                "total": users_total,
                "active": users_active,
                "inactive": users_total - users_active,
                "superadmins": self._count(User, User.is_superadmin.is_(True)),
                "withBirthDate": self._count(User, User.birth_date.isnot(None)),
                "loggedInLast7Days": self._count(
                    User,
                    User.last_login_at.isnot(None),
                    User.last_login_at >= week_ago,
                ),
                "loggedInLast30Days": self._count(
                    User,
                    User.last_login_at.isnot(None),
                    User.last_login_at >= month_ago,
                ),
                "withoutDirectRoles": self._count_users_without_roles(),
                "withoutGroups": self._count_users_without_groups(),
            },
            "apps": {
                "total": apps_total,
                "active": apps_active,
                "inactive": apps_total - apps_active,
                "routesTotal": routes_total,
                "routesActive": routes_active,
                "routesInactive": routes_total - routes_active,
                "byType": self._apps_by_type(),
            },
            "roles": {
                "total": roles_total,
                "system": roles_system,
                "custom": roles_total - roles_system,
                "withoutUsers": self._roles_without_users(),
                "topByUsers": self._top_roles_by_users(),
            },
            "groups": {
                "total": groups_total,
                "active": groups_active,
                "inactive": groups_total - groups_active,
                "withoutUsers": self._groups_without_users(),
                "topByUsers": self._top_groups_by_users(),
                "topByRoles": self._top_groups_by_roles(),
            },
            "permissions": {
                "total": self._count(Permission),
            },
            "assignments": {
                "userRoles": self._junction_count(user_roles),
                "userGroups": self._junction_count(user_groups),
                "groupRoles": self._junction_count(group_roles),
                "rolePermissions": self._junction_count(role_permissions),
            },
        }

    def _count(self, model, *filters) -> int:
        query = self.session.query(func.count()).select_from(model)
        for condition in filters:
            query = query.filter(condition)
        return int(query.scalar() or 0)

    def _junction_count(self, table) -> int:
        return int(self.session.execute(select(func.count()).select_from(table)).scalar() or 0)

    def _count_users_without_roles(self) -> int:
        return int(
            self.session.query(func.count(User.id))
            .filter(
                ~exists().where(user_roles.c.user_id == User.id),
            )
            .scalar()
            or 0
        )

    def _count_users_without_groups(self) -> int:
        return int(
            self.session.query(func.count(User.id))
            .filter(
                ~exists().where(user_groups.c.user_id == User.id),
            )
            .scalar()
            or 0
        )

    def _roles_without_users(self) -> int:
        return int(
            self.session.query(func.count(Role.id))
            .filter(
                ~exists().where(user_roles.c.role_id == Role.id),
            )
            .scalar()
            or 0
        )

    def _groups_without_users(self) -> int:
        return int(
            self.session.query(func.count(Group.id))
            .filter(
                ~exists().where(user_groups.c.group_id == Group.id),
            )
            .scalar()
            or 0
        )

    def _apps_by_type(self) -> list[dict]:
        rows = (
            self.session.query(App.type, func.count(App.id))
            .group_by(App.type)
            .order_by(func.count(App.id).desc())
            .all()
        )
        return [{"type": row[0] or "unknown", "count": int(row[1])} for row in rows]

    def _top_roles_by_users(self, limit: int = 5) -> list[dict]:
        rows = (
            self.session.query(
                Role.id,
                Role.name,
                func.count(user_roles.c.user_id).label("user_count"),
            )
            .join(user_roles, Role.id == user_roles.c.role_id)
            .group_by(Role.id, Role.name)
            .order_by(func.count(user_roles.c.user_id).desc())
            .limit(limit)
            .all()
        )
        return [
            {"id": str(row.id), "name": row.name, "count": int(row.user_count)}
            for row in rows
        ]

    def _top_groups_by_users(self, limit: int = 5) -> list[dict]:
        rows = (
            self.session.query(
                Group.id,
                Group.name,
                func.count(user_groups.c.user_id).label("user_count"),
            )
            .join(user_groups, Group.id == user_groups.c.group_id)
            .group_by(Group.id, Group.name)
            .order_by(func.count(user_groups.c.user_id).desc())
            .limit(limit)
            .all()
        )
        return [
            {"id": str(row.id), "name": row.name, "count": int(row.user_count)}
            for row in rows
        ]

    def _top_groups_by_roles(self, limit: int = 5) -> list[dict]:
        rows = (
            self.session.query(
                Group.id,
                Group.name,
                func.count(group_roles.c.role_id).label("role_count"),
            )
            .join(group_roles, Group.id == group_roles.c.group_id)
            .group_by(Group.id, Group.name)
            .order_by(func.count(group_roles.c.role_id).desc())
            .limit(limit)
            .all()
        )
        return [
            {"id": str(row.id), "name": row.name, "count": int(row.role_count)}
            for row in rows
        ]
