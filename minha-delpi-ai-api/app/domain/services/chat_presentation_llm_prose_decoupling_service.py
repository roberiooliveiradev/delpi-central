"""Desacopla prosa template da apresentação quando a síntese LLM monta o texto do chat."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_operational_narrative_synthesis_service import (
    ChatOperationalNarrativeSynthesisService,
)
from app.domain.services.chat_presentation_prose_delivery_service import (
    ChatPresentationProseDeliveryService,
)


class ChatPresentationLlmProseDecouplingService:
    @classmethod
    def should_decouple(
        cls,
        message: str | None,
        tool_calls: list | None,
    ) -> bool:
        if not ChatOperationalNarrativeSynthesisService.should_force_llm_synthesis(
            message,
            tool_calls,
        ):
            return False

        return ChatPresentationProseDeliveryService.llm_prose_globally_available()

    @classmethod
    def apply_to_tool_calls(
        cls,
        tool_calls: list | None,
        *,
        message: str | None = None,
    ) -> bool:
        del message

        if not isinstance(tool_calls, list):
            return False

        changed = False

        for tool_call in tool_calls:
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict) or not metadata.get("ok"):
                continue

            if cls.decouple_metadata(metadata):
                changed = True

        return changed

    @classmethod
    def decouple_metadata(cls, metadata: dict[str, Any]) -> bool:
        if not isinstance(metadata, dict):
            return False

        if metadata.get("llmProseDecoupled"):
            return False

        text_presentation = metadata.get("textPresentation")
        archived_markdown = ""

        if isinstance(text_presentation, dict):
            archived_markdown = str(text_presentation.get("markdown") or "").strip()

        humanized = metadata.get("humanizedSummary")
        archived_humanized: dict[str, Any] | None = None

        if isinstance(humanized, dict):
            archived_humanized = {
                key: value
                for key, value in humanized.items()
                if value not in (None, "", [])
            }

        if not archived_markdown and not archived_humanized:
            return False

        metadata["templateProseArchive"] = {
            "textPresentationMarkdown": archived_markdown,
            "humanizedSummary": archived_humanized,
        }
        metadata["llmProseDecoupled"] = True
        metadata["proseDeliveryMode"] = "llm"

        if isinstance(text_presentation, dict):
            text_presentation["markdown"] = ""

        if isinstance(humanized, dict):
            humanized["linhas"] = []
            humanized["linhas_detalhe"] = []

        decision = metadata.get("presentationDecision")

        if not isinstance(decision, dict):
            decision = {}
            metadata["presentationDecision"] = decision

        decision["proseSource"] = "llm"
        decision["insight"] = ""

        metadata.pop("storyPresentation", None)

        from app.domain.services.chat_presentation_render_pipeline_service import (
            ChatPresentationRenderPipelineService,
        )

        ChatPresentationRenderPipelineService.finalize(metadata)
        return True

    @classmethod
    def is_decoupled(cls, metadata: dict[str, Any] | None) -> bool:
        return isinstance(metadata, dict) and bool(metadata.get("llmProseDecoupled"))
