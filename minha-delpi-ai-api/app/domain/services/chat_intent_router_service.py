"""Roteamento de intenção do turno — Playbook 01 (chat base, observabilidade + prioridade)."""

from __future__ import annotations

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
    requires_llm: bool = True
    priority_applied: int = 0
    flags: tuple[str, ...] = ()
    resolved_from_memory: dict[str, str] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "intent": self.intent,
            "isFollowUp": self.is_follow_up,
            "confidence": round(self.confidence, 2),
            "requiresTool": self.requires_tool,
            "requiresRag": self.requires_rag,
            "requiresLlm": self.requires_llm,
            "priorityApplied": self.priority_applied,
        }

        if self.sub_intent:
            payload["subIntent"] = self.sub_intent

        if self.flags:
            payload["flags"] = list(self.flags)

        if self.resolved_from_memory:
            payload["resolvedFromMemory"] = dict(self.resolved_from_memory)

        return payload


def _resolve_entities_from_memory(
    message: str,
    *,
    previous_messages: list[Any] | None,
) -> dict[str, str] | None:
    from app.domain.services.chat_product_query_intent_service import (
        ChatProductQueryIntentService,
    )

    code_in_message = ChatProductQueryIntentService.extract_product_code(message)
    code = ChatProductQueryIntentService.resolve_product_code(
        message,
        previous_messages=previous_messages,
    )

    if not code or code_in_message:
        return None

    if not ChatProductQueryIntentService.references_previous_product(message):
        return None

    return {"productCode": code}


