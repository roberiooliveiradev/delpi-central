from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from fastapi import Request

import tv_app.core.security as core_security
from tv_app.application.services.playlist_access_service import (
    PlaylistAccess,
    PlaylistAccessService,
)
from tv_app.application.services.tv_dashboard_content_service import message
from tv_app.core.responses import fail
from tv_app.core.security import GovernedWriteAuthzError, TV_READ, TV_WRITE, assert_permission
from tv_app.interface.http.auth_http import resolve_user

NeedLevel = Literal["read", "edit", "manage"]

_access = PlaylistAccessService()


def require_playlist_access(
    request: Request,
    playlist_id: UUID,
    *,
    need: NeedLevel,
) -> tuple[Any, PlaylistAccess] | Any:
    """Retorna `(user, access)` ou Response de erro. Sem acesso → 404."""
    user = resolve_user(request)
    if need == "read":
        try:
            assert_permission(user, TV_READ)
        except PermissionError as exc:
            return fail(str(exc), 403)
    else:
        # Material writes: human principal + fresh effective Core RBAC before
        # resource authorization (fail-closed — never stale cache).
        try:
            user = core_security.require_fresh_write_authorization(
                user,
                authorization=request.headers.get("Authorization"),
                permission=TV_WRITE,
            )
        except GovernedWriteAuthzError as exc:
            return fail(str(exc), exc.status_code)

    access = _access.resolve(playlist_id, user)
    ok = (
        access.can_read
        if need == "read"
        else access.can_edit
        if need == "edit"
        else access.can_manage
    )
    if not ok:
        return fail(message("playlistNotFound"), 404)
    return user, access


def require_governed_write(
    request: Request,
    *,
    permission: str = TV_WRITE,
) -> tuple[Any, None] | Any:
    """Unscoped human-governed material write (no playlist resource yet).

    Returns ``(user, None)`` or an error Response. Same gate as
    ``require_playlist_access`` edit/manage: end-user principal + fresh Core
    RBAC + permission. Internal S2S surfaces are explicit exceptions and do
    not use this helper.
    """
    user = resolve_user(request)
    try:
        user = core_security.require_fresh_write_authorization(
            user,
            authorization=request.headers.get("Authorization"),
            permission=permission,
        )
    except GovernedWriteAuthzError as exc:
        return fail(str(exc), exc.status_code)
    return user, None


async def arequire_governed_write(
    request: Request,
    *,
    permission: str = TV_WRITE,
) -> tuple[Any, None] | Any:
    """Async twin of ``require_governed_write`` for async route handlers."""
    user = resolve_user(request)
    try:
        user = await core_security.arequire_fresh_write_authorization(
            user,
            authorization=request.headers.get("Authorization"),
            permission=permission,
        )
    except GovernedWriteAuthzError as exc:
        return fail(str(exc), exc.status_code)
    return user, None


def is_access_error(result: object) -> bool:
    return not isinstance(result, tuple)
