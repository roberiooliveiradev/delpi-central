from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from fastapi import Request

from tv_app.application.services.playlist_access_service import (
    PlaylistAccess,
    PlaylistAccessService,
)
from tv_app.application.services.tv_dashboard_content_service import message
from tv_app.core.responses import fail
from tv_app.core.security import TV_READ, TV_WRITE, assert_permission
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
    try:
        assert_permission(user, TV_READ if need == "read" else TV_WRITE)
    except PermissionError as exc:
        return fail(str(exc), 403)

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


def is_access_error(result: object) -> bool:
    return not isinstance(result, tuple)
