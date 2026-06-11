"""Gate CI — renderPlan tier A (Playbook 13 P6)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.domain.services.chat_presentation_evidence_first_layout_service import (
    ChatPresentationEvidenceFirstLayoutService,
)
from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)


@dataclass(frozen=True)
class RenderPlanCoverageGap:
    case_id: str
    profile_key: str
    path: str
    detail: str


def _validate_render_plan_contract(metadata: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    render_plan = metadata.get("renderPlan")

    if not isinstance(render_plan, dict):
        issues.append("renderPlan ausente")
        return issues

    if render_plan.get("version") != 1:
        issues.append("renderPlan.version != 1")

    segments = render_plan.get("segments")

    if not isinstance(segments, list) or not segments:
        issues.append("renderPlan.segments vazio")
        return issues

    decision = metadata.get("presentationDecision") or {}
    layout_mode = str(render_plan.get("layoutMode") or decision.get("layoutMode") or "").strip()

    if not layout_mode:
        issues.append("renderPlan.layoutMode ausente")

    plan = metadata.get("stackPresentationPlan")

    if isinstance(plan, dict):
        policy = str(plan.get("tailVisualPolicy") or "").strip()

        if not policy:
            issues.append("stackPresentationPlan.tailVisualPolicy ausente")

        hints = plan.get("renderHints")

        if not isinstance(hints, dict):
            issues.append("stackPresentationPlan.renderHints ausente")
        elif not str(hints.get("textRenderMode") or "").strip():
            issues.append("renderHints.textRenderMode ausente")

    if ChatPresentationEvidenceFirstLayoutService.is_active(metadata):
        policy = str((plan or {}).get("tailVisualPolicy") or "").strip()

        if policy == "allowlist" and metadata.get("dashboardPresentation") is not None:
            issues.append("dashboardPresentation presente no Automático + allowlist")

        kinds = {str(item.get("kind") or "").strip().lower() for item in segments if isinstance(item, dict)}

        if "dashboard" in kinds:
            issues.append("renderPlan inclui dashboard no Automático evidence-first")

    return issues


def find_render_plan_gaps() -> list[RenderPlanCoverageGap]:
    from app.application.use_cases.execute_external_action_use_case import (
        ExecuteExternalActionUseCase,
    )
    from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta

    use_case = ExecuteExternalActionUseCase(
        repository=None,
        gateway=None,
        policy=None,
        audit_repository=None,
    )
    gaps: list[RenderPlanCoverageGap] = []

    for case in ChatPresentationVocabularyService.playbook12_tier_a_pipeline_cases():
        if not isinstance(case, dict):
            continue

        case_id = str(case.get("id") or "").strip() or "unknown"
        profile_key = str(case.get("profile_key") or "").strip()
        path = str(case.get("path") or "").strip()
        fixture = str(case.get("fixture") or "").strip()
        user_message = str(case.get("user_message") or "").strip()

        if not path or not fixture:
            gaps.append(
                RenderPlanCoverageGap(
                    case_id=case_id,
                    profile_key=profile_key,
                    path=path,
                    detail="fixture ou path ausente em tierAPipelineCases",
                )
            )
            continue

        try:
            envelope = load_api_delpi_fixture_with_meta(fixture)
        except (FileNotFoundError, ValueError, KeyError) as exc:
            gaps.append(
                RenderPlanCoverageGap(
                    case_id=case_id,
                    profile_key=profile_key,
                    path=path,
                    detail=f"fixture indisponível: {exc}",
                )
            )
            continue

        metadata = use_case._build_presentation_metadata(
            action={"path": path},
            sanitized_data=envelope,
            resolved_path=path,
            request_parameters={"userMessage": user_message} if user_message else {},
        )
        issues = _validate_render_plan_contract(metadata)

        for issue in issues:
            gaps.append(
                RenderPlanCoverageGap(
                    case_id=case_id,
                    profile_key=profile_key,
                    path=path,
                    detail=issue,
                )
            )

    return gaps


def validate_render_plan_for_ci() -> dict[str, Any]:
    gaps = find_render_plan_gaps()

    return {
        "renderPlanGaps": [asdict(gap) for gap in gaps],
        "ok": not gaps,
    }
