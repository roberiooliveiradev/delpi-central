"""Comparação hierárquica BOM PDF × SG1010 — ignora cabos-filho de 50xx e ruído de roteiro."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.services.chat_drawing_bom_reference_noise_service import (
    ChatDrawingBomReferenceNoiseService,
)
from app.domain.services.chat_drawing_component_code_normalization_service import (
    ChatDrawingComponentCodeNormalizationService,
)
from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_drawing_structure_index_service import (
    ChatDrawingStructureIndexService,
)
from app.domain.services.chat_drawing_regional_scope_service import (
    ChatDrawingRegionalScopeService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


@dataclass(frozen=True)
class BomComparisonResult:
    missing_in_pdf: tuple[str, ...]
    extra_in_pdf: tuple[str, ...]
    pdf_bom_codes: tuple[str, ...]
    api_codes: tuple[str, ...]


class ChatDrawingBomComparisonService:
    @classmethod
    def compare(
        cls,
        *,
        root: dict,
        pdf_extract: dict,
        product_code: str,
    ) -> BomComparisonResult:
        api_codes = cls.collect_structure_bom_codes(root, product_code)
        raw_pdf_codes = set(pdf_extract.get("componentCodes") or [])
        raw_pdf_codes.update(pdf_extract.get("intermediateCodes") or [])

        pdf_bom_codes = cls.normalize_pdf_bom_codes(
            raw_pdf_codes,
            child_cable_parents=cls.collect_child_cable_parents(root),
        )
        pdf_bom_codes |= cls.intermediate_codes_matched_by_description(
            root=root,
            pdf_extract=pdf_extract,
        )
        pdf_bom_codes = cls._drop_catalog_alternate_duplicates(
            pdf_bom_codes,
            catalog_map=ChatDrawingStructureIndexService.collect_catalog_alternate_map(root),
            api_codes=api_codes,
            child_cable_parents=cls.collect_child_cable_parents(root),
        )
        pdf_bom_codes -= ChatDrawingBomReferenceNoiseService.collect_reference_noise_codes(
            pdf_extract
        )

        missing = sorted(api_codes - pdf_bom_codes)
        extra = sorted(
            code
            for code in (pdf_bom_codes - api_codes)
            if code != ChatProductQueryIntentService.normalize_product_code(product_code)
        )

        return BomComparisonResult(
            missing_in_pdf=tuple(missing),
            extra_in_pdf=tuple(extra),
            pdf_bom_codes=tuple(sorted(pdf_bom_codes)),
            api_codes=tuple(sorted(api_codes)),
        )

    @classmethod
    def intermediate_codes_matched_by_description(
        cls,
        *,
        root: dict,
        pdf_extract: dict,
    ) -> set[str]:
        haystack = cls._pdf_description_haystack(pdf_extract)

        if not haystack:
            return set()

        matched: set[str] = set()

        for row in ChatDrawingStructureIndexService.flatten_items(
            root.get("structure") if isinstance(root.get("structure"), dict) else None
        ):
            if not row.code or not ChatDrawingPatternsService.is_intermediate_family(
                row.code
            ):
                continue

            signature = ChatDrawingPatternsService.intermediate_description_signature(
                row.description
            )

            if signature and signature in haystack:
                matched.add(row.code)
                continue

            for marker in cls._intermediate_color_markers(signature or ""):
                if marker in haystack:
                    matched.add(row.code)
                    break

        return matched

    @classmethod
    def _intermediate_color_markers(cls, signature: str) -> tuple[str, ...]:
        match = ChatDrawingPatternsService.compile_validation(
            "intermediateColorSignature"
        ).match(str(signature or "").upper())

        if not match:
            return ()

        color = match.group(1)

        return ChatDrawingPatternsService.intermediate_color_ocr_markers(color)

    @classmethod
    def _pdf_description_haystack(cls, pdf_extract: dict) -> str:
        scoped = ChatDrawingRegionalScopeService.scoped_haystack(
            pdf_extract,
            domains=("bom", "dimensions", "stamp"),
        )

        if scoped:
            return scoped

        parts: list[str] = []

        def add_text(raw: object) -> None:
            text = str(raw or "").strip()

            if text:
                parts.append(text.upper().replace(" ", ""))

        add_text(pdf_extract.get("fullText"))

        source_metadata = pdf_extract.get("sourceMetadata")

        if isinstance(source_metadata, dict):
            for key in ChatDrawingPatternsService.pdf_haystack_source_metadata_keys():
                add_text(source_metadata.get(key))

            region_texts = source_metadata.get("regionTexts")

            if isinstance(region_texts, dict):
                for value in region_texts.values():
                    add_text(value)

        title_block = pdf_extract.get("titleBlock")

        if isinstance(title_block, dict):
            add_text(title_block.get("rawText"))

        for row in pdf_extract.get("bomRows") or []:
            if not isinstance(row, dict):
                continue

            for key in ChatDrawingPatternsService.pdf_haystack_bom_row_keys():
                add_text(row.get(key))

        return "".join(parts)

    @classmethod
    def collect_structure_bom_codes(cls, root: dict, product_code: str) -> set[str]:
        return ChatDrawingStructureIndexService.collect_bom_line_codes(root, product_code)

    @classmethod
    def collect_child_cable_parents(cls, root: dict) -> dict[str, set[str]]:
        return ChatDrawingStructureIndexService.collect_child_cable_parent_map(root)

    @classmethod
    def normalize_pdf_bom_codes(
        cls,
        pdf_codes: set[str],
        *,
        child_cable_parents: dict[str, set[str]],
    ) -> set[str]:
        normalized_codes: set[str] = set()
        parents_50xx = {
            code
            for code in pdf_codes
            if ChatDrawingPatternsService.is_intermediate_family(str(code))
        }

        for raw_code in pdf_codes:
            code = ChatDrawingComponentCodeNormalizationService.normalize_extracted(
                raw_code
            )

            if not code:
                continue

            parent = child_cable_parents.get(code) or set()

            if parent & parents_50xx:
                continue

            normalized_codes.add(code)

        return normalized_codes

    @classmethod
    def _drop_catalog_alternate_duplicates(
        cls,
        pdf_codes: set[str],
        *,
        catalog_map: dict[str, str],
        api_codes: set[str],
        child_cable_parents: dict[str, set[str]],
    ) -> set[str]:
        """Remove MP alternativo do PDF quando o MP canônico ou o PI pai já está no PDF/API."""
        resolved = set(pdf_codes)

        for alternate, primary in catalog_map.items():
            if alternate not in resolved:
                continue

            if primary in resolved or primary in api_codes:
                resolved.discard(alternate)
                continue

            parent_intermediates = child_cable_parents.get(primary) or set()

            if parent_intermediates & (resolved | api_codes):
                resolved.discard(alternate)

        return resolved
