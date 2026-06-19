"""Escopo regional do PDF por domínio de validação — BOM, cotas e carimbo (Onda 14.5)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_document_vision_bom_service import ChatDocumentVisionBomService
from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_drawing_validation_content_service import (
    ChatDrawingValidationContentService,
)
from app.domain.services.chat_pdf_annotation_table_service import (
    ChatPdfAnnotationTableService,
)


class ChatDrawingRegionalScopeService:
    _BOM_SOURCE_KEYS = (
        "bom_region",
        "stamp_bom_table",
        "annotation_table",
        "pdf_annotations_bom",
        "full_text_section",
    )

    @classmethod
    def resolve(
        cls,
        *,
        metadata: dict[str, Any] | None,
        full_text: str = "",
    ) -> dict[str, Any]:
        meta = metadata if isinstance(metadata, dict) else {}
        region_texts = meta.get("regionTexts") if isinstance(meta.get("regionTexts"), dict) else {}

        bom_scope = cls._resolve_bom_scope(meta, region_texts, full_text)
        dimensions_scope = cls._resolve_dimensions_scope(meta, region_texts, full_text)
        stamp_scope = cls._resolve_stamp_scope(meta, region_texts)

        return {
            "bom": bom_scope,
            "dimensions": dimensions_scope,
            "stamp": stamp_scope,
        }

    @classmethod
    def build_bom_sources(
        cls,
        scopes: dict[str, Any],
        *,
        full_text: str = "",
    ) -> list[tuple[str, str]]:
        sources: list[tuple[str, str]] = []
        bom = scopes.get("bom") if isinstance(scopes.get("bom"), dict) else {}

        text = str(bom.get("text") or "").strip()
        source_key = str(bom.get("sourceKey") or "").strip()

        if text and source_key:
            sources.append((source_key, text))

        normalized = str(full_text or "").strip()

        if (
            not sources
            and normalized
            and ChatDrawingPatternsService.bom_section().search(normalized)
        ):
            score = ChatDocumentVisionBomService.score_bom_text(normalized)

            if score >= 0:
                sources.append(("full_text_section", normalized))

        return sources

    @classmethod
    def scope_label(cls, source_key: str | None) -> str:
        key = str(source_key or "").strip()

        if not key:
            return ChatDrawingValidationContentService.get(
                "regionalScopeSources",
                "unavailable",
                default="—",
            )

        return ChatDrawingValidationContentService.get(
            "regionalScopeSources",
            key,
            default=key,
        )

    @classmethod
    def serialize(cls, scopes: dict[str, Any]) -> dict[str, Any]:
        serialized: dict[str, Any] = {}

        for domain, payload in scopes.items():
            if not isinstance(payload, dict):
                continue

            serialized[str(domain)] = {
                "sourceKey": payload.get("sourceKey"),
                "available": bool(payload.get("available")),
                "charCount": int(payload.get("charCount") or 0),
            }

        return serialized

    @classmethod
    def scoped_haystack(
        cls,
        pdf_extract: dict[str, Any],
        *,
        domains: tuple[str, ...] = ("bom", "dimensions"),
    ) -> str:
        scopes = pdf_extract.get("validationScopes")

        if not isinstance(scopes, dict) or not cls._scopes_include_text(scopes):
            metadata = pdf_extract.get("sourceMetadata")

            scopes = cls.resolve(
                metadata=metadata if isinstance(metadata, dict) else {},
                full_text="",
            )

        parts: list[str] = []

        for domain in domains:
            payload = scopes.get(domain)

            if not isinstance(payload, dict):
                continue

            text = str(payload.get("text") or "").strip()

            if text:
                parts.append(text.upper().replace(" ", ""))

        for row in pdf_extract.get("bomRows") or []:
            if not isinstance(row, dict):
                continue

            for key in ("description", "desc", "text", "quantity"):
                value = str(row.get(key) or "").strip()

                if value:
                    parts.append(value.upper().replace(" ", ""))

        return "".join(parts)

    @classmethod
    def _scopes_include_text(cls, scopes: dict[str, Any]) -> bool:
        for payload in scopes.values():
            if not isinstance(payload, dict):
                continue

            if str(payload.get("text") or "").strip():
                return True

        return False

    @classmethod
    def extract_bom_table_slice(cls, text: str) -> str | None:
        normalized = str(text or "").strip()

        if not normalized:
            return None

        header_match = ChatDrawingPatternsService.bom_table_header().search(normalized)

        if not header_match:
            return None

        lines: list[str] = []

        for line in normalized[header_match.start() :].splitlines():
            stripped = line.strip()

            if not stripped:
                continue

            if ChatDocumentVisionBomService.is_revision_noise_line(stripped):
                break

            if cls._line_is_client_reference_only(stripped):
                continue

            lines.append(stripped)

        slice_text = "\n".join(lines).strip()

        if not slice_text:
            return None

        rows = ChatDocumentVisionBomService.extract_bom_rows(
            slice_text,
            region_scoped=True,
        )

        if rows:
            return slice_text

        if ChatDrawingPatternsService.bom_section().search(slice_text):
            return slice_text

        return None

    @classmethod
    def _resolve_bom_scope(
        cls,
        meta: dict[str, Any],
        region_texts: dict[str, Any],
        full_text: str,
    ) -> dict[str, Any]:
        candidates: list[tuple[str, str, str]] = []

        bom_region = str(region_texts.get("bom") or meta.get("bomText") or "").strip()

        if bom_region:
            candidates.append(("bom_region", bom_region, bom_region))

        stamp_text = str(region_texts.get("stamp") or meta.get("stampText") or "").strip()
        stamp_table = cls.extract_bom_table_slice(stamp_text)

        if stamp_table:
            candidates.append(("stamp_bom_table", stamp_table, stamp_table))
        elif stamp_text:
            stamp_rows = ChatDocumentVisionBomService.extract_bom_rows(
                stamp_text,
                region_scoped=True,
            )

            if stamp_rows and ChatDocumentVisionBomService.score_bom_text(stamp_text) >= 0:
                candidates.append(("stamp_bom_table", stamp_text, stamp_text))

        annotation_tables = meta.get("annotationTables")

        if isinstance(annotation_tables, list):
            table_text = ChatPdfAnnotationTableService.table_text(annotation_tables).strip()

            if table_text:
                table_slice = cls.extract_bom_table_slice(table_text) or table_text
                candidates.append(("annotation_table", table_slice, table_text))

        annotation_text = str(meta.get("annotationText") or "").strip()

        if annotation_text:
            annotation_slice = cls.extract_bom_table_slice(annotation_text)

            if annotation_slice:
                candidates.append(
                    ("pdf_annotations_bom", annotation_slice, annotation_text)
                )

        normalized = str(full_text or "").strip()

        if normalized and ChatDrawingPatternsService.bom_section().search(normalized):
            candidates.append(("full_text_section", normalized, normalized))

        best_key = ""
        best_text = ""
        best_score = -1

        for source_key, candidate_text, _raw in candidates:
            score = ChatDocumentVisionBomService.score_bom_text(candidate_text)

            if score <= best_score:
                continue

            rows = ChatDocumentVisionBomService.extract_bom_rows(
                candidate_text,
                region_scoped=True,
            )

            if not rows and source_key != "full_text_section":
                continue

            best_score = score
            best_key = source_key
            best_text = candidate_text

        if not best_text:
            return cls._empty_scope()

        return {
            "sourceKey": best_key,
            "text": best_text,
            "available": True,
            "charCount": len(best_text),
            "selectionScore": best_score,
        }

    @classmethod
    def _resolve_dimensions_scope(
        cls,
        meta: dict[str, Any],
        region_texts: dict[str, Any],
        full_text: str,
    ) -> dict[str, Any]:
        dimensions_text = str(
            region_texts.get("dimensions") or meta.get("dimensionsText") or ""
        ).strip()

        if dimensions_text:
            return {
                "sourceKey": "dimensions_region",
                "text": dimensions_text,
                "available": True,
                "charCount": len(dimensions_text),
                "fallbackText": "",
            }

        cad_text = str(meta.get("cadReferenceText") or "").strip()

        if cad_text and not cls._text_is_bom_contaminated(cad_text):
            return {
                "sourceKey": "cad_reference",
                "text": "",
                "available": False,
                "charCount": 0,
                "fallbackText": cad_text,
            }

        normalized = str(full_text or "").strip()

        if normalized and not cls._text_is_bom_contaminated(normalized):
            return {
                "sourceKey": "cad_reference",
                "text": "",
                "available": False,
                "charCount": 0,
                "fallbackText": normalized[:1200],
            }

        return cls._empty_scope()

    @classmethod
    def _resolve_stamp_scope(
        cls,
        meta: dict[str, Any],
        region_texts: dict[str, Any],
    ) -> dict[str, Any]:
        stamp_text = str(region_texts.get("stamp") or meta.get("stampText") or "").strip()

        if not stamp_text:
            return cls._empty_scope()

        return {
            "sourceKey": "stamp_region",
            "text": stamp_text,
            "available": True,
            "charCount": len(stamp_text),
        }

    @classmethod
    def _empty_scope(cls) -> dict[str, Any]:
        return {
            "sourceKey": None,
            "text": "",
            "available": False,
            "charCount": 0,
        }

    @classmethod
    def _text_is_bom_contaminated(cls, text: str) -> bool:
        normalized = str(text or "")

        if ChatDrawingPatternsService.bom_section().search(normalized):
            return True

        intermediate_hits = ChatDrawingPatternsService.intermediate_code().findall(
            normalized
        )

        return len(intermediate_hits) >= 2

    @classmethod
    def _line_is_client_reference_only(cls, line: str) -> bool:
        stripped = str(line or "").strip().upper()

        if not stripped:
            return False

        for pattern in ChatDrawingPatternsService.bom_client_reference_noise_patterns():
            if pattern.search(stripped):
                return True

        return False
