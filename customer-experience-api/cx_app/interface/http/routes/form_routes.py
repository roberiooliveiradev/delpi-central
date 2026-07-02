from __future__ import annotations

from fastapi import APIRouter, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from cx_app.application.services.form_response_service import (
    FormResponseValidationError,
)
from cx_app.application.services.form_service import (
    FormNotFoundError,
    FormValidationError,
)
from cx_app.composition.cx_composer import (
    build_form_response_service,
    build_form_service,
)
from cx_app.core.auth_actor import actor_name_from_request, actor_sub_from_request
from cx_app.core.responses import fail, ok
from cx_app.core.security import (
    CX_FORMS_MANAGE,
    CX_FORMS_READ,
    CX_FORMS_WRITE,
    assert_permission,
)
from cx_app.domain.form import AnswerInput, FormInput, FormUpdate, QuestionInput, ResponseInput
from cx_app.interface.http.auth_http import resolve_user

router = APIRouter(prefix="/forms", tags=["Forms"])
public_router = APIRouter(prefix="/public/forms", tags=["Public"])


# ----- payloads --------------------------------------------------------------


class FormPayload(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class FormUpdatePayload(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class QuestionPayload(BaseModel):
    id: str | None = None
    type: str
    label: str = Field(min_length=1, max_length=200)
    helpText: str | None = Field(default=None, max_length=2000)
    required: bool = False
    options: list[str] = Field(default_factory=list)


class QuestionsPayload(BaseModel):
    questions: list[QuestionPayload] = Field(default_factory=list)


class AnswerPayload(BaseModel):
    questionId: str
    text: str | None = Field(default=None, max_length=2000)
    rating: int | None = None
    choices: list[str] = Field(default_factory=list)


class ResponsePayload(BaseModel):
    respondentName: str = Field(min_length=1, max_length=200)
    respondentCompany: str | None = Field(default=None, max_length=200)
    answers: list[AnswerPayload] = Field(default_factory=list)


# ----- admin -----------------------------------------------------------------


def _guard(request: Request, permission: str):
    user = resolve_user(request)
    try:
        assert_permission(user, permission)
    except PermissionError as exc:
        return fail(str(exc), 403)
    return None


@router.post("")
def create_form(request: Request, payload: FormPayload):
    denied = _guard(request, CX_FORMS_WRITE)
    if denied:
        return denied
    try:
        data = build_form_service().create(
            FormInput(title=payload.title, description=payload.description),
            created_by=actor_sub_from_request(request),
            created_by_name=actor_name_from_request(request),
        )
    except FormValidationError as exc:
        return fail(str(exc), 422)
    return ok(data, message="Formulário criado.", status_code=201)


@router.get("")
def list_forms(request: Request):
    denied = _guard(request, CX_FORMS_READ)
    if denied:
        return denied
    return ok({"items": build_form_service().list_admin()}, message="Formulários listados.")


@router.get("/{form_id}")
def get_form(request: Request, form_id: str):
    denied = _guard(request, CX_FORMS_READ)
    if denied:
        return denied
    try:
        data = build_form_service().get_admin(form_id)
    except FormNotFoundError:
        return fail("Formulário não encontrado.", 404)
    return ok(data, message="Formulário encontrado.")


@router.patch("/{form_id}")
def update_form(request: Request, form_id: str, payload: FormUpdatePayload):
    denied = _guard(request, CX_FORMS_WRITE)
    if denied:
        return denied
    try:
        data = build_form_service().update(
            form_id, FormUpdate(title=payload.title, description=payload.description)
        )
    except FormNotFoundError:
        return fail("Formulário não encontrado.", 404)
    except FormValidationError as exc:
        return fail(str(exc), 422)
    return ok(data, message="Formulário atualizado.")


@router.put("/{form_id}/questions")
def set_questions(request: Request, form_id: str, payload: QuestionsPayload):
    denied = _guard(request, CX_FORMS_WRITE)
    if denied:
        return denied
    try:
        data = build_form_service().set_questions(
            form_id,
            [
                QuestionInput(
                    id=q.id,
                    label=q.label,
                    question_type=q.type,
                    help_text=q.helpText,
                    is_required=q.required,
                    options=q.options,
                )
                for q in payload.questions
            ],
        )
    except FormNotFoundError:
        return fail("Formulário não encontrado.", 404)
    except FormValidationError as exc:
        return fail(str(exc), 422)
    return ok(data, message="Perguntas atualizadas.")


@router.post("/{form_id}/activate")
def activate_form(request: Request, form_id: str):
    denied = _guard(request, CX_FORMS_MANAGE)
    if denied:
        return denied
    try:
        data = build_form_service().activate(form_id)
    except FormNotFoundError:
        return fail("Formulário não encontrado.", 404)
    return ok(data, message="Formulário publicado.")


@router.post("/{form_id}/deactivate")
def deactivate_form(request: Request, form_id: str):
    denied = _guard(request, CX_FORMS_MANAGE)
    if denied:
        return denied
    try:
        data = build_form_service().deactivate(form_id)
    except FormNotFoundError:
        return fail("Formulário não encontrado.", 404)
    return ok(data, message="Formulário despublicado.")


@router.delete("/{form_id}")
def delete_form(request: Request, form_id: str):
    denied = _guard(request, CX_FORMS_MANAGE)
    if denied:
        return denied
    try:
        build_form_service().delete(form_id)
    except FormNotFoundError:
        return fail("Formulário não encontrado.", 404)
    return ok(None, message="Formulário excluído.")


@router.get("/{form_id}/qr")
def download_form_qr(request: Request, form_id: str):
    denied = _guard(request, CX_FORMS_READ)
    if denied:
        return denied
    result = build_form_service().read_qr_by_id(form_id)
    if result is None:
        return fail("QR code não encontrado.", 404)
    content, mime = result
    return Response(
        content=content,
        media_type=mime,
        headers={"Content-Disposition": f'attachment; filename="qr-form-{form_id}.png"'},
    )


@router.get("/{form_id}/responses")
def list_form_responses(
    request: Request,
    form_id: str,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    denied = _guard(request, CX_FORMS_READ)
    if denied:
        return denied
    try:
        data = build_form_response_service().list_responses(
            form_id, limit=limit, offset=offset
        )
    except FormNotFoundError:
        return fail("Formulário não encontrado.", 404)
    return ok(data, message="Respostas listadas.")


@router.get("/{form_id}/dashboard")
def form_dashboard(request: Request, form_id: str):
    denied = _guard(request, CX_FORMS_READ)
    if denied:
        return denied
    try:
        data = build_form_response_service().dashboard(form_id)
    except FormNotFoundError:
        return fail("Formulário não encontrado.", 404)
    return ok(data, message="Dashboard do formulário.")


# ----- público (sem login) ---------------------------------------------------


@public_router.get("/{token}")
def get_public_form(token: str):
    try:
        data = build_form_service().get_public(token)
    except FormNotFoundError:
        return fail("Formulário não encontrado ou indisponível.", 404)
    return ok(data, message="OK")


@public_router.post("/{token}/responses")
def submit_form_response(token: str, payload: ResponsePayload):
    try:
        data = build_form_response_service().submit(
            token,
            ResponseInput(
                respondent_name=payload.respondentName,
                respondent_company=payload.respondentCompany,
                answers=[
                    AnswerInput(
                        question_id=a.questionId,
                        text=a.text,
                        rating=a.rating,
                        choices=a.choices,
                    )
                    for a in payload.answers
                ],
            ),
        )
    except FormNotFoundError:
        return fail("Formulário não encontrado ou indisponível.", 404)
    except FormResponseValidationError as exc:
        return fail(str(exc), 422)
    return ok(data, message="Resposta registrada. Obrigado!", status_code=201)
