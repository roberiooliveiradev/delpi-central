"""Métricas de inteligência e tokens — conclusão de turno."""

from __future__ import annotations

import time

from app.application.services.chat_intelligence_metadata_service import (
    ChatIntelligenceMetadataService,
)
from app.application.services.chat_turn.chat_turn_completion_models import (
    ChatTurnCompletionInput,
)
from app.infrastructure.llm.llm_request_context import get_active_config, get_active_llm_provider


class ChatTurnCompletionIntelligenceService:
    @classmethod
    def build_block(
        cls,
        turn: ChatTurnCompletionInput,
        *,
        answer: str,
        tool_calls: list,
    ) -> tuple[dict, int, dict]:
        prepared_rag = getattr(turn.prepared, "rag", None)

        intelligence_metadata = ChatIntelligenceMetadataService.build(
            sources=turn.sources,
            tool_context=turn.tool_context,
            embedding_cache_stats=cls.embedding_cache_stats(),
            pipeline_timings=turn.pipeline_timings.to_dict(),
            rag_stats=prepared_rag if isinstance(prepared_rag, dict) else None,
            pipeline=ChatIntelligenceMetadataService.build_pipeline_flags(
                fast_path=turn.fast_path,
                operational_optimize=turn.operational_optimize,
                tool_context=turn.tool_context,
                skip_rag=turn.skip_rag,
                analysis_mode=turn.analysis_mode,
                stages=turn.pipeline_stages,
                direct_answer=turn.direct_answer,
            ),
        )
        latency_ms = int((time.perf_counter() - turn.started_at) * 1000)
        prompt_tokens_estimated = cls.estimate_tokens_from_messages(turn.llm_messages)
        completion_tokens_estimated = cls.estimate_tokens(answer)
        total_tokens_estimated = prompt_tokens_estimated + completion_tokens_estimated
        estimated_cost = cls.estimate_cost(
            prompt_tokens=prompt_tokens_estimated,
            completion_tokens=completion_tokens_estimated,
        )

        return (
            intelligence_metadata,
            latency_ms,
            {
                "prompt_tokens_estimated": prompt_tokens_estimated,
                "completion_tokens_estimated": completion_tokens_estimated,
                "total_tokens_estimated": total_tokens_estimated,
                "estimated_cost": estimated_cost,
            },
        )

    @staticmethod
    def embedding_cache_stats() -> dict | None:
        try:
            from app.composition.external_action_composer import get_embedding_cache_stats

            return get_embedding_cache_stats()
        except Exception:
            return None

    @classmethod
    def estimate_cost(cls, *, prompt_tokens: int, completion_tokens: int) -> float | None:
        try:
            from app.application.services.llm_cost_estimator_service import (
                LlmCostEstimatorService,
            )

            active = get_active_config()

            return LlmCostEstimatorService().estimate_cost(
                provider=get_active_llm_provider(),
                model=active.model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )
        except Exception:
            return None

    @classmethod
    def estimate_tokens_from_messages(cls, messages: list[dict]) -> int:
        total = 0

        for item in messages:
            if isinstance(item, dict):
                total += cls.estimate_tokens(str(item.get("content") or ""))

        return total

    @staticmethod
    def estimate_tokens(value: str) -> int:
        normalized = str(value or "").strip()

        if not normalized:
            return 0

        return max(1, round(len(normalized) / 4))
