"""Catálogo enxuto de actions para o loop agentic (Onda 11.3.1)."""

from __future__ import annotations

from typing import Any, Protocol

from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)
from app.infrastructure.config.settings import Settings


class ExternalActionCatalogRepositoryPort(Protocol):
    def find_candidate_actions(
        self,
        query: str,
        limit: int = 8,
        *,
        allowed_action_ids: list[str] | None = None,
    ) -> list[dict]: ...


class ChatAgenticCatalogService:
    _INTENT_PATH_HINTS: dict[str, tuple[str, ...]] = {
        ChatProductQueryIntent.STOCK: ("/stock", "stock", "estoque"),
        ChatProductQueryIntent.STRUCTURE: ("/structure", "structure", "estrutura", "bom"),
        ChatProductQueryIntent.PARENTS: ("/parents", "parents", "where-used", "onde"),
        ChatProductQueryIntent.SUMMARY: ("/summary", "summary", "resumo"),
        ChatProductQueryIntent.ANALYSER: ("/analyser", "analyser", "analisador", "ficha"),
        ChatProductQueryIntent.DESCRIPTION: ("/products/{code}", "/products/", "detail", "cadastro"),
    }

    _GENERIC_PRODUCT_HINTS = ("/products/", "product", "produto")

    @classmethod
    def resolve_limit(cls) -> int:
        return max(1, Settings.CHAT_AGENTIC_CATALOG_MAX_ACTIONS)

    @classmethod
    def build_action_ids(
        cls,
        message: str,
        allowed_action_ids: list[str] | None,
        repository: ExternalActionCatalogRepositoryPort | None,
    ) -> list[str]:
        allowed = [
            str(item).strip()
            for item in (allowed_action_ids or [])
            if str(item).strip()
        ]

        if not allowed:
            return []

        limit = cls.resolve_limit()
        candidates: list[dict[str, Any]] = []

        if repository is not None:
            candidates = repository.find_candidate_actions(
                message,
                limit=max(limit, limit * 2),
                allowed_action_ids=allowed,
            )

        if not candidates:
            return allowed[:limit]

        intent = ChatProductQueryIntentService.resolve_product_intent(message)
        ranked = cls._rank_candidates(candidates, intent=intent)

        action_ids: list[str] = []

        for action in ranked:
            action_id = str(action.get("actionId") or "").strip()

            if not action_id or action_id in action_ids:
                continue

            action_ids.append(action_id)

            if len(action_ids) >= limit:
                break

        return action_ids

    @classmethod
    def describe_catalog(
        cls,
        message: str,
        allowed_action_ids: list[str] | None,
        repository: ExternalActionCatalogRepositoryPort | None,
    ) -> dict[str, object]:
        action_ids = cls.build_action_ids(message, allowed_action_ids, repository)

        return {
            "actionIds": action_ids,
            "size": len(action_ids),
            "maxActions": cls.resolve_limit(),
            "intent": ChatProductQueryIntentService.resolve_product_intent(message),
        }

    @classmethod
    def _rank_candidates(cls, candidates: list[dict[str, Any]], *, intent: str) -> list[dict[str, Any]]:
        hints = cls._INTENT_PATH_HINTS.get(intent) or cls._GENERIC_PRODUCT_HINTS

        def score(action: dict[str, Any]) -> tuple[int, str]:
            haystack = " ".join(
                str(action.get(key) or "")
                for key in ("path", "operationId", "summary", "description", "actionId")
            ).lower()

            match_score = sum(2 if hint in haystack else 0 for hint in hints)

            if intent == ChatProductQueryIntent.FULL and any(
                hint in haystack for hint in cls._GENERIC_PRODUCT_HINTS
            ):
                match_score += 1

            return (-match_score, str(action.get("actionId") or ""))

        return sorted(candidates, key=score)
