from __future__ import annotations

from typing import Any

from fastapi import APIRouter, File, Form, Header, Query, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field

from tm_app.application.services.html_sanitizer import TmAtaHtmlSanitizer
from tm_app.application.services.meeting_minutes_service import MeetingMinutesService
from tm_app.core.responses import fail, ok
from tm_app.infrastructure.llm.kimi_llm_gateway import AtaGenerationError, KimiLlmGateway

router = APIRouter(tags=["Transformômetro Meeting Minutes"])
service = MeetingMinutesService()
kimi_gateway = KimiLlmGateway()


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
    chair_name: str | None = None
    secretary_name: str | None = None
    agenda_html: str = ""
    body_html: str = ""
    decisions_html: str = ""
    pending_html: str = ""
    observations_html: str = ""
    participants: list[dict[str, Any]] = Field(default_factory=list)
    signers: list[dict[str, Any]] | None = None


class UpdateMinuteRequest(BaseModel):
    title: str | None = None
    meeting_type: str | None = None
    meeting_date: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    location: str | None = None
    responsible_user_id: str | None = None
    responsible_name: str | None = None
    chair_name: str | None = None
    secretary_name: str | None = None
    agenda_html: str | None = None
    body_html: str | None = None
    decisions_html: str | None = None
    pending_html: str | None = None
    observations_html: str | None = None
    participants: list[dict[str, Any]] | None = None
    signers: list[dict[str, Any]] | None = None


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


class CancelRequest(BaseModel):
    reason: str | None = None


class GenerateFromTranscriptRequest(BaseModel):
    """Gera seções da ata a partir de transcrição — sem persistir."""

    model_config = ConfigDict(populate_by_name=True)

    unit_code: str = Field(..., alias="unitCode", min_length=1)
    meeting_date: str = Field(..., alias="meetingDate", min_length=1)
    title: str | None = None
    transcript_html: str = Field(..., alias="transcriptHtml", min_length=1)
    source: str = Field(..., min_length=1)


def _handle(exc: Exception):
    if isinstance(exc, PermissionError):
        return fail(str(exc), 403)
    if isinstance(exc, LookupError):
        return fail(str(exc), 404)
    if isinstance(exc, ValueError):
        return fail(str(exc), 400)
    if isinstance(exc, AtaGenerationError):
        return fail(str(exc), 502)
    raise exc


@router.get("", operation_id="list_meeting_minutes")
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
        return ok(
            service.list_minutes(
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
        )
    except Exception as exc:
        return _handle(exc)


@router.get("/pending-signatures", operation_id="list_meeting_minutes_pending_signatures")
def pending_signatures(request: Request):
    try:
        return ok(service.pending_signatures(request.state.user))
    except Exception as exc:
        return _handle(exc)


@router.post("/generate-from-transcript", operation_id="generate_meeting_minute_from_transcript")
def generate_from_transcript(request: Request, body: GenerateFromTranscriptRequest):
    """Gera as 5 seções HTML via Kimi — não salva no banco."""
    try:
        service._assert(request.state.user, "manage", body.unit_code)
        sections = kimi_gateway.generate_from_transcript(body.transcript_html)
        sanitized = {
            key: TmAtaHtmlSanitizer.sanitize(value) for key, value in sections.items()
        }
        return ok(
            {
                "unitCode": body.unit_code,
                "meetingDate": body.meeting_date,
                "title": body.title,
                "source": body.source,
                **sanitized,
            }
        )
    except Exception as exc:
        return _handle(exc)


@router.post("", operation_id="create_meeting_minute")
def create(request: Request, body: CreateMinuteRequest):
    try:
        return ok(service.create(request.state.user, body.model_dump()), status_code=201)
    except Exception as exc:
        return _handle(exc)


@router.get("/{minute_id}", operation_id="get_meeting_minute")
def detail(request: Request, minute_id: str):
    try:
        return ok(service.get_detail(request.state.user, minute_id))
    except Exception as exc:
        return _handle(exc)


@router.patch("/{minute_id}", operation_id="update_meeting_minute")
def update(request: Request, minute_id: str, body: UpdateMinuteRequest):
    try:
        payload = {key: value for key, value in body.model_dump().items() if value is not None}
        return ok(service.update(request.state.user, minute_id, payload))
    except Exception as exc:
        return _handle(exc)


@router.post("/{minute_id}/versions", operation_id="create_meeting_minute_version")
def version(request: Request, minute_id: str, body: VersionRequest):
    try:
        return ok(service.create_version(request.state.user, minute_id, body.model_dump()), status_code=201)
    except Exception as exc:
        return _handle(exc)


@router.put("/{minute_id}/participants", operation_id="replace_meeting_minute_participants")
def participants(request: Request, minute_id: str, body: dict[str, Any]):
    try:
        return ok(service.set_participants(request.state.user, minute_id, body.get("participants") or []))
    except Exception as exc:
        return _handle(exc)


@router.put("/{minute_id}/signers", operation_id="replace_meeting_minute_signers")
def signers(request: Request, minute_id: str, body: SignersRequest):
    try:
        return ok(service.set_signers(request.state.user, minute_id, body.signers))
    except Exception as exc:
        return _handle(exc)


@router.post("/{minute_id}/send-for-signature", operation_id="send_meeting_minute_for_signature")
def send(request: Request, minute_id: str):
    try:
        return ok(service.send_for_signature(request.state.user, minute_id))
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/{minute_id}/resend-sign-invites",
    operation_id="resend_meeting_minute_sign_invites",
)
def resend_sign_invites(request: Request, minute_id: str):
    try:
        return ok(service.resend_sign_invites(request.state.user, minute_id))
    except Exception as exc:
        return _handle(exc)


