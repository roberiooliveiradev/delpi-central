"""Comparação hierárquica BOM PDF × SG1010 — ignora cabos-filho de 50xx e ruído de roteiro."""

from __future__ import annotations

import re
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

        if cls._prefer_structured_bom_rows(pdf_extract):
            raw_pdf_codes: set[str] = set()
        else:
            raw_pdf_codes = set(pdf_extract.get("componentCodes") or [])
            raw_pdf_codes.update(pdf_extract.get("intermediateCodes") or [])

        pdf_bom_codes = cls.normalize_pdf_bom_codes(
            raw_pdf_codes,
            child_cable_parents=cls.collect_child_cable_parents(root),
        )
        pdf_bom_codes |= cls.collect_primary_bom_row_codes(
            pdf_extract,
            structured_only=cls._prefer_structured_bom_rows(pdf_extract),
        )
        pdf_bom_codes |= cls.collect_supplemental_presence_codes(
            pdf_extract,
            api_codes=set(api_codes),
        )
        pdf_bom_codes |= cls.intermediate_codes_matched_by_description(
            root=root,
            pdf_extract=pdf_extract,
        )
        pdf_bom_codes |= cls.collect_haystack_presence_codes(
            pdf_extract,
            api_codes=set(api_codes),
        )
        pdf_bom_codes = cls._drop_catalog_alternate_duplicates(
            pdf_bom_codes,
            catalog_map=ChatDrawingStructureIndexService.collect_catalog_alternate_map(root),
            api_codes=api_codes,
            child_cable_parents=cls.collect_child_cable_parents(root),
        )
        pdf_bom_codes = cls._apply_catalog_prefix_crosswalk(
            pdf_bom_codes,
            api_codes=set(api_codes),
        )
        structure_all_codes = ChatDrawingStructureIndexService.collect_all_codes(
            root,
            product_code,
        )
        matched_codes, false_row_codes = cls.reconcile_bom_row_description_matches(
            root=root,
            pdf_extract=pdf_extract,
            api_codes=set(structure_all_codes),
        )
        pdf_bom_codes |= matched_codes
        pdf_bom_codes -= false_row_codes
        pdf_bom_codes -= ChatDrawingBomReferenceNoiseService.collect_reference_noise_codes(
            pdf_extract
        )

        normalized_product = ChatProductQueryIntentService.normalize_product_code(
            product_code
        )

        missing = sorted(api_codes - pdf_bom_codes)
        extra = sorted(
            code
            for code in (pdf_bom_codes - api_codes)
            if code != normalized_product and code not in structure_all_codes
        )

        return BomComparisonResult(
            missing_in_pdf=tuple(missing),
            extra_in_pdf=tuple(extra),
            pdf_bom_codes=tuple(sorted(pdf_bom_codes)),
            api_codes=tuple(sorted(api_codes)),
        )

    @classmethod
    def collect_primary_bom_row_codes(
        cls,
        pdf_extract: dict,
        *,
        structured_only: bool = False,
    ) -> set[str]:
        codes: set[str] = set()
        structured_sources = ChatDrawingPatternsService.bom_structured_quantity_sources()

        for row in pdf_extract.get("bomRows") or []:
            if not isinstance(row, dict):
                continue

            if ChatDrawingBomReferenceNoiseService.is_client_reference_row(row):
                continue

            if structured_only:
                source = str(row.get("quantitySource") or "").strip().lower()

                if structured_sources and source not in structured_sources:
                    continue

                if not row.get("quantityTrusted"):
                    continue

            code = ChatProductQueryIntentService.normalize_product_code(
                str(row.get("code") or "")
            )

            if code:
                codes.add(code)

        return codes

    @classmethod
    def _prefer_structured_bom_rows(cls, pdf_extract: dict) -> bool:
        refinement = pdf_extract.get("bomVisionRefinement")

        if isinstance(refinement, dict) and int(refinement.get("columnRowCount") or 0) > 0:
            return True

        min_rows = int(
            ChatDrawingPatternsService.bom_comparison_rule("preferStructuredRowsMinCount", 2)
            or 2
        )
        structured_sources = ChatDrawingPatternsService.bom_structured_quantity_sources()
        structured_rows = 0

        for row in pdf_extract.get("bomRows") or []:
            if not isinstance(row, dict):
                continue

            code = ChatProductQueryIntentService.normalize_product_code(
                str(row.get("code") or "")
            )

            if not code:
                continue

            source = str(row.get("quantitySource") or "").strip().lower()

            if structured_sources and source not in structured_sources:
                continue

            structured_rows += 1

        return structured_rows >= min_rows

    @classmethod
    def collect_supplemental_presence_codes(
        cls,
        pdf_extract: dict,
        *,
        api_codes: set[str],
    ) -> set[str]:
        """Presença OCR (componentCodes / linhas não confiáveis) quando BOM colunar domina quantidades."""
        if not cls._prefer_structured_bom_rows(pdf_extract):
            return set()

        codes: set[str] = set()
        structured_sources = ChatDrawingPatternsService.bom_structured_quantity_sources()

        for raw in pdf_extract.get("componentCodes") or []:
            code = ChatProductQueryIntentService.normalize_product_code(str(raw or ""))

            if code and code in api_codes:
                codes.add(code)

        for row in pdf_extract.get("bomRows") or []:
            if not isinstance(row, dict):
                continue

            if ChatDrawingBomReferenceNoiseService.is_client_reference_row(row):
                continue

            code = ChatProductQueryIntentService.normalize_product_code(
                str(row.get("code") or "")
            )

            if not code or code not in api_codes:
                continue

            if code in codes:
                continue

            source = str(row.get("quantitySource") or "").strip().lower()

            if structured_sources and source in structured_sources and row.get("quantityTrusted"):
                continue

            codes.add(code)

        return codes

    @classmethod
    def collect_haystack_presence_codes(
        cls,
        pdf_extract: dict,
        *,
        api_codes: set[str],
    ) -> set[str]:
        """Códigos presentes no haystack regional (carimbo/BOM) mas ausentes de componentCodes."""
        haystack_parts: list[str] = []
        primary = cls._pdf_description_haystack(pdf_extract)

        if primary:
            haystack_parts.append(primary)

        source_metadata = pdf_extract.get("sourceMetadata")

        if isinstance(source_metadata, dict):
            for key in ChatDrawingPatternsService.pdf_haystack_source_metadata_keys():
                text = str(source_metadata.get(key) or "").strip()

                if text:
                    haystack_parts.append(text.upper())

        full_text = str(pdf_extract.get("fullText") or "").strip()

        if full_text:
            haystack_parts.append(full_text.upper())

        if not haystack_parts or not api_codes:
            return set()

        pattern = ChatDrawingPatternsService.component_code()
        codes: set[str] = set()

        for haystack in haystack_parts:
            for match in pattern.finditer(haystack):
                code = ChatProductQueryIntentService.normalize_product_code(
                    str(match.group(1) or "")
                )

                if code and code in api_codes:
                    codes.add(code)

        return codes

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
    def resolve_pdf_intermediate_codes(
        cls,
        *,
        root: dict,
        pdf_extract: dict,
        product_code: str,
    ) -> set[str]:
        """Intermediários efetivos no PDF — mesma reconciliação da comparação BOM."""
        pdf_intermediate = {
            ChatProductQueryIntentService.normalize_product_code(str(code))
            for code in (pdf_extract.get("intermediateCodes") or [])
            if code
            and ChatDrawingPatternsService.is_intermediate_family(str(code))
        }
        description_matched = cls.intermediate_codes_matched_by_description(
            root=root,
            pdf_extract=pdf_extract,
        )
        intermediate_matched, intermediate_false_rows = (
            cls.reconcile_intermediate_bom_row_description_matches(
                root=root,
                pdf_extract=pdf_extract,
                api_codes=set(
                    ChatDrawingStructureIndexService.collect_all_codes(
                        root,
                        product_code,
                    )
                ),
            )
        )
        pdf_intermediate |= description_matched | intermediate_matched

        structure_all_codes = ChatDrawingStructureIndexService.collect_all_codes(
            root,
            product_code,
        )
        _, false_row_codes = cls.reconcile_bom_row_description_matches(
            root=root,
            pdf_extract=pdf_extract,
            api_codes=set(structure_all_codes),
        )
        false_row_codes |= intermediate_false_rows
        for row in pdf_extract.get("bomRows") or []:
            if not isinstance(row, dict):
                continue

            row_code = ChatProductQueryIntentService.normalize_product_code(
                str(row.get("code") or "")
            )

            if (
                row_code
                and ChatDrawingPatternsService.is_intermediate_family(row_code)
                and ChatDrawingBomReferenceNoiseService.is_false_intermediate_bom_row(row)
            ):
                false_row_codes.add(row_code)

        pdf_intermediate -= {
            code
            for code in false_row_codes
            if ChatDrawingPatternsService.is_intermediate_family(str(code))
        }
        pdf_intermediate -= cls._fulltext_only_intermediate_phantoms(
            pdf_intermediate,
            pdf_extract=pdf_extract,
            description_matched=description_matched | intermediate_matched,
            false_row_codes=false_row_codes,
        )

        return pdf_intermediate

    @classmethod
    def reconcile_intermediate_bom_row_description_matches(
        cls,
        *,
        root: dict,
        pdf_extract: dict,
        api_codes: set[str],
    ) -> tuple[set[str], set[str]]:
        """Linha BOM 50xx com dígito OCR errado mas assinatura CB/CT alinhada ao cadastro."""
        structure = root.get("structure") if isinstance(root.get("structure"), dict) else {}
        api_intermediates = [
            row
            for row in ChatDrawingStructureIndexService.flatten_items(structure)
            if row.code in api_codes
            and ChatDrawingPatternsService.is_intermediate_family(str(row.code))
            and str(row.description or "").strip()
        ]
        matched: set[str] = set()
        false_row_codes: set[str] = set()

        for bom_row in pdf_extract.get("bomRows") or []:
            if not isinstance(bom_row, dict):
                continue

            if ChatDrawingBomReferenceNoiseService.is_client_reference_row(bom_row):
                continue

            row_code = ChatProductQueryIntentService.normalize_product_code(
                str(bom_row.get("code") or "")
            )
            row_desc = str(bom_row.get("description") or "").strip()

            if (
                not row_code
                or not row_desc
                or not ChatDrawingPatternsService.is_intermediate_family(row_code)
            ):
                continue

            row_haystack = row_desc.upper().replace(" ", "")
            best_api_code: str | None = None

            for struct_row in api_intermediates:
                signature = ChatDrawingPatternsService.intermediate_description_signature(
                    struct_row.description
                )

                if signature and signature in row_haystack:
                    best_api_code = struct_row.code
                    break

                for marker in cls._intermediate_color_markers(signature or ""):
                    if marker in row_haystack:
                        best_api_code = struct_row.code
                        break

                if best_api_code:
                    break

            if not best_api_code:
                continue

            matched.add(best_api_code)

            if row_code != best_api_code and row_code not in api_codes:
                false_row_codes.add(row_code)

        return matched, false_row_codes

    @classmethod
    def _fulltext_only_intermediate_phantoms(
        cls,
        pdf_intermediate: set[str],
        *,
        pdf_extract: dict,
        description_matched: set[str],
        false_row_codes: set[str],
    ) -> set[str]:
        """50xx só em lista OCR sem linha BOM nem assinatura de descrição."""
        row_intermediates = {
            ChatProductQueryIntentService.normalize_product_code(str(row.get("code") or ""))
            for row in pdf_extract.get("bomRows") or []
            if isinstance(row, dict)
            and ChatDrawingPatternsService.is_intermediate_family(str(row.get("code") or ""))
        }

        return {
            code
            for code in pdf_intermediate
            if code not in description_matched
            and code not in row_intermediates
            and code not in false_row_codes
            and not cls._intermediate_has_bom_row_description_evidence(
                code,
                pdf_extract=pdf_extract,
            )
        }

    @classmethod
    def _intermediate_has_bom_row_description_evidence(
        cls,
        code: str,
        *,
        pdf_extract: dict,
    ) -> bool:
        normalized = ChatProductQueryIntentService.normalize_product_code(code)

        for row in pdf_extract.get("bomRows") or []:
            if not isinstance(row, dict):
                continue

            row_code = ChatProductQueryIntentService.normalize_product_code(
                str(row.get("code") or "")
            )

            if row_code != normalized:
                continue

            description = str(row.get("description") or "").strip()

            if not description:
                return False

            if ChatDrawingBomReferenceNoiseService.is_false_intermediate_bom_row(row):
                return False

            return ChatDrawingBomReferenceNoiseService._intermediate_description_has_cable_evidence(
                description
            )

        return False

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
    def _apply_catalog_prefix_crosswalk(
        cls,
        pdf_codes: set[str],
        *,
        api_codes: set[str],
    ) -> set[str]:
        """Código catálogo 40xxxxxx no PDF → 10xxxxxx quando o MP canônico está na API."""
        if not bool(
            ChatDrawingPatternsService.bom_comparison_rule(
                "catalogPrefixCrosswalkEnabled",
                True,
            )
        ):
            return set(pdf_codes)

        from_prefix = str(
            ChatDrawingPatternsService.bom_comparison_rule(
                "catalogPrefixCrosswalkFrom",
                "40",
            )
            or "40"
        )
        to_prefix = str(
            ChatDrawingPatternsService.bom_comparison_rule(
                "catalogPrefixCrosswalkTo",
                "10",
            )
            or "10"
        )
        resolved = set(pdf_codes)

        for code in list(resolved):
            if not code.startswith(from_prefix) or len(code) != 8:
                continue

            primary = f"{to_prefix}{code[2:]}"

            if primary in api_codes:
                resolved.discard(code)
                resolved.add(primary)

        return resolved

    @classmethod
    def reconcile_bom_row_description_matches(
        cls,
        *,
        root: dict,
        pdf_extract: dict,
        api_codes: set[str],
    ) -> tuple[set[str], set[str]]:
        """Linha BOM com código OCR errado mas descrição alinhada ao cadastro API."""
        min_ratio = float(
            ChatDrawingPatternsService.bom_comparison_rule(
                "descriptionRowMatchMinOverlapRatio",
                0.5,
            )
            or 0.5
        )
        min_tokens = int(
            ChatDrawingPatternsService.bom_comparison_rule(
                "descriptionRowMatchMinOverlapTokens",
                3,
            )
            or 3
        )
        structure = root.get("structure") if isinstance(root.get("structure"), dict) else {}
        structure_rows = [
            row
            for row in ChatDrawingStructureIndexService.flatten_items(structure)
            if row.code in api_codes and str(row.description or "").strip()
        ]
        matched: set[str] = set()
        false_row_codes: set[str] = set()

        for bom_row in pdf_extract.get("bomRows") or []:
            if not isinstance(bom_row, dict):
                continue

            if ChatDrawingBomReferenceNoiseService.is_client_reference_row(bom_row):
                continue

            row_code = ChatProductQueryIntentService.normalize_product_code(
                str(bom_row.get("code") or "")
            )
            row_desc = str(bom_row.get("description") or "").strip()

            if not row_code or not row_desc:
                continue

            row_tokens = cls._description_match_tokens(row_desc)

            if len(row_tokens) < min_tokens:
                continue

            best_api_code: str | None = None
            best_ratio = 0.0

            for struct_row in structure_rows:
                api_tokens = cls._description_match_tokens(struct_row.description)
                overlap = row_tokens & api_tokens

                if len(overlap) < min_tokens:
                    continue

                ratio = len(overlap) / len(api_tokens)

                if ratio >= min_ratio and ratio > best_ratio:
                    best_ratio = ratio
                    best_api_code = struct_row.code

            if best_api_code:
                matched.add(best_api_code)

                if row_code not in api_codes:
                    false_row_codes.add(row_code)

        return matched, false_row_codes

    @classmethod
    def _description_match_tokens(cls, text: str) -> set[str]:
        normalized = str(text or "").upper()
        tokens: set[str] = set()

        for match in re.finditer(r"[A-Z]{3,}", normalized):
            token = match.group(0)

            if token in {
                "COM",
                "PARA",
                "ROHS",
                "DELPI",
                "FLEXTRONICS",
                "FLEXTRONIGS",
                "NBR",
                "STYLE",
                "COD",
            }:
                continue

            tokens.add(token)

        for match in re.finditer(r"\d{1,2}(?:-\d{1,2})?AWG", normalized):
            tokens.add(match.group(0))

        for match in re.finditer(r"\d{1,2}(?:-\d{1,2})?ANG", normalized):
            tokens.add(match.group(0))

        return tokens

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
