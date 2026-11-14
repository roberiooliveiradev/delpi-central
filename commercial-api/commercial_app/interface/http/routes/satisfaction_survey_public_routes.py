from __future__ import annotations

import logging
import re

from fastapi import APIRouter, Request

from commercial_app.application.use_cases.manage_satisfaction_surveys import (
    ManageSatisfactionSurveysUseCase,
    SatisfactionSurveyError,
    SubmitPublicResponseCommand,
)
from commercial_app.composition.commercial_composer import (
    build_manage_satisfaction_surveys_use_case,
)
from commercial_app.core.responses import fail, ok
from commercial_app.interface.http.schemas.satisfaction_survey_schemas import (
    PublicResponseBody,
)

logger = logging.getLogger("commercial.satisfaction_survey.public")

router = APIRouter(
    prefix="/public/satisfaction-surveys",
    tags=["Satisfaction surveys (public)"],
)

_TOKEN_RE = re.compile(r"^[A-Za-z0-9_\-]{16,128}$")


def _use_case() -> ManageSatisfactionSurveysUseCase:
    return build_manage_satisfaction_surveys_use_case()


def _map_error(exc: SatisfactionSurveyError, *, operation_id: str):
    # Never leak recipient/campaign identity on invalid tokens.
    return fail(
        exc.message,
        exc.status_code,
        data={"code": exc.code} if exc.code else None,
        operation_id=operation_id,
    )


def _validate_token_shape(token: str) -> str | None:
    raw = (token or "").strip()
    if not _TOKEN_RE.match(raw):
        return None
    return raw


@router.get("/{token}", operation_id="get_public_satisfaction_survey")
def get_public_satisfaction_survey(_request: Request, token: str):
    safe = _validate_token_shape(token)
    if safe is None:
        return fail(
            "Link inválido ou expirado.",
            404,
            data={"code": "invalid_token"},
            operation_id="get_public_satisfaction_survey",
        )
    try:
        payload = _use_case().load_public_form(safe)
        return ok(
            payload,
            message="Formulário público carregado.",
            operation_id="get_public_satisfaction_survey",
        )
    except SatisfactionSurveyError as exc:
        return _map_error(exc, operation_id="get_public_satisfaction_survey")
    except Exception:
        logger.exception("get_public_satisfaction_survey_failed")
        return fail(
            "Erro temporário ao carregar a pesquisa.",
            503,
            data={"code": "temporary_error"},
            operation_id="get_public_satisfaction_survey",
        )


@router.post("/{token}/response", operation_id="submit_public_satisfaction_response")
def submit_public_satisfaction_response(
    _request: Request, token: str, body: PublicResponseBody
):
    safe = _validate_token_shape(token)
    if safe is None:
        return fail(
            "Link inválido ou expirado.",
            404,
            data={"code": "invalid_token"},
            operation_id="submit_public_satisfaction_response",
        )
    try:
        result = _use_case().submit_public_response(
            SubmitPublicResponseCommand(
                token=safe,
                overall_score=body.overall_score,
                recommendation_score=body.recommendation_score,
                dimensions=body.dimensions,
                strengths=body.strengths,
                improvements=body.improvements,
                unmet_needs=body.unmet_needs,
            )
        )
        return ok(
            result,
            message="Resposta registrada.",
            status_code=201,
            operation_id="submit_public_satisfaction_response",
        )
    except SatisfactionSurveyError as exc:
        return _map_error(exc, operation_id="submit_public_satisfaction_response")
    except Exception:
        logger.exception("submit_public_satisfaction_response_failed")
        return fail(
            "Não foi possível confirmar o envio. Tente novamente.",
            503,
            data={"code": "temporary_error"},
            operation_id="submit_public_satisfaction_response",
        )
