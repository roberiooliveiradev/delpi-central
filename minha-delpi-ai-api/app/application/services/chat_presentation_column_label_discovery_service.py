"""Descobre rótulos PT-BR para colunas ausentes do vocabulário — web + LLM."""

from __future__ import annotations

import logging
from threading import Lock
from typing import ClassVar

from app.domain.ports.presentation_field_label_cache_port import (
    PresentationFieldLabelCachePort,
)
from app.domain.services.chat_domain_config_service import ChatDomainConfigService
from app.domain.services.chat_presentation_column_label_enrichment_service import (
    ChatPresentationColumnLabelEnrichmentService,
)
from app.domain.services.external_actions.external_action_column_label_service import (
    ExternalActionColumnLabelService,
)
from app.domain.services.presentation_column_label_llm_service import (
    PresentationColumnLabelLlmService,
)
from app.domain.services.presentation_column_label_web_search_service import (
    PresentationColumnLabelWebSearchService,
)

logger = logging.getLogger(__name__)


class ChatPresentationColumnLabelDiscoveryService:
    _cache: dict[str, str] = {}
    _lock = Lock()
    _cache_port: ClassVar[PresentationFieldLabelCachePort | None] = None

    @classmethod
    def configure_cache(cls, port: PresentationFieldLabelCachePort | None) -> None:
        cls._cache_port = port

    @classmethod
    def clear_cache(cls) -> None:
        with cls._lock:
            cls._cache.clear()

    @classmethod
    def is_enabled(cls) -> bool:
        return ChatDomainConfigService.chat_presentation_column_label_discovery_enabled()

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

        del profile_labels, fields
        pending: list[str] = []
        resolved: dict[str, str] = {}

        for key in keys:
            token = str(key or "").strip()

            if not token:
                continue

            cached = cls._cache_get(token)

            if not cached:
                cached = cls._persistent_get(token)
                if cached:
                    cls._cache_set(token, cached)

            if cached:
                resolved[token] = cached
                continue

            if ExternalActionColumnLabelService.is_catalog_field_resolved(
                token,
                schema_labels=schema_labels,
            ):
                continue

            pending.append(token)

        if not pending:
            return resolved

        max_keys = max(1, ChatDomainConfigService.chat_presentation_column_label_max_keys())
        pending = pending[:max_keys]

        web_snippets = cls._gather_web_snippets(pending)
        llm_labels = cls._translate_with_llm(pending, path=path, web_snippets=web_snippets)

        for key, label in llm_labels.items():
            normalized = ChatPresentationColumnLabelEnrichmentService.normalize_label(label)
            if not normalized:
                continue
            humanized = ExternalActionColumnLabelService._humanize_field_key(key)
            if normalized.casefold() == humanized.casefold():
                continue
            cls._cache_set(key, normalized)
            cls._persistent_put(key, normalized)
            resolved[key] = normalized

        return resolved

    @classmethod
    def _cache_get(cls, key: str) -> str | None:
        with cls._lock:
            value = cls._cache.get(key)

        return str(value).strip() if value else None

    @classmethod
    def _cache_set(cls, key: str, label: str) -> None:
        max_size = max(50, ChatDomainConfigService.chat_presentation_column_label_cache_size())

        with cls._lock:
            if len(cls._cache) >= max_size:
                oldest = next(iter(cls._cache))
                cls._cache.pop(oldest, None)

            cls._cache[key] = label

    @classmethod
    def _persistent_get(cls, key: str) -> str | None:
        port = cls._cache_port
        if port is None:
            return None

        try:
            value = port.get_label(key)
        except Exception:
            logger.debug("presentation_field_label_cache_get_skipped", extra={"fieldKey": key})
            return None

        return str(value).strip() if value else None

    @classmethod
    def _persistent_put(cls, key: str, label: str) -> None:
        port = cls._cache_port
        if port is None:
            return

        try:
            port.put_label(key, label, source="LLM_LOCALIZATION")
        except Exception:
            logger.debug("presentation_field_label_cache_put_skipped", extra={"fieldKey": key})

    @classmethod
    def _gather_web_snippets(cls, keys: list[str]) -> dict[str, str]:
        if not (
            ChatDomainConfigService.chat_web_search_enabled()
            and ChatDomainConfigService.chat_presentation_column_label_web_search_enabled()
        ):
            return {}

        max_queries = max(0, ChatDomainConfigService.chat_presentation_column_label_web_max_queries())
        snippets: dict[str, str] = {}

        for key in keys[:max_queries]:
            query = ChatPresentationColumnLabelEnrichmentService.build_web_search_query(key)
            payload = PresentationColumnLabelWebSearchService.search(query, max_results=2)

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

        raw = PresentationColumnLabelLlmService.generate(messages)

        return ChatPresentationColumnLabelEnrichmentService.parse_llm_labels(
            raw,
            expected_keys=keys,
        )
