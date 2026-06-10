"""Enriquecimento canônico de narrativa humanizada — qualquer action com painéis ricos."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_presentation_operational_table_service import (
    ChatPresentationOperationalTableService as _OpsTable,
)
from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)
from app.domain.services.chat_rich_presentation_text_service import (
    ChatRichPresentationTextService,
)

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
        if cls._resolve_narrative_mode(metadata) == "skip":
            return False

        visuals = ChatRichPresentationTextService.count_complementary_visuals(metadata)

        if visuals.get("table", 0) + visuals.get("kpi", 0) + visuals.get("chart", 0) < 1:
            return False

        if cls._markdown_has_header(markdown, "panoramaHeader") and cls._markdown_has_attention(
            markdown
        ):
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

        if cls._markdown_has_header(existing, "panoramaHeader"):
            return existing

        scope_block = existing

        if _SCOPE_MARKER in existing:
            parts = existing.split(_SCOPE_MARKER, 1)
            scope_block = parts[1].strip() if len(parts) > 1 else ""

        if scope_block and not cls._markdown_has_header(enriched_body, "panoramaHeader"):
            return f"{_SCOPE_MARKER}\n\n{scope_block}\n\n{enriched_body}".strip()

        return enriched_body

    @classmethod
    def _build_enriched_body(cls, metadata: dict[str, Any], markdown: str) -> str | None:
        if cls._resolve_narrative_mode(metadata) == "skip":
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
        panorama_header = cls._header_text("panoramaHeader")
        attention_prefix = cls._attention_prefix()

        lines = [
            line.strip()
            for line in markdown.splitlines()
            if line.strip()
            and not line.strip().startswith("###")
            and _SCOPE_MARKER not in line
            and not (panorama_header and line.startswith(panorama_header))
            and not (attention_prefix and attention_prefix in line)
        ]

        return "\n\n".join(lines[:4]).strip()

    @classmethod
    def _is_field_value_profile_table(cls, table: dict[str, Any] | None) -> bool:
        if not isinstance(table, dict) or table.get("type") != "table":
            return False

        rows = table.get("rows") or []

        if not isinstance(rows, list) or not rows:
            return False

        sample = rows[0]

        if not isinstance(sample, dict):
            return False

        keys = {str(key).strip().lower() for key in sample.keys()}

        return keys == {"campo", "valor"} or keys == {"field", "value"}

    @classmethod
    def _build_panorama_from_profile_table(cls, metadata: dict[str, Any]) -> str | None:
        profile = cls._find_profile_table(metadata)

        if not profile or not cls._is_field_value_profile_table(profile):
            return None

        rows = profile.get("rows") or []

        if not rows:
            return None

        header = cls._text("panoramaHeader")
        bullets = [
            f"- **{row.get('campo') or row.get('field') or '—'}:** "
            f"{row.get('valor') or row.get('value') or '—'}"
            for row in rows
            if isinstance(row, dict)
            and (
                str(row.get("campo") or row.get("field") or "").strip()
                or str(row.get("valor") or row.get("value") or "").strip()
            )
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

            if not label or value is None or cls._is_technical_kpi_label(label):
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
        if not cls._has_meaningful_complementary_visuals(metadata):
            return None

        humanized = metadata.get("humanizedSummary")

        if isinstance(humanized, dict):
            hint_lines = humanized.get("linhas") or []

            for line in hint_lines:
                token = str(line or "").strip().lower()

                if "abaixo" in token or "lista" in token or "painel" in token:
                    return cls._text("conclusionPanelsHint")

        return cls._text("conclusionPanelsHint")

    @classmethod
    def _has_meaningful_complementary_visuals(cls, metadata: dict[str, Any]) -> bool:
        list_table = cls._find_list_table(metadata)

        if isinstance(list_table, dict):
            rows = list_table.get("rows") or []

            if isinstance(rows, list) and rows:
                return True

        profile = cls._find_profile_table(metadata)

        if isinstance(profile, dict):
            rows = profile.get("rows") or []

            if isinstance(rows, list) and rows:
                return True

        kpi = metadata.get("kpiPresentation")

        if isinstance(kpi, dict) and kpi.get("type") == "kpi":
            cards = kpi.get("cards") or []

            for card in cards:
                if not isinstance(card, dict):
                    continue

                label = str(card.get("label") or "").strip()
                value = card.get("value")

                if label and value is not None and not cls._is_technical_kpi_label(label):
                    return True

        visuals = ChatRichPresentationTextService.count_complementary_visuals(metadata)

        return bool(visuals.get("chart", 0))

    @classmethod
    def _is_technical_kpi_label(cls, label: str) -> bool:
        token = str(label or "").strip().lower().replace("_", " ")

        exclude = ChatAssistantContentService.list(
            "presenter_content",
            "humanizedNarrative",
            "kpiHighlightExcludeLabels",
        )

        return any(str(term).strip().lower() in token for term in exclude)

    @classmethod
    def _find_profile_table(cls, metadata: dict[str, Any]) -> dict[str, Any] | None:
        profile = metadata.get("profileTablePresentation")

        if isinstance(profile, dict) and profile.get("type") == "table":
            return profile if cls._is_field_value_profile_table(profile) else None

        bulk = metadata.get("tablePresentations")

        if isinstance(bulk, list):
            for table in bulk:
                if (
                    isinstance(table, dict)
                    and str(table.get("role") or "").strip() == "profile"
                    and cls._is_field_value_profile_table(table)
                ):
                    return table

        for key in ("tablePresentation", "presentation"):
            table = metadata.get(key)

            if (
                isinstance(table, dict)
                and str(table.get("role") or "").strip() == "profile"
                and cls._is_field_value_profile_table(table)
            ):
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
    def _resolve_narrative_mode(cls, metadata: dict[str, Any]) -> str:
        path = str(metadata.get("path") or "")
        entity = cls._metadata_entity(metadata)

        return ChatPresentationProfileService.humanized_narrative_mode(path, entity)

    @classmethod
    def _header_text(cls, key: str) -> str:
        return cls._text(key).strip()

    @classmethod
    def _attention_prefix(cls) -> str:
        prefix = cls._text("attentionHeaderPrefix").strip()

        if prefix:
            return prefix

        return cls._header_text("attentionHeader")

    @classmethod
    def _markdown_has_header(cls, markdown: str, key: str) -> bool:
        header = cls._header_text(key)

        return bool(header and header in markdown)

    @classmethod
    def _markdown_has_attention(cls, markdown: str) -> bool:
        prefix = cls._attention_prefix()

        return bool(prefix and prefix in markdown)

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
