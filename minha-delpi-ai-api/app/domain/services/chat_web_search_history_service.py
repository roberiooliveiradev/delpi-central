"""Histórico recente de pesquisa web na conversa — compartilhado por save/listagem."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_web_search_direct_answer_service import (
    ChatWebSearchDirectAnswerService,
)


class ChatWebSearchHistoryService:
    @classmethod
    def extract_recent_bundle(cls, previous_messages: list[Any] | None) -> dict | None:
        if not previous_messages:
            return None

        for item in reversed(previous_messages[-16:]):
            role = str(
                getattr(item, "role", None) or cls._dict_value(item, "role") or ""
            ).lower()

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
                    and str(entry.get("sourceType") or entry.get("scope") or "")
                    in {"web", "web_search"}
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
            }

        return None

    @classmethod
    def has_recent_web_search(cls, previous_messages: list[Any] | None) -> bool:
        return cls.extract_recent_bundle(previous_messages) is not None

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

            tool_meta = tool_call.get("metadata") or {}

            if tool_meta.get("ok") is True:
                payload = tool_meta
                break

        return ChatWebSearchDirectAnswerService.build_sources(payload)

    @staticmethod
    def _message_metadata(message: Any) -> dict:
        metadata = getattr(message, "metadata", None)

        if isinstance(metadata, dict):
            return metadata

        if isinstance(message, dict):
            value = message.get("metadata")

            return value if isinstance(value, dict) else {}

        return {}

    @staticmethod
    def _dict_value(message: Any, key: str):
        if isinstance(message, dict):
            return message.get(key)

        return None
