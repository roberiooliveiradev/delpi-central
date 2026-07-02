from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, File, Form, Query, Request, UploadFile
from fastapi.responses import Response

from cx_app.application.services.participant_service import ParticipantNotFoundError
from cx_app.application.services.photo_storage import PhotoValidationError
from cx_app.composition.cx_composer import build_participant_service
from cx_app.core.auth_actor import actor_name_from_request, actor_sub_from_request
from cx_app.core.responses import fail, ok
from cx_app.core.security import (
    CX_PARTICIPANTS_MANAGE,
    CX_PARTICIPANTS_READ,
    CX_PARTICIPANTS_WRITE,
    assert_permission,
)
from cx_app.domain.participant import ParticipantInput, ParticipantUpdate
from cx_app.interface.http.auth_http import resolve_user

router = APIRouter(prefix="/participants", tags=["Participants"])


def _parse_visit_date(value: str) -> date:
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError) as exc:
        raise ValueError("Data da visita inválida. Use o formato AAAA-MM-DD.") from exc


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


@router.post("")
async def create_participant(
    request: Request,
    full_name: str = Form(...),
    company_name: str = Form(...),
    visit_date: str = Form(...),
    participant_info: str | None = Form(None),
    thank_you_message: str | None = Form(None),
    photo: UploadFile = File(...),
):
    user = resolve_user(request)
    try:
        assert_permission(user, CX_PARTICIPANTS_WRITE)
    except PermissionError as exc:
        return fail(str(exc), 403)

    if not _clean(full_name) or not _clean(company_name):
        return fail("Nome e empresa do participante são obrigatórios.", 422)

    try:
        parsed_date = _parse_visit_date(visit_date)
    except ValueError as exc:
        return fail(str(exc), 422)

    photo_bytes = await photo.read()

    try:
        data = build_participant_service().create(
            ParticipantInput(
                full_name=full_name.strip(),
                company_name=company_name.strip(),
                visit_date=parsed_date,
                participant_info=_clean(participant_info),
                thank_you_message=_clean(thank_you_message),
            ),
            photo_bytes=photo_bytes,
            photo_mime=photo.content_type,
            created_by=actor_sub_from_request(request),
            created_by_name=actor_name_from_request(request),
        )
    except PhotoValidationError as exc:
        return fail(str(exc), 422)

    return ok(data, message="Participante cadastrado e QR code gerado.", status_code=201)


@router.get("")
def list_participants(
    request: Request,
    company: str | None = Query(None),
    visit_date: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    user = resolve_user(request)
    try:
        assert_permission(user, CX_PARTICIPANTS_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)

    parsed_date: date | None = None
    if visit_date:
        try:
            parsed_date = _parse_visit_date(visit_date)
        except ValueError as exc:
            return fail(str(exc), 422)

    items, total = build_participant_service().list_admin(
        limit=limit, offset=offset, company=_clean(company), visit_date=parsed_date
    )
    return ok(
        {"items": items, "total": total, "limit": limit, "offset": offset},
        message="Participantes listados.",
    )


@router.get("/{participant_id}")
def get_participant(request: Request, participant_id: str):
    user = resolve_user(request)
    try:
        assert_permission(user, CX_PARTICIPANTS_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)

    try:
        data = build_participant_service().get_admin(participant_id)
    except ParticipantNotFoundError:
        return fail("Participante não encontrado.", 404)
    return ok(data, message="Participante encontrado.")


@router.patch("/{participant_id}")
async def update_participant(
    request: Request,
    participant_id: str,
    full_name: str | None = Form(None),
    company_name: str | None = Form(None),
    visit_date: str | None = Form(None),
    participant_info: str | None = Form(None),
    thank_you_message: str | None = Form(None),
    photo: UploadFile | None = File(None),
):
    user = resolve_user(request)
    try:
        assert_permission(user, CX_PARTICIPANTS_WRITE)
    except PermissionError as exc:
        return fail(str(exc), 403)

    parsed_date: date | None = None
    if visit_date:
        try:
            parsed_date = _parse_visit_date(visit_date)
        except ValueError as exc:
            return fail(str(exc), 422)

    photo_bytes = await photo.read() if photo is not None else None

    try:
        data = build_participant_service().update(
            participant_id,
            ParticipantUpdate(
                full_name=_clean(full_name),
                company_name=_clean(company_name),
                visit_date=parsed_date,
                participant_info=_clean(participant_info),
                thank_you_message=_clean(thank_you_message),
            ),
            photo_bytes=photo_bytes,
            photo_mime=photo.content_type if photo is not None else None,
        )
    except ParticipantNotFoundError:
        return fail("Participante não encontrado.", 404)
    except PhotoValidationError as exc:
        return fail(str(exc), 422)

    return ok(data, message="Participante atualizado.")


@router.post("/{participant_id}/deactivate")
def deactivate_participant(request: Request, participant_id: str):
    user = resolve_user(request)
    try:
        assert_permission(user, CX_PARTICIPANTS_MANAGE)
    except PermissionError as exc:
        return fail(str(exc), 403)

    try:
        data = build_participant_service().deactivate(participant_id)
    except ParticipantNotFoundError:
        return fail("Participante não encontrado.", 404)
    return ok(data, message="Link público desativado.")


@router.post("/{participant_id}/activate")
def activate_participant(request: Request, participant_id: str):
    user = resolve_user(request)
    try:
        assert_permission(user, CX_PARTICIPANTS_MANAGE)
    except PermissionError as exc:
        return fail(str(exc), 403)

    try:
        data = build_participant_service().activate(participant_id)
    except ParticipantNotFoundError:
        return fail("Participante não encontrado.", 404)
    return ok(data, message="Link público reativado.")


@router.delete("/{participant_id}")
def delete_participant(request: Request, participant_id: str):
    user = resolve_user(request)
    try:
        assert_permission(user, CX_PARTICIPANTS_MANAGE)
    except PermissionError as exc:
        return fail(str(exc), 403)

    try:
        build_participant_service().delete(participant_id)
    except ParticipantNotFoundError:
        return fail("Participante não encontrado.", 404)
    return ok(None, message="Participante excluído.")


@router.get("/{participant_id}/qr")
def download_qr(request: Request, participant_id: str):
    user = resolve_user(request)
    try:
        assert_permission(user, CX_PARTICIPANTS_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)

    result = build_participant_service().read_qr_by_id(participant_id)
    if result is None:
        return fail("QR code não encontrado.", 404)
    content, mime = result
    return Response(
        content=content,
        media_type=mime,
        headers={"Content-Disposition": f'attachment; filename="qr-{participant_id}.png"'},
    )


