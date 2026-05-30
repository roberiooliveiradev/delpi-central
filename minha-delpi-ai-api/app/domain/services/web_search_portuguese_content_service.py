"""Enriquece resultados de busca web com resumo em português (Wikipedia PT)."""

from __future__ import annotations

import logging
import re
import unicodedata
from urllib.parse import quote

import requests

from app.domain.services.web_search_query_service import (
    USELESS_RESULT_SOURCES,
    WebSearchQueryService,
)
from app.infrastructure.config.settings import Settings

logger = logging.getLogger("minha-delpi-ai-api.web_search")


class WebSearchPortugueseContentService:
    WIKIPEDIA_PT_SUMMARY_URL = "https://pt.wikipedia.org/api/rest_v1/page/summary/"
    WIKIPEDIA_USER_AGENT = "MinhaDelpiWebSearch/1.0 (https://delpi.com.br; chat-web-search)"

    _ENGLISH_MARKERS = re.compile(
        r"\b(the|and|with|language|programming|high-level|general-purpose|software)\b",
        re.IGNORECASE,
    )

    _TOPIC_STOPWORDS = frozenset(
        {
            "linguagem",
            "programacao",
            "programação",
            "sobre",
            "internet",
            "web",
            "online",
            "pesquise",
            "pesquisa",
            "busque",
            "busca",
            "definicao",
            "definição",
            "noticias",
            "notícias",
        }
    )

    @classmethod
    def build_fallback_payload(cls, query: str) -> dict | None:
        """Último recurso quando provedores web não retornam snippet útil."""
        topic = WebSearchQueryService.extract_primary_entity(query)

        if not topic:
            topic = cls._extract_topic(query)

        if not topic:
            return None

        results: list[dict] = []
        seen_urls: set[str] = set()

        for title in cls._fallback_title_candidates(topic):
            summary = cls._request_wikipedia_summary(title)

            if not summary:
                continue

            url = str(summary.get("url") or "").strip()

            if not url or url in seen_urls:
                continue

            seen_urls.add(url)
            results.append(summary)

            if len(results) >= Settings.CHAT_WEB_SEARCH_MAX_RESULTS:
                break

        if not results:
            return None

        cleaned_query = WebSearchQueryService.normalize_query(query)

        return {
            "query": cleaned_query,
            "results": results,
            "provider": "wikipedia_pt_fallback",
            "searchStatus": "success",
            "localizedFor": "pt-BR",
            "localizedSource": "wikipedia_pt_fallback",
        }

    @classmethod
    def _fallback_title_candidates(cls, topic: str) -> list[str]:
        candidates = cls._topic_title_candidates(topic)
        entity = str(topic or "").strip()

        if entity:
            candidates.extend(
                [
                    entity,
                    f"{entity} International",
                    "TE Connectivity" if entity.casefold() == "tyco" else "",
                ]
            )

        deduped: list[str] = []

        for item in candidates:
            cleaned = str(item or "").strip()

            if cleaned and cleaned not in deduped:
                deduped.append(cleaned)

        return deduped

    @classmethod
    def localize_payload(cls, payload: dict | None) -> dict | None:
        if not isinstance(payload, dict) or payload.get("searchStatus") != "success":
            return payload

        query = str(payload.get("query") or "").strip()

        if not query:
            return payload

        primary = cls._primary_result(payload)

        if not primary or not cls._looks_english_snippet(str(primary.get("snippet") or "")):
            return payload

        should_localize = cls._looks_portuguese_query(query) or len(
            WebSearchQueryService.extract_entity_tokens(query)
        ) == 1

        if not should_localize:
            return payload

        topic = cls._extract_topic(query)

        if not topic:
            return payload

        localized = cls._fetch_wikipedia_pt_summary(topic)

        if not localized:
            return payload

        results = list(payload.get("results") or [])
        filtered = [
            item
            for item in results
            if str(item.get("url") or "") != localized["url"]
        ]

        return {
            **payload,
            "results": [localized, *filtered],
            "localizedFor": "pt-BR",
            "localizedSource": "wikipedia_pt",
        }

    @classmethod
    def _primary_result(cls, payload: dict) -> dict | None:
        results = payload.get("results")

        if not isinstance(results, list) or not results:
            return None

        for item in results:
            if isinstance(item, dict) and str(item.get("source") or "") not in USELESS_RESULT_SOURCES:
                return item

        return None

    @classmethod
    def _looks_portuguese_query(cls, query: str) -> bool:
        normalized = WebSearchQueryService.normalize_query(query)

        if WebSearchQueryService._looks_portuguese(normalized.casefold()):
            return True

        return bool(re.search(r"[áàâãéêíóôõúç]", normalized, re.IGNORECASE))

    @classmethod
    def _looks_english_snippet(cls, snippet: str) -> bool:
        text = snippet.strip()

        if not text:
            return False

        if re.search(r"[áàâãéêíóôõúç]", text, re.IGNORECASE):
            return False

        return bool(cls._ENGLISH_MARKERS.search(text))

    @classmethod
    def _extract_topic(cls, query: str) -> str:
        entity = WebSearchQueryService.extract_primary_entity(query)

        if entity:
            return entity

        normalized = WebSearchQueryService.normalize_query(query).casefold()
        normalized = unicodedata.normalize("NFKD", normalized)
        normalized = "".join(char for char in normalized if not unicodedata.combining(char))

        for pt_phrase, _ in WebSearchQueryService._PT_TO_EN_PHRASES:
            normalized = normalized.replace(
                unicodedata.normalize("NFKD", pt_phrase)
                .encode("ascii", "ignore")
                .decode("ascii"),
                " ",
            )

        tokens = [
            token
            for token in re.split(r"[^\w]+", normalized)
            if token and token not in cls._TOPIC_STOPWORDS and len(token) > 1
        ]

        if not tokens:
            return ""

        return tokens[0][:1].upper() + tokens[0][1:]

    @classmethod
    def _fetch_wikipedia_pt_summary(cls, topic: str) -> dict | None:
        candidates = cls._topic_title_candidates(topic)

        for title in candidates:
            summary = cls._request_wikipedia_summary(title)

            if summary:
                return summary

        return None

    @classmethod
    def _topic_title_candidates(cls, topic: str) -> list[str]:
        cleaned = str(topic or "").strip()

        if not cleaned:
            return []

        candidates = [cleaned]

        if cleaned.casefold() == "python":
            candidates.extend(["Python (linguagem de programação)", "Python"])

        if cleaned.casefold() == "tyco":
            candidates.extend(
                [
                    "Tyco International",
                    "TE Connectivity",
                    "Johnson Controls",
                ]
            )

        deduped: list[str] = []

        for item in candidates:
            if item not in deduped:
                deduped.append(item)

        return deduped

    @classmethod
    def _request_wikipedia_summary(cls, title: str) -> dict | None:
        url = f"{cls.WIKIPEDIA_PT_SUMMARY_URL}{quote(title.replace(' ', '_'))}"

        try:
            response = requests.get(
                url,
                headers={
                    "Accept": "application/json",
                    "User-Agent": cls.WIKIPEDIA_USER_AGENT,
                },
                timeout=Settings.CHAT_WEB_SEARCH_TIMEOUT_SECONDS,
            )

            if response.status_code == 404:
                return None

            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            logger.debug("Wikipedia PT indisponível para %r: %s", title, exc)
            return None

        extract = str(payload.get("extract") or "").strip()
        page_title = str(payload.get("title") or title).strip()
        content_urls = payload.get("content_urls") or {}
        page_url = str((content_urls.get("desktop") or {}).get("page") or "").strip()

        if not extract:
            return None

        return {
            "title": page_title,
            "snippet": extract,
            "url": page_url or f"https://pt.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}",
            "source": "wikipedia_pt",
        }
