# app/domain/services/permission_resolver.py

from uuid import UUID
from typing import Union, List

from app.infrastructure.db.models import (
    Permission,
    UserPermission,
    User,
)
from app.extensions.permission_cache import (
    get_cached_permissions,
    set_cached_permissions,
)
from app.extensions.db import db


def resolve_user_permissions(
    user_or_id: Union[str, UUID, User],
    use_cache: bool = True,
) -> List[str]:
    """
    Resolve permissões efetivas do usuário:

    - superadmin
    - roles diretas
    - roles via grupos
    - overrides

    Versão segura (sem joins duplicados).
    """

    # ---------------------------------------------------------
    # Resolve user
    # ---------------------------------------------------------

    if isinstance(user_or_id, (str, UUID)):
        user = db.session.get(User, user_or_id)
    else:
        user = user_or_id

    if not user:
        return []

    user_id = str(user.id)

    # ---------------------------------------------------------
    # Cache
    # ---------------------------------------------------------

    if use_cache:
        cached = get_cached_permissions(user_id)
        if cached is not None:
            return cached

    permissions = set()

    # ---------------------------------------------------------
    # Superadmin
    # ---------------------------------------------------------

    if getattr(user, "is_superadmin", False):
        result = [
            code for (code,) in db.session.query(Permission.code).all()
        ]
        if use_cache:
            set_cached_permissions(user_id, result)
        return result

    # ---------------------------------------------------------
    # Roles diretas (via relacionamento já carregado)
    # ---------------------------------------------------------

    for role in user.roles:
        for perm in role.permissions:
            permissions.add(perm.code)

    # ---------------------------------------------------------
    # Roles via grupos
    # ---------------------------------------------------------

    for group in user.groups:
        for role in group.roles:
            for perm in role.permissions:
                permissions.add(perm.code)

    # ---------------------------------------------------------
    # Overrides
    # ---------------------------------------------------------

    overrides = (
        db.session.query(UserPermission)
        .filter(UserPermission.user_id == user.id)
        .all()
    )

    for override in overrides:
        perm = db.session.get(Permission, override.permission_id)
        if not perm:
            continue

        if override.granted:
            permissions.add(perm.code)
        else:
            permissions.discard(perm.code)

    result = list(permissions)

    if use_cache:
        set_cached_permissions(user_id, result)

    return result