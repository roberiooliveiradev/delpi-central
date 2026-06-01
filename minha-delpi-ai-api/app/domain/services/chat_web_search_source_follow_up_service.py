"""Follow-up sobre fontes da última pesquisa web (chips pós-pesquisa)."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_web_search_history_service import (
    ChatWebSearchHistoryService,
)


class ChatWebSearchSourceFollowUpService:
    _LIST_SOURCES_MARKERS = (
        "liste os links",
        "lista os links",
        "listar os links",
        "liste as fontes",
        "lista as fontes",
        "listar as fontes",
        "links das fontes",
        "links da pesquisa",
        "link das fontes",
        "mostre os links",
        "mostra os links",
        "mostrar os links",
        "quais foram as fontes",
        "quais sao as fontes",
        "quais são as fontes",
        "abrir fontes",
        "urls das fontes",
        "url das fontes",
    )

    _WEB_CONTEXT_TERMS = (
        "pesquisa web",
        "busca na web",
        "pesquisa na web",
        "fontes da pesquisa",
        "fontes da busca",
        "fonte documental",
        "fontes documentais",
        "internet",
        "resultados da pesquisa",
    )

    _SUMMARIZE_MARKERS = (
        "resuma em topicos",
        "resuma em tópicos",
        "resumir pesquisa",
        "resumir a pesquisa",
        "resumo da pesquisa",
        "resumo dos resultados",
        "resultados da pesquisa web",
    )

    _EXTRACT_PARAMS_MARKERS = (
        "extraia parametros",
        "extraia parâmetros",
        "parametros tecnicos",
        "parâmetros técnicos",
        "tabela markdown",
    )

    _COMPARE_MARKERS = (
        "compare as fontes",
        "comparar as fontes",
        "compare as fontes da pesquisa",
        "destaque divergencias",
        "destaque divergências",
    )

    @classmethod
    def is_web_research_follow_up_request(cls, message: str | None) -> bool:
        return (
            cls.is_list_sources_request(message)
            or cls.is_summarize_request(message)
            or cls.is_extract_params_request(message)
            or cls.is_compare_sources_request(message)
        )

    @classmethod
    def blocks_external_action_selection(
        cls,
        message: str | None,
        previous_messages: list[Any] | None = None,
    ) -> bool:
        if not cls.is_web_research_follow_up_request(message):
            return False

        return ChatWebSearchHistoryService.has_recent_web_search(previous_messages)

    @classmethod
    def build_post_search_follow_up_answer(
        cls,
        message: str | None,
        previous_messages: list[Any] | None,
    ) -> str | None:
        return (
            cls.build_list_links_answer(message, previous_messages)
            or cls.build_summarize_answer(message, previous_messages)
            or cls.build_extract_params_answer(message, previous_messages)
            or cls.build_compare_sources_answer(message, previous_messages)
        )

    @classmethod
    def is_list_sources_request(cls, message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if not any(marker in normalized for marker in cls._LIST_SOURCES_MARKERS):
            if not (
                ("liste" in normalized or "lista" in normalized or "listar" in normalized)
                and ("link" in normalized or "fonte" in normalized or "url" in normalized)
            ):
                return False

        return any(term in normalized for term in cls._WEB_CONTEXT_TERMS) or (
            "fonte" in normalized and ("acima" in normalized or "anterior" in normalized)
        )

    @classmethod
    def build_list_links_answer(
        cls,
        message: str | None,
        previous_messages: list[Any] | None,
    ) -> str | None:
        if not cls.is_list_sources_request(message):
            return None

        bundle = ChatWebSearchHistoryService.extract_recent_bundle(previous_messages)

        if not bundle:
            return (
                "Não encontrei uma **pesquisa na web** recente nesta conversa.\n\n"
                "Faça primeiro uma busca (ex.: «pesquise na web sobre …») e depois peça "
                "para listar os links das fontes."
            )

        sources = bundle.get("sources") or []

        if not sources:
            return (
                "A última pesquisa web não trouxe fontes com URL para listar. "
                "Tente ampliar a busca ou usar «pesquisa profunda na web»."
            )

        query = str(bundle.get("query") or "").strip()
        lines = ["**Links das fontes da pesquisa web**", ""]

        if query:
            lines.append(f"*Consulta:* {query}")
            lines.append("")

        for index, source in enumerate(sources, start=1):
            title = str(
                source.get("title") or source.get("sourceRef") or f"Fonte {index}"
            ).strip()
            url = str(source.get("sourceRef") or source.get("url") or "").strip()

            if not url:
                continue

            official = source.get("isOfficial") is True
            badge = " *(oficial)*" if official else ""
            lines.append(f"{index}. [{title}]({url}){badge}")

        if len(lines) <= 2:
            return (
                "Não há URLs utilizáveis nas fontes da última pesquisa web. "
                "Repita a busca ou peça «pesquisa profunda na web»."
            )

        return "\n".join(lines).strip()

    @classmethod
    def is_summarize_request(cls, message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if not any(marker in normalized for marker in cls._SUMMARIZE_MARKERS):
            if not (
                ("resuma" in normalized or "resumo" in normalized)
                and "pesquisa web" in normalized
            ):
                return False

        return any(term in normalized for term in cls._WEB_CONTEXT_TERMS)

    @classmethod
    def is_extract_params_request(cls, message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if not any(marker in normalized for marker in cls._EXTRACT_PARAMS_MARKERS):
            if "parametr" not in normalized or "pesquisa web" not in normalized:
                return False

        return any(term in normalized for term in cls._WEB_CONTEXT_TERMS) or (
            "fonte" in normalized and "pesquisa" in normalized
        )

    @classmethod
    def is_compare_sources_request(cls, message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if not any(marker in normalized for marker in cls._COMPARE_MARKERS):
            if not (
                ("compare" in normalized or "compar" in normalized)
                and "fonte" in normalized
                and "pesquisa web" in normalized
            ):
                return False

        return True

    @classmethod
    def build_summarize_answer(
        cls,
        message: str | None,
        previous_messages: list[Any] | None,
    ) -> str | None:
        if not cls.is_summarize_request(message):
            return None

        bundle = ChatWebSearchHistoryService.extract_recent_bundle(previous_messages)

        if not bundle:
            return cls._missing_web_search_message()

        query = str(bundle.get("query") or "").strip()
        lines = ["**Resumo em tópicos — pesquisa web**", ""]

        if query:
            lines.append(f"*Consulta:* {query}")
            lines.append("")

        bullets = cls._topic_bullets_from_bundle(bundle)

        if not bullets:
            return (
                "A última pesquisa web não trouxe trechos utilizáveis para resumir. "
                "Tente «pesquisa profunda na web» ou reformule o tema."
            )

        lines.extend(bullets)
        return "\n".join(lines).strip()

    @classmethod
    def build_extract_params_answer(
        cls,
        message: str | None,
        previous_messages: list[Any] | None,
    ) -> str | None:
        if not cls.is_extract_params_request(message):
            return None

        bundle = ChatWebSearchHistoryService.extract_recent_bundle(previous_messages)

        if not bundle:
            return cls._missing_web_search_message()

        rows = cls._parameter_rows_from_bundle(bundle)

        if not rows:
            return (
                "Não encontrei parâmetros técnicos explícitos nos trechos da última pesquisa web. "
                "Peça «pesquisa profunda na web» com o nome do produto ou norma."
            )

        query = str(bundle.get("query") or "").strip()
        lines = ["**Parâmetros técnicos (trechos das fontes)**", ""]

        if query:
            lines.append(f"*Consulta:* {query}")
            lines.append("")

        lines.append("| Dado / parâmetro | Fonte |")
        lines.append("| --- | --- |")

        for param, source in rows[:12]:
            param_cell = param.replace("|", "\\|")
            lines.append(f"| {param_cell} | {source} |")

        if len(rows) > 12:
            lines.append("")
            lines.append(f"_… e mais {len(rows) - 12} linha(s) nas fontes originais._")

        return "\n".join(lines).strip()

    @classmethod
    def build_compare_sources_answer(
        cls,
        message: str | None,
        previous_messages: list[Any] | None,
    ) -> str | None:
        if not cls.is_compare_sources_request(message):
            return None

        bundle = ChatWebSearchHistoryService.extract_recent_bundle(previous_messages)

        if not bundle:
            return cls._missing_web_search_message()

        sources = bundle.get("sources") or []
        snippets = cls._snippet_entries_from_bundle(bundle)

        if len(sources) < 2 and len(snippets) < 2:
            return (
                "Há poucas fontes na última pesquisa web para comparar. "
                "Use «pesquisa profunda na web» para ampliar o conjunto."
            )

        query = str(bundle.get("query") or "").strip()
        lines = ["**Comparação das fontes da pesquisa web**", ""]

        if query:
            lines.append(f"*Consulta:* {query}")
            lines.append("")

        for index, entry in enumerate(snippets[:8], start=1):
            title = entry["title"]
            url = entry["url"]
            snippet = entry["snippet"]
            official = " *(oficial)*" if entry.get("isOfficial") else ""
            lines.append(f"### {index}. {title}{official}")
            lines.append("")
            lines.append(snippet[:500] + ("…" if len(snippet) > 500 else ""))

            if url:
                lines.append("")
                lines.append(f"[Abrir fonte]({url})")

            lines.append("")

        divergences = cls._heuristic_divergence_note(snippets)

        if divergences:
            lines.append("**Possíveis divergências**")
            lines.append("")
            lines.append(divergences)

        lines.append(
            "_Revise os links acima; a comparação automática usa apenas os trechos "
            "retornados pela busca, não o conteúdo integral das páginas._"
        )

        return "\n".join(lines).strip()

    @classmethod
    def _missing_web_search_message(cls) -> str:
        return (
            "Não encontrei uma **pesquisa na web** recente nesta conversa.\n\n"
            "Faça primeiro uma busca (ex.: «pesquise na web sobre …») e depois use "
            "os atalhos **Após pesquisa web**."
        )

    @classmethod
    def _topic_bullets_from_bundle(cls, bundle: dict) -> list[str]:
        bullets: list[str] = []

        for entry in cls._snippet_entries_from_bundle(bundle)[:10]:
            title = entry["title"]
            snippet = entry["snippet"]
            host = cls._hostname(entry.get("url") or "")
            excerpt = cls._first_sentence(snippet)

            if not excerpt:
                continue

            bullets.append(f"- **{title}** ({host}): {excerpt}")

        return bullets

    @classmethod
    def _parameter_rows_from_bundle(cls, bundle: dict) -> list[tuple[str, str]]:
        rows: list[tuple[str, str]] = []
        seen: set[str] = set()
        param_pattern = re.compile(
            r"(?:"
            r"\d+[\s,.]?\d*\s*(?:mm|cm|m|kg|g|v|a|w|kw|hz|°c|bar|mpa|rpm|%|pol)\b|"
            r"(?:ip\d{2}|iec\s*\d+|nr[\s-]?\d+|abnt\s*n?br\s*\d+)|"
            r"(?:modelo|serie|série|tensao|tensão|corrente|potencia|potência|"
            r"dimensao|dimensão|peso|material|classe)\s*[:\-]?\s*[\w\s./\-]{2,40}"
            r")",
            re.IGNORECASE,
        )

        for entry in cls._snippet_entries_from_bundle(bundle):
            title = entry["title"]
            snippet = entry["snippet"]
            source_label = f"[{title}]({entry['url']})" if entry.get("url") else title

            for match in param_pattern.finditer(snippet):
                token = re.sub(r"\s+", " ", match.group(0)).strip()

                if len(token) < 4:
                    continue

                key = token.casefold()

                if key in seen:
                    continue

                seen.add(key)
                rows.append((token, source_label))

            if len(rows) >= 12:
                break

        if rows:
            return rows

        for entry in cls._snippet_entries_from_bundle(bundle)[:6]:
            excerpt = cls._first_sentence(entry["snippet"])

            if not excerpt:
                continue

            source_label = (
                f"[{entry['title']}]({entry['url']})" if entry.get("url") else entry["title"]
            )
            rows.append((excerpt[:120], source_label))

        return rows

    @classmethod
    def _snippet_entries_from_bundle(cls, bundle: dict) -> list[dict]:
        entries: list[dict] = []
        seen_urls: set[str] = set()
        results = bundle.get("results") or []

        for item in results:
            if not isinstance(item, dict):
                continue

            url = str(item.get("url") or "").strip()
            snippet = str(item.get("snippet") or "").strip()

            if not snippet:
                continue

            key = url.casefold() if url else snippet[:80].casefold()

            if key in seen_urls:
                continue

            seen_urls.add(key)
            entries.append(
                {
                    "title": str(item.get("title") or cls._hostname(url) or "Fonte").strip(),
                    "url": url,
                    "snippet": snippet,
                    "isOfficial": False,
                }
            )

        for source in bundle.get("sources") or []:
            if not isinstance(source, dict):
                continue

            url = str(source.get("sourceRef") or source.get("url") or "").strip()
            key = url.casefold()

            if key and key in seen_urls:
                continue

            title = str(source.get("title") or cls._hostname(url) or "Fonte").strip()
            snippet = str(source.get("snippet") or "").strip()

            if not snippet and not url:
                continue

            if key:
                seen_urls.add(key)

            entries.append(
                {
                    "title": title,
                    "url": url,
                    "snippet": snippet or f"Fonte: {title}",
                    "isOfficial": source.get("isOfficial") is True,
                }
            )

        return entries

    @classmethod
    def _heuristic_divergence_note(cls, snippets: list[dict]) -> str:
        if len(snippets) < 2:
            return ""

        hosts = {cls._hostname(entry.get("url") or "") for entry in snippets}
        hosts.discard("")

        if len(hosts) >= 2:
            return (
                "As fontes vêm de **domínios diferentes**; confira números e especificações "
                "no site do fabricante ou manual oficial antes de decidir."
            )

        return (
            "Os trechos podem enfatizar aspectos distintos do mesmo tema; "
            "valide dados críticos na documentação oficial."
        )

    @staticmethod
    def _hostname(url: str) -> str:
        hostname = urlparse(str(url or "").strip()).hostname or ""

        if hostname.startswith("www."):
            return hostname[4:]

        return hostname or "fonte"

    @staticmethod
    def _first_sentence(text: str) -> str:
        cleaned = re.sub(r"\s+", " ", str(text or "").strip())

        if not cleaned:
            return ""

        parts = re.split(r"(?<=[.!?])\s+", cleaned, maxsplit=1)

        return parts[0][:280]
