"""Person-profile photo façade — S2S token stays server-side (avatar Minha DELPI)."""

from __future__ import annotations

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from helpdesk_app.infrastructure.core_person_profile_service import CorePersonProfileService
from helpdesk_app.interface.http.actor import require_actor

router = APIRouter(tags=["Helpdesk Person Profiles"])

_profiles = CorePersonProfileService()


@router.get("/person-profiles/{user_id}/photo")
def get_person_profile_photo(request: Request, user_id: str):
    require_actor(request)
    uid = (user_id or "").strip()
    if not uid:
        return JSONResponse(status_code=422, content={"error": "validation_error"})
    if not _profiles.configured():
        return JSONResponse(status_code=404, content={"error": "not_found"})
    photo = _profiles.get_photo_bytes(uid)
    if photo is None:
        return JSONResponse(status_code=404, content={"error": "not_found"})
    content, content_type, file_name = photo
    return Response(
        content=content,
        media_type=content_type or "application/octet-stream",
        headers={"Content-Disposition": f'inline; filename="{file_name}"'},
    )
