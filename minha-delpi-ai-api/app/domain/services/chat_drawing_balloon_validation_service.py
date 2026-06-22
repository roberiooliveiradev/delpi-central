"""Validação fase 1 — presença de códigos BOM nas anotações/balões do PDF."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_drawing_validation_content_service import (
    ChatDrawingValidationContentService,
)
from app.domain.services.chat_pdf_annotation_table_service import (
    ChatPdfAnnotationTableService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


@dataclass(frozen=True)
class BalloonCoverageResult:
    bom_codes: tuple[str, ...]
    annotation_codes: tuple[str, ...]
    missing_in_annotations: tuple[str, ...]
    annotations_available: bool


class ChatDrawingBalloonValidationService:
    @classmethod
    def evaluate(cls, *, pdf_extract: dict) -> BalloonCoverageResult:
        bom_codes = cls._collect_bom_codes(pdf_extract)
        annotation_text = cls._annotation_haystack(pdf_extract)
        structured_codes = cls._collect_structured_bom_annotation_codes(pdf_extract)
        annotations_available = bool(annotation_text.strip()) or bool(structured_codes)
        annotation_codes = cls._extract_codes(annotation_text)
        annotation_set = set(annotation_codes) | structured_codes
        missing = tuple(
            sorted(code for code in bom_codes if code not in annotation_set)
        )

        return BalloonCoverageResult(
            bom_codes=bom_codes,
            annotation_codes=annotation_codes,
            missing_in_annotations=missing,
            annotations_available=annotations_available,
        )

    @classmethod
    def build_check_items(cls, *, pdf_extract: dict) -> list[dict[str, Any]]:
        result = cls.evaluate(pdf_extract=pdf_extract)

        if not result.bom_codes:
            return []

        content = ChatDrawingValidationContentService
        items: list[dict[str, Any]] = []

        if not result.annotations_available:
            items.append(
                content.item_from_template(
                    "balloon_coverage_unavailable",
                    status="pending",
                    pdf_evidence=content.evidence("pendingPdf"),
                    api_evidence=content.evidence("dash"),
                )
            )
            return items

        if result.missing_in_annotations:
            items.append(
                content.item_from_template(
                    "balloon_missing_codes",
                    status="pending",
                    pdf_evidence=content.evidence_format(
                        "codeCount",
                        count=str(len(result.missing_in_annotations)),
                    ),
                    api_evidence=", ".join(result.missing_in_annotations[:8]),
                )
            )
        else:
            items.append(
                content.item_from_template(
                    "balloon_presence_ok",
                    status="ok",
                    pdf_evidence=content.evidence_format(
                        "codeCount",
                        count=str(len(result.bom_codes)),
                    ),
                    api_evidence=content.evidence("linked"),
                )
            )

        return items

    @classmethod
    def _collect_structured_bom_annotation_codes(cls, pdf_extract: dict) -> set[str]:
        refinement = pdf_extract.get("bomVisionRefinement")

        if not isinstance(refinement, dict) or int(refinement.get("columnRowCount") or 0) <= 0:
            scopes = pdf_extract.get("validationScopes")

            if not isinstance(scopes, dict):
                return set()

            bom_scope = scopes.get("bom")

            if not isinstance(bom_scope, dict) or not bom_scope.get("available"):
                return set()

        codes: set[str] = set()

        for row in pdf_extract.get("bomRows") or []:
            if not isinstance(row, dict):
                continue

            code = ChatProductQueryIntentService.normalize_product_code(
                str(row.get("code") or "")
            )

            if code:
                codes.add(code)

        return codes

    @classmethod
    def _collect_bom_codes(cls, pdf_extract: dict) -> tuple[str, ...]:
        codes: set[str] = set()

        for raw in pdf_extract.get("componentCodes") or []:
            code = ChatProductQueryIntentService.normalize_product_code(str(raw or ""))

            if code:
                codes.add(code)

        for row in pdf_extract.get("bomRows") or []:
            if not isinstance(row, dict):
                continue

            code = ChatProductQueryIntentService.normalize_product_code(
                str(row.get("code") or "")
            )

            if code:
                codes.add(code)

        return tuple(sorted(codes))

    @classmethod
    def _annotation_haystack(cls, pdf_extract: dict) -> str:
        parts: list[str] = []
        source_metadata = pdf_extract.get("sourceMetadata")

        if isinstance(source_metadata, dict):
            annotation_text = source_metadata.get("annotationText")

            if annotation_text:
                parts.append(str(annotation_text))

            tables = source_metadata.get("annotationTables")

            if isinstance(tables, list):
                parts.append(ChatPdfAnnotationTableService.table_text(tables))

        tables = pdf_extract.get("annotationTables")

        if isinstance(tables, list):
            parts.append(ChatPdfAnnotationTableService.table_text(tables))

        return "\n".join(part for part in parts if part)

    @classmethod
    def _extract_codes(cls, text: str) -> tuple[str, ...]:
        codes: set[str] = set()
        pattern = ChatDrawingPatternsService.component_code()

        for match in pattern.finditer(str(text or "")):
            code = ChatProductQueryIntentService.normalize_product_code(match.group(1))

            if code:
                codes.add(code)

        return tuple(sorted(codes))
