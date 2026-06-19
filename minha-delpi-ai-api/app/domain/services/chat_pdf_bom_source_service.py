"""Montagem de fontes de texto para fusão/parsing de BOM — chat base."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_pdf_annotation_table_service import (
    ChatPdfAnnotationTableService,
)


class ChatPdfBomSourceService:
    @classmethod
    def build_sources(
        cls,
        *,
        full_text: str,
        metadata: dict[str, Any] | None,
    ) -> list[tuple[str, str]]:
        meta = metadata if isinstance(metadata, dict) else {}
        sources: list[tuple[str, str]] = []

        bom_text = str(meta.get("bomText") or "").strip()

        if bom_text:
            sources.append(("bom_region", bom_text))

        annotation_tables = meta.get("annotationTables")

        if not isinstance(annotation_tables, list):
            annotation_tables = []

        annotation_table_text = ChatPdfAnnotationTableService.table_text(annotation_tables)

        if annotation_table_text:
            sources.append(("annotation_table", annotation_table_text))

        annotation_text = str(meta.get("annotationText") or "").strip()

        if annotation_text:
            sources.append(("pdf_annotations", annotation_text))

        stamp_text = str(meta.get("stampText") or "").strip()

        if stamp_text:
            sources.append(("stamp_region", stamp_text))

        normalized = str(full_text or "").strip()

        if normalized:
            sources.append(("full_text", normalized))

        return sources

    @classmethod
    def structured_source_blob(
        cls,
        sources: list[tuple[str, str]],
        *,
        exclude_full_text: bool = True,
    ) -> str:
        chunks: list[str] = []

        for source_name, source_text in sources:
            if exclude_full_text and source_name == "full_text":
                continue

            normalized = str(source_text or "").strip()

            if normalized:
                chunks.append(normalized)

        return "\n\n".join(chunks)
