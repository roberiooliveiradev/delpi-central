"""Chips pós-pesquisa web — Playbook pesquisa web, Fase 5."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


@lru_cache(maxsize=1)
def _playbook() -> dict[str, Any]:
    return ChatAssistantContentService.load_personality_playbook()


class ChatWebSearchFollowUpService:
    @classmethod
    def is_primary_web_search_turn(
        cls,
        tool_calls: list | None = None,
        *,
        metadata: dict | None = None,
    ) -> bool:
        """Web_search foi a ferramenta principal do turno (sem action operacional paralela)."""
        had_web = False
        had_operational = False

        for call in tool_calls or []:
            if not isinstance(call, dict):
                continue

            name = str(call.get("name") or "").strip()

            if name == "web_search":
                status = str((call.get("metadata") or {}).get("searchStatus") or "").strip()

                if status in {"", "success"}:
                    had_web = True

                continue

            if name == "execute_external_action":
                had_operational = True
                continue

            path = str((call.get("metadata") or {}).get("path") or call.get("path") or "")

            if path.startswith("/"):
                had_operational = True

        if had_web:
            return not had_operational

        if isinstance(metadata, dict):
            research = metadata.get("webSearchResearch")

            if isinstance(research, dict) and str(research.get("searchStatus") or "") == "success":
                return True

            web_search = metadata.get("webSearch")

            if isinstance(web_search, dict) and web_search.get("enabled"):
                return True

        return False

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
        prepend = _playbook().get("webSearchFollowUpPrepend") or {}

        if status == "no_results":
            labels = list(_playbook().get("webSearchFollowUpChipsNoResults") or [])
        else:
            labels = list(_playbook().get("webSearchFollowUpChips") or [])

        queries = _playbook().get("webSearchFollowUpQueries") or {}
        integration_mode = str((payload or {}).get("integrationMode") or "").strip()
        prefer_official = (payload or {}).get("preferOfficial") is True

        if status != "no_results" and integration_mode == "source_compare":
            labels = cls._prepend_unique(
                labels,
                str(prepend.get("sourceCompare") or "").strip(),
            )

        if status != "no_results" and prefer_official:
            labels = cls._prepend_unique(
                labels,
                str(prepend.get("preferOfficial") or "").strip(),
            )

        if had_attachments and status == "no_results":
            labels = cls._prepend_unique(
                labels,
                str(prepend.get("attachmentNoResults") or "").strip(),
            )

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

        fallback = str(_playbook().get("webSearchDefaultTopic") or "").strip()

        return str(message or "").strip() or fallback

    @staticmethod
    def _prepend_unique(labels: list, value: str) -> list:
        if not value:
            return [str(item) for item in labels if str(item).strip()]

        cleaned = [str(item) for item in labels if str(item).strip()]

        if value in cleaned:
            return cleaned

        return [value, *cleaned]
