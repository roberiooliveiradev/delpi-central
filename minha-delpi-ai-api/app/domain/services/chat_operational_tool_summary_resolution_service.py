"""Resolução de resumo substantivo a partir de metadata de tool operacional."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_humanized_data_response_service import (
    ChatHumanizedDataResponseService,
)
from app.domain.services.chat_presentation_prose_delivery_service import (
    ChatPresentationProseDeliveryService,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)


@lru_cache(maxsize=1)
def _content() -> dict[str, Any]:
    return ChatAssistantContentService.load_bundle("data_interpretation")


class ChatOperationalToolSummaryResolutionService:
    @classmethod
    def resolve_tool_summary(cls, tool_meta: dict) -> dict | None:
        path = str(tool_meta.get("path") or "").strip()
        commentary = ChatHumanizedDataResponseService.resolve_commentary_from_metadata(tool_meta)
        commentary_lines: list[str] = []

        if isinstance(commentary, dict):
            summary = str(commentary.get("summary") or "").strip()

            if summary:
                commentary_lines.append(summary)

            commentary_lines.extend(
                str(line).strip()
                for line in (commentary.get("highlights") or [])
                if str(line or "").strip() and str(line).strip() not in commentary_lines
            )
            narrative = str(commentary.get("narrativeInsight") or "").strip()

            if narrative and narrative not in commentary_lines:
                commentary_lines.insert(0, narrative)

            attention = [
                str(line).strip()
                for line in (commentary.get("attention") or [])
                if str(line or "").strip()
            ]
            commentary_lines.extend(
                line for line in attention if line not in commentary_lines
            )

        effective_humanized = ChatPresentationProseDeliveryService.resolve_effective_humanized_summary(
            tool_meta,
        )

        if isinstance(effective_humanized, dict):
            title = str(effective_humanized.get("titulo") or "").strip()
            lines = list(
                ChatPresentationProseDeliveryService.resolve_humanized_lines_for_facts(
                    tool_meta,
                )
            )

            for line in commentary_lines:
                if line not in lines:
                    lines.append(line)

            if (
                title
                and title.lower() not in cls._generic_titles()
                and cls._has_substantive_lines(lines)
            ):
                return {"titulo": title, "linhas": lines, "path": path}

            if cls._has_substantive_lines(lines):
                return {
                    "titulo": title or cls._title_from_path(path),
                    "linhas": lines,
                    "path": path,
                }

        if cls._has_substantive_lines(commentary_lines):
            return {
                "titulo": cls._title_from_path(path),
                "linhas": commentary_lines,
                "path": path,
            }

        preview = str(tool_meta.get("responsePreview") or "").strip()

        if not preview or not path:
            return None

        try:
            data = json.loads(preview)
            represented = ExternalActionResultPresenter().present(data, path=path)
        except (json.JSONDecodeError, TypeError, ValueError):
            return None

        if not isinstance(represented, dict):
            return None

        title = str(represented.get("titulo") or cls._title_from_path(path)).strip()
        lines = [
            str(line).strip()
            for line in (represented.get("linhas") or [])
            if str(line or "").strip()
        ]

        if not cls._has_substantive_lines(lines):
            return None

        return {"titulo": title, "linhas": lines, "path": path}

    @classmethod
    def _generic_line_markers(cls) -> tuple[str, ...]:
        return tuple(str(item) for item in (_content().get("genericLineMarkers") or ()))

    @classmethod
    def _generic_titles(cls) -> tuple[str, ...]:
        return tuple(str(item) for item in (_content().get("genericTitles") or ()))

    @classmethod
    def _has_substantive_lines(cls, lines: list[str]) -> bool:
        substantive = [line for line in lines if not cls._is_generic_line(line)]

        return len(substantive) >= 1

    @classmethod
    def _is_generic_line(cls, line: str) -> bool:
        lowered = line.lower()

        return any(marker in lowered for marker in cls._generic_line_markers())

    @classmethod
    def _title_from_path(cls, path: str) -> str:
        lowered = str(path or "").lower()
        titles = _content().get("pathTitles") or {}

        if "/guide" in lowered:
            return str(titles.get("guide") or "Consulta operacional")

        if "/stock" in lowered:
            return str(titles.get("stock") or "Consulta operacional")

        if "/structure" in lowered:
            return str(titles.get("structure") or "Consulta operacional")

        if "/inspection" in lowered:
            return str(titles.get("inspection") or "Consulta operacional")

        return str(titles.get("default") or "Consulta operacional")
