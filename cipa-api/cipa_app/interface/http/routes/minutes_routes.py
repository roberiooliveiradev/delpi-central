from __future__ import annotations

from typing import Any

from fastapi import APIRouter, File, Form, Header, Query, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from cipa_app.application.use_cases.meeting_minutes_service import MeetingMinutesService
from cipa_app.core.responses import fail, ok

router = APIRouter(prefix="/minutes", tags=["CIPA Minutes"])
service = MeetingMinutesService()


class CreateMinuteRequest(BaseModel):
    unit_code: str
    title: str
    meeting_type: str = "ordinary"
    meeting_date: str
    start_time: str | None = None
    end_time: str | None = None
    location: str | None = None
    responsible_user_id: str | None = None
    responsible_name: str | None = None
    president_name: str | None = None
    secretary_name: str | None = None
    agenda_html: str = ""
    body_html: str = ""
    decisions_html: str = ""
    pending_html: str = ""
    observations_html: str = ""


class UpdateMinuteRequest(BaseModel):
    title: str | None = None
    meeting_type: str | None = None
    meeting_date: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    location: str | None = None
    responsible_user_id: str | None = None
    responsible_name: str | None = None
    president_name: str | None = None
    secretary_name: str | None = None
    agenda_html: str | None = None
    body_html: str | None = None
    decisions_html: str | None = None
    pending_html: str | None = None
    observations_html: str | None = None
    participants: list[dict[str, Any]] | None = None
    action_items: list[dict[str, Any]] | None = None


class TransitionRequest(BaseModel):
    to_status: str
    reason: str | None = None


class VersionRequest(BaseModel):
    change_reason: str
    agenda_html: str | None = None
    body_html: str | None = None
    decisions_html: str | None = None
    pending_html: str | None = None
    observations_html: str | None = None


class SignersRequest(BaseModel):
    signers: list[dict[str, Any]] = Field(default_factory=list)


class RefuseRequest(BaseModel):
    reason: str


def _handle(exc: Exception):
    if isinstance(exc, PermissionError):
        return fail(str(exc), 403)
    if isinstance(exc, LookupError):
        return fail(str(exc), 404)
    if isinstance(exc, ValueError):
        return fail(str(exc), 400)
    raise exc


