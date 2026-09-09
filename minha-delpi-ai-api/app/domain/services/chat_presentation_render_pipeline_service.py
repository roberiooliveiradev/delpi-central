"""Playbook 13 P6 — pipeline final de apresentação (structure dedup + prune + renderPlan)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_presentation_payload_pruning_service import (
    ChatPresentationPayloadPruningService,
)
from app.domain.services.chat_presentation_render_plan_service import (
    ChatPresentationRenderPlanService,
)
from app.domain.services.chat_presentation_structure_dedup_service import (
    ChatPresentationStructureDedupService,
)


class ChatPresentationRenderPipelineService:
    """Ponto canônico pós-markdown/embeds: dedupe estrutural, payload pruned e plano de renderização."""

    @classmethod
    def finalize(cls, metadata: dict[str, Any]) -> None:
        if not isinstance(metadata, dict):
            return

        cls._sync_explicit_session_before_render(metadata)
        cls._sync_stack_layout_policy_before_render(metadata)
        # Structure dedup antes do prune/renderPlan — MFE confia em structureDedupApplied + plan.
        ChatPresentationStructureDedupService.dedupe_metadata(metadata)
        ChatPresentationPayloadPruningService.prune(metadata)

        from app.domain.services.presentation_intelligence_orchestrator_service import (
            PresentationIntelligenceOrchestratorService,
        )

        user_message = None
        if isinstance(metadata.get("userMessage"), str):
            user_message = metadata.get("userMessage")
        elif isinstance(metadata.get("originalUserMessage"), str):
            user_message = metadata.get("originalUserMessage")

        PresentationIntelligenceOrchestratorService.apply_before_render_plan(
            metadata,
            user_message=user_message,
            composer_enabled=bool(metadata.get("presentationComposerAuthoritative")),
            composer_spec=metadata.get("presentationComposerSpec"),
        )

        # PI may change selected (ex.: table → heatmap) and materialize chart slots;
        # refresh single-layout suppressions so the new primary is not toolbar-suppressed.
        plan = metadata.get("stackPresentationPlan")
        if not isinstance(plan, dict):
            plan = {}
            metadata["stackPresentationPlan"] = plan
        ChatPresentationPayloadPruningService._suppress_sibling_kinds_for_single(
            metadata,
            plan,
        )

        ChatPresentationRenderPlanService.build(metadata)

        from app.domain.services.chat_presentation_llm_composition_service import (
            ChatPresentationLlmCompositionService,
        )

        # Após plano determinístico: anota allowed markers; merge se markdown já tiver [[…]].
        ChatPresentationLlmCompositionService.apply_after_deterministic_plan(metadata)

    @classmethod
    def _sync_stack_layout_policy_before_render(cls, metadata: dict[str, Any]) -> None:
        decision = metadata.get("presentationDecision")

        if not isinstance(decision, dict):
            return

        from app.domain.services.chat_presentation_route_policy_service import (
            ChatPresentationRoutePolicyService,
        )

        path = str(metadata.get("path") or "")

        if decision.get("availableViews"):
            ChatPresentationRoutePolicyService.apply_visual_order(
                decision,
                path=path,
                metadata=metadata,
            )

    @classmethod
    def _sync_explicit_session_before_render(cls, metadata: dict[str, Any]) -> None:
        from app.domain.services.chat_presentation_primary_view_service import (
            ChatPresentationPrimaryViewService,
        )

        ChatPresentationPrimaryViewService.sync_render_contract_for_explicit_session(
            metadata,
        )
