"""Chips pós-pesquisa web — Playbook pesquisa web, Fase 5."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.infrastructure.content.content_service import ContentService


@lru_cache(maxsize=1)
def _playbook() -> dict[str, Any]:
    return ContentService.personality_playbook()


class ChatWebSearchFollowUpService:
    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict,
        *,
        tool_context: dict | None,
        message: str,
        had_attachments: bool = False,
    ) -> None:
        payload = None

        if isinstance(tool_context, dict):
            raw_payload = tool_context.get("webSearchPayload")

            if isinstance(raw_payload, dict):
                payload = raw_payload

        if not payload and not metadata.get("webSearchResearch"):
            return

        suggestions = cls.build(
            payload=payload,
            message=message,
            research=metadata.get("webSearchResearch"),
            had_attachments=had_attachments,
        )

        if suggestions:
            metadata["webSearchFollowUpSuggestions"] = suggestions

    @classmethod
    def build(
        cls,
        *,
        payload: dict | None,
        message: str = "",
        research: dict | None = None,
        had_attachments: bool = False,
    ) -> list[dict[str, str]]:
        status = cls._resolve_status(payload, research)

        if status == "no_results":
            labels = list(_playbook().get("webSearchFollowUpChipsNoResults") or [])
        else:
            labels = list(_playbook().get("webSearchFollowUpChips") or [])

        queries = _playbook().get("webSearchFollowUpQueries") or {}
        topic = cls._resolve_topic(payload, message)
        integration_mode = str((payload or {}).get("integrationMode") or "").strip()
        prefer_official = (payload or {}).get("preferOfficial") is True

        if status != "no_results" and integration_mode == "source_compare":
            labels = cls._prepend_unique(labels, "Comparar fontes")

        if status != "no_results" and prefer_official:
            labels = cls._prepend_unique(labels, "Só fontes oficiais")

        if had_attachments and status == "no_results":
            labels = cls._prepend_unique(labels, "Usar anexo")

        suggestions: list[dict[str, str]] = []

        for label in labels[:8]:
            template = str(queries.get(label) or "").strip()

            if not template:
                continue

            query = (
                template.replace("{query}", "{{searchQuery}}")
                .replace("{topic}", "{{searchQuery}}")
                .strip()
            )

            if not query:
                continue

            suggestions.append({"label": str(label), "query": query})

        return suggestions

    @classmethod
    def _resolve_status(cls, payload: dict | None, research: dict | None) -> str:
        if isinstance(payload, dict):
            status = str(payload.get("searchStatus") or "").strip()

            if status:
                return status

        if isinstance(research, dict):
            status = str(research.get("searchStatus") or "").strip()

            if status:
                return status

        if isinstance(research, dict) and (research.get("sourceCount") or 0) > 0:
            return "success"

        return "success"

    @classmethod
    def _resolve_topic(cls, payload: dict | None, message: str) -> str:
        if isinstance(payload, dict):
            query = str(payload.get("query") or "").strip()

            if query:
                return query

        return str(message or "").strip() or "o tema pesquisado"

    @staticmethod
    def _prepend_unique(labels: list, value: str) -> list:
        cleaned = [str(item) for item in labels if str(item).strip()]

        if value in cleaned:
            return cleaned

        return [value, *cleaned]
