"""Síntese grounded enrich-then-insight e narrate-only — fatos cruzados sem dump técnico."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_operational_llm_synthesis_brief_direct_service import (
    ChatOperationalLlmSynthesisBriefDirectService,
)
from app.domain.services.chat_operational_llm_synthesis_context_service import (
    ChatOperationalLlmSynthesisContextService,
)
from app.domain.services.chat_turn_grounding_content_service import (
    ChatTurnGroundingContentService,
)
from app.domain.services.chat_turn_grounding_service import ChatTurnGroundingService


class ChatGroundedInsightAnswerService:
    @classmethod
    def apply_enrich_context(
        cls,
        message: str,
        previous_messages: list[Any] | None,
        tool_context: dict | None,
        *,
        workspace_context: dict | None = None,
    ) -> tuple[bool, dict]:
        stage = cls._resolve_stage(workspace_context, tool_context)

        if stage != "grounded_enrich_insight":
            return False, dict(tool_context or {})

        excerpt = cls._resolve_excerpt(workspace_context, tool_context)
        updated = cls._inject_insight_context(
            message,
            previous_messages,
            tool_context,
            excerpt=excerpt,
            workspace_context=workspace_context,
        )
        updated["groundedEnrichInsight"] = True

        return True, updated

    @classmethod
    def apply_narrate_insight_context(
        cls,
        message: str,
        previous_messages: list[Any] | None,
        tool_context: dict | None,
        *,
        workspace_context: dict | None = None,
    ) -> tuple[bool, dict]:
        stage = cls._resolve_stage(workspace_context, tool_context)

        if stage != "grounded_narrate_insight":
            return False, dict(tool_context or {})

        excerpt = cls._resolve_excerpt(workspace_context, tool_context)
        updated = cls._inject_insight_context(
            message,
            previous_messages,
            tool_context,
            excerpt=excerpt,
            workspace_context=workspace_context,
        )
        updated["groundedInsightNarrate"] = True

        return True, updated

    @classmethod
    def build_template_fallback(
        cls,
        message: str,
        tool_calls: list[Any] | None,
        *,
        workspace_context: dict | None = None,
        tool_context: dict | None = None,
        response_mode: str | None = None,
    ) -> str | None:
        from app.domain.services.chat_operational_llm_synthesis_turn_finalization_service import (
            ChatOperationalLlmSynthesisTurnFinalizationService,
        )

        lead = ChatOperationalLlmSynthesisBriefDirectService.try_build_quality_fallback(
            message,
            tool_calls,
            response_mode=response_mode,
        )

        if lead:
            return ChatOperationalLlmSynthesisTurnFinalizationService._finalize_body(
                lead,
                message=message,
                tool_calls=tool_calls,
                response_mode=str(response_mode or "normal"),
                response_mode_effect="llm_synthesis",
            )

        facts = ChatOperationalLlmSynthesisContextService.build_facts_addon(
            tool_calls,
            response_mode=response_mode,
        ).strip()

        if facts:
            return facts.lstrip("\n").strip()

        excerpt = cls._resolve_excerpt(workspace_context, tool_context)
        excerpt_block = ChatTurnGroundingContentService.format_excerpt_prompt_block(excerpt)

        return excerpt_block.strip() or None

    @classmethod
    def _inject_insight_context(
        cls,
        message: str,
        previous_messages: list[Any] | None,
        tool_context: dict | None,
        *,
        excerpt: dict[str, Any] | None,
        workspace_context: dict | None,
    ) -> dict:
        from app.domain.services.chat_conversation_context_service import (
            ChatConversationContextService,
        )

        updated = dict(tool_context or {})
        updated.pop("directAnswer", None)

        blocks: list[str] = []
        narrate_instruction = ChatTurnGroundingContentService.narrate_instruction()

        if narrate_instruction:
            blocks.append(narrate_instruction)

        excerpt_block = ChatTurnGroundingContentService.format_excerpt_prompt_block(excerpt)

        if excerpt_block:
            blocks.append(excerpt_block)

        analysis_block = ChatConversationContextService.build_analysis_context(
            previous_messages,
            message=message,
        )

        if analysis_block:
            blocks.append(analysis_block)

        merged = "\n\n".join(block for block in blocks if block).strip()
        existing = str(updated.get("context") or "").strip()

        if merged:
            updated["context"] = (
                f"{existing}\n\n{merged}".strip() if existing else merged
            )

        updated["analysisMode"] = True
        turn_grounding = (workspace_context or {}).get("turnGrounding")

        if isinstance(turn_grounding, dict) and turn_grounding:
            updated["turnGrounding"] = dict(turn_grounding)

        return updated

    @classmethod
    def _resolve_stage(
        cls,
        workspace_context: dict | None,
        tool_context: dict | None,
    ) -> str:
        for source in (tool_context, workspace_context):
            if not isinstance(source, dict):
                continue

            turn_grounding = source.get("turnGrounding")

            if isinstance(turn_grounding, dict):
                stage = str(turn_grounding.get("stage") or "").strip()

                if stage:
                    return stage

        return ""

    @classmethod
    def _resolve_excerpt(
        cls,
        workspace_context: dict | None,
        tool_context: dict | None,
    ) -> dict[str, Any] | None:
        from app.application.services.chat_grounded_narrate_answer_service import (
            ChatGroundedNarrateAnswerService,
        )

        return ChatGroundedNarrateAnswerService._resolve_excerpt(
            workspace_context,
            tool_context,
        )

    @classmethod
    def is_insight_stage(cls, workspace_context: dict | None, tool_context: dict | None) -> bool:
        stage = cls._resolve_stage(workspace_context, tool_context)

        return stage in {
            "grounded_enrich_insight",
            "grounded_narrate_insight",
        }

    @classmethod
    def is_recap_stage(cls, workspace_context: dict | None, tool_context: dict | None) -> bool:
        stage = cls._resolve_stage(workspace_context, tool_context)

        if stage == "grounded_narrate_recap":
            return True

        excerpt = cls._resolve_excerpt(workspace_context, tool_context)

        if not isinstance(excerpt, dict):
            return False

        message = str((tool_context or {}).get("currentMessage") or "")

        return bool(message) and ChatTurnGroundingService.should_narrate_excerpt(
            message,
            excerpt,
        )
