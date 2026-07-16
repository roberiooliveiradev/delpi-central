from __future__ import annotations

from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from cipa_app.application.use_cases.user_signature_service import UserSignatureService
from cipa_app.core.responses import fail, ok

router = APIRouter(prefix="/signatures", tags=["CIPA Signature Profile"])
service = UserSignatureService()


class UpdateSignatureProfileRequest(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=200)


def _handle(exc: Exception):
    if isinstance(exc, PermissionError):
        return fail(str(exc), 403)
    if isinstance(exc, LookupError):
        return fail(str(exc), 404)
    if isinstance(exc, ValueError):
        return fail(str(exc), 400)
    raise exc


@router.get("/me")
def get_my_signature_profile(request: Request):
    try:
        return ok(service.get_me(request.state.user))
    except Exception as exc:
        return _handle(exc)


@router.put("/me")
def update_my_signature_profile(request: Request, body: UpdateSignatureProfileRequest):
    try:
        return ok(service.update_display_name(request.state.user, body.display_name))
    except Exception as exc:
        return _handle(exc)


@router.post("/me/image")
async def upload_my_signature_image(
    request: Request,
    file: UploadFile | None = File(None),
    signature: UploadFile | None = File(None),
):
    try:
        upload = file or signature
        if upload is None:
            return fail("Envie o arquivo PNG no campo 'file' ou 'signature'.", 400)
        raw = await upload.read()
        return ok(service.save_image(request.state.user, raw))
    except Exception as exc:
        return _handle(exc)


@router.get("/me/image")
def get_my_signature_image(request: Request):
    try:
        png = service.read_image(request.state.user)
        return Response(content=png, media_type="image/png")
    except Exception as exc:
        return _handle(exc)
