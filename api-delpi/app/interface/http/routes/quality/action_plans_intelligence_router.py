from __future__ import annotations

import logging

from fastapi import APIRouter, Body
from pydantic import BaseModel, Field

from delpi_auth.authorization import require_any_permission

from app.application.security.api_delpi_permissions import QUALITY_ACTION_PLANS_READ_PERMISSIONS
from app.application.use_cases.quality_action_plans.quality_intelligence_use_cases import (
    AssessRecurrenceOnOpeningRequest,
)
from app.composition.quality_intelligence_composer import (
    build_assess_recurrence_on_opening_use_case,
)
from app.core.responses import error_response
from app.interface.http.openapi_agent_metadata import OpenApiAgentMetadataBuilder
from app.interface.http.route_response_helpers import api_delpi_success
from app.infrastructure.persistence.plugins.plugin_base_repository import PluginsRepositoryError
from app.utils.logger import log_error

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/action-plans/intelligence", tags=["PAC Qualidade — inteligência"])

_PAC_BASE = "/quality/action-plans"


def _pac_openapi(operation_id: str, subpath: str) -> dict:
    return OpenApiAgentMetadataBuilder.from_contract(
        operation_id,
        path=f"{_PAC_BASE}{subpath}",
    )


class RecurrenceOpeningAssessmentBody(BaseModel):
    problem_description: str = Field(..., min_length=3)
    product_code: str | None = None
    failure_mode: str | None = None
    branch_code: str | None = Field(default=None, pattern="^(01|02)$")
    symptoms: list[str] | None = None
    root_cause_category: str | None = None
    recurrence_key: str | None = Field(default=None, max_length=500)


@router.post(
    "/recurrence-opening-assessment",
    **_pac_openapi(
        "assess_quality_action_plan_recurrence_on_opening",
        "/intelligence/recurrence-opening-assessment",
    ),
)
@require_any_permission(QUALITY_ACTION_PLANS_READ_PERMISSIONS)
def assess_recurrence_on_opening(body: RecurrenceOpeningAssessmentBody = Body(...)):
    try:
        use_case = build_assess_recurrence_on_opening_use_case()
        result = use_case.execute(
            AssessRecurrenceOnOpeningRequest(
                problem_description=body.problem_description,
                product_code=body.product_code,
                failure_mode=body.failure_mode,
                branch_code=body.branch_code,
                symptoms=body.symptoms,
                root_cause_category=body.root_cause_category,
                recurrence_key=body.recurrence_key,
            )
        )
        return api_delpi_success(
            result,
            operation_id="assess_quality_action_plan_recurrence_on_opening",
        )
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except PluginsRepositoryError:
        log_error(logger, "Erro ao avaliar recorrência na abertura PAC.")
        return error_response(
            "Erro ao avaliar recorrência histórica.",
            status_code=500,
            code="PAC_INTELLIGENCE_ERROR",
        )
