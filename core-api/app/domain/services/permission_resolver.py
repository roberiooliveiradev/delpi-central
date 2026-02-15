# app/domain/services/permission_resolver.py

from app.infrastructure.db.models import (
    Role,
    Permission,
    user_roles,
    role_permissions,
    user_groups,
    group_roles,
    UserPermission
)
from app.extensions.db import db


def resolve_user_permissions(user):

    permissions = set()

    # Superadmin bypass
    if user.is_superadmin:
        all_permissions = Permission.query.all()
        return [p.code for p in all_permissions]

    # Roles diretas
    for role in user.roles:
        for perm in role.permissions:
            permissions.add(perm.code)

    # Roles via grupo
    for group in user.groups:
        for role in group.roles:
            for perm in role.permissions:
                permissions.add(perm.code)

    # Overrides
    overrides = UserPermission.query.filter_by(user_id=user.id).all()

    for override in overrides:
        perm = Permission.query.get(override.permission_id)
        if override.granted:
            permissions.add(perm.code)
        else:
            permissions.discard(perm.code)

    return list(permissions)
