"""Provedores de busca web (DuckDuckGo Instant Answer, Tavily, Serper, Bing)."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import ClassVar

import requests

from app.domain.services.web_search_query_service import WebSearchQueryService
from app.infrastructure.config.settings import Settings

logger = logging.getLogger("minha-delpi-ai-api.web_search")


class WebSearchProvider(ABC):
    name: ClassVar[str]

    @abstractmethod
    def is_configured(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def search(self, query: str, *, max_results: int) -> dict:
        raise NotImplementedError

    @staticmethod
    def _empty_payload(query: str, provider: str, *, error: str | None = None) -> dict:
        payload: dict = {
            "query": WebSearchQueryService.normalize_query(query),
            "results": [],
            "provider": provider,
        }

        if error:
            payload["error"] = error

        return payload

    @staticmethod
    def _success_payload(
        query: str,
        provider: str,
        results: list[dict],
        *,
        max_results: int,
    ) -> dict:
        cleaned = WebSearchQueryService.normalize_query(query)

        return {
            "query": cleaned,
            "results": results[:max_results],
            "provider": provider,
            "searchStatus": "success",
        }


class DuckDuckGoInstantProvider(WebSearchProvider):
    name = "duckduckgo_instant_answer"
    INSTANT_ANSWER_URL = "https://api.duckduckgo.com/"

    def is_configured(self) -> bool:
        return True

    def search(self, query: str, *, max_results: int) -> dict:
        cleaned_query = WebSearchQueryService.normalize_query(query)

        if not cleaned_query:
            return self._empty_payload("", self.name)

        limit = max(1, min(max_results, 8))

        try:
            response = requests.get(
                self.INSTANT_ANSWER_URL,
                params={
                    "q": cleaned_query,
                    "format": "json",
                    "no_redirect": 1,
                    "no_html": 1,
                    "skip_disambig": 1,
                },
                timeout=Settings.CHAT_WEB_SEARCH_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            logger.warning("DuckDuckGo falhou para %r: %s", cleaned_query, exc)
            return self._empty_payload(cleaned_query, self.name, error="web_search_unavailable")

        results: list[dict] = []

        abstract = str(payload.get("AbstractText") or "").strip()
        abstract_url = str(payload.get("AbstractURL") or "").strip()
        heading = str(payload.get("Heading") or "").strip()

        if abstract:
            results.append(
                {
                    "title": heading or cleaned_query,
                    "snippet": abstract,
                    "url": abstract_url or None,
                    "source": "instant_answer",
                }
            )

        for topic in payload.get("RelatedTopics") or []:
            if len(results) >= limit:
                break

            if isinstance(topic, dict) and topic.get("Text"):
                results.append(
                    {
                        "title": str(topic.get("Text") or "")[:120],
                        "snippet": str(topic.get("Text") or "").strip(),
                        "url": str(topic.get("FirstURL") or "").strip() or None,
                        "source": "related_topic",
                    }
                )
                continue

            if isinstance(topic, dict):
                for nested in topic.get("Topics") or []:
                    if len(results) >= limit:
                        break

                    if not isinstance(nested, dict) or not nested.get("Text"):
                        continue

                    results.append(
                        {
                            "title": str(nested.get("Text") or "")[:120],
                            "snippet": str(nested.get("Text") or "").strip(),
                            "url": str(nested.get("FirstURL") or "").strip() or None,
                            "source": "related_topic",
                        }
                    )

        if not results:
            return self._empty_payload(cleaned_query, self.name)

        return self._success_payload(cleaned_query, self.name, results, max_results=limit)


class TavilySearchProvider(WebSearchProvider):
    name = "tavily"
    SEARCH_URL = "https://api.tavily.com/search"

    def is_configured(self) -> bool:
        return bool(Settings.CHAT_WEB_SEARCH_TAVILY_API_KEY)

    def search(self, query: str, *, max_results: int) -> dict:
        cleaned_query = WebSearchQueryService.normalize_query(query)

        if not cleaned_query or not self.is_configured():
            return self._empty_payload(cleaned_query, self.name)

        limit = max(1, min(max_results, 8))

        try:
            response = requests.post(
                self.SEARCH_URL,
                json={
                    "api_key": Settings.CHAT_WEB_SEARCH_TAVILY_API_KEY,
                    "query": cleaned_query,
                    "search_depth": "basic",
                    "include_answer": False,
                    "max_results": limit,
                },
                timeout=Settings.CHAT_WEB_SEARCH_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            logger.warning("Tavily falhou para %r: %s", cleaned_query, exc)
            return self._empty_payload(cleaned_query, self.name, error="web_search_unavailable")

        results: list[dict] = []

        for item in payload.get("results") or []:
            if not isinstance(item, dict):
                continue

            snippet = str(item.get("content") or item.get("snippet") or "").strip()
            title = str(item.get("title") or cleaned_query).strip()
            url = str(item.get("url") or "").strip() or None

            if not snippet and not title:
                continue

            results.append(
                {
                    "title": title,
                    "snippet": snippet or title,
                    "url": url,
                    "source": "tavily",
                }
            )

        if not results:
            return self._empty_payload(cleaned_query, self.name)

        return self._success_payload(cleaned_query, self.name, results, max_results=limit)


class SerperSearchProvider(WebSearchProvider):
    name = "serper"
    SEARCH_URL = "https://google.serper.dev/search"

    def is_configured(self) -> bool:
        return bool(Settings.CHAT_WEB_SEARCH_SERPER_API_KEY)

    def search(self, query: str, *, max_results: int) -> dict:
        cleaned_query = WebSearchQueryService.normalize_query(query)

        if not cleaned_query or not self.is_configured():
            return self._empty_payload(cleaned_query, self.name)

        limit = max(1, min(max_results, 8))

        try:
            response = requests.post(
                self.SEARCH_URL,
                headers={
                    "X-API-KEY": Settings.CHAT_WEB_SEARCH_SERPER_API_KEY,
                    "Content-Type": "application/json",
                },
                json={"q": cleaned_query, "num": limit},
                timeout=Settings.CHAT_WEB_SEARCH_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            logger.warning("Serper falhou para %r: %s", cleaned_query, exc)
            return self._empty_payload(cleaned_query, self.name, error="web_search_unavailable")

        results: list[dict] = []

        for item in payload.get("organic") or []:
            if not isinstance(item, dict):
                continue

            snippet = str(item.get("snippet") or "").strip()
            title = str(item.get("title") or cleaned_query).strip()
            url = str(item.get("link") or "").strip() or None

            if not snippet and not title:
                continue

            results.append(
                {
                    "title": title,
                    "snippet": snippet or title,
                    "url": url,
                    "source": "serper",
                }
            )

        if not results:
            return self._empty_payload(cleaned_query, self.name)

        return self._success_payload(cleaned_query, self.name, results, max_results=limit)


class BingSearchProvider(WebSearchProvider):
    name = "bing"
    SEARCH_URL = "https://api.bing.microsoft.com/v7.0/search"

    def is_configured(self) -> bool:
        return bool(Settings.CHAT_WEB_SEARCH_BING_API_KEY)

    def search(self, query: str, *, max_results: int) -> dict:
        cleaned_query = WebSearchQueryService.normalize_query(query)

        if not cleaned_query or not self.is_configured():
            return self._empty_payload(cleaned_query, self.name)

        limit = max(1, min(max_results, 8))

        try:
            response = requests.get(
                self.SEARCH_URL,
                headers={"Ocp-Apim-Subscription-Key": Settings.CHAT_WEB_SEARCH_BING_API_KEY},
                params={"q": cleaned_query, "count": limit, "textDecorations": False},
                timeout=Settings.CHAT_WEB_SEARCH_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            logger.warning("Bing falhou para %r: %s", cleaned_query, exc)
            return self._empty_payload(cleaned_query, self.name, error="web_search_unavailable")

        results: list[dict] = []

        for item in (payload.get("webPages") or {}).get("value") or []:
            if not isinstance(item, dict):
                continue

            snippet = str(item.get("snippet") or "").strip()
            title = str(item.get("name") or cleaned_query).strip()
            url = str(item.get("url") or "").strip() or None

            if not snippet and not title:
                continue

            results.append(
                {
                    "title": title,
                    "snippet": snippet or title,
                    "url": url,
                    "source": "bing",
                }
            )

        if not results:
            return self._empty_payload(cleaned_query, self.name)

        return self._success_payload(cleaned_query, self.name, results, max_results=limit)


def resolve_web_search_providers() -> list[WebSearchProvider]:
    configured = {
        "tavily": TavilySearchProvider(),
        "serper": SerperSearchProvider(),
        "bing": BingSearchProvider(),
        "duckduckgo": DuckDuckGoInstantProvider(),
    }

    provider_name = Settings.resolve_web_search_provider()

    if provider_name == "auto":
        ordered_names = ("tavily", "serper", "bing", "duckduckgo")
        providers: list[WebSearchProvider] = []

        for name in ordered_names:
            provider = configured[name]

            if name == "duckduckgo" or provider.is_configured():
                providers.append(provider)

        return providers or [configured["duckduckgo"]]

    selected = configured.get(provider_name)

    if selected is None:
        return [configured["duckduckgo"]]

    if selected.name != "duckduckgo_instant_answer" and not selected.is_configured():
        logger.warning(
            "Provedor web_search=%s sem credenciais; usando DuckDuckGo.",
            provider_name,
        )
        return [configured["duckduckgo"]]

    return [selected]

