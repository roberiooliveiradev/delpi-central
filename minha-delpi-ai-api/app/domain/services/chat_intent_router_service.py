"""Roteamento de intenção do turno — Playbook 02 (chat base, prioridade + observabilidade)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class IntentRouteResult:
    intent: str
    sub_intent: str | None = None
    is_follow_up: bool = False
    confidence: float = 0.0
    requires_tool: bool = False
    requires_rag: bool = False
    requires_web: bool = False
    requires_canvas: bool = False
    requires_llm: bool = True
    priority_applied: int = 0
    flags: tuple[str, ...] = ()
    resolved_params: dict[str, str] | None = None
    ambiguous: bool = False
    candidates: tuple[str, ...] = ()
    decision: str | None = None
    reason: str | None = None
    mixed_steps: tuple[str, ...] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "intent": self.intent,
            "isFollowUp": self.is_follow_up,
            "confidence": round(self.confidence, 2),
            "requiresTool": self.requires_tool,
            "requiresRag": self.requires_rag,
            "requiresWeb": self.requires_web,
            "requiresCanvas": self.requires_canvas,
            "requiresLlm": self.requires_llm,
            "priorityApplied": self.priority_applied,
            "ambiguous": self.ambiguous,
        }

        if self.sub_intent:
            payload["subIntent"] = self.sub_intent

        if self.flags:
            payload["flags"] = list(self.flags)

        if self.resolved_params:
            params = dict(self.resolved_params)
            payload["resolvedParams"] = params
            payload["resolvedFromMemory"] = params

        if self.candidates:
            payload["candidates"] = list(self.candidates)

        if self.mixed_steps:
            payload["mixedSteps"] = list(self.mixed_steps)

        if self.decision:
            payload["decision"] = self.decision

        if self.reason:
            payload["reason"] = self.reason

        payload["router"] = {
            "intent": self.intent,
            "subIntent": self.sub_intent,
            "confidence": payload["confidence"],
            "decision": self.decision,
            "reason": self.reason,
        }

        payload["intentRouting"] = {
            key: payload[key]
            for key in (
                "intent",
                "subIntent",
                "isFollowUp",
                "confidence",
                "requiresTool",
                "requiresRag",
                "requiresWeb",
                "requiresCanvas",
                "requiresLlm",
                "resolvedParams",
                "ambiguous",
                "candidates",
                "mixedSteps",
            )
            if key in payload
        }

        return payload


def _working_memory_entities(workspace_context: dict | None) -> dict[str, str]:
    if not isinstance(workspace_context, dict):
        return {}

    working = workspace_context.get("workingMemory")

    if not isinstance(working, dict):
        return {}

    entities = working.get("lastEntities")

    if not isinstance(entities, dict):
        return {}

    return {
        str(key): str(value).strip()
        for key, value in entities.items()
        if value is not None and str(value).strip()
    }


def _resolve_entities_from_memory(
    message: str,
    *,
    previous_messages: list[Any] | None,
    workspace_context: dict | None = None,
) -> dict[str, str] | None:
    from app.domain.services.chat_product_query_intent_service import (
        ChatProductQueryIntentService,
    )
    from app.domain.services.chat_reference_resolution_service import (
        ChatReferenceResolutionService,
    )

    wm_entities = _working_memory_entities(workspace_context)
    params: dict[str, str] = dict(wm_entities)

    if ChatProductQueryIntentService.looks_like_scope_reset_operational_query(message):
        params.pop("productCode", None)

    if previous_messages:
        from app.domain.services.chat_conversation_memory_extractor import (
            ChatConversationMemoryExtractor,
        )

        snapshot = ChatConversationMemoryExtractor.enrich_snapshot(
            {},
            previous_messages=previous_messages,
        )
        resolved, _keys = ChatReferenceResolutionService.resolve_from_snapshot(
            message,
            snapshot,
        )

        for item in resolved:
            key = str(item.get("key") or "").strip()
            value = str(item.get("value") or "").strip()

            if key and value:
                params[key] = value

    code_in_message = ChatProductQueryIntentService.extract_product_code(message)
    code = ChatProductQueryIntentService.resolve_product_code(
        message,
        previous_messages=previous_messages,
    )

    if code and not code_in_message and ChatProductQueryIntentService.should_inherit_product_code(
        message
    ):
        params.setdefault("productCode", code)

    if params:
        return params

    if not code or code_in_message:
        return None

    if not ChatProductQueryIntentService.should_inherit_product_code(message):
        return None

    return {"productCode": code}


def _build_resolved_params(
    message: str,
    *,
    previous_messages: list[Any] | None,
    memory_entities: dict[str, str] | None,
    workspace_context: dict | None = None,
) -> dict[str, str] | None:
    from app.domain.services.chat_product_query_intent_service import (
        ChatProductQueryIntentService,
    )

    params: dict[str, str] = dict(_working_memory_entities(workspace_context))

    if memory_entities:
        params.update(memory_entities)

    code_in_message = ChatProductQueryIntentService.extract_product_code(message)

    if code_in_message:
        params["productCode"] = code_in_message

    return params or None


class ChatIntentRouterService:
    """Classifica intenção antes/durante o turno sem duplicar execução do pipeline."""

    _STAGE_INTENT: dict[str, tuple[str, str | None, int]] = {
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
        "meta_direct_answer": ("identity", "meta", 9),
        "unclear_request": ("clarification", "unclear", 9),
        "rag": ("rag_question", None, 8),
        "skip_rag": ("llm_general", "no_rag", 10),
        "web_save_sources": ("web_search", None, 7),
    }

    _SELF_HELP_PHRASES = (
        "o que você pode",
        "o que voce pode",
        "o que você faz",
        "o que voce faz",
        "o que consegue",
        "como uso você",
        "como uso voce",
        "como uso o chat",
        "quais consultas",
        "quais comandos",
        "quais ações",
        "quais acoes",
        "como anexo arquivo",
        "como uso a lousa",
        "como gero gráfico",
        "como gero grafico",
        "qual agente escolher",
        "como faço uma boa pergunta",
        "como faco uma boa pergunta",
        "você consegue corrigir texto",
        "voce consegue corrigir texto",
        "você consegue pesquisar na web",
        "voce consegue pesquisar na web",
    )

    _PRESENTATION_TERMS = (
        "mostre em tabela",
        "mostre em gráfico",
        "mostre em grafico",
        "em tabela",
        "em gráfico",
        "em grafico",
        "gere gráfico",
        "gere grafico",
        "em linha",
        "em pizza",
        "em rosca",
        "em barras",
        "mostre kpi",
        "mostre árvore",
        "mostre arvore",
        "transforme a tabela em gráfico",
        "exporte csv",
        "ver em gráfico",
        "ver em grafico",
    )

    _WEB_BLOCK_TERMS = (
        "não pesquise",
        "nao pesquise",
        "sem pesquisa na web",
        "sem pesquisa na internet",
        "não busque na web",
        "nao busque na web",
    )

    @classmethod
    def classify(
        cls,
        message: str,
        *,
        previous_messages: list[Any] | None = None,
        workspace_context: dict | None = None,
        attachment_ids: list[str] | None = None,
        allowed_action_ids: list[str] | None = None,
        text_task_pure: bool = False,
        text_task_category: str | None = None,
        analysis_mode: bool = False,
        operational_optimize: bool = False,
        canvas_operational_update: bool = False,
    ) -> IntentRouteResult:
        """Classificação pré-execução (prioridade Playbook 02)."""
        from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
        from app.domain.services.chat_canvas_intent_service import ChatCanvasIntentService
        from app.domain.services.chat_sql_safety_service import ChatSqlSafetyService
        from app.domain.services.chat_text_task_intent_service import ChatTextTaskIntentService

        history = previous_messages or []
        normalized = str(message or "").strip()

        if not normalized:
            return cls._with_decision(
                IntentRouteResult(
                    intent="llm_general",
                    confidence=0.3,
                    priority_applied=11,
                ),
                decision="llm_fallback",
                reason="empty_message",
            )

        from app.application.services.chat_active_pending_service import (
            ChatActivePendingService,
        )

        pending = ChatActivePendingService.find_from_messages(history)

        if pending:
            resolved = ChatActivePendingService.try_resolve(normalized, pending)

            if resolved:
                params = resolved.get("resolvedParams")

                return cls._with_decision(
                    IntentRouteResult(
                        intent="clarification",
                        sub_intent=str(pending.get("kind") or "pending"),
                        confidence=0.93,
                        requires_tool=bool(resolved.get("requiresTool")),
                        requires_rag=False,
                        requires_llm=False,
                        priority_applied=2,
                        resolved_params=dict(params) if isinstance(params, dict) else None,
                        flags=("active_pending_resolved", "clarification_answer"),
                    ),
                    decision="clarification_resume",
                    reason="active_pending_resolved",
                )

        if ChatSqlSafetyService.blocked_direct_answer(normalized):
            return cls._with_decision(
                IntentRouteResult(
                    intent="security",
                    sub_intent="sql_blocked",
                    confidence=0.99,
                    requires_llm=False,
                    priority_applied=1,
                    flags=("sql_safety",),
                ),
                decision="block_sql",
                reason="destructive_sql_blocked",
            )

        if attachment_ids and cls._looks_attachment_summary(normalized):
            return cls._with_decision(
                IntentRouteResult(
                    intent="attachment_task",
                    sub_intent="summary",
                    confidence=0.9,
                    requires_rag=True,
                    requires_llm=True,
                    priority_applied=7,
                    flags=("attachment_summary",),
                ),
                decision="attachment_summary",
                reason="summarize_attachment",
            )

        from app.domain.services.chat_drawing_intent_service import ChatDrawingIntentService

        if ChatDrawingIntentService.is_drawing_analysis_request(
            normalized,
            attachment_ids=attachment_ids,
        ):
            code = ChatDrawingIntentService.resolve_product_code(normalized)
            params = {"productCode": code} if code else None

            return cls._with_decision(
                IntentRouteResult(
                    intent="drawing_analysis",
                    sub_intent="pdf_api_validation",
                    confidence=0.94,
                    requires_tool=bool(code and allowed_action_ids),
                    requires_rag=bool(attachment_ids),
                    requires_llm=not bool(code),
                    priority_applied=5,
                    resolved_params=params,
                    flags=("drawing_analysis_delpi",),
                ),
                decision="drawing_analysis",
                reason="drawing_request",
            )

        from app.domain.services.chat_attachment_document_intent_service import (
            ChatAttachmentDocumentIntentService,
        )

        if (
            attachment_ids
            and ChatAttachmentDocumentIntentService.is_document_content_question(normalized)
        ):
            return cls._with_decision(
                IntentRouteResult(
                    intent="attachment_task",
                    sub_intent="read_content",
                    confidence=0.91,
                    requires_tool=False,
                    requires_rag=True,
                    requires_llm=True,
                    priority_applied=7,
                    flags=("attachment_document", "document_vision"),
                ),
                decision="attachment_read",
                reason="document_question_with_files",
            )

        if text_task_pure or ChatTextTaskIntentService.is_pure_text_task(
            normalized,
            previous_messages=history,
        ):
            sub = text_task_category or ChatTextTaskIntentService.classify(normalized)
            intent = "email_task" if sub == "email" else "text_task"

            return cls._with_decision(
                IntentRouteResult(
                    intent=intent,
                    sub_intent=sub,
                    confidence=0.92,
                    requires_tool=False,
                    requires_rag=False,
                    requires_llm=True,
                    priority_applied=3,
                    flags=("text_task_pure", "skip_tools"),
                ),
                decision="skip_tools",
                reason="explicit_text_task",
            )

        sql_sub = cls._sql_sub_intent(normalized)

        if sql_sub:
            execute = sql_sub == "sql_execute"

            return cls._with_decision(
                IntentRouteResult(
                    intent="sql_task",
                    sub_intent=sql_sub,
                    confidence=0.87,
                    requires_tool=execute,
                    requires_llm=True,
                    priority_applied=9,
                    flags=("sql_task",),
                ),
                decision="sql_route",
                reason=sql_sub,
            )

        compound_steps = cls._mixed_compound_steps(normalized)

        if compound_steps:
            return cls._with_decision(
                IntentRouteResult(
                    intent="mixed_task",
                    sub_intent="compound",
                    confidence=0.86,
                    requires_tool=True,
                    requires_rag="attachment_summary" in compound_steps,
                    requires_web="web_search" in compound_steps,
                    requires_llm=True,
                    priority_applied=3,
                    mixed_steps=compound_steps,
                    flags=("mixed_task", "mixed_compound"),
                ),
                decision="mixed_decompose",
                reason="compound_mixed_task",
            )

        if ChatTextTaskIntentService.is_mixed_text_and_operational(normalized):
            steps = cls._mixed_task_steps(normalized)

            return cls._with_decision(
                IntentRouteResult(
                    intent="mixed_task",
                    sub_intent="operational_then_text",
                    confidence=0.88,
                    requires_tool=True,
                    requires_rag=False,
                    requires_llm=True,
                    priority_applied=3,
                    mixed_steps=steps,
                    flags=("mixed_task",),
                ),
                decision="mixed_decompose",
                reason="operational_plus_text",
            )

        if ChatCanvasIntentService.is_canvas_request(normalized) or canvas_operational_update:
            return cls._with_decision(
                IntentRouteResult(
                    intent="canvas_task",
                    sub_intent="operational_update" if canvas_operational_update else "placement",
                    confidence=0.9,
                    requires_tool=canvas_operational_update,
                    requires_canvas=True,
                    requires_rag=False,
                    requires_llm=not canvas_operational_update,
                    priority_applied=4,
                ),
                decision="canvas_route",
                reason="canvas_request",
            )

        from app.domain.services.chat_presentation_format_refinement_service import (
            ChatPresentationFormatRefinementService,
        )

        if cls._looks_presentation(normalized) and not (
            ChatPresentationFormatRefinementService.looks_like_format_refinement(normalized)
        ):
            return cls._with_decision(
                IntentRouteResult(
                    intent="presentation_task",
                    sub_intent=cls._presentation_sub_intent(normalized),
                    confidence=0.86,
                    requires_tool=False,
                    requires_llm=True,
                    priority_applied=8,
                    flags=("presentation_task",),
                ),
                decision="presentation",
                reason="chart_or_table_request",
            )

        memory_entities = _resolve_entities_from_memory(
            normalized,
            previous_messages=history,
            workspace_context=workspace_context,
        )
        resolved_params = _build_resolved_params(
            normalized,
            previous_messages=history,
            memory_entities=memory_entities,
            workspace_context=workspace_context,
        )

        from app.domain.services.chat_follow_up_intent_service import ChatFollowUpIntentService

        is_follow_up = bool(memory_entities) or ChatFollowUpIntentService.is_operational_follow_up(
            normalized
        )

        from app.domain.services.chat_web_search_history_service import (
            ChatWebSearchHistoryService,
        )
        from app.domain.services.chat_web_search_source_follow_up_service import (
            ChatWebSearchSourceFollowUpService,
        )

        if history and ChatWebSearchHistoryService.has_recent_web_search(history):
            if ChatWebSearchSourceFollowUpService.is_list_sources_request(normalized):
                return cls._with_decision(
                    IntentRouteResult(
                        intent="follow_up",
                        sub_intent="web_list_sources",
                        is_follow_up=True,
                        confidence=0.92,
                        requires_tool=False,
                        requires_rag=False,
                        requires_llm=False,
                        priority_applied=5,
                    ),
                    decision="follow_up",
                    reason="web_search_list_sources",
                )

            if ChatWebSearchSourceFollowUpService.is_summarize_request(normalized):
                return cls._with_decision(
                    IntentRouteResult(
                        intent="follow_up",
                        sub_intent="web_summarize",
                        is_follow_up=True,
                        confidence=0.9,
                        requires_tool=False,
                        requires_rag=False,
                        requires_llm=False,
                        priority_applied=5,
                    ),
                    decision="follow_up",
                    reason="web_search_summarize",
                )

            if ChatWebSearchSourceFollowUpService.is_extract_params_request(normalized):
                return cls._with_decision(
                    IntentRouteResult(
                        intent="follow_up",
                        sub_intent="web_extract_params",
                        is_follow_up=True,
                        confidence=0.9,
                        requires_tool=False,
                        requires_rag=False,
                        requires_llm=False,
                        priority_applied=5,
                    ),
                    decision="follow_up",
                    reason="web_search_extract_params",
                )

            if ChatWebSearchSourceFollowUpService.is_compare_sources_request(normalized):
                return cls._with_decision(
                    IntentRouteResult(
                        intent="follow_up",
                        sub_intent="web_compare_sources",
                        is_follow_up=True,
                        confidence=0.9,
                        requires_tool=False,
                        requires_rag=False,
                        requires_llm=False,
                        priority_applied=5,
                    ),
                    decision="follow_up",
                    reason="web_search_compare_sources",
                )

        if history and ChatAnalysisIntentService.is_data_interpretation_request(normalized, history):
            return cls._with_decision(
                IntentRouteResult(
                    intent="follow_up",
                    sub_intent="data_interpretation",
                    is_follow_up=True,
                    confidence=0.9,
                    requires_tool=False,
                    requires_rag=False,
                    requires_llm=True,
                    priority_applied=5,
                    resolved_params=resolved_params,
                ),
                decision="follow_up",
                reason="data_interpretation",
            )

        if analysis_mode or ChatAnalysisIntentService.is_comparison_or_insight_request(normalized):
            return cls._with_decision(
                IntentRouteResult(
                    intent="operational_query",
                    sub_intent="analysis",
                    confidence=0.85,
                    requires_tool=True,
                    requires_rag=False,
                    requires_llm=True,
                    priority_applied=6,
                    flags=("analysis_mode",),
                    resolved_params=resolved_params,
                    is_follow_up=is_follow_up,
                ),
                decision="operational_action",
                reason="analysis_mode",
            )

        ambiguous, candidates = cls._operational_ambiguity(normalized, resolved_params)

        if operational_optimize or cls._looks_operational(normalized) or is_follow_up:
            sub = cls._operational_sub_intent(normalized)

            if is_follow_up and not sub:
                sub = ChatFollowUpIntentService.follow_up_type(normalized)
                sub = cls._map_follow_up_sub_intent(sub)

            return cls._with_decision(
                IntentRouteResult(
                    intent="operational_query",
                    sub_intent=sub,
                    is_follow_up=is_follow_up,
                    confidence=0.63 if ambiguous else 0.82,
                    requires_tool=bool(allowed_action_ids),
                    requires_rag=False,
                    requires_llm=False,
                    priority_applied=6,
                    resolved_params=resolved_params,
                    ambiguous=ambiguous,
                    candidates=candidates,
                ),
                decision="operational_action" if not ambiguous else "clarify_operational",
                reason="operational_keywords" if not ambiguous else "ambiguous_operational_scope",
            )

        if attachment_ids:
            return cls._with_decision(
                IntentRouteResult(
                    intent="attachment_task",
                    sub_intent="with_files",
                    confidence=0.8,
                    requires_tool=False,
                    requires_rag=True,
                    requires_llm=True,
                    priority_applied=7,
                ),
                decision="attachment_generic",
                reason="files_attached",
            )

        if not cls._blocks_web_search(normalized) and cls._looks_web_search(normalized):
            return cls._with_decision(
                IntentRouteResult(
                    intent="web_search",
                    confidence=0.9,
                    requires_web=True,
                    requires_tool=True,
                    requires_rag=False,
                    requires_llm=True,
                    priority_applied=7,
                    flags=("web_search_explicit",),
                ),
                decision="web_search",
                reason="explicit_web_request",
            )

        if cls._looks_rag_document(normalized):
            return cls._with_decision(
                IntentRouteResult(
                    intent="rag_question",
                    confidence=0.75,
                    requires_rag=True,
                    requires_llm=True,
                    priority_applied=8,
                    flags=("internal_document",),
                ),
                decision="rag_internal",
                reason="documental_wording",
            )

        if cls._looks_self_help(normalized):
            return cls._with_decision(
                IntentRouteResult(
                    intent="self_help",
                    sub_intent="capabilities_catalog",
                    confidence=0.88,
                    requires_llm=False,
                    priority_applied=10,
                    flags=("self_help", "capabilities_catalog"),
                ),
                decision="self_help",
                reason="capabilities_question",
            )

        if cls._looks_identity_question(normalized):
            return cls._with_decision(
                IntentRouteResult(
                    intent="identity",
                    confidence=0.88,
                    requires_llm=False,
                    priority_applied=10,
                ),
                decision="identity",
                reason="identity_question",
            )

        from app.application.services.chat_small_talk_service import ChatSmallTalkService

        if ChatSmallTalkService.is_small_talk(normalized):
            return cls._with_decision(
                IntentRouteResult(
                    intent="small_talk",
                    confidence=0.95,
                    requires_llm=False,
                    priority_applied=10,
                ),
                decision="small_talk",
                reason="greeting_or_thanks",
            )

        from app.application.services.chat_utility_direct_answer_service import (
            ChatUtilityDirectAnswerService,
        )

        if ChatUtilityDirectAnswerService.build_direct_answer(message=normalized):
            return cls._with_decision(
                IntentRouteResult(
                    intent="utility",
                    confidence=0.9,
                    requires_llm=False,
                    priority_applied=10,
                ),
                decision="utility_direct",
                reason="utility_pattern",
            )

        return cls._with_decision(
            IntentRouteResult(
                intent="llm_general",
                confidence=0.5,
                requires_rag=True,
                requires_llm=True,
                priority_applied=11,
                flags=("low_confidence_fallback",),
            ),
            decision="llm_fallback",
            reason="no_clear_intent",
        )

    @classmethod
    def resolve_executed(
        cls,
        *,
        message: str,
        pipeline_stages: list[str],
        previous_messages: list[Any] | None = None,
        workspace_context: dict | None = None,
        analysis_mode: bool = False,
        text_task_pure: bool = False,
        text_task_category: str | None = None,
        skip_rag: bool = False,
        direct_answer: str | None = None,
        tool_calls: list | None = None,
        attachment_ids: list[str] | None = None,
        allowed_action_ids: list[str] | None = None,
    ) -> IntentRouteResult:
        """Intenção efetiva após o turn prep (estágios reais do pipeline)."""
        stages = list(pipeline_stages or [])
        predicted = cls.classify(
            message,
            previous_messages=previous_messages,
            workspace_context=workspace_context,
            attachment_ids=attachment_ids,
            allowed_action_ids=allowed_action_ids,
            text_task_pure=text_task_pure,
            text_task_category=text_task_category,
            analysis_mode=analysis_mode,
        )

        web_executed = cls._tool_calls_include_web(tool_calls)

        best: IntentRouteResult | None = None

        for stage in stages:
            if stage.startswith("intent:"):
                continue

            if stage == "tools" and not tool_calls:
                if predicted.intent in {"attachment_document", "attachment_task"}:
                    continue

            mapping = cls._STAGE_INTENT.get(stage)

            if not mapping:
                continue

            intent, sub_intent, priority = mapping
            flags: list[str] = [f"stage:{stage}"]

            if stage == "tools" and tool_calls:
                flags.append("tools_executed")

            requires_web = web_executed or predicted.requires_web
            requires_canvas = predicted.requires_canvas or stage == "canvas"

            candidate = IntentRouteResult(
                intent=intent,
                sub_intent=sub_intent or predicted.sub_intent,
                is_follow_up=predicted.is_follow_up,
                confidence=max(predicted.confidence, 0.85),
                requires_tool=bool(tool_calls) or predicted.requires_tool,
                requires_rag=not skip_rag and stage == "rag",
                requires_web=requires_web,
                requires_canvas=requires_canvas,
                requires_llm=not bool(direct_answer)
                or stage
                not in (
                    "small_talk",
                    "utility_direct",
                    "capabilities",
                    "text_task",
                    "unclear_request",
                ),
                priority_applied=priority,
                flags=tuple(flags),
                resolved_params=predicted.resolved_params,
                ambiguous=predicted.ambiguous,
                candidates=predicted.candidates,
                mixed_steps=predicted.mixed_steps,
                decision=predicted.decision,
                reason=predicted.reason,
            )

            if best is None or priority < best.priority_applied:
                best = candidate

        if web_executed and (best is None or best.priority_applied > 7):
            best = cls._with_decision(
                IntentRouteResult(
                    intent="web_search",
                    confidence=0.9,
                    requires_web=True,
                    requires_tool=True,
                    requires_rag=False,
                    requires_llm=not bool(direct_answer),
                    priority_applied=7,
                    flags=("web_search_executed",),
                    resolved_params=predicted.resolved_params,
                ),
                decision="web_search",
                reason="web_search_tool_executed",
            )

        if text_task_pure and (best is None or best.priority_applied > 3):
            sub = text_task_category or predicted.sub_intent
            intent = "email_task" if sub == "email" else "text_task"

            return cls._with_decision(
                IntentRouteResult(
                    intent=intent,
                    sub_intent=sub,
                    confidence=0.9,
                    requires_rag=False,
                    requires_llm=True,
                    priority_applied=3,
                    flags=("text_task_pure", "skip_tools"),
                    resolved_params=predicted.resolved_params,
                ),
                decision="skip_tools",
                reason="explicit_text_task",
            )

        if best is not None:
            return cls._with_decision(best, decision=best.decision, reason=best.reason)

        return predicted

    @classmethod
    def build_fallback_prompt(cls) -> str:
        return (
            "Posso ajudar de algumas formas. Você quer:\n"
            "- corrigir ou escrever um texto;\n"
            "- consultar dados operacionais;\n"
            "- usar um arquivo ou documentação interna;\n"
            "- pesquisar na web;\n"
            "- colocar algo na lousa?"
        )

    @staticmethod
    def _with_decision(
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
    def _tool_calls_include_web(tool_calls: list | None) -> bool:
        for call in tool_calls or []:
            if not isinstance(call, dict):
                continue

            name = str(call.get("name") or call.get("tool") or "").strip().lower()

            if name == "web_search":
                return True

        return False

    @staticmethod
    def _mixed_compound_steps(message: str) -> tuple[str, ...] | None:
        lowered = message.lower()
        steps: list[str] = []

        has_web = any(
            term in lowered
            for term in (
                "pesquise na web",
                "pesquisa na web",
                "na internet",
                "busque na web",
            )
        )
        has_report = any(
            term in lowered for term in ("relatório", "relatorio", "resumo executivo", "report")
        )

        if has_web and has_report:
            steps.extend(["web_search", "report_compose"])

        has_attachment = any(
            term in lowered
            for term in ("resuma o pdf", "resuma esse pdf", "resuma o anexo", "resuma o arquivo")
        )
        has_canvas = any(term in lowered for term in ("lousa", "canvas"))

        if has_attachment and has_canvas:
            steps.extend(["attachment_summary", "canvas_placement"])

        has_table = "tabela" in lowered or "em tabela" in lowered
        has_chart = any(term in lowered for term in ("gráfico", "grafico", "em pizza", "em barras"))

        if has_table and has_chart:
            steps.extend(["presentation_table", "presentation_chart"])

        if len(steps) < 2:
            return None

        return tuple(steps)

    @staticmethod
    def _mixed_task_steps(message: str) -> tuple[str, ...]:
        steps: list[str] = []
        sub = ChatIntentRouterService._operational_sub_intent(message)

        if sub:
            steps.append(sub)
        else:
            steps.append("operational_lookup")

        from app.domain.services.chat_text_task_intent_service import ChatTextTaskIntentService

        category = ChatTextTaskIntentService.classify(message)

        if category == "email":
            steps.append("email_create")
        else:
            steps.append("text_compose")

        return tuple(steps)

    @staticmethod
    def _map_follow_up_sub_intent(follow_type: str | None) -> str | None:
        mapping = {
            "supplier": "supplier_lookup",
            "stock": "stock_lookup",
            "structure": "structure_lookup",
            "routing": "guide_lookup",
            "outbound_invoice": "sales_lookup",
        }

        return mapping.get(follow_type or "")

    @staticmethod
    def _looks_attachment_summary(message: str) -> bool:
        lowered = message.lower()

        return any(
            term in lowered
            for term in (
                "resuma esse pdf",
                "resuma o pdf",
                "resuma esse arquivo",
                "resuma o anexo",
                "resumir o pdf",
                "resumir esse documento",
            )
        )

    @staticmethod
    def _blocks_web_search(message: str) -> bool:
        lowered = message.lower()

        return any(term in lowered for term in ChatIntentRouterService._WEB_BLOCK_TERMS)

    @staticmethod
    def _looks_web_search(message: str) -> bool:
        from app.domain.services.chat_web_search_intent_service import ChatWebSearchIntentService

        if ChatWebSearchIntentService.matches(message):
            return True

        lowered = message.lower()

        return any(
            phrase in lowered
            for phrase in (
                "pesquise na web",
                "pesquisa na web",
                "procure na internet",
                "busque fonte oficial",
                "busque no site",
                "notícias recentes",
                "noticias recentes",
                "procure datasheet",
                "compare fontes externas",
                "veja fontes externas",
            )
        )

    @staticmethod
    def _sql_sub_intent(message: str) -> str | None:
        from app.domain.services.chat_sql_intent_service import ChatSqlIntentService

        return ChatSqlIntentService.router_sub_intent(message)

    @staticmethod
    def _looks_presentation(message: str) -> bool:
        lowered = message.lower()

        return any(term in lowered for term in ChatIntentRouterService._PRESENTATION_TERMS)

    @staticmethod
    def _presentation_sub_intent(message: str) -> str | None:
        lowered = message.lower()

        if "tabela" in lowered:
            return "table"

        if any(term in lowered for term in ("pizza", "rosca", "barras", "linha", "gráfico", "grafico")):
            return "chart"

        if "kpi" in lowered:
            return "kpi"

        if "árvore" in lowered or "arvore" in lowered:
            return "tree"

        return "presentation"

    @staticmethod
    def _operational_ambiguity(
        message: str,
        resolved_params: dict[str, str] | None,
    ) -> tuple[bool, tuple[str, ...]]:
        from app.domain.services.chat_product_query_intent_service import (
            ChatProductQueryIntentService,
        )

        code = (resolved_params or {}).get("productCode") or ChatProductQueryIntentService.extract_product_code(
            message
        )

        if not code:
            return False, ()

        lowered = message.lower()

        sub_intent = ChatIntentRouterService._operational_sub_intent(message)

        if sub_intent and sub_intent != "product_lookup":
            return False, ()

        if sub_intent == "product_lookup" and any(
            term in lowered
            for term in (
                "me fale",
                "fale do",
                "fale sobre",
                "informacoes sobre",
                "informações sobre",
                "dados do produto",
                "cadastro",
                "ficha",
                "resumo do produto",
            )
        ):
            return False, ()

        if (
            any(
                term in lowered
                for term in (
                    "estoque",
                    "fornecedor",
                    "venda",
                    "compra",
                    "estrutura",
                    "roteiro",
                    "inspeção",
                    "inspecao",
                    "preço",
                    "preco",
                )
            )
            or ChatIntentRouterService._mentions_supplier(lowered)
            or ChatIntentRouterService._mentions_outbound_invoice(lowered)
        ):
            return False, ()

        if "produto" not in lowered and code not in message:
            return False, ()

        candidates = (
            "product_lookup",
            "stock_lookup",
            "supplier_lookup",
            "structure_lookup",
            "sales_lookup",
            "purchase_lookup",
        )

        return True, candidates

    @staticmethod
    def _mentions_supplier(lowered: str) -> bool:
        return "fornecedor" in lowered or bool(re.search(r"\bfornece", lowered))

    @staticmethod
    def _mentions_outbound_invoice(lowered: str) -> bool:
        if any(
            term in lowered
            for term in (
                "notas fiscais de entrada",
                "nota de entrada",
                "notas de entrada",
            )
        ):
            return False

        if any(
            term in lowered
            for term in (
                "notas fiscais de saída",
                "notas fiscais de saida",
                "nota fiscal de saída",
                "nota fiscal de saida",
                "notas de saída",
                "notas de saida",
                "nota de saída",
                "nota de saida",
                "nf de saída",
                "nf de saida",
                "nfe de saída",
                "nfe de saida",
            )
        ):
            return True

        if "notas fiscais" in lowered and (
            "saída" in lowered or "saida" in lowered or "venda" in lowered
        ):
            return True

        return bool(re.search(r"\bnf(?:e)?\b", lowered)) and (
            "saída" in lowered or "saida" in lowered
        )

    @staticmethod
    def _looks_operational(message: str) -> bool:
        lowered = message.lower()

        return any(
            term in lowered
            for term in (
                "estoque",
                "produto",
                "fornecedor",
                "fornece",
                "roteiro",
                "estrutura",
                "inspeção",
                "inspecao",
                "venda",
                "faturamento",
                "pedido",
                "ov ",
                "compra",
                "filial",
                "armazém",
                "armazem",
                "preço",
                "preco",
                "saldo",
                "bom",
                "where used",
                "componentes",
                "protheus",
            )
        )

    @staticmethod
    def _operational_sub_intent(message: str) -> str | None:
        lowered = message.lower()

        if "estoque" in lowered:
            return "stock_lookup"

        if ChatIntentRouterService._mentions_outbound_invoice(lowered):
            return "sales_lookup"

        if any(
            term in lowered
            for term in (
                "vendas do produto",
                "venda do produto",
                "mostre vendas",
                "mostra vendas",
                "resumo de vendas",
            )
        ) or ("vendas" in lowered and "produto" in lowered and "estoque" not in lowered):
            return "sales_lookup"

        if "compra" in lowered:
            return "purchase_lookup"

        if ChatIntentRouterService._mentions_supplier(lowered):
            return "supplier_lookup"

        if "preço" in lowered or "preco" in lowered:
            return "price_lookup"

        if any(term in lowered for term in ("estrutura", "bom")):
            return "structure_lookup"

        if any(term in lowered for term in ("roteiro",)):
            return "guide_lookup"

        if any(term in lowered for term in ("inspeção", "inspecao")):
            return "inspection_lookup"

        if any(term in lowered for term in ("estrutura", "roteiro", "inspeção", "inspecao")):
            return "structure_lookup"

        if any(term in lowered for term in ("onde", "usado", "pais", "parents", "where used")):
            return "parents_lookup"

        if any(
            term in lowered
            for term in (
                "tabela",
                "tabelas",
                "coluna",
                "colunas",
                "protheus",
                "sx2",
                "sx3",
                "metadado",
            )
        ) and (
            "qual a tabela" in lowered
            or "qual tabela" in lowered
            or "buscar tabela" in lowered
            or "pesquisar tabela" in lowered
            or "schema da tabela" in lowered
        ):
            return "system_metadata"

        if "produto" in lowered:
            return "product_lookup"

        return None

    @staticmethod
    def _looks_rag_document(message: str) -> bool:
        lowered = message.lower()

        return any(
            term in lowered
            for term in (
                "documento",
                "norma",
                "procedimento",
                "política",
                "politica",
                "manual",
                "regulamento",
                "conformidade",
                "documentação interna",
                "documentacao interna",
                "base de conhecimento",
                "segundo o documento",
                "o que diz a norma",
            )
        )

    @classmethod
    def _looks_self_help(cls, message: str) -> bool:
        lowered = message.lower()

        return any(phrase in lowered for phrase in cls._SELF_HELP_PHRASES)

    @staticmethod
    def _looks_identity_question(message: str) -> bool:
        from app.application.services.chat_assistant_identity_service import (
            ChatAssistantIdentityService,
        )

        return ChatAssistantIdentityService.is_assistant_identity_question(message)

    @staticmethod
    def _looks_capabilities_question(message: str) -> bool:
        """Compatibilidade com chamadas legadas."""
        return ChatIntentRouterService._looks_self_help(message)
