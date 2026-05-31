"""Salvar fontes da pesquisa web como fonte textual do projeto — Pesquisa web Fase 5."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.composition.chat_composer import make_create_project_source_use_case
from app.domain.services.chat_web_search_direct_answer_service import (
    ChatWebSearchDirectAnswerService,
)

_SAVE_REQUEST_MARKERS = (
    "salvar fontes",
    "salve as fontes",
    "salve os links",
    "guardar fontes",
    "gravar fontes",
    "salvar no projeto",
    "salvar fontes no projeto",
    "salvar fontes da pesquisa",
    "salvar fontes da pesquisa web",
)


class ChatWebSearchSaveSourcesService:
    @classmethod
    def is_save_request(cls, message: str) -> bool:
        normalized = re.sub(r"\s+", " ", str(message or "").strip().lower())

        if not normalized:
            return False

        return any(marker in normalized for marker in _SAVE_REQUEST_MARKERS)

    @classmethod
    def build_direct_answer(
        cls,
        *,
        message: str,
        user_id: str,
        session,
        previous_messages: list[Any] | None,
    ) -> str | None:
        if not cls.is_save_request(message):
            return None

        project_id = getattr(session, "project_id", None)

        if not project_id:
            return (
                "Para **salvar fontes** no projeto, selecione ou crie um **projeto** nesta conversa "
                "e repita o pedido (ex.: «salve as fontes da pesquisa no projeto»)."
            )

        bundle = cls._extract_recent_web_search(previous_messages)

        if not bundle:
            return (
                "Não encontrei uma **pesquisa na web** recente nesta conversa para salvar.\n\n"
                "Faça primeiro uma busca (ex.: «pesquise na web sobre …») e depois peça "
                "«salvar fontes no projeto»."
            )

        sources = bundle.get("sources") or []

        if not sources:
            return (
                "A última pesquisa web não trouxe fontes úteis para salvar. "
                "Tente ampliar a busca ou usar «pesquisa profunda na web»."
            )

        markdown = cls._build_markdown(bundle)
        title = cls._build_title(bundle)
        query = str(bundle.get("query") or "").strip()

        try:
            result = make_create_project_source_use_case().execute_text(
                user_id=str(user_id),
                project_id=str(project_id),
                title=title,
                content=markdown,
                metadata={
                    "origin": "web_search",
                    "searchQuery": query,
                    "sourceCount": len(sources),
                    "savedAt": datetime.now(timezone.utc).isoformat(),
                },
            )
        except ValueError as exc:
            return f"Não foi possível salvar as fontes no projeto: {exc}"

        return (
            f"Salvei **{len(sources)}** fonte(s) da pesquisa web no **projeto atual** "
            f"como documento **«{result.title}»**.\n\n"
            "Elas ficam disponíveis em **Fontes do projeto** e podem ser usadas em novas "
            "perguntas neste projeto."
        )

    @classmethod
    def _extract_recent_web_search(cls, previous_messages: list[Any] | None) -> dict | None:
        if not previous_messages:
            return None

        for item in reversed(previous_messages[-16:]):
            role = str(getattr(item, "role", None) or cls._dict_value(item, "role") or "").lower()

            if role != "assistant":
                continue

            metadata = cls._message_metadata(item)

            if not metadata:
                continue

            research = metadata.get("webSearchResearch")

            if not isinstance(research, dict):
                sources = [
                    entry
                    for entry in (metadata.get("sources") or [])
                    if isinstance(entry, dict)
                    and str(entry.get("sourceType") or entry.get("scope") or "") in {
                        "web",
                        "web_search",
                    }
                ]

                if not sources:
                    continue

                return {
                    "query": "",
                    "sources": sources,
                    "research": None,
                }

            payload_sources = cls._sources_from_research(research, metadata)

            if not payload_sources:
                continue

            query = str(research.get("query") or "").strip()

            return {
                "query": query,
                "sources": payload_sources,
                "research": research,
                "projectName": None,
            }

        return None

    @classmethod
    def _sources_from_research(cls, research: dict, metadata: dict) -> list[dict]:
        sites = research.get("sites")

        if isinstance(sites, list) and sites:
            collected: list[dict] = []

            for site in sites:
                if not isinstance(site, dict):
                    continue

                url = str(site.get("url") or "").strip()

                if not url:
                    continue

                collected.append(
                    {
                        "title": str(site.get("title") or site.get("hostname") or url).strip(),
                        "sourceRef": url,
                        "sourceType": "web",
                        "isOfficial": site.get("isOfficial"),
                    }
                )

            if collected:
                return collected

        payload = {"searchStatus": "success", "results": []}
        tool_calls = metadata.get("toolCalls") or []

        for tool_call in reversed(tool_calls):
            if not isinstance(tool_call, dict):
                continue

            if str(tool_call.get("name") or "") != "web_search":
                continue

            data = tool_call.get("data")

            if isinstance(data, dict):
                payload = data
                break

        built = ChatWebSearchDirectAnswerService.build_sources(payload)

        return built

    @classmethod
    def _build_title(cls, bundle: dict) -> str:
        query = str(bundle.get("query") or "").strip()
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        if query:
            short = query if len(query) <= 48 else f"{query[:45]}…"

            return f"Pesquisa web — {short} ({stamp})"

        return f"Fontes pesquisa web ({stamp})"

    @classmethod
    def _build_markdown(cls, bundle: dict) -> str:
        query = str(bundle.get("query") or "").strip()
        sources = bundle.get("sources") or []
        lines = ["# Fontes — pesquisa na internet", ""]

        if query:
            lines.extend([f"**Consulta:** {query}", ""])

        lines.append(f"**Total de fontes:** {len(sources)}")
        lines.append("")

        for index, source in enumerate(sources, start=1):
            title = str(source.get("title") or source.get("sourceRef") or f"Fonte {index}").strip()
            url = str(source.get("sourceRef") or source.get("url") or "").strip()
            official = source.get("isOfficial") is True
            badge = " (oficial)" if official else ""

            lines.append(f"## {index}. {title}{badge}")

            if url:
                lines.append(f"- URL: {url}")

            lines.append("")

        research = bundle.get("research")

        if isinstance(research, dict):
            warnings = research.get("warnings")

            if isinstance(warnings, list) and warnings:
                lines.extend(["## Observações", ""])

                for warning in warnings[:6]:
                    token = str(warning or "").strip()

                    if token:
                        lines.append(f"- {token}")

                lines.append("")

        lines.append(
            "_Documento gerado automaticamente a partir da pesquisa web do chat Minha DELPI._"
        )

        return "\n".join(lines).strip()

    @staticmethod
    def _message_metadata(message) -> dict:
        metadata = getattr(message, "metadata", None)

        if isinstance(metadata, dict):
            return metadata

        return ChatWebSearchSaveSourcesService._dict_value(message, "metadata") or {}

    @staticmethod
    def _dict_value(message, key: str):
        if isinstance(message, dict):
            return message.get(key)

        return None
