"""Suporte transversal ao roteador de intenção."""

from __future__ import annotations

from app.domain.services.chat_intent_router.chat_intent_router_models import IntentRouteResult


class ChatIntentRouterSupportService:
    STAGE_INTENT: dict[str, tuple[str, str | None, int]] = {
        "text_task": ("text_task", None, 3),
        "text_task_mixed": ("mixed_task", None, 3),
        "canvas": ("canvas_task", None, 4),
        "data_interpretation": ("follow_up", "data_interpretation", 5),
        "data_interpretation_empty": ("follow_up", "data_interpretation_empty", 5),
        "web_list_sources": ("follow_up", "web_list_sources", 5),
        "web_summarize": ("follow_up", "web_summarize", 5),
        "web_extract_params": ("follow_up", "web_extract_params", 5),
        "web_compare_sources": ("follow_up", "web_compare_sources", 5),
        "operational_parameter": ("clarification", "missing_params", 2),
        "intent_disambiguation": ("operational_query", "scope_clarification", 6),
        "tools": ("operational_query", None, 6),
        "capabilities": ("self_help", "capabilities_catalog", 9),
        "small_talk": ("small_talk", None, 9),
        "utility_direct": ("utility", None, 9),
        "attachment_welcome": ("attachment_task", "welcome", 7),
        "attachment_document": ("attachment_document", "read_content", 5),
        "drawing_analysis": ("drawing_analysis", "delpi_pdf", 5),
        "identity_shortcut": ("identity", "user_profile", 9),
        "assistant_identity_shortcut": ("identity", "assistant_profile", 9),
        "meta_direct_answer": ("identity", "meta", 9),
        "unclear_request": ("clarification", "unclear", 9),
        "rag": ("rag_question", None, 8),
        "skip_rag": ("llm_general", "no_rag", 10),
        "web_save_sources": ("web_search", None, 7),
    }

    @staticmethod
    def build_fallback_prompt() -> str:
        return (
            "Posso ajudar de algumas formas. Você quer:\n"
            "- corrigir ou escrever um texto;\n"
            "- consultar dados operacionais;\n"
            "- usar um arquivo ou documentação interna;\n"
            "- pesquisar na web;\n"
            "- colocar algo na lousa?"
        )

    @staticmethod
    def with_decision(
        route: IntentRouteResult,
        *,
        decision: str | None = None,
        reason: str | None = None,
    ) -> IntentRouteResult:
        if decision == route.decision and reason == route.reason:
            return route

        return IntentRouteResult(
            intent=route.intent,
            sub_intent=route.sub_intent,
            is_follow_up=route.is_follow_up,
            confidence=route.confidence,
            requires_tool=route.requires_tool,
            requires_rag=route.requires_rag,
            requires_web=route.requires_web,
            requires_canvas=route.requires_canvas,
            requires_llm=route.requires_llm,
            priority_applied=route.priority_applied,
            flags=route.flags,
            resolved_params=route.resolved_params,
            ambiguous=route.ambiguous,
            candidates=route.candidates,
            decision=decision or route.decision,
            reason=reason or route.reason,
            mixed_steps=route.mixed_steps,
        )

    @staticmethod
    def tool_calls_include_web(tool_calls: list | None) -> bool:
        for call in tool_calls or []:
            if not isinstance(call, dict):
                continue

            name = str(call.get("name") or call.get("tool") or "").strip().lower()

            if name == "web_search":
                return True

        return False
