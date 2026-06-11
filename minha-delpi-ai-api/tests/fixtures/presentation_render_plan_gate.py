"""Gate CI — renderPlan tier A (Playbook 13 P6)."""

from __future__ import annotations

import re
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


_VISUAL_TOKEN_TO_KEY: dict[str, str] = {
    "kpi": "kpiPresentation",
    "tree": "treePresentation",
    "chart": "chartPresentation",
    "dashboard": "dashboardPresentation",
    "table": "tablePresentation",
}


def _segment_kinds(segments: list[Any]) -> set[str]:
    return {
        str(item.get("kind") or "").strip().lower()
        for item in segments
        if isinstance(item, dict)
    }


_GFM_TABLE_RE = re.compile(r"\|[^\n]+\|\s*\n\s*\|[-: ]+\|")
_PRESENTATION_MARKER_RE = re.compile(
    r"\[\[(?:tabela|table|grafico|chart|arvore|tree|kpi|dashboard)",
    re.IGNORECASE,
)


def _markdown_embed_issues(markdown: str) -> list[str]:
    issues: list[str] = []

    if _GFM_TABLE_RE.search(markdown):
        issues.append("tabela GFM embutida")

    if "```" in markdown:
        issues.append("code fence embutido")

    if _PRESENTATION_MARKER_RE.search(markdown):
        issues.append("marcador visual [[...]]")

    return issues


def _validate_suppressed_presentations_removed(metadata: dict[str, Any]) -> list[str]:
    """MFE render-only: chaves suprimidas pela API não podem permanecer no payload."""
    issues: list[str] = []
    plan = metadata.get("stackPresentationPlan")

    if not isinstance(plan, dict):
        return issues

    hints = plan.get("renderHints")

    if not isinstance(hints, dict):
        return issues

    for kind in hints.get("suppressedKinds") or []:
        normalized = str(kind).strip().lower()
        key = _VISUAL_TOKEN_TO_KEY.get(normalized)

        if key and metadata.get(key) is not None:
            issues.append(f"{key} listado em renderHints.suppressedKinds mas presente no payload")

    return issues


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

        explicit = str(metadata.get("explicitSessionFormat") or "").strip().lower()

        if not explicit:
            markdown = str((metadata.get("textPresentation") or {}).get("markdown") or "")

            for embed_issue in _markdown_embed_issues(markdown):
                issues.append(f"textPresentation com embed no Automático: {embed_issue}")

            hints = (plan or {}).get("renderHints") if isinstance(plan, dict) else {}

            if str((hints or {}).get("textRenderMode") or "").strip() != "compact":
                issues.append("renderHints.textRenderMode != compact no evidence-first Automático")

    if layout_mode == "stack" and isinstance(plan, dict):
        kinds = _segment_kinds(segments)
        tail_order = plan.get("tailVisualOrder") or []

        for token in tail_order:
            normalized = str(token).strip().lower()
            source = _VISUAL_TOKEN_TO_KEY.get(normalized)

            if not source or not metadata.get(source):
                continue

            if normalized not in kinds:
                issues.append(f"renderPlan omite tail visual {normalized} presente no payload")

    if (
        layout_mode == "single"
        and str(decision.get("selected") or "").strip().lower() == "text"
        and ChatPresentationEvidenceFirstLayoutService.is_active(metadata)
    ):
        non_prose = _segment_kinds(segments) - {"markdown", "decision"}

        if non_prose:
            issues.append(
                "renderPlan inclui visuais em layout single text-first evidence-first",
            )

    issues.extend(_validate_suppressed_presentations_removed(metadata))

    return issues


P6_EXTENDED_PIPELINE_CASES: tuple[dict[str, str], ...] = (
    {
        "id": "analyser_integrated_stack",
        "profile_key": "analyser",
        "path": "/products/90269001/analyser",
        "fixture": "product_analyser_90269001.json",
        "user_message": "",
    },
    {
        "id": "product_detail_single",
        "profile_key": "product_detail",
        "path": "/products/90269001",
        "fixture": "product_detail_90269001.json",
        "user_message": "",
    },
    {
        "id": "factory_status_auto_reference",
        "profile_key": "factory_status",
        "path": "/products/90269002/factory-status",
        "fixture": "product_factory_status_90269002.json",
        "user_message": "",
    },
    {
        "id": "production_status_auto",
        "profile_key": "production_status",
        "path": "/products/90269002/production-status",
        "fixture": "product_production_status_90269002.json",
        "user_message": "",
    },
)


def _iter_render_plan_pipeline_cases() -> tuple[dict[str, Any], ...]:
    tier_a = ChatPresentationVocabularyService.playbook12_tier_a_pipeline_cases()
    merged: list[dict[str, Any]] = [dict(item) for item in tier_a if isinstance(item, dict)]

    seen_ids = {str(item.get("id") or "").strip() for item in merged}

    for case in P6_EXTENDED_PIPELINE_CASES:
        case_id = str(case.get("id") or "").strip()

        if case_id and case_id not in seen_ids:
            merged.append(dict(case))
            seen_ids.add(case_id)

    return tuple(merged)


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

    for case in _iter_render_plan_pipeline_cases():
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
