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

        plan["presentationMode"] = PRESENTATION_MODE
        plan["tailVisualOrder"] = cls._resolve_tail_visual_order(metadata)

        nested = decision.get("stackPresentationPlan")

        if isinstance(nested, dict):
            nested["presentationMode"] = PRESENTATION_MODE
            nested["tailVisualOrder"] = plan["tailVisualOrder"]

    @classmethod
    def _resolve_tail_visual_order(cls, metadata: dict[str, Any]) -> list[str]:
        order: list[str] = []

        if cls._has_presentation(metadata, "chartPresentation", "chart"):
            order.append("chart")

        return order

    @classmethod
    def _has_presentation(cls, metadata: dict[str, Any], key: str, presentation_type: str) -> bool:
        presentation = metadata.get(key)

        if isinstance(presentation, dict) and str(presentation.get("type") or "") == presentation_type:
            return True

        bundled = metadata.get("chartPresentation")

        if key == "chartPresentation" and isinstance(bundled, dict):
            return str(bundled.get("type") or "") == "chart"

        return False
