"""Enriquecimento canônico de narrativa humanizada — qualquer action com painéis ricos."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_presentation_operational_table_service import (
    ChatPresentationOperationalTableService as _OpsTable,
)
from app.domain.services.chat_presentation_route_policy_service import (
    ChatPresentationRoutePolicyService,
)
from app.domain.services.chat_rich_presentation_text_service import (
    ChatRichPresentationTextService,
)

_ATTENTION_HEADER_RE = re.compile(r"\*\*Pontos de atenção")
_PANORAMA_HEADER_RE = re.compile(r"\*\*Panorama\*\*")
_SCOPE_MARKER = "<!-- section:scope -->"


class ChatPresentationHumanizedNarrativeService:
    @classmethod
    def enrich_metadata(cls, metadata: dict[str, Any]) -> None:
        if not isinstance(metadata, dict):
            return

        text_presentation = metadata.get("textPresentation")

        if not isinstance(text_presentation, dict):
            return

        markdown = str(text_presentation.get("markdown") or "").strip()

        if not markdown or not cls._should_enrich(metadata, markdown):
            return

        body = cls._build_enriched_body(metadata, markdown)

        if not body:
            return

        title = str(text_presentation.get("title") or "").strip()
        header = f"### {title}" if title and title not in markdown.splitlines()[0] else ""

        if header and markdown.startswith("###"):
            first_line = markdown.splitlines()[0]
            remainder = "\n".join(markdown.splitlines()[1:]).strip()
            merged_body = cls._merge_scope_and_body(remainder, body)
            text_presentation["markdown"] = f"{first_line}\n\n{merged_body}".strip()
            return

        if header:
            text_presentation["markdown"] = f"{header}\n\n{body}".strip()
            return

        text_presentation["markdown"] = body

    @classmethod
    def _should_enrich(cls, metadata: dict[str, Any], markdown: str) -> bool:
        path = str(metadata.get("path") or "").lower()

        if ChatPresentationRoutePolicyService.is_stock_route(
            path,
            entity=cls._metadata_entity(metadata),
        ):
            return False

        visuals = ChatRichPresentationTextService.count_complementary_visuals(metadata)

        if visuals.get("table", 0) + visuals.get("kpi", 0) + visuals.get("chart", 0) < 1:
            return False

        if _PANORAMA_HEADER_RE.search(markdown) and _ATTENTION_HEADER_RE.search(markdown):
            return False

        body_lines = [
            line.strip()
            for line in markdown.splitlines()
            if line.strip()
            and not line.strip().startswith("###")
            and _SCOPE_MARKER not in line
        ]

        return len(body_lines) <= 6

    @classmethod
    def _merge_scope_and_body(cls, existing: str, enriched_body: str) -> str:
        if not existing:
            return enriched_body

        if _PANORAMA_HEADER_RE.search(existing):
            return existing

        scope_block = existing

        if _SCOPE_MARKER in existing:
            parts = existing.split(_SCOPE_MARKER, 1)
            scope_block = parts[1].strip() if len(parts) > 1 else ""

        if scope_block and not _PANORAMA_HEADER_RE.search(enriched_body):
            return f"{_SCOPE_MARKER}\n\n{scope_block}\n\n{enriched_body}".strip()

        return enriched_body

    @classmethod
    def _build_enriched_body(cls, metadata: dict[str, Any], markdown: str) -> str | None:
        path = str(metadata.get("path") or "").lower()

        if "/pricing" in path:
            return None

        parts: list[str | None] = []
        intro = cls._extract_scope_intro(markdown)

        if intro:
            parts.append(f"{_SCOPE_MARKER}\n\n{intro}")

        panorama = cls._build_panorama_from_profile_table(metadata)

        if panorama:
            parts.append(panorama)

        highlights = cls._build_highlights_from_kpi(metadata)

        if highlights:
            parts.append(highlights)

        attention = cls._build_generic_attention(metadata)

        if attention:
            parts.append(attention)

        conclusion = cls._build_conclusion(metadata)

        if conclusion:
            parts.append(conclusion)

        merged = _OpsTable.join_markdown_blocks(parts)

        return merged or None

    @classmethod
    def _extract_scope_intro(cls, markdown: str) -> str:
        lines = [
            line.strip()
            for line in markdown.splitlines()
            if line.strip()
            and not line.strip().startswith("###")
            and _SCOPE_MARKER not in line
            and not line.startswith("**Panorama**")
            and not _ATTENTION_HEADER_RE.search(line)
        ]

        return "\n\n".join(lines[:4]).strip()

    @classmethod
    def _build_panorama_from_profile_table(cls, metadata: dict[str, Any]) -> str | None:
        profile = cls._find_profile_table(metadata)

        if not profile:
            return None

        rows = profile.get("rows") or []

        if not rows:
            return None

        header = cls._text("panoramaHeader")
        bullets = [
            f"- **{row.get('campo') or row.get('label') or '—'}:** {row.get('valor') or row.get('value') or '—'}"
            for row in rows
            if isinstance(row, dict)
        ]

        if not bullets:
            return None

        return "\n".join([header, *bullets])

    @classmethod
    def _build_highlights_from_kpi(cls, metadata: dict[str, Any]) -> str | None:
        kpi = metadata.get("kpiPresentation")

        if not isinstance(kpi, dict) or kpi.get("type") != "kpi":
            return None

        cards = kpi.get("cards") or []
        lines: list[str] = []

        for card in cards:
            if not isinstance(card, dict):
                continue

            label = str(card.get("label") or "").strip()
            value = card.get("value")
            unit = str(card.get("unit") or "").strip()

            if not label or value is None:
                continue

            if unit == "R$":
                formatted = cls._format_currency(value)
            elif unit == "%":
                formatted = f"{value}%"
            elif unit:
                formatted = f"{value} {unit}"
            else:
                formatted = str(int(value)) if isinstance(value, float) and value == int(value) else str(value)

            lines.append(f"- **{label}:** {formatted}")

        if not lines:
            return None

        return "\n".join([cls._text("quickReadingHeader"), *lines])

    @classmethod
    def _build_generic_attention(cls, metadata: dict[str, Any]) -> str | None:
        lines: list[str] = []
        list_table = cls._find_list_table(metadata)

        if list_table:
            rows = list_table.get("rows") or []

            if isinstance(rows, list) and len(rows) > 25:
                lines.append(
                    cls._text(
                        "attentionLargeList",
                        count=str(len(rows)),
                    )
                )

        if lines:
            return "\n".join(
                [
                    cls._text("attentionHeader"),
                    *[f"{index}. {line}" for index, line in enumerate(lines, start=1)],
                ]
            )

        return None

    @classmethod
    def _build_conclusion(cls, metadata: dict[str, Any]) -> str | None:
        humanized = metadata.get("humanizedSummary")

        if isinstance(humanized, dict):
            hint_lines = humanized.get("linhas") or []

            for line in hint_lines:
                token = str(line or "").strip().lower()

                if "abaixo" in token or "lista" in token or "painel" in token:
                    return cls._text("conclusionPanelsHint")

        visuals = ChatRichPresentationTextService.count_complementary_visuals(metadata)

        if visuals.get("table", 0) or visuals.get("chart", 0) or visuals.get("kpi", 0):
            return cls._text("conclusionPanelsHint")

        return None

    @classmethod
    def _find_profile_table(cls, metadata: dict[str, Any]) -> dict[str, Any] | None:
        profile = metadata.get("profileTablePresentation")

        if isinstance(profile, dict) and profile.get("type") == "table":
            return profile

        bulk = metadata.get("tablePresentations")

        if isinstance(bulk, list):
            for table in bulk:
                if isinstance(table, dict) and str(table.get("role") or "").strip() == "profile":
                    return table

        for key in ("tablePresentation", "presentation"):
            table = metadata.get(key)

            if isinstance(table, dict) and str(table.get("role") or "").strip() == "profile":
                return table

        return None

    @classmethod
    def _find_list_table(cls, metadata: dict[str, Any]) -> dict[str, Any] | None:
        bulk = metadata.get("tablePresentations")

        if isinstance(bulk, list):
            for table in bulk:
                if isinstance(table, dict) and str(table.get("role") or "").strip() == "list":
                    return table

        table = metadata.get("tablePresentation")

        if isinstance(table, dict) and str(table.get("role") or "").strip() == "list":
            return table

        return None

    @classmethod
    def _format_currency(cls, value: object) -> str:
        if isinstance(value, (int, float)):
            number = float(value)

            if number == int(number):
                formatted = f"{int(number):,}".replace(",", ".")
            else:
                formatted = f"{number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            return f"R$ {formatted}"

        return str(value)

    @classmethod
    def _text(cls, key: str, **values: str) -> str:
        template = ChatAssistantContentService.get(
            "presenter_content",
            "humanizedNarrative",
            key,
            default="",
        )

        if not template:
            return ""

        try:
            return template.format(**values)
        except KeyError:
            return template

    @classmethod
    def _metadata_entity(cls, metadata: dict[str, Any]) -> str | None:
        api_meta = metadata.get("apiDelpiResponseMeta")

        if not isinstance(api_meta, dict):
            return None

        raw_entity = api_meta.get("entity")

        if isinstance(raw_entity, str) and raw_entity.strip():
            return raw_entity.strip()

        return None
