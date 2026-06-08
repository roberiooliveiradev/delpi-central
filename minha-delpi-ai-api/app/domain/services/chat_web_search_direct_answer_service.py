"""Resposta direta formatada a partir do payload de web_search (bypass LLM)."""

from __future__ import annotations

from urllib.parse import urlparse

from app.domain.services.web_search_query_service import USELESS_RESULT_SOURCES
from app.domain.services.chat_domain_config_service import ChatDomainConfigService


class ChatWebSearchDirectAnswerService:
    @classmethod
    def is_enabled(cls) -> bool:
        return ChatDomainConfigService.chat_web_search_direct_response_enabled()

    @classmethod
    def extract_useful_results(cls, payload: dict | None) -> list[dict]:
        if not isinstance(payload, dict):
            return []

        results = payload.get("results")

        if not isinstance(results, list):
            return []

        return [
            item
            for item in results
            if isinstance(item, dict)
            and str(item.get("source") or "") not in USELESS_RESULT_SOURCES
            and str(item.get("snippet") or "").strip()
        ]

    @classmethod
    def format(cls, payload: dict | None, *, message: str = "") -> str | None:
        if not cls.is_enabled() or not isinstance(payload, dict):
            return None

        status = str(payload.get("searchStatus") or "").strip()

        if status == "no_results":
            return cls._format_no_results(payload, message=message)

        if status != "success":
            return None

        results = payload.get("results")

        if not isinstance(results, list):
            return None

        useful = cls.extract_useful_results(payload)

        if not useful:
            return cls._format_no_results(payload, message=message)

        from app.domain.services.web_search_query_service import WebSearchQueryService

        ranked = WebSearchQueryService.rank_results_for_query(
            {"results": useful},
            str(payload.get("query") or message or ""),
        )
        ranked_useful = cls.extract_useful_results(ranked) or useful

        if payload.get("localizedFor") == "pt-BR":
            primary = ranked_useful[0]
        else:
            primary = ranked_useful[0]

        from app.domain.services.chat_assistant_content_service import (
            ChatAssistantContentService,
        )

        query = str(payload.get("query") or message or "").strip()
        default_query = ChatAssistantContentService.get(
            "web_search",
            "defaultQuery",
            default="sua pergunta",
        )
        default_title = ChatAssistantContentService.get(
            "web_search",
            "defaultTitle",
            default="Resultado da busca",
        )
        title = str(primary.get("title") or query or default_title).strip()
        snippet = str(primary.get("snippet") or "").strip()
        url = str(primary.get("url") or "").strip()

        lines = [
            ChatAssistantContentService.format(
                "web_search",
                "intro",
                query=query or default_query,
            ),
            "",
            f"## {title}",
            "",
            snippet,
        ]

        extra_sources = cls._format_source_links(useful, exclude_url=url)

        if extra_sources:
            lines.extend(
                [
                    "",
                    ChatAssistantContentService.get(
                        "web_search",
                        "otherSourcesHeader",
                    ),
                    *extra_sources,
                ]
            )

        if url and not extra_sources:
            lines.extend(
                [
                    "",
                    f"{ChatAssistantContentService.get('web_search', 'primarySourceHeader')} {url}",
                ]
            )

        if payload.get("localizedFor") == "pt-BR":
            lines.extend(
                [
                    "",
                    ChatAssistantContentService.get(
                        "web_search",
                        "localizedFooter",
                    ),
                ]
            )
        else:
            retried = str(payload.get("retriedQuery") or "").strip()

            if retried and retried.casefold() != query.casefold():
                lines.extend(
                    [
                        "",
                        ChatAssistantContentService.format(
                            "web_search",
                            "retriedQueryFooter",
                            query=retried,
                        ),
                    ]
                )

        from app.domain.services.chat_web_search_source_evaluation_service import (
            ChatWebSearchSourceEvaluationService,
        )

        warnings_block = ChatWebSearchSourceEvaluationService.format_warnings_block(payload)

        if warnings_block:
            lines.append(warnings_block)

        from app.domain.services.chat_web_search_integration_service import (
            ChatWebSearchIntegrationService,
        )

        integration_footer = ChatWebSearchIntegrationService.format_integration_footer(payload)

        if integration_footer:
            lines.append(integration_footer)

        return "\n".join(line for line in lines if line is not None).strip()

    @classmethod
    def build_sources(cls, payload: dict | None) -> list[dict]:
        if not isinstance(payload, dict) or payload.get("searchStatus") != "success":
            return []

        results = payload.get("results")

        if not isinstance(results, list):
            return []

        sources: list[dict] = []
        seen_urls: set[str] = set()

        for item in results:
            if not isinstance(item, dict):
                continue

            if str(item.get("source") or "") in USELESS_RESULT_SOURCES:
                continue

            url = str(item.get("url") or "").strip()

            if not url or url in seen_urls:
                continue

            seen_urls.add(url)
            raw_title = str(item.get("title") or "").strip()
            title = raw_title or cls._hostname(url)

            if len(title) > 56:
                title = cls._hostname(url)

            entry = {
                "title": title,
                "sourceType": "web",
                "sourceRef": url,
                "scope": "web_search",
            }

            evaluated_type = str(item.get("sourceType") or "").strip()

            if evaluated_type:
                entry["sourceType"] = evaluated_type
                entry["qualityScore"] = item.get("qualityScore")
                entry["isOfficial"] = item.get("isOfficial")

            sources.append(entry)

            if len(sources) >= max(1, int(ChatDomainConfigService.chat_web_search_max_results())):
                break

        return sources

    @classmethod
    def _hostname(cls, url: str) -> str:
        hostname = urlparse(url).hostname or url

        if hostname.startswith("www."):
            return hostname[4:]

        return hostname

    @classmethod
    def _format_no_results(cls, payload: dict, *, message: str) -> str:
        from app.domain.services.chat_assistant_content_service import (
            ChatAssistantContentService,
        )

        query = str(payload.get("query") or message or "").strip()
        default_query = ChatAssistantContentService.get(
            "web_search",
            "defaultQuery",
            default="sua pergunta",
        )

        return ChatAssistantContentService.format(
            "web_search",
            "noResults",
            query=query or default_query,
        )

    @classmethod
    def _format_source_links(cls, results: list[dict], *, exclude_url: str = "") -> list[str]:
        links: list[str] = []
        seen: set[str] = set()

        for item in results[1:6]:
            title = str(item.get("title") or "").strip()
            url = str(item.get("url") or "").strip()

            if not url or url in seen or url == exclude_url:
                continue

            seen.add(url)
            label = title if title and title != url else url
            links.append(f"- {label}: {url}")

        return links