class ChatIntentRouterService:
    """Classifica intenção antes/durante o turno sem duplicar execução do pipeline."""

    _STAGE_INTENT: dict[str, tuple[str, str | None, int]] = {
        "text_task": ("text_task", None, 3),
        "text_task_mixed": ("text_task", "mixed_operational", 3),
        "canvas": ("canvas_task", None, 4),
        "data_interpretation": ("follow_up", "data_interpretation", 5),
        "data_interpretation_empty": ("follow_up", "data_interpretation_empty", 5),
        "operational_parameter": ("clarification", "missing_params", 2),
        "tools": ("operational_query", None, 6),
        "capabilities": ("capabilities", None, 9),
        "small_talk": ("small_talk", None, 9),
        "utility_direct": ("utility", None, 9),
        "attachment_welcome": ("attachment_task", "welcome", 7),
        "identity_shortcut": ("identity", "user_profile", 9),
        "meta_direct_answer": ("identity", "meta", 9),
        "rag": ("rag_question", None, 8),
        "skip_rag": ("llm_general", "no_rag", 10),
    }

    @classmethod
    def classify(
        cls,
        message: str,
        *,
        previous_messages: list[Any] | None = None,
        attachment_ids: list[str] | None = None,
        allowed_action_ids: list[str] | None = None,
        text_task_pure: bool = False,
        text_task_category: str | None = None,
        analysis_mode: bool = False,
        operational_optimize: bool = False,
        canvas_operational_update: bool = False,
    ) -> IntentRouteResult:
        """Classificação pré-execução (prioridade do Playbook 01)."""
        from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
        from app.domain.services.chat_canvas_intent_service import ChatCanvasIntentService
        from app.domain.services.chat_sql_safety_service import ChatSqlSafetyService
        from app.domain.services.chat_text_task_intent_service import ChatTextTaskIntentService

        history = previous_messages or []
        normalized = str(message or "").strip()

        if not normalized:
            return IntentRouteResult(
                intent="llm_general",
                confidence=0.3,
                priority_applied=10,
            )

        if ChatSqlSafetyService.blocked_direct_answer(normalized):
            return IntentRouteResult(
                intent="security",
                sub_intent="sql_blocked",
                confidence=0.99,
                requires_llm=False,
                priority_applied=1,
                flags=("sql_safety",),
            )

        if text_task_pure or ChatTextTaskIntentService.is_pure_text_task(
            normalized,
            previous_messages=history,
        ):
            return IntentRouteResult(
                intent="text_task",
                sub_intent=text_task_category or ChatTextTaskIntentService.classify(normalized),
                confidence=0.92,
                requires_tool=False,
                requires_rag=False,
                requires_llm=True,
                priority_applied=3,
                flags=("text_task_pure",),
            )

        if ChatTextTaskIntentService.is_mixed_text_and_operational(normalized):
            return IntentRouteResult(
                intent="text_task",
                sub_intent="mixed_operational",
                confidence=0.88,
                requires_tool=True,
                requires_rag=False,
                requires_llm=True,
                priority_applied=3,
                flags=("text_task_mixed",),
            )

        if ChatCanvasIntentService.is_canvas_request(normalized) or canvas_operational_update:
            return IntentRouteResult(
                intent="canvas_task",
                sub_intent="operational_update" if canvas_operational_update else "placement",
                confidence=0.9,
                requires_tool=canvas_operational_update,
                requires_rag=False,
                requires_llm=not canvas_operational_update,
                priority_applied=4,
            )

        if history and ChatAnalysisIntentService.is_data_interpretation_request(
            normalized,
            history,
        ):
            return IntentRouteResult(
                intent="follow_up",
                sub_intent="data_interpretation",
                is_follow_up=True,
                confidence=0.9,
                requires_tool=False,
                requires_rag=False,
                requires_llm=True,
                priority_applied=5,
            )

        if analysis_mode or ChatAnalysisIntentService.is_comparison_or_insight_request(
            normalized
        ):
            return IntentRouteResult(
                intent="operational_query",
                sub_intent="analysis",
                confidence=0.85,
                requires_tool=True,
                requires_rag=False,
                requires_llm=True,
                priority_applied=6,
                flags=("analysis_mode",),
            )

        memory_entities = _resolve_entities_from_memory(
            normalized,
            previous_messages=history,
        )

        if operational_optimize or cls._looks_operational(normalized):
            return IntentRouteResult(
                intent="operational_query",
                sub_intent=cls._operational_sub_intent(normalized),
                is_follow_up=bool(memory_entities),
                confidence=0.82,
                requires_tool=bool(allowed_action_ids),
                requires_rag=False,
                requires_llm=False,
                priority_applied=6,
                resolved_from_memory=memory_entities,
            )

        if attachment_ids:
            return IntentRouteResult(
                intent="attachment_task",
                sub_intent="with_files",
                confidence=0.8,
                requires_tool=False,
                requires_rag=True,
                requires_llm=True,
                priority_applied=7,
            )

        if cls._looks_rag_document(normalized):
            return IntentRouteResult(
                intent="rag_question",
                confidence=0.75,
                requires_rag=True,
                requires_llm=True,
                priority_applied=8,
            )

        if cls._looks_capabilities_question(normalized):
            return IntentRouteResult(
                intent="capabilities",
                confidence=0.88,
                requires_llm=False,
                priority_applied=9,
            )

        if cls._looks_identity_question(normalized):
            return IntentRouteResult(
                intent="identity",
                confidence=0.88,
                requires_llm=False,
                priority_applied=9,
            )

        from app.application.services.chat_small_talk_service import ChatSmallTalkService

        if ChatSmallTalkService.is_small_talk(normalized):
            return IntentRouteResult(
                intent="small_talk",
                confidence=0.95,
                requires_llm=False,
                priority_applied=9,
            )

        from app.application.services.chat_utility_direct_answer_service import (
            ChatUtilityDirectAnswerService,
        )

        if ChatUtilityDirectAnswerService.build_direct_answer(message=normalized):
            return IntentRouteResult(
                intent="utility",
                confidence=0.9,
                requires_llm=False,
                priority_applied=9,
            )

        return IntentRouteResult(
            intent="llm_general",
            confidence=0.5,
            requires_rag=True,
            requires_llm=True,
            priority_applied=10,
        )

    @classmethod
    def resolve_executed(
        cls,
        *,
        message: str,
        pipeline_stages: list[str],
        analysis_mode: bool = False,
        text_task_pure: bool = False,
        text_task_category: str | None = None,
        skip_rag: bool = False,
        direct_answer: str | None = None,
        tool_calls: list | None = None,
    ) -> IntentRouteResult:
        """Intenção efetiva após o turn prep (estágios reais do pipeline)."""
        stages = list(pipeline_stages or [])
        predicted = cls.classify(
            message,
            text_task_pure=text_task_pure,
            text_task_category=text_task_category,
            analysis_mode=analysis_mode,
        )

        best: IntentRouteResult | None = None

        for stage in stages:
            if stage.startswith("intent:"):
                continue

            mapping = cls._STAGE_INTENT.get(stage)

            if not mapping:
                continue

            intent, sub_intent, priority = mapping
            flags: list[str] = [f"stage:{stage}"]

            if stage == "tools" and tool_calls:
                flags.append("tools_executed")

            candidate = IntentRouteResult(
                intent=intent,
                sub_intent=sub_intent or predicted.sub_intent,
                is_follow_up=predicted.is_follow_up,
                confidence=max(predicted.confidence, 0.85),
                requires_tool=bool(tool_calls) or predicted.requires_tool,
                requires_rag=not skip_rag and stage == "rag",
                requires_llm=not bool(direct_answer)
                or stage
                not in (
                    "small_talk",
                    "utility_direct",
                    "capabilities",
                    "text_task",
                ),
                priority_applied=priority,
                flags=tuple(flags),
                resolved_from_memory=predicted.resolved_from_memory,
            )

            if best is None or priority < best.priority_applied:
                best = candidate

        if text_task_pure and (best is None or best.priority_applied > 3):
            return IntentRouteResult(
                intent="text_task",
                sub_intent=text_task_category,
                confidence=0.9,
                requires_rag=False,
                priority_applied=3,
                flags=("text_task_pure",),
            )

        if best is not None:
            return best

        return predicted

    @staticmethod
    def _looks_operational(message: str) -> bool:
        lowered = message.lower()

        return any(
            term in lowered
            for term in (
                "estoque",
                "produto",
                "fornecedor",
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
            )
        )

    @staticmethod
    def _operational_sub_intent(message: str) -> str | None:
        lowered = message.lower()

        if "estoque" in lowered:
            return "stock_lookup"

        if any(
            term in lowered
            for term in (
                "vendas do produto",
                "venda do produto",
                "mostre vendas",
                "mostra vendas",
                "resumo de vendas",
            )
        ) or (
            "vendas" in lowered
            and "produto" in lowered
            and "estoque" not in lowered
        ):
            return "sales_lookup"

        if "fornecedor" in lowered:
            return "supplier_lookup"

        if any(term in lowered for term in ("estrutura", "roteiro", "inspeção", "inspecao")):
            return "structure_lookup"

        if any(term in lowered for term in ("onde", "usado", "pais", "parents")):
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
            )
        )

    @staticmethod
    def _looks_capabilities_question(message: str) -> bool:
        lowered = message.lower()

        return any(
            phrase in lowered
            for phrase in (
                "o que você pode",
                "o que voce pode",
                "o que consegue",
                "quais consultas",
                "quais ações",
                "quais acoes",
            )
        )

    @staticmethod
    def _looks_identity_question(message: str) -> bool:
        from app.application.services.chat_assistant_identity_service import (
            ChatAssistantIdentityService,
        )

        return ChatAssistantIdentityService.is_assistant_identity_question(message)
