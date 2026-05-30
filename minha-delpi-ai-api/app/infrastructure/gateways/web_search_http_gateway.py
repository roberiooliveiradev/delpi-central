from __future__ import annotations

import logging
from urllib.parse import quote_plus

import requests

from app.infrastructure.config.settings import Settings

logger = logging.getLogger("minha-delpi-ai-api.web_search")


class WebSearchHttpGateway:
    """Gateway MVP para busca pública via DuckDuckGo Instant Answer (sem API key)."""

    INSTANT_ANSWER_URL = "https://api.duckduckgo.com/"

    def search(self, query: str, *, max_results: int | None = None) -> dict:
        cleaned_query = str(query or "").strip()

        if not cleaned_query:
            return {"query": "", "results": [], "provider": "duckduckgo_instant_answer"}

        limit = max(1, min(int(max_results or Settings.CHAT_WEB_SEARCH_MAX_RESULTS), 8))

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
            logger.warning("Falha na busca web para %r: %s", cleaned_query, exc)
            return {
                "query": cleaned_query,
                "results": [],
                "provider": "duckduckgo_instant_answer",
                "error": "web_search_unavailable",
            }

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
            results.append(
                {
                    "title": cleaned_query,
                    "snippet": (
                        "Não foi possível obter um resumo instantâneo. "
                        f"Consulte manualmente: https://duckduckgo.com/?q={quote_plus(cleaned_query)}"
                    ),
                    "url": f"https://duckduckgo.com/?q={quote_plus(cleaned_query)}",
                    "source": "fallback_link",
                }
            )

        return {
            "query": cleaned_query,
            "results": results[:limit],
            "provider": "duckduckgo_instant_answer",
        }
