"""Gate Playbook 13 — qualidade humanizada por shape."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_data_insight_service import ChatDataInsightService
from app.domain.services.chat_humanized_response_quality_service import (
    ChatHumanizedResponseQualityService,
)
from app.domain.services.chat_operational_commentary_enrichment_service import (
    ChatOperationalCommentaryEnrichmentService,
)
from app.domain.services.chat_presentation_coverage_service import (
    ChatPresentationCoverageService,
)
from tests.fixtures.humanized_data_response_cases import HUMANIZED_DATA_SHAPE_CASES


def _build_metadata_for_case(case: dict[str, Any]) -> dict[str, Any]:
    if case.get("error_only"):
        return {"path": case.get("path") or "", "ok": False}

    metadata: dict[str, Any] = {
        "path": str(case.get("path") or ""),
        "stackPresentationPlan": {
            "presentationProfileKey": str(case.get("profile_key") or "generic"),
        },
        "textPresentation": {"markdown": "### Dados\n\nConsulta operacional."},
    }
    data: dict[str, Any] = {}

    if isinstance(case.get("data"), dict):
        data = dict(case["data"])
    elif isinstance(case.get("rows"), list):
        data = {"items": case["rows"]}

    pagination = data.get("pagination")

    if isinstance(pagination, dict) and data.get("total") is None:
        raw_total = pagination.get("total")

        if raw_total is not None:
            data["total"] = raw_total

    profile_key = str(case.get("profile_key") or "").strip()

    if profile_key in {"factory_status", "stock", "production_status", "shipping_status"}:
        ChatOperationalCommentaryEnrichmentService.enrich_metadata(metadata, data=data)
        return metadata

    insight = ChatDataInsightService.build(metadata, data)

    if insight:
        metadata["dataCommentary"] = insight
        metadata["dataAnswer"] = insight if insight.get("summary") else None

        if metadata.get("dataAnswer") is None:
            from app.domain.services.chat_humanized_data_response_service import (
                ChatHumanizedDataResponseService,
            )

            metadata["dataAnswer"] = ChatHumanizedDataResponseService.to_data_answer(insight)

    return metadata


def validate_humanized_shape_cases() -> list[str]:
    gaps: list[str] = []

    for case in HUMANIZED_DATA_SHAPE_CASES:
        metadata = _build_metadata_for_case(case)
        case_gaps = ChatHumanizedResponseQualityService.evaluate_expectations(
            metadata,
            expect=case.get("expect"),
        )

        for gap in case_gaps:
            gaps.append(f"{case['id']}: {gap}")

    return gaps


def validate_humanized_coverage_for_ci(
    *,
    openapi_baseline_path=None,
) -> list[str]:
    rows = ChatPresentationCoverageService.build_matrix(baseline_path=openapi_baseline_path)
    return ChatPresentationCoverageService.find_humanized_coverage_gaps(rows)


def validate_humanized_answer_for_ci(
    *,
    openapi_baseline_path=None,
) -> dict[str, object]:
    shape_gaps = validate_humanized_shape_cases()
    coverage_gaps = validate_humanized_coverage_for_ci(
        openapi_baseline_path=openapi_baseline_path,
    )
    gaps = shape_gaps + coverage_gaps

    return {
        "humanizedGaps": gaps,
        "gapCount": len(gaps),
        "ok": not gaps,
    }
