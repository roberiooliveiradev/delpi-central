"""Planejamento de busca web — Playbook pesquisa web, Fase 2 (chat base)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_web_search_intent_service import ChatWebSearchIntentService
from app.domain.services.web_search_query_service import WebSearchQueryService
from app.infrastructure.config.settings import Settings


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
    _DEEP_TERMS = (
        "pesquisa profunda",
        "busca profunda",
        "investigacao completa",
        "investigação completa",
        "investigue a fundo",
        "pesquise a fundo",
        "analise completa",
        "análise completa",
        "compare fontes",
        "comparar fontes",
        "valide com fontes",
    )

    _QUICK_TERMS = (
        "pesquisa rapida",
        "pesquisa rápida",
        "busca rapida",
        "busca rápida",
        "resumo rapido",
        "resumo rápido",
    )

    _OFFICIAL_TERMS = (
        "manual oficial",
        "site oficial",
        "fonte oficial",
        "fontes oficiais",
        "datasheet",
        "data sheet",
        "ficha tecnica",
        "ficha técnica",
        "documentacao oficial",
        "documentação oficial",
        "norma abnt",
        "norma nr",
        "nr-",
        "abnt",
        "pdf oficial",
    )

    _KNOWN_BRAND_DOMAINS: tuple[tuple[str, str], ...] = (
        ("weg", "weg.net"),
        ("siemens", "siemens.com"),
        ("schneider", "se.com"),
        ("abb", "abb.com"),
        ("rockwell", "rockwellautomation.com"),
        ("omron", "omron.com"),
        ("festo", "festo.com"),
    )

    @classmethod
    def plan(cls, message: str) -> WebSearchPlan | None:
        raw = str(message or "").strip()

        if not raw or not ChatWebSearchIntentService.matches(raw):
            return None

        base_query = ChatWebSearchIntentService.extract_query(raw)

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
        if any(term in normalized for term in cls._DEEP_TERMS):
            return "deep"

        if any(term in normalized for term in cls._QUICK_TERMS):
            return "quick"

        if any(term in normalized for term in cls._OFFICIAL_TERMS):
            return "deep"

        return "quick"

    @classmethod
    def _prefers_official(cls, normalized: str) -> bool:
        return any(term in normalized for term in cls._OFFICIAL_TERMS)

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
        cap = max(1, min(int(Settings.CHAT_WEB_SEARCH_MAX_RESULTS), 8))

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

        return None
