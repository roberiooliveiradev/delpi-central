"""Despacho de fluxos canônicos a partir do resultado da turn analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_assistant_identity_service import (
    ChatAssistantIdentityService,
)
from app.domain.services.chat_small_talk_service import ChatSmallTalkService
from app.domain.services.chat_turn_analysis_content_service import (
    ChatTurnAnalysisContentService,
)
from app.domain.services.chat_turn_analysis_service import ChatTurnAnalysisResult


@dataclass(frozen=True)
class ChatTurnAnalysisDispatch:
    """Plano de despacho pós-análise (antes de RAG/síntese pesada)."""

    kind: str
    direct_answer: str | None = None
    skip_rag: bool = False
    skip_tools: bool = False
    text_correction_mode: bool = False
    force_assistant_identity_skip: bool = False
    force_common_chat_guidance: bool = False
    clear_action_ids: bool = False
    pipeline_stage: str | None = None
    category: str | None = None


class ChatTurnAnalysisDispatchService:
    """Mapeia intent/decision da analysis para atalhos do pipeline."""

    @classmethod
    def normalize_intent(cls, intent: str | None) -> str | None:
        raw = str(intent or "").strip().lower().replace("-", "_")
        if not raw:
            return None

        aliases = ChatTurnAnalysisContentService.dispatch_intent_aliases()
        if raw in aliases:
            return str(aliases[raw]).strip().lower() or raw

        allowed = ChatTurnAnalysisContentService.dispatch_intents()
        if raw in allowed:
            return raw

        # Prefixos comuns do LLM (assistant_identity → identity).
        for canonical in allowed:
            if raw.endswith(canonical) or canonical in raw:
                return canonical

        return raw

    @classmethod
    def resolve(
        cls,
        result: ChatTurnAnalysisResult | None,
        *,
        message: str,
        workspace_context: dict | None,
        previous_messages: list | None = None,
        operational_tools_enabled: bool = False,
    ) -> ChatTurnAnalysisDispatch | None:
        if result is None:
            return None

        decision = str(result.decision or "").strip().lower()
        intent = cls.normalize_intent(result.intent)
        sub = str(result.sub_intent or "").strip().lower() or None

        if decision == "clarify":
            from app.domain.services.chat_clarification_policy_service import (
                ChatClarificationPolicyService,
            )

            answer = result.direct_answer()
            policy = ChatClarificationPolicyService.evaluate_turn_analysis_clarify(
                message,
                clarify_answer=answer,
            )
            if policy.action == "continue":
                return None

            return ChatTurnAnalysisDispatch(
                kind="clarify",
                direct_answer=policy.answer or answer,
                skip_rag=True,
                skip_tools=True,
                pipeline_stage="turn_analysis_clarify",
            )

        if intent in {"identity", "assistant_identity"}:
            category = cls._identity_category(sub)
            answer = ChatAssistantIdentityService.build_direct_answer_for_category(
                category=category,
                workspace_context=workspace_context or {},
            )
            if not answer:
                return None
            return ChatTurnAnalysisDispatch(
                kind="identity",
                direct_answer=answer,
                skip_rag=True,
                skip_tools=True,
                force_assistant_identity_skip=True,
                clear_action_ids=True,
                pipeline_stage="assistant_identity_shortcut",
                category=category,
            )

        if intent in {"small_talk", "greeting"}:
            category = cls._small_talk_category(sub)
            answer = ChatSmallTalkService.build_direct_answer_for_category(
                category=category,
                message=message,
                workspace_context=workspace_context or {},
                previous_messages=previous_messages,
            )
            if not answer:
                return None
            return ChatTurnAnalysisDispatch(
                kind="small_talk",
                direct_answer=answer,
                skip_rag=True,
                skip_tools=True,
                clear_action_ids=True,
                pipeline_stage="small_talk",
                category=category,
            )

        if intent in {"text_correction", "text_task"}:
            return ChatTurnAnalysisDispatch(
                kind="text_correction",
                skip_rag=True,
                skip_tools=True,
                text_correction_mode=True,
                clear_action_ids=True,
                pipeline_stage="text_correction",
            )

        if intent == "capabilities":
            answer = cls._capabilities_direct(
                message=message,
                workspace_context=workspace_context or {},
            )
            if answer:
                return ChatTurnAnalysisDispatch(
                    kind="capabilities",
                    direct_answer=answer,
                    skip_rag=True,
                    skip_tools=True,
                    clear_action_ids=True,
                    pipeline_stage="capabilities",
                )
            return ChatTurnAnalysisDispatch(
                kind="capabilities",
                skip_rag=True,
                clear_action_ids=True,
                pipeline_stage="capabilities",
            )

        if decision == "execute":
            if not operational_tools_enabled:
                return ChatTurnAnalysisDispatch(
                    kind="execute_needs_agent",
                    skip_rag=True,
                    skip_tools=True,
                    force_common_chat_guidance=True,
                    clear_action_ids=True,
                    pipeline_stage="common_chat_operational_guidance",
                )
            return ChatTurnAnalysisDispatch(
                kind="execute",
                skip_rag=False,
                skip_tools=False,
                pipeline_stage="turn_analysis_execute",
            )

        if decision == "narrate":
            # Conversa geral: evita RAG quando analysis não pediu doc.
            return ChatTurnAnalysisDispatch(
                kind="narrate",
                skip_rag=cls._should_skip_rag_for_narrate(intent),
                skip_tools=True,
                clear_action_ids=True,
                pipeline_stage="turn_analysis_narrate",
            )

        return None

    @classmethod
    def _should_skip_rag_for_narrate(cls, intent: str | None) -> bool:
        # Só força RAG se intent explícito de documento/RAG.
        if intent in {"rag_question", "rag", "document_question", "knowledge"}:
            return False
        return True

    @classmethod
    def _identity_category(cls, sub_intent: str | None) -> str:
        allowed = {
            "who",
            "what",
            "role",
            "limits",
            "origin",
            "usage",
            "goodquestion",
        }
        if sub_intent in allowed:
            return "goodQuestion" if sub_intent == "goodquestion" else sub_intent
        return "who"

    @classmethod
    def _small_talk_category(cls, sub_intent: str | None) -> str:
        if sub_intent in {
            "greeting",
            "thanks",
            "praise",
            "farewell",
            "ack",
            "closure",
            "how_are_you",
        }:
            if sub_intent == "how_are_you":
                return "greeting"
            return sub_intent
        return "greeting"

    @classmethod
    def _capabilities_direct(
        cls,
        *,
        message: str,
        workspace_context: dict[str, Any],
    ) -> str | None:
        from app.application.services.chat_capabilities_service import (
            ChatCapabilitiesService,
        )

        return ChatCapabilitiesService.resolve_capability_answer(
            message=message,
            workspace_context=workspace_context,
            allowed_action_ids=list(workspace_context.get("allowedActionIds") or []),
        )
