"""Layout canônico Playbook 13 — interpretação (dataAnswer) na narrativa do chat.

Modo ``summary_then_evidence``: a leitura vai no ``textPresentation.markdown`` (prosa
natural do chat); tabelas e gráficos ficam nos slots de evidência — sem card separado,
sem repetir panorama/ficha/destaques/painel composto.
"""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_rich_presentation_text_service import (
    ChatRichPresentationTextService,
)

PRESENTATION_MODE = "summary_then_evidence"


class ChatPresentationEvidenceFirstLayoutService:
    @classmethod
    def presentation_mode(cls) -> str:
        return PRESENTATION_MODE

    @classmethod
    def is_active(cls, metadata: dict[str, Any]) -> bool:
        if not isinstance(metadata, dict):
            return False

        decision = metadata.get("presentationDecision")

        if isinstance(decision, dict):
            mode = str(decision.get("presentationMode") or "").strip()

            if mode == PRESENTATION_MODE:
                return True

        plan = metadata.get("stackPresentationPlan")

        if isinstance(plan, dict):
            mode = str(plan.get("presentationMode") or "").strip()

            if mode == PRESENTATION_MODE:
                return True

        return False

    @classmethod
    def can_activate(cls, metadata: dict[str, Any]) -> bool:
        if not isinstance(metadata, dict):
            return False

        data_answer = metadata.get("dataAnswer")

        if not isinstance(data_answer, dict):
            return False

        summary = data_answer.get("summary")

        if not isinstance(summary, dict):
            return False

        return bool(str(summary.get("answer") or "").strip())

    @classmethod
    def activate(cls, metadata: dict[str, Any]) -> bool:
        if not cls.can_activate(metadata):
            return False

        decision = metadata.get("presentationDecision")

        if not isinstance(decision, dict):
            decision = {}
            metadata["presentationDecision"] = decision

        decision["presentationMode"] = PRESENTATION_MODE
        return True

    @classmethod
    def compose(cls, metadata: dict[str, Any]) -> None:
        if not cls.is_active(metadata):
            return

        metadata.pop("storyPresentation", None)
        ChatRichPresentationTextService.prepare_evidence_first_chat_narrative(metadata)

        decision = metadata.get("presentationDecision")

        if not isinstance(decision, dict):
            return

        if str(decision.get("layoutMode") or "").strip().casefold() != "stack":
            return

        plan = metadata.get("stackPresentationPlan")

        if not isinstance(plan, dict):
            return

        cls._apply_evidence_first_stack_plan(metadata, plan)

        nested = decision.get("stackPresentationPlan")

        if isinstance(nested, dict):
            cls._apply_evidence_first_stack_plan(metadata, nested, source_plan=plan)

    @classmethod
    def _resolve_tail_visual_order(cls, metadata: dict[str, Any]) -> list[str]:
        from app.domain.services.chat_presentation_stack_order_service import (
            ChatPresentationStackOrderService,
        )

        return ChatPresentationStackOrderService._resolve_tail_visual_order(metadata)

    @classmethod
    def finalize_narrative_after_embeds(cls, metadata: dict[str, Any]) -> None:
        """Reaplica strip de markdown embutido após serviços de embed do modo Texto."""
        if not cls.is_active(metadata):
            return

        ChatRichPresentationTextService.prepare_evidence_first_chat_narrative(metadata)

    @classmethod
    def _resolve_evidence_first_tail_visual_order(cls, metadata: dict[str, Any]) -> list[str]:
        explicit = str(metadata.get("explicitSessionFormat") or "").strip().lower()
        order = cls._resolve_tail_visual_order(metadata)

        if explicit == "dashboard":
            return order

        filtered = [
            token
            for token in order
            if str(token).strip().lower() != "dashboard"
        ]

        if filtered:
            return filtered

        return cls._available_evidence_tail_visuals(metadata)

    @classmethod
    def _available_evidence_tail_visuals(cls, metadata: dict[str, Any]) -> list[str]:
        counts = ChatRichPresentationTextService.count_complementary_visuals(metadata)
        order: list[str] = []

        for token in ("kpi", "tree", "chart"):
            if int(counts.get(token) or 0) >= 1:
                order.append(token)

        return order

    @classmethod
    def _apply_evidence_first_stack_plan(
        cls,
        metadata: dict[str, Any],
        plan: dict[str, Any],
        *,
        source_plan: dict[str, Any] | None = None,
    ) -> None:
        if isinstance(source_plan, dict):
            tail_order = list(source_plan.get("tailVisualOrder") or [])
        else:
            tail_order = cls._resolve_evidence_first_tail_visual_order(metadata)

        plan["presentationMode"] = PRESENTATION_MODE
        plan["tailVisualPolicy"] = "allowlist"
        plan["tailVisualOrder"] = tail_order
        cls._sync_tail_visuals_narrative_slot(plan)
        cls._apply_native_view_stack_plan(metadata, plan)

    @classmethod
    def _sync_tail_visuals_narrative_slot(cls, plan: dict[str, Any]) -> None:
        tail_order = plan.get("tailVisualOrder") or []
        narrative_order = plan.get("narrativeOrder")

        if not isinstance(narrative_order, list):
            narrative_order = []

        has_tail_slot = any(
            str(slot).strip().lower() == "tailvisuals" for slot in narrative_order
        )

        if tail_order and not has_tail_slot:
            narrative_order = [*narrative_order, "tailVisuals"]
        elif not tail_order and has_tail_slot:
            narrative_order = [
                slot
                for slot in narrative_order
                if str(slot).strip().lower() != "tailvisuals"
            ]

        plan["narrativeOrder"] = narrative_order

    @classmethod
    def _apply_native_view_stack_plan(cls, metadata: dict[str, Any], plan: dict[str, Any]) -> None:
        explicit = str(metadata.get("explicitSessionFormat") or "").strip().lower()

        if explicit != "dashboard":
            return

        plan["tableRoleOrder"] = []
        plan["profileFirst"] = False
        plan["narrativeOrder"] = [
            slot
            for slot in (plan.get("narrativeOrder") or ["lead", "operationalTables", "tailVisuals"])
            if slot not in {"profileTables", "operationalTables", "highlights"}
        ]

        visibility = plan.get("sectionVisibility")

        if isinstance(visibility, dict):
            visibility["profile"] = False
            visibility["guide"] = False
            visibility["structure"] = False
            visibility["highlights"] = False
