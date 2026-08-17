from __future__ import annotations

from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from tm_app.application.services.user_signature_service import UserSignatureService
from tm_app.core.responses import fail, ok

router = APIRouter(prefix="/transformometro/signatures", tags=["Transformômetro Assinaturas"])
service = UserSignatureService()

class UpdateSignatureProfileRequest(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=200)
def _handle(exc: Exception):
    if isinstance(exc, PermissionError): return fail(str(exc),403)
    if isinstance(exc, LookupError): return fail(str(exc),404)
    if isinstance(exc, ValueError): return fail(str(exc),400)
    raise exc
@router.get("/me", operation_id="get_my_signature_profile")
def get_me(request: Request):
    try: return ok(service.get_me(request.state.user))
    except Exception as exc: return _handle(exc)
@router.put("/me", operation_id="update_my_signature_profile")
def update_me(request: Request, body: UpdateSignatureProfileRequest):
    try: return ok(service.update_display_name(request.state.user,body.display_name))
    except Exception as exc: return _handle(exc)
@router.post("/me/image", operation_id="upload_my_signature_image")
async def save_image(request: Request,file:UploadFile|None=File(None),signature:UploadFile|None=File(None)):
    try:
        upload=file or signature
        if not upload: return fail("Envie o arquivo PNG no campo 'file' ou 'signature'.",400)
        return ok(service.save_image(request.state.user,await upload.read()))
    except Exception as exc: return _handle(exc)
@router.get("/me/image", operation_id="get_my_signature_image")
def image(request: Request):
    try: return Response(service.read_image(request.state.user),media_type="image/png")
    except Exception as exc: return _handle(exc)
