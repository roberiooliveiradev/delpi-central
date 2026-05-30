"""Resposta direta formatada a partir do payload de web_search (bypass LLM)."""

from __future__ import annotations

from app.domain.services.web_search_query_service import USELESS_RESULT_SOURCES
from app.infrastructure.config.settings import Settings


class ChatWebSearchDirectAnswerService:
    @classmethod
    def is_enabled(cls) -> bool:
        return Settings.CHAT_WEB_SEARCH_DIRECT_RESPONSE_ENABLED

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

        useful = [
            item
            for item in results
            if isinstance(item, dict)
            and str(item.get("source") or "") not in USELESS_RESULT_SOURCES
            and str(item.get("snippet") or "").strip()
        ]

        if not useful:
            return cls._format_no_results(payload, message=message)

        primary = next(
            (item for item in useful if item.get("source") == "instant_answer"),
            useful[0],
        )

        query = str(payload.get("query") or message or "").strip()
        title = str(primary.get("title") or query or "Resultado da busca").strip()
        snippet = str(primary.get("snippet") or "").strip()
        url = str(primary.get("url") or "").strip()

        lines = [
            f"Consultei a **internet pública** sobre *{query or 'sua pergunta'}*.",
            "",
            f"## {title}",
            "",
            snippet,
        ]

        extra_sources = cls._format_source_links(useful, exclude_url=url)

        if extra_sources:
            lines.extend(["", "**Outras fontes encontradas:**", *extra_sources])

        if url:
            lines.extend(["", f"**Fonte principal:** {url}"])

        retried = str(payload.get("retriedQuery") or "").strip()

        if retried and retried.casefold() != query.casefold():
            lines.extend(["", f"*(Busca complementada em inglês: «{retried}».)*"])

        return "\n".join(line for line in lines if line is not None).strip()

    @classmethod
    def _format_no_results(cls, payload: dict, *, message: str) -> str:
        query = str(payload.get("query") or message or "").strip()

        return (
            f"Realizei uma busca na **internet pública** sobre *{query or 'sua pergunta'}*, "
            "mas não encontrei resultados úteis para montar um resumo.\n\n"
            "Sugestões: reformule a pergunta, use termos mais específicos ou informe o tema "
            "em inglês se for um assunto técnico internacional."
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
