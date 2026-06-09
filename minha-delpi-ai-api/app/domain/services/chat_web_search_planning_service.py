"""Planejamento de busca web — Playbook pesquisa web, Fase 2 (chat base)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_web_search_intent_service import ChatWebSearchIntentService
from app.domain.services.web_search_query_service import WebSearchQueryService
from app.domain.services.chat_domain_config_service import ChatDomainConfigService
from app.domain.services.chat_web_search_vocabulary_service import (
    ChatWebSearchVocabularyService,
)



@dataclass(frozen=True)
class WebSearchPlan:
    mode: str
    queries: tuple[str, ...]
    prefer_official: bool
    max_results: int
    intent: str

    def primary_query(self) -> str:
        return self.queries[0] if self.queries else ""


class ChatWebSearchPlanningService:
    @classmethod
    def _deep_terms(cls) -> tuple[str, ...]:
        return ChatWebSearchVocabularyService.terms("planning", "deepTerms")

    @classmethod
    def _quick_terms(cls) -> tuple[str, ...]:
        return ChatWebSearchVocabularyService.terms("planning", "quickTerms")

    @classmethod
    def _official_terms(cls) -> tuple[str, ...]:
        return ChatWebSearchVocabularyService.terms("planning", "officialTerms")




    _KNOWN_BRAND_DOMAINS: tuple[tuple[str, str], ...] = (
        ("weg", "weg.net"),
        ("siemens", "siemens.com"),
        ("schneider", "se.com"),
        ("abb", "abb.com"),
        ("rockwell", "rockwellautomation.com"),
        ("omron", "omron.com"),
        ("festo", "festo.com"),
    )

    _STANDARDS_DOMAIN_HINTS: tuple[tuple[str, str], ...] = (
        ("abnt", "abnt.org.br"),
        ("nr-10", "gov.br"),
        ("nr 10", "gov.br"),
        ("norma nr", "gov.br"),
        ("iso ", "iso.org"),
        ("iec ", "iec.ch"),
    )

    @classmethod
    def plan(
        cls,
        message: str,
        *,
        integration: object | None = None,
        base_query_override: str | None = None,
        trigger_mode: str = "default",
    ) -> WebSearchPlan | None:
        raw = str(message or "").strip()

        if not raw:
            return None

        if not ChatWebSearchIntentService.is_web_search_plan_eligible(
            raw,
            trigger_mode=trigger_mode,
        ):
            return None

        base_query = str(base_query_override or "").strip() or ChatWebSearchIntentService.extract_query(raw)

        if not base_query:
            return None

        normalized = ChatMessageNormalizationService.normalize_for_matching(raw)
        mode = cls._resolve_mode(normalized)
        prefer_official = cls._prefers_official(normalized)
        intent = cls._resolve_intent(normalized, prefer_official=prefer_official)
        queries = cls._build_queries(
            base_query,
            normalized,
            mode=mode,
            prefer_official=prefer_official,
        )
        max_results = cls._resolve_max_results(mode)

        if integration is not None and hasattr(integration, "merge_queries"):
            queries = integration.merge_queries(queries)

        if not queries:
            return None

        return WebSearchPlan(
            mode=mode,
            queries=queries,
            prefer_official=prefer_official,
            max_results=max_results,
            intent=intent,
        )

    @classmethod
    def _resolve_mode(cls, normalized: str) -> str:
        if any(term in normalized for term in cls._deep_terms()):
            return "deep"

        if any(term in normalized for term in cls._quick_terms()):
            return "quick"

        if any(term in normalized for term in cls._official_terms()):
            return "deep"

        return "quick"

    @classmethod
    def _prefers_official(cls, normalized: str) -> bool:
        return any(term in normalized for term in cls._official_terms())

    @classmethod
    def _resolve_intent(cls, normalized: str, *, prefer_official: bool) -> str:
        if prefer_official:
            if any(term in normalized for term in ("datasheet", "data sheet", "manual", "pdf")):
                return "technical_document_search"

            return "official_source_search"

        if any(term in normalized for term in ("noticia", "notícia", "recente", "2024", "2025", "2026")):
            return "recent_news_search"

        return "factual_search"

    @classmethod
    def _resolve_max_results(cls, mode: str) -> int:
        cap = max(1, min(int(ChatDomainConfigService.chat_web_search_max_results()), 8))

        if mode == "deep":
            return cap

        return min(3, cap)

    @classmethod
    def _build_queries(
        cls,
        base_query: str,
        normalized_message: str,
        *,
        mode: str,
        prefer_official: bool,
    ) -> tuple[str, ...]:
        ordered: list[str] = []

        def add(value: str) -> None:
            cleaned = WebSearchQueryService.normalize_query(value)

            if cleaned and cleaned not in ordered:
                ordered.append(cleaned)

        add(base_query)

        if prefer_official:
            add(f"{base_query} manual oficial pdf")
            add(f"{base_query} datasheet pdf")

            site_query = cls._site_restricted_query(base_query, normalized_message)

            if site_query:
                add(site_query)

        for candidate in WebSearchQueryService.build_search_candidates(base_query):
            add(candidate)

        if mode == "deep" and any(
            term in normalized_message for term in ("noticia", "notícia", "recente")
        ):
            year_match = re.search(r"\b(20\d{2})\b", normalized_message)
            year = year_match.group(1) if year_match else "2026"
            add(f"{base_query} noticias {year}")

        max_queries = 6 if mode == "deep" else 3

        return tuple(ordered[:max_queries])

    @classmethod
    def _site_restricted_query(cls, base_query: str, normalized_message: str) -> str | None:
        haystack = f"{normalized_message} {base_query}".lower()

        for brand, domain in cls._KNOWN_BRAND_DOMAINS:
            if brand in haystack:
                return f"site:{domain} {base_query}"

        for hint, domain in cls._STANDARDS_DOMAIN_HINTS:
            if hint in haystack:
                if domain == "gov.br":
                    return f"site:gov.br {base_query}"

                return f"site:{domain} {base_query}"

        inferred = cls._infer_official_domain_from_query(base_query)

        if inferred:
            return f"site:{inferred} {base_query}"

        return None

    @classmethod
    def _infer_official_domain_from_query(cls, base_query: str) -> str | None:
        tokens = re.findall(r"[a-z0-9][\w-]{2,}", str(base_query or "").lower())

        for token in tokens:
            for brand, domain in cls._KNOWN_BRAND_DOMAINS:
                if token == brand or token in domain.split(".")[0]:
                    return domain

        return None
