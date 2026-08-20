"""Busca mensagens da sessão para refrescar contexto (correção / ordens / clip)."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_follow_up_intent_service import ChatFollowUpIntentService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_response_mode_context_budget_service import (
    ChatResponseModeContextBudgetService,
)


class ChatConversationMessageSearchService:
    _BUNDLE = "conversation_message_search"

    @classmethod
    def should_search(
        cls,
        message: str | None,
        *,
        history_clipped: bool = False,
        context_refresh_suggested: bool = False,
    ) -> bool:
        if context_refresh_suggested:
            return True

        if ChatFollowUpIntentService.is_retry_or_continue_request(message):
            return True

        normalized = ChatMessageNormalizationService.normalize_for_matching(
            message or "",
        )
        if not normalized:
            return False

        for token in cls._explicit_triggers():
            if token and token in normalized:
                return True

        if history_clipped and ChatFollowUpIntentService.is_operational_follow_up(
            message
        ):
            return True

        # Correções típicas («não é X, é Y», «eu pedi em tabela»).
        if re.search(
            r"\b(n[aã]o\s+[eé]\b|eu\s+pedi|como\s+pedi|em\s+vez\s+de|corrija)\b",
            normalized,
        ):
            return True

        return False

    @classmethod
    def search(
        cls,
        *,
        message: str | None,
        previous_messages: list[Any] | None,
        response_mode: str | None = None,
        history_clipped: bool = False,
        context_refresh_suggested: bool = False,
        degraded_stages: list[str] | None = None,
    ) -> dict[str, Any]:
        from app.domain.services.chat_latency_budget_service import (
            ChatLatencyBudgetService,
        )

        budget = ChatResponseModeContextBudgetService.resolve(response_mode)
        lookback_limit = ChatLatencyBudgetService.resolve_message_search_lookback(
            budget.message_search_lookback_messages,
            degraded_stages=degraded_stages,
        )
        triggered = cls.should_search(
            message,
            history_clipped=history_clipped,
            context_refresh_suggested=context_refresh_suggested,
        )

        if not triggered:
            return {
                "triggered": False,
                "hits": [],
                "promptBlock": "",
                "query": str(message or "").strip(),
            }

        lookback = list(previous_messages or [])[-lookback_limit:]
        query_tokens = cls._tokens(message)
        scored: list[tuple[float, dict[str, Any]]] = []

        for index, item in enumerate(lookback):
            if not isinstance(item, dict):
                continue
            role = str(item.get("role") or "").strip().lower()
            content = str(item.get("content") or "").strip()
            if not content:
                continue
            score = cls._score(content, query_tokens, role=role)
            if score <= 0:
                continue
            scored.append(
                (
                    score,
                    {
                        "role": role or "unknown",
                        "content": content,
                        "index": index,
                        "score": round(score, 3),
                    },
                )
            )

        scored.sort(key=lambda pair: (-pair[0], -pair[1]["index"]))
        hits: list[dict[str, Any]] = []
        total_chars = 0

        for _, hit in scored:
            snippet = str(hit["content"])
            remaining = budget.message_search_max_chars - total_chars
            if remaining <= 0 or len(hits) >= budget.message_search_max_hits:
                break
            clipped = snippet[:remaining]
            total_chars += len(clipped)
            hits.append({**hit, "content": clipped})

        return {
            "triggered": True,
            "hits": hits,
            "promptBlock": cls.format_prompt_block(hits),
            "query": str(message or "").strip(),
            "lookback": len(lookback),
            "lookbackLimit": lookback_limit,
            "hitCount": len(hits),
            "degraded": bool(degraded_stages),
        }

    @classmethod
    def format_prompt_block(cls, hits: list[dict[str, Any]]) -> str:
        if not hits:
            return ""

        title = ChatAssistantContentService.get(
            cls._BUNDLE,
            "promptBlockTitle",
            default="Evidências da conversa",
        )
        intro = ChatAssistantContentService.get(
            cls._BUNDLE,
            "promptBlockIntro",
            default="",
        )
        lines = [title, intro] if intro else [title]

        for offset, hit in enumerate(hits, start=1):
            role = hit.get("role") or "unknown"
            content = str(hit.get("content") or "").strip()
            lines.append(f"[{offset}] ({role}) {content}")

        return "\n".join(line for line in lines if line).strip()

    @classmethod
    def _explicit_triggers(cls) -> list[str]:
        node = ChatAssistantContentService.get_node(cls._BUNDLE, "explicitTriggers")
        if not isinstance(node, list):
            return []
        return [
            ChatMessageNormalizationService.normalize_for_matching(str(item))
            for item in node
            if str(item).strip()
        ]

    @classmethod
    def _tokens(cls, message: str | None) -> set[str]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(
            message or "",
        )
        return {token for token in re.findall(r"[a-z0-9]{3,}", normalized)}

    @classmethod
    def _score(cls, content: str, query_tokens: set[str], *, role: str) -> float:
        normalized = ChatMessageNormalizationService.normalize_for_matching(content)
        content_tokens = {token for token in re.findall(r"[a-z0-9]{3,}", normalized)}
        overlap = len(query_tokens & content_tokens)
        score = float(overlap)
        if role == "user":
            score += 1.5
        if ChatFollowUpIntentService.is_retry_or_continue_request(content):
            score *= 0.2
        return score