@router.get("")
def list_minutes(
    request: Request,
    unit_code: str | None = None,
    status: str | None = None,
    meeting_type: str | None = None,
    q: str | None = None,
    pending_for_me: bool = False,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    try:
        data = service.list_minutes(
            request.state.user,
            {
                "unit_code": unit_code,
                "status": status,
                "meeting_type": meeting_type,
                "q": q,
                "pending_for_me": pending_for_me,
                "date_from": date_from,
                "date_to": date_to,
                "limit": limit,
                "offset": offset,
            },
        )
        return ok(data)
    except Exception as exc:
        return _handle(exc)


@router.get("/pending-signatures")
def pending_signatures(request: Request):
    try:
        return ok(service.pending_signatures(request.state.user))
    except Exception as exc:
        return _handle(exc)


@router.post("")
def create_minute(request: Request, body: CreateMinuteRequest):
    try:
        return ok(service.create(request.state.user, body.model_dump()), status_code=201)
    except Exception as exc:
        return _handle(exc)


@router.get("/{minute_id}")
def get_minute(request: Request, minute_id: str):
    try:
        return ok(service.get_detail(request.state.user, minute_id))
    except Exception as exc:
        return _handle(exc)


@router.patch("/{minute_id}")
def update_minute(request: Request, minute_id: str, body: UpdateMinuteRequest):
    try:
        payload = {k: v for k, v in body.model_dump().items() if v is not None}
        return ok(service.update(request.state.user, minute_id, payload))
    except Exception as exc:
        return _handle(exc)


@router.post("/{minute_id}/transition")
def transition(request: Request, minute_id: str, body: TransitionRequest):
    try:
        return ok(service.transition(request.state.user, minute_id, body.to_status, body.reason))
    except Exception as exc:
        return _handle(exc)


@router.post("/{minute_id}/versions")
def create_version(request: Request, minute_id: str, body: VersionRequest):
    try:
        return ok(service.create_version(request.state.user, minute_id, body.model_dump()), status_code=201)
    except Exception as exc:
        return _handle(exc)


@router.get("/{minute_id}/versions")
def list_versions(request: Request, minute_id: str):
    try:
        detail = service.get_detail(request.state.user, minute_id)
        return ok({"items": detail["versions"]})
    except Exception as exc:
        return _handle(exc)


@router.put("/{minute_id}/participants")
def put_participants(request: Request, minute_id: str, body: dict[str, Any]):
    try:
        return ok(
            service.update(
                request.state.user,
                minute_id,
                {"participants": body.get("participants") or []},
            )
        )
    except Exception as exc:
        return _handle(exc)


@router.put("/{minute_id}/signers")
def put_signers(request: Request, minute_id: str, body: SignersRequest):
    try:
        return ok(service.set_signers(request.state.user, minute_id, body.signers))
    except Exception as exc:
        return _handle(exc)


@router.post("/{minute_id}/send-for-signature")
def send_for_signature(request: Request, minute_id: str):
    try:
        return ok(service.send_for_signature(request.state.user, minute_id))
    except Exception as exc:
        return _handle(exc)


@router.get("/{minute_id}/sign-context")
def sign_context(request: Request, minute_id: str):
    try:
        return ok(service.sign_context(request.state.user, minute_id))
    except Exception as exc:
        return _handle(exc)


@router.post("/{minute_id}/signatures")
async def register_signature(
    request: Request,
    minute_id: str,
    signature: UploadFile = File(...),
    display_name_confirmed: str = Form(...),
    terms_accepted: bool = Form(...),
    session_id: str | None = Form(None),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    try:
        raw = await signature.read()
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        data = service.sign(
            request.state.user,
            minute_id,
            png_bytes=raw,
            display_name_confirmed=display_name_confirmed,
            terms_accepted=terms_accepted,
            client_ip=client_ip,
            user_agent=user_agent,
            session_id=session_id,
            idempotency_key=idempotency_key,
        )
        return ok(data, status_code=201)
    except Exception as exc:
        return _handle(exc)


@router.post("/{minute_id}/signatures/refuse")
def refuse_signature(request: Request, minute_id: str, body: RefuseRequest):
    try:
        return ok(service.refuse(request.state.user, minute_id, body.reason))
    except Exception as exc:
        return _handle(exc)


@router.post("/{minute_id}/finalize")
def finalize(request: Request, minute_id: str):
    try:
        return ok(service.finalize(request.state.user, minute_id))
    except Exception as exc:
        return _handle(exc)


@router.post("/{minute_id}/cancel")
def cancel(request: Request, minute_id: str, body: RefuseRequest):
    try:
        return ok(service.transition(request.state.user, minute_id, "cancelled", body.reason))
    except Exception as exc:
        return _handle(exc)


@router.get("/{minute_id}/audit")
def audit(request: Request, minute_id: str):
    try:
        return ok(service.audit(request.state.user, minute_id))
    except Exception as exc:
        return _handle(exc)


@router.get("/{minute_id}/export.pdf")
def export_pdf(request: Request, minute_id: str):
    try:
        raw, filename = service.export_pdf(request.state.user, minute_id)
        return Response(
            content=raw,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as exc:
        return _handle(exc)


@router.post("/{minute_id}/attachments")
async def add_attachment(request: Request, minute_id: str, file: UploadFile = File(...)):
    try:
        raw = await file.read()
        data = service.add_attachment(
            request.state.user,
            minute_id,
            file_name=file.filename or "file",
            content_type=file.content_type or "application/octet-stream",
            raw=raw,
        )
        return ok(data, status_code=201)
    except Exception as exc:
        return _handle(exc)


@router.delete("/{minute_id}")
def delete_minute(request: Request, minute_id: str):
    try:
        return ok(service.soft_delete(request.state.user, minute_id))
    except Exception as exc:
        return _handle(exc)
