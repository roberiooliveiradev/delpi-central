"""User-parity person-profile facade — S2S token stays server-side."""

from __future__ import annotations

from fastapi import APIRouter, Query, Request, Response

from tm_app.application.security.authorization_policy import (
    AuthorizationDenied,
    TransformometroAuthorizationPolicy,
)
from tm_app.core.responses import fail, ok
from tm_app.infrastructure.gateways.core_person_profile_s2s_gateway import (
    CorePersonProfileS2SGateway,
)

router = APIRouter(prefix="/transformometro", tags=["Transformômetro Person Profiles"])
_authz = TransformometroAuthorizationPolicy()
_gateway = CorePersonProfileS2SGateway()

_LOOKUP_MAX_IDS = 50


def _require_access(request: Request):
    user = getattr(request.state, "user", None)
    try:
        _authz.require_access(user)
    except AuthorizationDenied as exc:
        return fail(str(exc), exc.status_code)
    return None


def _parse_ids(raw: str | None) -> list[str]:
    if not raw or not str(raw).strip():
        return []
    seen: set[str] = set()
    out: list[str] = []
    for part in str(raw).split(","):
        uid = part.strip()
        if not uid or uid in seen:
            continue
        seen.add(uid)
        out.append(uid)
        if len(out) >= _LOOKUP_MAX_IDS:
            break
    return out


@router.get(
    "/person-profiles/photo-flags",
    operation_id="list_transformometro_person_profile_photo_flags",
)
def list_person_profile_photo_flags(request: Request, ids: str = Query(default="")):
    if denied := _require_access(request):
        return denied
    user_ids = _parse_ids(ids)
    flags = _gateway.lookup_has_photo(user_ids)
    items = [
        {"user_id": uid, "has_photo": bool(flags.get(uid))}
        for uid in user_ids
    ]
    return ok({"items": items})


@router.get(
    "/person-profiles/{user_id}/photo",
    operation_id="get_transformometro_person_profile_photo",
)
def get_person_profile_photo(request: Request, user_id: str):
    if denied := _require_access(request):
        return denied
    uid = (user_id or "").strip()
    if not uid:
        return fail("user_id inválido.", 400)
    photo = _gateway.get_photo_bytes(uid)
    if photo is None:
        return fail("Foto não encontrada.", 404)
    content, content_type, file_name = photo
    return Response(
        content=content,
        media_type=content_type or "application/octet-stream",
        headers={"Content-Disposition": f'inline; filename="{file_name}"'},
    )
