from __future__ import annotations

from fastapi import APIRouter, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from cipa_app.application.use_cases.sipat_survey_service import SipatSurveyService
from cipa_app.core.responses import fail, ok

router = APIRouter(prefix="/sipat/surveys", tags=["CIPA SIPAT"])
public_router = APIRouter(prefix="/public/sipat", tags=["CIPA SIPAT Public"])
service = SipatSurveyService()


class QuestionPayload(BaseModel):
    question_type: str
    label: str = Field(..., min_length=1)
    help_text: str | None = None
    is_required: bool = True
    options: list[str] | None = None


class CreateSurveyRequest(BaseModel):
    unit_code: str
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    template_id: str | None = None
    opens_at: str | None = None
    closes_at: str | None = None
    questions: list[QuestionPayload] | None = None


class UpdateSurveyRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    opens_at: str | None = None
    closes_at: str | None = None
    questions: list[QuestionPayload] | None = None


class ApplyTemplateRequest(BaseModel):
    template_id: str


class PublicAnswerItem(BaseModel):
    question_id: str
    value: str | None = None
    value_text: str | None = None
    choice: str | None = None
    choices: list[str] | None = None


class PublicSubmitRequest(BaseModel):
    answers: list[PublicAnswerItem]


def _handle(exc: Exception):
    if isinstance(exc, PermissionError):
        return fail(str(exc), 403)
    if isinstance(exc, LookupError):
        return fail(str(exc), 404)
    if isinstance(exc, ValueError):
        return fail(str(exc), 400)
    raise exc


@router.get("")
def list_surveys(request: Request, unit_code: str = Query(...)):
    try:
        return ok(service.list_surveys(request.state.user, unit_code=unit_code))
    except Exception as exc:
        return _handle(exc)


@router.post("")
def create_survey(request: Request, body: CreateSurveyRequest):
    try:
        return ok(service.create_survey(request.state.user, body.model_dump()), status_code=201)
    except Exception as exc:
        return _handle(exc)


@router.get("/{survey_id}")
def get_survey(request: Request, survey_id: str):
    try:
        return ok(service.get_survey(request.state.user, survey_id))
    except Exception as exc:
        return _handle(exc)


@router.patch("/{survey_id}")
def update_survey(request: Request, survey_id: str, body: UpdateSurveyRequest):
    try:
        return ok(
            service.update_survey(
                request.state.user,
                survey_id,
                body.model_dump(exclude_unset=True),
            )
        )
    except Exception as exc:
        return _handle(exc)


@router.post("/{survey_id}/apply-template")
def apply_template(request: Request, survey_id: str, body: ApplyTemplateRequest):
    try:
        return ok(service.apply_template(request.state.user, survey_id, body.template_id))
    except Exception as exc:
        return _handle(exc)


@router.post("/{survey_id}/clone")
def clone_survey(request: Request, survey_id: str):
    try:
        return ok(service.clone_survey(request.state.user, survey_id), status_code=201)
    except Exception as exc:
        return _handle(exc)


@router.post("/{survey_id}/publish")
def publish_survey(request: Request, survey_id: str):
    try:
        return ok(service.publish(request.state.user, survey_id))
    except Exception as exc:
        return _handle(exc)


@router.post("/{survey_id}/close")
def close_survey(request: Request, survey_id: str):
    try:
        return ok(service.close(request.state.user, survey_id))
    except Exception as exc:
        return _handle(exc)


@router.delete("/{survey_id}")
def delete_survey(request: Request, survey_id: str):
    try:
        return ok(service.delete_survey(request.state.user, survey_id))
    except Exception as exc:
        return _handle(exc)


@router.get("/{survey_id}/qr")
def download_qr(request: Request, survey_id: str):
    try:
        raw, filename = service.qr_bytes(request.state.user, survey_id)
        return Response(
            content=raw,
            media_type="image/png",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as exc:
        return _handle(exc)


@router.get("/{survey_id}/summary")
def survey_summary(request: Request, survey_id: str):
    try:
        return ok(service.summary(request.state.user, survey_id))
    except Exception as exc:
        return _handle(exc)


@router.get("/{survey_id}/export.xlsx")
def export_excel(request: Request, survey_id: str):
    try:
        raw, filename = service.export_excel(request.state.user, survey_id)
        return Response(
            content=raw,
            media_type=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as exc:
        return _handle(exc)


@public_router.get("/{token}")
def public_get_survey(token: str):
    try:
        return ok(service.get_public(token))
    except Exception as exc:
        return _handle(exc)


@public_router.post("/{token}/responses")
def public_submit(token: str, body: PublicSubmitRequest):
    try:
        return ok(
            service.submit_public(
                token,
                {"answers": [item.model_dump() for item in body.answers]},
            ),
            status_code=201,
        )
    except Exception as exc:
        return _handle(exc)
