"""Montagem de fontes de texto para fusão/parsing de BOM — chat base."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_drawing_regional_scope_service import (
    ChatDrawingRegionalScopeService,
)
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
        scopes = meta.get("validationScopes")

        if not isinstance(scopes, dict) or not ChatDrawingRegionalScopeService._scopes_include_text(
            scopes
        ):
            scopes = ChatDrawingRegionalScopeService.resolve(
                metadata=meta,
                full_text=full_text,
            )

        return ChatDrawingRegionalScopeService.build_bom_sources(
            scopes,
            full_text=full_text,
        )

    @classmethod
    def structured_source_blob(
        cls,
        sources: list[tuple[str, str]],
        *,
        exclude_full_text: bool = True,
    ) -> str:
        chunks: list[str] = []

        for source_name, source_text in sources:
            if exclude_full_text and source_name == "full_text_section":
                continue

            normalized = str(source_text or "").strip()

            if normalized:
                chunks.append(normalized)

        return "\n\n".join(chunks)
