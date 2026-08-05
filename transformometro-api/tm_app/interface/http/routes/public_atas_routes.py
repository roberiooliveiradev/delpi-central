from __future__ import annotations

from fastapi import APIRouter, File, Form, Header, Request, UploadFile
from pydantic import BaseModel

from tm_app.application.services.meeting_minutes_service import MeetingMinutesService
from tm_app.core.responses import fail, ok

public_router = APIRouter(
    prefix="/public/atas/sign-invites",
    tags=["Transformômetro Atas Public"],
)
service = MeetingMinutesService()


class PublicRefuseRequest(BaseModel):
    reason: str


def _handle(exc: Exception):
    if isinstance(exc, PermissionError):
        return fail(str(exc), 403)
    if isinstance(exc, LookupError):
        return fail(str(exc), 404)
    if isinstance(exc, ValueError):
        return fail(str(exc), 400)
    raise exc


@public_router.get("/{token}")
def public_sign_context(token: str):
    try:
        return ok(service.public_sign_context(token))
    except Exception as exc:
        return _handle(exc)


@public_router.post("/{token}/sign")
async def public_sign(
    request: Request,
    token: str,
    signature: UploadFile = File(...),
    display_name_confirmed: str = Form(...),
    terms_accepted: bool = Form(...),
    session_id: str | None = Form(None),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    try:
        return ok(
            service.public_sign(
                token,
                png_bytes=await signature.read(),
                display_name_confirmed=display_name_confirmed,
                terms_accepted=terms_accepted,
                client_ip=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                session_id=session_id,
                idempotency_key=idempotency_key,
            ),
            status_code=201,
        )
    except Exception as exc:
        return _handle(exc)


@public_router.post("/{token}/refuse")
def public_refuse(token: str, body: PublicRefuseRequest):
    try:
        return ok(service.public_refuse(token, body.reason))
    except Exception as exc:
        return _handle(exc)