@router.get("/{minute_id}/sign-context", operation_id="get_meeting_minute_sign_context")
def sign_context(request: Request, minute_id: str):
    try:
        return ok(service.sign_context(request.state.user, minute_id))
    except Exception as exc:
        return _handle(exc)


@router.post("/{minute_id}/signatures", operation_id="sign_meeting_minute")
async def sign(
    request: Request,
    minute_id: str,
    signature: UploadFile = File(...),
    display_name_confirmed: str = Form(...),
    terms_accepted: bool = Form(...),
    session_id: str | None = Form(None),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    try:
        return ok(
            service.sign(
                request.state.user,
                minute_id,
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


@router.get("/{minute_id}/signatures/{signature_id}/image", operation_id="get_meeting_minute_signature_image")
def image(request: Request, minute_id: str, signature_id: str):
    try:
        return Response(service.signature_image(request.state.user, minute_id, signature_id), media_type="image/png")
    except Exception as exc:
        return _handle(exc)


@router.post("/{minute_id}/signatures/refuse", operation_id="refuse_meeting_minute_signature")
def refuse(request: Request, minute_id: str, body: RefuseRequest):
    try:
        return ok(service.refuse(request.state.user, minute_id, body.reason))
    except Exception as exc:
        return _handle(exc)


@router.post("/{minute_id}/finalize", operation_id="finalize_meeting_minute")
def finalize(request: Request, minute_id: str):
    try:
        return ok(service.finalize(request.state.user, minute_id))
    except Exception as exc:
        return _handle(exc)


@router.post("/{minute_id}/cancel", operation_id="cancel_meeting_minute")
def cancel(request: Request, minute_id: str, body: CancelRequest | None = None):
    try:
        return ok(service.cancel(request.state.user, minute_id, (body.reason if body else None)))
    except Exception as exc:
        return _handle(exc)


@router.get("/{minute_id}/export.pdf", operation_id="export_meeting_minute_pdf")
def export(request: Request, minute_id: str):
    try:
        raw, name = service.export_pdf(request.state.user, minute_id)
        return Response(
            raw,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{name}"'},
        )
    except Exception as exc:
        return _handle(exc)


@router.get("/{minute_id}/audit", operation_id="get_meeting_minute_audit")
def audit(request: Request, minute_id: str):
    try:
        return ok(service.audit(request.state.user, minute_id))
    except Exception as exc:
        return _handle(exc)


@router.delete("/{minute_id}", operation_id="delete_meeting_minute")
def delete(request: Request, minute_id: str):
    try:
        return ok(service.soft_delete(request.state.user, minute_id))
    except Exception as exc:
        return _handle(exc)
