"""Extração BOM de desenho DELPI — orquestra fontes base + regras 50xx/revisão."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_document_vision_bom_service import (
    ChatDocumentVisionBomService,
)
from app.domain.services.chat_drawing_bom_reference_noise_service import (
    ChatDrawingBomReferenceNoiseService,
)
from app.domain.services.chat_drawing_bom_row_sanitization_service import (
    ChatDrawingBomRowSanitizationService,
)
from app.domain.services.chat_drawing_component_code_normalization_service import (
    ChatDrawingComponentCodeNormalizationService,
)
from app.domain.services.chat_drawing_intermediate_code_service import (
    ChatDrawingIntermediateCodeService,
)
from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_pdf_bom_source_service import ChatPdfBomSourceService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


class ChatDrawingPdfBomExtractionService:
    @classmethod
    def extract(
        cls,
        *,
        full_text: str,
        metadata: dict[str, Any] | None,
        product_code: str | None,
    ) -> dict[str, Any]:
        normalized = str(full_text or "").strip()
        bom_sources = ChatPdfBomSourceService.build_sources(
            full_text=normalized,
            metadata=metadata,
            product_code=product_code,
        )

        bom_rows, component_codes, bom_source = ChatDocumentVisionBomService.resolve_from_sources(
            bom_sources,
            exclude_product_code=product_code,
        )

        if bom_rows:
            raw_bom_rows = list(bom_rows)
            bom_rows = ChatDrawingBomRowSanitizationService.sanitize_rows(
                bom_rows,
                product_code=product_code,
            )

            revision_only_codes = ChatDocumentVisionBomService.codes_only_in_revision_lines(
                normalized
            )

            if bom_rows:
                revision_only_codes -= set(
                    ChatDocumentVisionBomService.bom_component_codes(bom_rows)
                )

            intermediate_codes = ChatDrawingIntermediateCodeService.collect_codes(
                full_text=normalized,
                bom_rows=bom_rows,
                bom_sources=bom_sources,
                product_code=product_code,
                revision_only_codes=revision_only_codes,
            )

            component_codes = ChatDocumentVisionBomService.merge_component_codes_from_rows(
                list(component_codes or []),
                bom_rows,
            )
            component_codes.extend(
                ChatDrawingBomRowSanitizationService.nested_component_codes(raw_bom_rows)
            )
        else:
            revision_only_codes = ChatDocumentVisionBomService.codes_only_in_revision_lines(
                normalized
            )

            intermediate_codes = ChatDrawingIntermediateCodeService.collect_codes(
                full_text=normalized,
                bom_rows=bom_rows,
                bom_sources=bom_sources,
                product_code=product_code,
                revision_only_codes=revision_only_codes,
            )

        if not bom_rows and not component_codes:
            component_codes = cls._extract_component_codes_from_text(
                normalized,
                exclude=product_code,
            )

        component_codes = cls._finalize_component_codes(
            component_codes,
            product_code=product_code,
            revision_only_codes=revision_only_codes,
            intermediate_codes=intermediate_codes,
            pdf_context={
                "productCode": product_code,
                "fullText": normalized,
                "bomRows": bom_rows,
                "sourceMetadata": metadata,
            },
        )

        component_codes = ChatDrawingBomRowSanitizationService.dedupe_component_codes(
            component_codes,
        )

        payload: dict[str, Any] = {
            "componentCodes": component_codes,
            "intermediateCodes": intermediate_codes,
        }

        if bom_rows:
            payload["bomRows"] = bom_rows

        if bom_source:
            payload["bomSource"] = bom_source

        scopes = metadata.get("validationScopes") if isinstance(metadata, dict) else None

        if isinstance(scopes, dict):
            bom_scope = scopes.get("bom")

            if isinstance(bom_scope, dict) and bom_scope.get("sourceKey"):
                payload["bomSource"] = str(bom_scope["sourceKey"])

        return payload

    @classmethod
    def _finalize_component_codes(
        cls,
        component_codes: list[str],
        *,
        product_code: str | None,
        revision_only_codes: set[str],
        intermediate_codes: list[str],
        pdf_context: dict | None = None,
    ) -> list[str]:
        product_norm = ChatProductQueryIntentService.normalize_product_code(
            product_code or ""
        )
        filtered = [
            code
            for code in component_codes
            if code not in revision_only_codes and code != product_norm
            and not (
                product_norm
                and ChatDrawingBomRowSanitizationService.is_product_code_ghost(
                    code,
                    product_norm,
                )
            )
        ]
        intermediate_set = set(intermediate_codes)
        reference_noise = ChatDrawingBomReferenceNoiseService.collect_reference_noise_codes(
            pdf_context or {}
        )

        return [
            code
            for code in filtered
            if code not in reference_noise
            and (
                not ChatDrawingPatternsService.is_intermediate_family(str(code))
                or code in intermediate_set
            )
        ]

    @classmethod
    def _extract_component_codes_from_text(
        cls,
        text: str,
        *,
        exclude: str | None,
    ) -> list[str]:
        exclude_norm = ChatProductQueryIntentService.normalize_product_code(exclude or "")
        found: list[str] = []

        for match in ChatDrawingPatternsService.component_code().finditer(text):
            code = ChatDrawingComponentCodeNormalizationService.normalize_extracted(
                ChatProductQueryIntentService.normalize_product_code(match.group(1))
            )

            if not code or code == exclude_norm or code in found:
                continue

            found.append(code)

        return found
