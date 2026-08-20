"""Orçamento de latência por responseMode — degrada estágios opcionais."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_operational_narrative_synthesis_service import (
    ChatOperationalNarrativeSynthesisService,
)
from app.domain.services.chat_response_mode_content_service import (
    ChatResponseModeContentService,
)
from app.domain.services.chat_response_mode_service import ChatResponseModeService


class ChatLatencyBudgetService:
    """Decide skip de RAG documental opcional e lookback reduzido de message search."""

    TOOL_CONTEXT_DEGRADED_KEY = "degradedStages"

    @classmethod
    def _degradation_node(cls) -> dict[str, Any]:
        node = ChatAssistantContentService.get_node("response_modes", "latencyDegradation")

        return node if isinstance(node, dict) else {}

    @classmethod
    def latency_target_sec(cls, response_mode: str | None, *, default: int = 5) -> int:
        mode = ChatResponseModeService.normalize(response_mode)

        return ChatResponseModeContentService.latency_target_sec(mode, default=default)

    @classmethod
    def exceeds_target(
        cls,
        elapsed_sec: float,
        response_mode: str | None,
        *,
        default_target: int = 5,
    ) -> bool:
        target = float(cls.latency_target_sec(response_mode, default=default_target))

        return float(elapsed_sec or 0.0) > target

    @classmethod
    def message_search_lookback_factor(cls) -> float:
        raw = cls._degradation_node().get("messageSearchLookbackFactor")

        try:
            value = float(raw)
        except (TypeError, ValueError):
            value = 0.5

        return min(1.0, max(0.1, value))

    @classmethod
    def min_message_search_lookback(cls) -> int:
        raw = cls._degradation_node().get("minMessageSearchLookback")

        try:
            return max(1, int(raw))
        except (TypeError, ValueError):
            return 10

    @classmethod
    def stage_name(cls, key: str, *, default: str) -> str:
        stages = cls._degradation_node().get("stages")

        if isinstance(stages, dict):
            token = str(stages.get(key) or "").strip()

            if token:
                return token

        return default

    @classmethod
    def degraded_stages_from(cls, tool_context: dict | None) -> list[str]:
        if not isinstance(tool_context, dict):
            return []

        raw = tool_context.get(cls.TOOL_CONTEXT_DEGRADED_KEY)

        if not isinstance(raw, list):
            return []

        return [str(item).strip() for item in raw if str(item).strip()]

    @classmethod
    def append_degraded_stage(cls, tool_context: dict | None, stage: str) -> list[str]:
        stages = list(cls.degraded_stages_from(tool_context))
        token = str(stage or "").strip()

        if token and token not in stages:
            stages.append(token)

        if isinstance(tool_context, dict):
            tool_context[cls.TOOL_CONTEXT_DEGRADED_KEY] = stages

        return stages

    @classmethod
    def resolve_message_search_lookback(
        cls,
        base_lookback: int,
        *,
        degraded_stages: list[str] | None = None,
    ) -> int:
        stages = [str(item).strip() for item in (degraded_stages or []) if str(item).strip()]
        message_stage = cls.stage_name("messageSearch", default="message_search")

        if message_stage not in stages:
            return max(1, int(base_lookback))

        reduced = int(float(base_lookback) * cls.message_search_lookback_factor())

        return max(cls.min_message_search_lookback(), reduced)

    @classmethod
    def maybe_skip_optional_documentary_rag(
        cls,
        *,
        skip_rag: bool,
        elapsed_sec: float,
        response_mode: str | None,
        tool_context: dict | None,
        requires_documentary_rag: bool,
    ) -> tuple[bool, str | None]:
        """Pula RAG documental opcional se o prep já estourou o alvo do modo.

        Não degrada quando RAG é obrigatório nem quando há resultados de tool
        em síntese LLM que mantiveram RAG de propósito.
        """

        if skip_rag:
            return True, None

        if not cls.exceeds_target(elapsed_sec, response_mode):
            return False, None

        if requires_documentary_rag:
            return False, None

        if cls._tool_results_need_synthesis(tool_context):
            return False, None

        stage = cls.stage_name("rag", default="rag")

        return True, stage

    @classmethod
    def maybe_mark_message_search_degraded(
        cls,
        *,
        elapsed_sec: float,
        response_mode: str | None,
        tool_context: dict | None,
    ) -> str | None:
        if not cls.exceeds_target(elapsed_sec, response_mode):
            return None

        stage = cls.stage_name("messageSearch", default="message_search")
        cls.append_degraded_stage(tool_context, stage)

        return stage

    @classmethod
    def _tool_results_need_synthesis(cls, tool_context: dict | None) -> bool:
        if not isinstance(tool_context, dict):
            return False

        effect = str(tool_context.get("responseModeEffect") or "").strip()

        if not ChatOperationalNarrativeSynthesisService.is_llm_synthesis_effect(effect):
            return False

        tool_calls = tool_context.get("toolCalls") or []

        if not isinstance(tool_calls, list) or not tool_calls:
            return False

        # Síntese com fatos de tool e RAG ainda habilitado: não cortar documental.
        return not bool(tool_context.get("directAnswer"))
