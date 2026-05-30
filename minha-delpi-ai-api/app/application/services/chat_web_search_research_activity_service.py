"""Metadados de atividade de pesquisa web para painel «Fontes» no chat."""

from __future__ import annotations

from urllib.parse import urlparse

from app.domain.services.chat_web_search_direct_answer_service import (
    ChatWebSearchDirectAnswerService,
)
from app.domain.services.web_search_query_service import USELESS_RESULT_SOURCES


class ChatWebSearchResearchActivityService:
    @classmethod
    def build(
        cls,
        *,
        tool_context: dict | None,
        pipeline_stages: list[str] | None = None,
        latency_ms: int | None = None,
    ) -> dict | None:
        if not isinstance(tool_context, dict):
            return None

        payload = tool_context.get("webSearchPayload")

        if not isinstance(payload, dict):
            return None

        web_sources = tool_context.get("webSources")

        if not isinstance(web_sources, list):
            web_sources = []

        sites = cls._build_sites(payload, web_sources)
        attempted_queries = cls._resolve_attempted_queries(payload)
        synthesized = "web_search_synthesis" in (pipeline_stages or [])
        steps = cls._build_steps(
            payload,
            attempted_queries=attempted_queries,
            sites=sites,
            synthesized=synthesized,
        )

        if not steps and not sites:
            return None

        return {
            "sourceCount": len(sites) or len(web_sources),
            "durationMs": latency_ms,
            "provider": str(payload.get("provider") or "").strip() or None,
            "query": str(payload.get("query") or "").strip() or None,
            "attemptedQueries": attempted_queries or None,
            "searchStatus": str(payload.get("searchStatus") or "").strip() or None,
            "synthesized": synthesized,
            "steps": steps,
            "sites": sites,
        }

    @classmethod
    def _resolve_attempted_queries(cls, payload: dict) -> list[str]:
        raw = payload.get("attemptedQueries")

        if isinstance(raw, list):
            queries = [str(item or "").strip() for item in raw if str(item or "").strip()]

            if queries:
                return queries

        primary = str(payload.get("query") or "").strip()
        retried = str(payload.get("retriedQuery") or "").strip()

        if primary and retried and retried.casefold() != primary.casefold():
            return [primary, retried]

        if primary:
            return [primary]

        if retried:
            return [retried]

        return []

    @classmethod
    def _build_sites(cls, payload: dict, web_sources: list) -> list[dict]:
        sites: list[dict] = []
        seen_urls: set[str] = set()

        for item in web_sources:
            if not isinstance(item, dict):
                continue

            url = str(item.get("sourceRef") or item.get("url") or "").strip()

            if not url or url in seen_urls:
                continue

            seen_urls.add(url)
            title = str(item.get("title") or "").strip()
            sites.append(
                {
                    "hostname": cls._hostname(url),
                    "url": url,
                    "title": title or cls._hostname(url),
                }
            )

        results = payload.get("results")

        if isinstance(results, list):
            for item in results:
                if not isinstance(item, dict):
                    continue

                if str(item.get("source") or "") in USELESS_RESULT_SOURCES:
                    continue

                url = str(item.get("url") or "").strip()

                if not url or url in seen_urls:
                    continue

                seen_urls.add(url)
                title = str(item.get("title") or "").strip()
                sites.append(
                    {
                        "hostname": cls._hostname(url),
                        "url": url,
                        "title": title or cls._hostname(url),
                    }
                )

        return sites

    @classmethod
    def _build_steps(
        cls,
        payload: dict,
        *,
        attempted_queries: list[str],
        sites: list[dict],
        synthesized: bool,
    ) -> list[dict]:
        steps: list[dict] = []
        queries = attempted_queries or [str(payload.get("query") or "").strip()]
        queries = [query for query in queries if query]

        if not queries:
            queries = ["consulta web"]

        for index, query in enumerate(queries):
            is_last = index == len(queries) - 1
            step_sites = sites if is_last and sites else []

            steps.append(
                {
                    "id": f"web-search-query-{index}",
                    "type": "search",
                    "message": cls._search_step_message(query),
                    "query": query,
                    "state": "done",
                    "sites": step_sites,
                }
            )

        if synthesized:
            steps.append(
                {
                    "id": "web-search-synthesis",
                    "type": "synthesis",
                    "message": "Organizando resultados em seções estruturadas",
                    "state": "done",
                }
            )

        if sites:
            steps.append(
                {
                    "id": "web-search-organize",
                    "type": "organize",
                    "message": f"Consolidando {len(sites)} fonte(s) públicas para a resposta",
                    "state": "done",
                }
            )

        return steps

    @classmethod
    def _search_step_message(cls, query: str) -> str:
        cleaned = str(query or "").strip()

        if not cleaned:
            return "Buscando informações na internet pública"

        return f"Buscando «{cleaned}» na internet pública"

    @classmethod
    def _hostname(cls, url: str) -> str:
        hostname = urlparse(str(url or "").strip()).hostname or str(url or "").strip()

        if hostname.startswith("www."):
            return hostname[4:]

        return hostname or "fonte"

    @classmethod
    def attach_to_assistant_metadata(
        cls,
        assistant_metadata: dict,
        *,
        tool_context: dict | None,
        pipeline_stages: list[str] | None = None,
        latency_ms: int | None = None,
    ) -> None:
        research = cls.build(
            tool_context=tool_context,
            pipeline_stages=pipeline_stages,
            latency_ms=latency_ms,
        )

        if research:
            assistant_metadata["webSearchResearch"] = research
