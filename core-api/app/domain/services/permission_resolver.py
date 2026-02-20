# app/domain/services/permission_resolver.py

from app.infrastructure.db.models import (
    Permission,
    UserPermission,
)
from app.extensions.permission_cache import (
    get_cached_permissions,
    set_cached_permissions,
)
from app.extensions.db import db

from uuid import UUID
from app.infrastructure.db.models import User


def resolve_user_permissions(user_or_id,  use_cache: bool = True):
    """
    Resolve todas as permissões efetivas do usuário considerando:
    - superadmin
    - roles diretas
    - roles via grupo
    - overrides (grant / revoke)
    Utiliza cache em memória para evitar consultas repetidas.
    """
    if isinstance(user_or_id, (str, UUID)):
        user = User.query.get(user_or_id)
    else:
        user = user_or_id

    if not user:
        return []
    if use_cache:
        cached = get_cached_permissions(user.id)
        if cached is not None:
            return cached

    permissions = set()

    # 🔥 Superadmin bypass total
    if getattr(user, "is_superadmin", False):
        all_permissions = Permission.query.all()
        result = [p.code for p in all_permissions]
        set_cached_permissions(user.id, result)
        return result

    # Roles diretas
    for role in user.roles:
        for perm in role.permissions:
            permissions.add(perm.code)

    # Roles via grupos
    for group in user.groups:
        for role in group.roles:
            for perm in role.permissions:
                permissions.add(perm.code)

    # Overrides
    overrides = UserPermission.query.filter_by(user_id=user.id).all()
    for override in overrides:
        perm = Permission.query.get(override.permission_id)
        if not perm:
            continue

        if override.granted:
            permissions.add(perm.code)
        else:
            permissions.discard(perm.code)

    result = list(permissions)
    set_cached_permissions(user.id, result)

    return result
