from __future__ import annotations

import logging

from fastapi import APIRouter, Body, File, Form, UploadFile
from pydantic import BaseModel, Field

from delpi_auth.authorization import require_any_permission

from app.application.security.api_delpi_permissions import QUALITY_ACTION_PLANS_READ_PERMISSIONS
from app.application.use_cases.quality_action_plans.quality_intelligence_use_cases import (
    AssessRecurrenceOnOpeningRequest,
    KnowledgeGraphRequest,
)
from app.composition.quality_intelligence_composer import (
    build_assess_recurrence_on_opening_use_case,
    build_get_quality_knowledge_graph_use_case,
)
from app.core.responses import error_response
from app.domain.services.quality_action_plans.pac_evidence_ocr_tag_suggestion_service import (
    PacEvidenceOcrTagSuggestionService,
)
from app.infrastructure.ocr.pac_evidence_image_ocr_service import PacEvidenceImageOcrService
from app.interface.http.openapi_agent_metadata_builder import OpenApiAgentMetadataBuilder
from app.interface.http.route_response_helpers import api_delpi_success
from app.infrastructure.persistence.plugins.plugin_base_repository import PluginsRepositoryError

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


class SuggestEvidenceTagsBody(BaseModel):
    ocr_text: str | None = None
    file_name: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=2000)


def _build_evidence_tag_suggestion(
    *,
    ocr_text: str | None,
    file_name: str | None,
    description: str | None,
    ocr_meta: dict | None = None,
) -> dict:
    suggestion = PacEvidenceOcrTagSuggestionService.suggest(
        ocr_text=ocr_text,
        file_name=file_name,
        description=description,
    )
    suggestion["ocr"] = ocr_meta or {
        "used": bool((ocr_text or "").strip()),
        "reason": "provided_text" if (ocr_text or "").strip() else "none",
    }
    return suggestion


@router.get(
    "/knowledge-graph",
    **_pac_openapi(
        "get_quality_action_plan_knowledge_graph",
        "/intelligence/knowledge-graph",
    ),
)
@require_any_permission(QUALITY_ACTION_PLANS_READ_PERMISSIONS)
def get_quality_knowledge_graph(
    branch_code: str | None = None,
    product_code: str | None = None,
    limit: int | None = None,
):
    try:
        use_case = build_get_quality_knowledge_graph_use_case()
        result = use_case.execute(
            KnowledgeGraphRequest(
                branch_code=branch_code,
                product_code=product_code,
                limit=limit,
            )
        )
        return api_delpi_success(
            result,
            operation_id="get_quality_action_plan_knowledge_graph",
        )
    except PluginsRepositoryError:
        logger.exception("Erro ao montar grafo de conhecimento PAC.")
        return error_response(
            "Erro ao consultar grafo de conhecimento.",
            status_code=500,
            code="PAC_INTELLIGENCE_ERROR",
        )


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
        logger.exception("Erro ao avaliar recorrência na abertura PAC.")
        return error_response(
            "Erro ao avaliar recorrência histórica.",
            status_code=500,
            code="PAC_INTELLIGENCE_ERROR",
        )


@router.post(
    "/suggest-evidence-tags",
    **_pac_openapi(
        "suggest_quality_action_plan_evidence_tags",
        "/intelligence/suggest-evidence-tags",
    ),
)
@require_any_permission(QUALITY_ACTION_PLANS_READ_PERMISSIONS)
def suggest_evidence_tags(body: SuggestEvidenceTagsBody = Body(...)):
    if not any(
        [
            (body.ocr_text or "").strip(),
            (body.file_name or "").strip(),
            (body.description or "").strip(),
        ]
    ):
        return error_response(
            "Informe ao menos ocr_text, file_name ou description.",
            status_code=400,
        )

    return api_delpi_success(
        _build_evidence_tag_suggestion(
            ocr_text=body.ocr_text,
            file_name=body.file_name,
            description=body.description,
        ),
        operation_id="suggest_quality_action_plan_evidence_tags",
    )


@router.post(
    "/suggest-evidence-tags/from-image",
    **_pac_openapi(
        "suggest_quality_action_plan_evidence_tags_from_image",
        "/intelligence/suggest-evidence-tags/from-image",
    ),
)
@require_any_permission(QUALITY_ACTION_PLANS_READ_PERMISSIONS)
async def suggest_evidence_tags_from_image(
    file: UploadFile = File(...),
    file_name: str | None = Form(default=None),
    description: str | None = Form(default=None),
):
    content = await file.read()
    ocr_meta = PacEvidenceImageOcrService.extract_text_from_bytes(
        content,
        mime_type=file.content_type,
    )
    return api_delpi_success(
        _build_evidence_tag_suggestion(
            ocr_text=ocr_meta.get("text"),
            file_name=file_name or file.filename,
            description=description,
            ocr_meta=ocr_meta,
        ),
        operation_id="suggest_quality_action_plan_evidence_tags_from_image",
    )
