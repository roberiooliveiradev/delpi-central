from __future__ import annotations

from fastapi import APIRouter, File, Query, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from cx_app.application.services.form_response_service import (
    FormResponseValidationError,
)
from cx_app.application.services.form_service import (
    FormNotFoundError,
    FormValidationError,
)
from cx_app.application.services.photo_storage import PhotoValidationError
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
from cx_app.domain.form import (
    AnswerInput,
    FormInput,
    FormUpdate,
    PageInput,
    QuestionInput,
    ResponseInput,
)
from cx_app.interface.http.auth_http import resolve_user

router = APIRouter(prefix="/forms", tags=["Forms"])
public_router = APIRouter(prefix="/public/forms", tags=["Public"])


# ----- payloads --------------------------------------------------------------


class FormPayload(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    oneQuestionPerPage: bool = False


class FormUpdatePayload(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    oneQuestionPerPage: bool | None = None


class PagePayload(BaseModel):
    id: str | None = None
    title: str | None = Field(default=None, max_length=200)
    backgroundImageFilename: str | None = None
    pointImageFilename: str | None = None


class QuestionPayload(BaseModel):
    id: str | None = None
    type: str
    label: str = Field(min_length=1, max_length=200)
    helpText: str | None = Field(default=None, max_length=2000)
    required: bool = False
    options: list[str] = Field(default_factory=list)
    pageId: str | None = None
    pageIndex: int | None = Field(default=None, ge=0)
    pointImageFilename: str | None = None


class QuestionsPayload(BaseModel):
    oneQuestionPerPage: bool | None = None
    pages: list[PagePayload] = Field(default_factory=list)
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
            FormInput(
                title=payload.title,
                description=payload.description,
                one_question_per_page=payload.oneQuestionPerPage,
            ),
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
            form_id,
            FormUpdate(
                title=payload.title,
                description=payload.description,
                one_question_per_page=payload.oneQuestionPerPage,
            ),
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
        data = build_form_service().set_structure(
            form_id,
            one_question_per_page=payload.oneQuestionPerPage,
            pages=[
                PageInput(
                    id=p.id,
                    title=p.title,
                    background_image_filename=p.backgroundImageFilename,
                    point_image_filename=p.pointImageFilename,
                )
                for p in payload.pages
            ],
            questions=[
                QuestionInput(
                    id=q.id,
                    label=q.label,
                    question_type=q.type,
                    help_text=q.helpText,
                    is_required=q.required,
                    options=q.options,
                    page_id=q.pageId,
                    page_index=q.pageIndex,
                    point_image_filename=q.pointImageFilename,
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


@router.post("/{form_id}/background-image")
async def upload_form_background(request: Request, form_id: str, image: UploadFile = File(...)):
    denied = _guard(request, CX_FORMS_WRITE)
    if denied:
        return denied
    content = await image.read()
    try:
        data = build_form_service().upload_background(
            form_id, content=content, mime_type=image.content_type
        )
    except FormNotFoundError:
        return fail("Formulário não encontrado.", 404)
    except PhotoValidationError as exc:
        return fail(str(exc), 422)
    return ok(data, message="Imagem de fundo atualizada.")


@router.delete("/{form_id}/background-image")
def remove_form_background(request: Request, form_id: str):
    denied = _guard(request, CX_FORMS_WRITE)
    if denied:
        return denied
    try:
        data = build_form_service().remove_background(form_id)
    except FormNotFoundError:
        return fail("Formulário não encontrado.", 404)
    return ok(data, message="Imagem de fundo removida.")


@router.post("/{form_id}/pages/{page_id}/background-image")
async def upload_page_background(
    request: Request, form_id: str, page_id: str, image: UploadFile = File(...)
):
    denied = _guard(request, CX_FORMS_WRITE)
    if denied:
        return denied
    content = await image.read()
    try:
        data = build_form_service().upload_page_background(
            form_id, page_id, content=content, mime_type=image.content_type
        )
    except FormNotFoundError:
        return fail("Página não encontrada.", 404)
    except PhotoValidationError as exc:
        return fail(str(exc), 422)
    return ok(data, message="Imagem de fundo da página atualizada.")


@router.post("/{form_id}/pages/{page_id}/point-image")
async def upload_page_point_image(
    request: Request, form_id: str, page_id: str, image: UploadFile = File(...)
):
    denied = _guard(request, CX_FORMS_WRITE)
    if denied:
        return denied
    content = await image.read()
    try:
        data = build_form_service().upload_page_point_image(
            form_id, page_id, content=content, mime_type=image.content_type
        )
    except FormNotFoundError:
        return fail("Página não encontrada.", 404)
    except PhotoValidationError as exc:
        return fail(str(exc), 422)
    return ok(data, message="Imagem ilustrativa da página atualizada.")


@router.post("/{form_id}/questions/{question_id}/point-image")
async def upload_question_point_image(
    request: Request, form_id: str, question_id: str, image: UploadFile = File(...)
):
    denied = _guard(request, CX_FORMS_WRITE)
    if denied:
        return denied
    content = await image.read()
    try:
        data = build_form_service().upload_question_point_image(
            form_id, question_id, content=content, mime_type=image.content_type
        )
    except FormNotFoundError:
        return fail("Pergunta não encontrada.", 404)
    except PhotoValidationError as exc:
        return fail(str(exc), 422)
    return ok(data, message="Imagem ilustrativa da pergunta atualizada.")


# ----- público (sem login) ---------------------------------------------------


@public_router.get("/{token}")
def get_public_form(token: str):
    try:
        data = build_form_service().get_public(token)
    except FormNotFoundError:
        return fail("Formulário não encontrado ou indisponível.", 404)
    return ok(data, message="OK")


@public_router.get("/{token}/background")
def get_public_form_background(token: str):
    try:
        result = build_form_service().read_public_background(token)
    except FormNotFoundError:
        return fail("Formulário não encontrado ou indisponível.", 404)
    if result is None:
        return fail("Imagem não encontrada.", 404)
    content, mime = result
    return Response(content=content, media_type=mime)


@public_router.get("/{token}/pages/{page_id}/background")
def get_public_page_background(token: str, page_id: str):
    try:
        result = build_form_service().read_public_page_background(token, page_id)
    except FormNotFoundError:
        return fail("Formulário não encontrado ou indisponível.", 404)
    if result is None:
        return fail("Imagem não encontrada.", 404)
    content, mime = result
    return Response(content=content, media_type=mime)


@public_router.get("/{token}/pages/{page_id}/point-image")
def get_public_page_point(token: str, page_id: str):
    try:
        result = build_form_service().read_public_page_point(token, page_id)
    except FormNotFoundError:
        return fail("Formulário não encontrado ou indisponível.", 404)
    if result is None:
        return fail("Imagem não encontrada.", 404)
    content, mime = result
    return Response(content=content, media_type=mime)


@public_router.get("/{token}/questions/{question_id}/point-image")
def get_public_question_point(token: str, question_id: str):
    try:
        result = build_form_service().read_public_question_point(token, question_id)
    except FormNotFoundError:
        return fail("Formulário não encontrado ou indisponível.", 404)
    if result is None:
        return fail("Imagem não encontrada.", 404)
    content, mime = result
    return Response(content=content, media_type=mime)


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
