"""Respostas diretas para preferências de sessão e ambiguidade de memória."""

from __future__ import annotations

from app.domain.services.chat_behavior_instruction_service import (
    ChatBehaviorInstructionService,
)
from app.domain.services.chat_follow_up_intent_service import (
    ChatFollowUpIntentService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.services.chat_text_task_intent_service import ChatTextTaskIntentService


class ChatSessionMemoryDirectAnswerService:
    @classmethod
    def build(
        cls,
        *,
        message: str,
        workspace_context: dict | None,
    ) -> str | None:
        working_memory = (workspace_context or {}).get("workingMemory") or {}

        from app.domain.services.chat_episodic_memory_service import (
            ChatEpisodicMemoryService,
        )

        episodic_answer = ChatEpisodicMemoryService.build_recall_direct_answer(
            working_memory
        )

        if episodic_answer:
            return episodic_answer

        from app.domain.services.chat_memory_ux_service import ChatMemoryUxService

        memory_answer = ChatMemoryUxService.build_direct_answer(message, working_memory)

        if memory_answer:
            return memory_answer

        edit_pref = ChatMemoryUxService.build_edit_preference_direct_answer(message)

        if edit_pref:
            return edit_pref

        ambiguity = working_memory.get("memoryAmbiguity")

        if isinstance(ambiguity, dict):
            return cls._build_ambiguity_answer(ambiguity)

        from app.domain.services.chat_conversation_state_service import (
            ChatConversationStateService,
        )

        continuation_answer = ChatConversationStateService.build_continuation_direct_answer(
            working_memory
        )

        if continuation_answer:
            return continuation_answer

        if ChatTextTaskIntentService.is_pure_text_task(message):
            return None

        if ChatProductQueryIntentService.extract_product_code(message):
            return None

        if ChatFollowUpIntentService.is_operational_follow_up(message):
            return None

        from app.domain.services.chat_user_preference_manager_service import (
            ChatUserPreferenceManagerService,
        )

        pref_ack = ChatUserPreferenceManagerService.build_ack_direct_answer(message)

        if pref_ack:
            return pref_ack

        detected = ChatBehaviorInstructionService.detect(message)

        if detected.get("scope") != "session":
            return None

        return cls._build_preference_ack(detected)

    @classmethod
    def _build_ambiguity_answer(cls, ambiguity: dict) -> str:
        candidates = ambiguity.get("candidates") or []

        if len(candidates) >= 2:
            options = " ou ".join(str(code) for code in candidates[:3])

            return (
                f"Para seguir com segurança, confirme com qual item você quer comparar: {options}?"
            )

        hint = str(ambiguity.get("promptHint") or "").strip()

        if hint:
            return hint

        return "Preciso de um pouco mais de contexto antes de usar a consulta anterior."

    @classmethod
    def _build_preference_ack(cls, instructions: dict[str, str]) -> str:
        parts: list[str] = []

        if instructions.get("answerLength") == "short":
            parts.append("responder de forma curta")

        tone = instructions.get("tone")

        if tone == "formal":
            parts.append("usar tom formal")
        elif tone == "direct":
            parts.append("ser mais direto e objetivo")
        elif tone == "simple":
            parts.append("usar linguagem simples")

        if instructions.get("responseFormat") == "table":
            parts.append("priorizar respostas em tabela quando couber")
        elif instructions.get("responseFormat") == "topics":
            parts.append("responder em tópicos")

        if instructions.get("finalVersionOnly") == "true":
            parts.append("entregar só a versão final em correções, sem explicação longa")

        if not parts:
            return "Combinado. Vou seguir essa preferência nesta conversa."

        joined = ", ".join(parts[:-1]) + (" e " + parts[-1] if len(parts) > 1 else parts[0])

        return f"Combinado. Nesta conversa, vou {joined}."
