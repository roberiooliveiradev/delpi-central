from __future__ import annotations

import logging

from app.domain.services.web_search_query_service import WebSearchQueryService
from app.infrastructure.config.settings import Settings
from app.infrastructure.gateways.web_search_providers import resolve_web_search_providers

logger = logging.getLogger("minha-delpi-ai-api.web_search")


class WebSearchHttpGateway:
    """Orquestra provedores de busca web com retry EN e fallback honesto."""

    def search(self, query: str, *, max_results: int | None = None) -> dict:
        cleaned_query = WebSearchQueryService.normalize_query(query)

        if not cleaned_query:
            return WebSearchQueryService.build_no_results_payload("", provider="none")

        limit = max(1, min(int(max_results or Settings.CHAT_WEB_SEARCH_MAX_RESULTS), 8))
        providers = resolve_web_search_providers()
        attempted_queries: list[str] = []
        last_provider = providers[-1].name if providers else "duckduckgo_instant_answer"

        for provider in providers:
            last_provider = provider.name

            for candidate_query in self._query_candidates(cleaned_query):
                if candidate_query in attempted_queries:
                    continue

                attempted_queries.append(candidate_query)
                payload = provider.search(candidate_query, max_results=limit)

                if WebSearchQueryService.is_useful_payload(payload):
                    payload["query"] = cleaned_query

                    if candidate_query != cleaned_query:
                        payload["retriedQuery"] = candidate_query

                    if len(attempted_queries) > 1:
                        payload["attemptedQueries"] = attempted_queries

                    return payload

        logger.info(
            "Busca web sem resultados úteis (query=%r, providers=%s, attempts=%s)",
            cleaned_query,
            [provider.name for provider in providers],
            attempted_queries,
        )

        no_results = WebSearchQueryService.build_no_results_payload(
            cleaned_query,
            provider=last_provider,
        )

        if len(attempted_queries) > 1:
            no_results["attemptedQueries"] = attempted_queries
            no_results["retriedQuery"] = attempted_queries[-1]

        from app.domain.services.web_search_portuguese_content_service import (
            WebSearchPortugueseContentService,
        )

        fallback = WebSearchPortugueseContentService.build_fallback_payload(cleaned_query)

        if WebSearchQueryService.is_useful_payload(fallback):
            if len(attempted_queries) > 1:
                fallback["attemptedQueries"] = attempted_queries

            return fallback

        return no_results

    def _query_candidates(self, query: str) -> list[str]:
        return WebSearchQueryService.build_search_candidates(query)
