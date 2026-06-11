"""Descobre rótulos PT-BR para colunas ausentes do vocabulário — web + LLM."""

from __future__ import annotations

import logging
from threading import Lock

from app.domain.services.chat_presentation_column_label_enrichment_service import (
    ChatPresentationColumnLabelEnrichmentService,
)
from app.domain.services.external_actions.external_action_column_label_service import (
    ExternalActionColumnLabelService,
)
from app.infrastructure.config.settings import Settings

logger = logging.getLogger(__name__)


class ChatPresentationColumnLabelDiscoveryService:
    _cache: dict[str, str] = {}
    _lock = Lock()

    @classmethod
    def clear_cache(cls) -> None:
        with cls._lock:
            cls._cache.clear()

    @classmethod
    def is_enabled(cls) -> bool:
        return bool(Settings.CHAT_PRESENTATION_COLUMN_LABEL_DISCOVERY_ENABLED)

    @classmethod
    def resolve_labels(
        cls,
        keys: list[str],
        *,
        path: str = "",
        schema_labels: dict[str, str] | None = None,
        profile_labels: dict[str, str] | None = None,
        fields: dict[str, str] | None = None,
    ) -> dict[str, str]:
        if not cls.is_enabled():
            return {}

        label_service = ExternalActionColumnLabelService()
        catalog_fields = fields or {}
        pending: list[str] = []
        resolved: dict[str, str] = {}

        for key in keys:
            token = str(key or "").strip()

            if not token:
                continue

            cached = cls._cache_get(token)

            if cached:
                resolved[token] = cached
                continue

            profile_label = (profile_labels or {}).get(token)

            if ChatPresentationColumnLabelEnrichmentService.is_catalog_resolved(
                token,
                schema_labels=schema_labels,
                profile_label=profile_label,
                fields=catalog_fields,
                snake_key=ExternalActionColumnLabelService._snake_case_key(token),
            ):
                continue

            pending.append(token)

        if not pending:
            return resolved

        max_keys = max(1, int(Settings.CHAT_PRESENTATION_COLUMN_LABEL_MAX_KEYS))
        pending = pending[:max_keys]

        web_snippets = cls._gather_web_snippets(pending)
        llm_labels = cls._translate_with_llm(pending, path=path, web_snippets=web_snippets)

        for key, label in llm_labels.items():
            normalized = ChatPresentationColumnLabelEnrichmentService.normalize_label(label)

            if normalized:
                cls._cache_set(key, normalized)
                resolved[key] = normalized

        return resolved

    @classmethod
    def _cache_get(cls, key: str) -> str | None:
        with cls._lock:
            value = cls._cache.get(key)

        return str(value).strip() if value else None

    @classmethod
    def _cache_set(cls, key: str, label: str) -> None:
        max_size = max(50, int(Settings.CHAT_PRESENTATION_COLUMN_LABEL_CACHE_SIZE))

        with cls._lock:
            if len(cls._cache) >= max_size:
                oldest = next(iter(cls._cache))
                cls._cache.pop(oldest, None)

            cls._cache[key] = label

    @classmethod
    def _gather_web_snippets(cls, keys: list[str]) -> dict[str, str]:
        if not (
            Settings.CHAT_WEB_SEARCH_ENABLED
            and Settings.CHAT_PRESENTATION_COLUMN_LABEL_WEB_SEARCH_ENABLED
        ):
            return {}

        from app.domain.services.chat_web_search_intent_service import (
            ChatWebSearchIntentService,
        )

        if not ChatWebSearchIntentService.is_feature_enabled():
            return {}

        try:
            from app.infrastructure.gateways.web_search_http_gateway import (
                WebSearchHttpGateway,
            )
        except ImportError:
            return {}

        gateway = WebSearchHttpGateway()
        max_queries = max(0, int(Settings.CHAT_PRESENTATION_COLUMN_LABEL_WEB_MAX_QUERIES))
        snippets: dict[str, str] = {}

        for key in keys[:max_queries]:
            query = ChatPresentationColumnLabelEnrichmentService.build_web_search_query(key)

            try:
                payload = gateway.search(
                    query,
                    max_results=2,
                )
            except Exception as exc:
                logger.debug("column label web search failed for %s: %s", key, exc)
                continue

            if not isinstance(payload, dict):
                continue

            results = payload.get("results")

            if not isinstance(results, list):
                continue

            parts: list[str] = []

            for item in results[:2]:
                if not isinstance(item, dict):
                    continue

                title = str(item.get("title") or "").strip()
                snippet = str(item.get("snippet") or "").strip()
                chunk = " — ".join(part for part in (title, snippet) if part)

                if chunk:
                    parts.append(chunk)

            if parts:
                snippets[key] = " | ".join(parts)[:500]

        return snippets

    @classmethod
    def _translate_with_llm(
        cls,
        keys: list[str],
        *,
        path: str,
        web_snippets: dict[str, str],
    ) -> dict[str, str]:
        messages = ChatPresentationColumnLabelEnrichmentService.build_llm_messages(
            keys,
            path=path,
            web_snippets=web_snippets,
        )

        if not messages[0].get("content"):
            return {}

        try:
            from app.composition.llm_composer import make_llm_gateway

            raw = make_llm_gateway().generate(messages)
        except Exception as exc:
            logger.warning("column label LLM discovery failed: %s", exc)
            return {}

        return ChatPresentationColumnLabelEnrichmentService.parse_llm_labels(
            str(raw or ""),
            expected_keys=keys,
        )
