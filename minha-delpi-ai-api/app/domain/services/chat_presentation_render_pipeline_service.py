"""Playbook 13 P6 — pipeline final de apresentação (prune + renderPlan)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_presentation_payload_pruning_service import (
    ChatPresentationPayloadPruningService,
)
from app.domain.services.chat_presentation_render_plan_service import (
    ChatPresentationRenderPlanService,
)


class ChatPresentationRenderPipelineService:
    """Ponto canônico pós-markdown/embeds: payload pruned e plano de renderização."""

    @classmethod
    def finalize(cls, metadata: dict[str, Any]) -> None:
        if not isinstance(metadata, dict):
            return

        cls._sync_explicit_session_before_render(metadata)
        cls._sync_stack_layout_policy_before_render(metadata)
        ChatPresentationPayloadPruningService.prune(metadata)
        ChatPresentationRenderPlanService.build(metadata)

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
