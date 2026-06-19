"""Montagem de fontes de texto para fusão/parsing de BOM — chat base."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_document_vision_bom_service import ChatDocumentVisionBomService
from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_drawing_regional_scope_service import (
    ChatDrawingRegionalScopeService,
)


class ChatPdfBomSourceService:
    @classmethod
    def build_sources(
        cls,
        *,
        full_text: str,
        metadata: dict[str, Any] | None,
        product_code: str | None = None,
    ) -> list[tuple[str, str]]:
        meta = metadata if isinstance(metadata, dict) else {}
        scopes = meta.get("validationScopes")

        if not isinstance(scopes, dict) or not ChatDrawingRegionalScopeService._scopes_include_text(
            scopes
        ):
            scopes = ChatDrawingRegionalScopeService.resolve(
                metadata=meta,
                full_text=full_text,
                product_code=product_code,
            )

        sources = ChatDrawingRegionalScopeService.build_bom_sources(
            scopes,
            full_text=full_text,
        )
        cls._append_supplementary_bom_sources(
            sources,
            metadata=meta,
            full_text=full_text,
            product_code=product_code,
        )

        return sources

    @classmethod
    def _append_supplementary_bom_sources(
        cls,
        sources: list[tuple[str, str]],
        *,
        metadata: dict[str, Any],
        full_text: str,
        product_code: str | None,
    ) -> None:
        primary_text = str(sources[0][1] if sources else "").strip()
        primary_rows = ChatDocumentVisionBomService.extract_bom_rows(
            primary_text,
            exclude_product_code=product_code,
            region_scoped=True,
        )
        primary_meaningful = ChatDocumentVisionBomService.meaningful_bom_component_codes(
            primary_rows,
            exclude_product_code=product_code,
        )

        if len(primary_meaningful) >= 2:
            return

        seen_texts = {str(text or "").strip() for _, text in sources}

        stamp_text = str(metadata.get("stampText") or "").strip()
        stamp_table = ChatDrawingRegionalScopeService.extract_bom_table_slice(stamp_text)

        if stamp_table and stamp_table not in seen_texts:
            sources.append(("stamp_bom_table", stamp_table))
            seen_texts.add(stamp_table)

        normalized = str(full_text or "").strip()

        if normalized and normalized not in seen_texts:
            upper = normalized.upper()
            has_bom_markers = bool(
                ChatDrawingPatternsService.bom_table_header().search(upper)
                or ChatDrawingPatternsService.bom_section().search(normalized)
            )
            score = ChatDocumentVisionBomService.score_bom_text(
                normalized,
                exclude_product_code=product_code,
            )

            if has_bom_markers or score >= 20:
                sources.append(("full_text_section", normalized))
                seen_texts.add(normalized)

        cad_text = str(metadata.get("cadReferenceText") or "").strip()

        if cad_text and cad_text not in seen_texts:
            cad_rows = ChatDocumentVisionBomService.extract_bom_rows(
                cad_text,
                exclude_product_code=product_code,
                region_scoped=True,
            )
            cad_meaningful = ChatDocumentVisionBomService.meaningful_bom_component_codes(
                cad_rows,
                exclude_product_code=product_code,
            )

            if len(cad_meaningful) > len(primary_meaningful):
                sources.append(("cad_reference_bom", cad_text))

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
