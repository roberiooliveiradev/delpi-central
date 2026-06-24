"""Tabelas operacionais embutidas em markdown no modo Texto — Playbook 12 R14."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_operational_response_profile_service import (
    ChatOperationalResponseProfileService,
)
from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)
from app.domain.services.chat_rich_presentation_text_service import (
    ChatRichPresentationTextService,
)

_MAX_TABLE_ROWS = 50


class ChatPresentationTableMarkdownService:
    @classmethod
    def embed_tables_in_text_presentation(cls, metadata: dict[str, Any]) -> None:
        if not isinstance(metadata, dict):
            return

        if metadata.get("ok") is False:
            return

        if not cls._should_embed_tables(metadata):
            return

        text_presentation = metadata.get("textPresentation")

        if not isinstance(text_presentation, dict):
            return

        markdown = str(text_presentation.get("markdown") or "").strip()

        if not markdown:
            return

        sections = cls.build_table_sections(metadata)

        if not sections:
            return

        body = markdown

        for section in sections:
            if section in body:
                continue

            body = f"{body}\n\n{section}".strip()

        text_presentation["markdown"] = body

    @classmethod
    def build_table_sections(cls, metadata: dict[str, Any]) -> list[str]:
        sections: list[str] = []

        for table in cls._collect_tables(metadata):
            section = cls._table_section(table)

            if section:
                sections.append(section)

        return sections

    @classmethod
    def _table_section(cls, table: dict[str, Any]) -> str:
        title = str(table.get("title") or "").strip()
        columns_raw = table.get("columns")
        rows = table.get("rows")

        if not isinstance(rows, list) or not rows:
            return ""

        dict_rows = [row for row in rows if isinstance(row, dict)][: _MAX_TABLE_ROWS]

        if not dict_rows:
            return ""

        columns: list[tuple[str, str]] = []

        if isinstance(columns_raw, list):
            for column in columns_raw:
                if not isinstance(column, dict):
                    continue

                key = str(column.get("key") or "").strip()
                label = str(column.get("label") or key).strip()

                if key:
                    columns.append((key, label or key))

        if not columns:
            sample = dict_rows[0]

            columns = [
                (key, str(key).replace("_", " ").strip())
                for key in sample.keys()
                if str(key).strip() and not str(key).startswith("_")
            ]

        if not columns:
            return ""

        from app.domain.services.external_actions.presenters.presentation_table_host_service import (
            markdown_table,
        )

        table_lines = markdown_table(columns, dict_rows)

        if not table_lines:
            return ""

        truncated = len(rows) > len(dict_rows)
        heading = title or ChatAssistantContentService.get(
            "presenter_content",
            "generic",
            "tableSectionHeader",
            default="**Tabela**",
        )

        if title:
            heading = f"**{title}**"

        parts = [heading, "", *table_lines]

        if truncated:
            parts.append("")
            parts.append(
                ChatAssistantContentService.format(
                    "presenter_content",
                    "generic",
                    "tableRowsTruncated",
                    remaining=len(rows) - len(dict_rows),
                )
            )

        return "\n".join(parts).strip()

    @classmethod
    def _collect_tables(cls, metadata: dict[str, Any]) -> list[dict[str, Any]]:
        collected: list[dict[str, Any]] = []
        seen: set[str] = set()

        for key in ("profileTablePresentation", "tablePresentation", "presentation"):
            table = metadata.get(key)

            if isinstance(table, dict) and table.get("type") == "table":
                signature = cls._table_signature(table)

                if signature and signature not in seen:
                    collected.append(table)
                    seen.add(signature)

        bulk = metadata.get("tablePresentations")

        if isinstance(bulk, list):
            for table in bulk:
                if not isinstance(table, dict) or table.get("type") != "table":
                    continue

                signature = cls._table_signature(table)

                if signature and signature not in seen:
                    collected.append(table)
                    seen.add(signature)

        return collected

    @staticmethod
    def _table_signature(table: dict[str, Any]) -> str:
        title = str(table.get("title") or "").strip()
        role = str(table.get("role") or "").strip()
        rows = table.get("rows")

        row_count = len(rows) if isinstance(rows, list) else 0

        return f"{role}|{title}|{row_count}"

    @classmethod
    def _should_embed_tables(cls, metadata: dict[str, Any]) -> bool:
        from app.domain.services.chat_presentation_text_mode_service import (
            ChatPresentationTextModeService,
        )

        if not ChatPresentationTextModeService.should_embed_in_markdown(metadata):
            return False

        path = str(metadata.get("path") or "").strip()
        entity = cls._resolve_entity(path)
        profile = ChatPresentationProfileService.resolve_profile(path, entity)

        return profile.get("textEmbedTablesInMarkdown") is True

    @classmethod
    def _resolve_entity(cls, path: str) -> str | None:
        entity = str(
            ChatOperationalResponseProfileService.resolve({}, path=path).entity or ""
        ).strip()

        return entity or None
