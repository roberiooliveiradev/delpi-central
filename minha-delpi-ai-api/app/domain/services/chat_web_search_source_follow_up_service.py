"""Follow-up sobre fontes da última pesquisa web (ex.: listar links)."""

from __future__ import annotations

from typing import Any

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
