"""Validação BOM, 50xx e cotas (PDF × estrutura API) — Onda 12.3+."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_drawing_bom_comparison_service import (
    ChatDrawingBomComparisonService,
)
from app.domain.services.chat_drawing_bom_quantity_semantics_service import (
    ChatDrawingBomQuantitySemanticsService,
)
from app.domain.services.chat_drawing_intermediate_code_service import (
    ChatDrawingIntermediateCodeService,
)
from app.domain.services.chat_drawing_intermediate_semantics_service import (
    ChatDrawingIntermediateSemanticsService,
)
from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_drawing_regional_scope_service import (
    ChatDrawingRegionalScopeService,
)
from app.domain.services.chat_drawing_tolerance_service import ChatDrawingToleranceService
from app.domain.services.chat_drawing_total_length_reference_service import (
    ChatDrawingTotalLengthReferenceService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.services.chat_drawing_validation_content_service import (
    ChatDrawingValidationContentService,
)
from app.domain.services.chat_drawing_validation_rule_registry_service import (
    ChatDrawingValidationRuleRegistryService,
)


class ChatDrawingStructureValidationService:
    @classmethod
    def build_check_items(
        cls,
        *,
        root: dict,
        pdf_extract: dict,
        product_code: str,
    ) -> list[dict[str, Any]]:
        if not isinstance(pdf_extract, dict) or not pdf_extract.get("legible"):
            return []

        items: list[dict[str, Any]] = []
        content = ChatDrawingValidationContentService
        bom_scope = cls._bom_scope(pdf_extract)
        bom_scope_label = ChatDrawingRegionalScopeService.scope_label(
            bom_scope.get("sourceKey")
        )
        bom_available = bool(bom_scope.get("available"))
        comparison = ChatDrawingBomComparisonService.compare(
            root=root,
            pdf_extract=pdf_extract,
            product_code=product_code,
        )
        has_pdf_bom_signal = bom_available or bool(pdf_extract.get("componentCodes"))
        group_code = cls._product_group_code(root)

        if ChatDrawingValidationRuleRegistryService.is_enabled(
            "bom_comparison",
            product_code,
            group_code=group_code,
        ):
            if not bom_available and not pdf_extract.get("componentCodes"):
                items.append(
                    content.item_from_template(
                        "bom_scope_unavailable",
                        status="pending",
                        pdf_evidence=content.evidence("pendingPdf"),
                        api_evidence=content.evidence("dash"),
                        recommendation_field="recommendationPending",
                        pdf_scope=bom_scope_label,
                    )
                )

            if has_pdf_bom_signal and comparison.missing_in_pdf:
                from app.domain.services.chat_drawing_multipage_coverage_service import (
                    ChatDrawingMultipageCoverageService,
                )

                items.append(
                    content.item_from_template(
                        "bom_missing",
                        status=ChatDrawingMultipageCoverageService.resolve_absence_check_status(
                            "critical_error",
                            pdf_extract=pdf_extract,
                            comparison=comparison,
                        ),
                        pdf_evidence=content.evidence("dash"),
                        api_evidence=", ".join(comparison.missing_in_pdf[:5]),
                        pdf_scope=bom_scope_label,
                    )
                )

            if has_pdf_bom_signal:
                bom_only_extra = sorted(
                    code
                    for code in comparison.extra_in_pdf
                    if not ChatDrawingPatternsService.is_intermediate_family(str(code))
                )

                if bom_only_extra:
                    items.append(
                        content.item_from_template(
                            "bom_extra",
                            status="critical_error",
                            pdf_evidence=", ".join(bom_only_extra[:8]),
                            api_evidence=content.evidence("dash"),
                            pdf_scope=bom_scope_label,
                        )
                    )

                if comparison.api_codes and comparison.pdf_bom_codes and not (
                    comparison.missing_in_pdf or comparison.extra_in_pdf
                ):
                    items.append(
                        content.item_from_template(
                            "bom_match_ok",
                            status="ok",
                            pdf_evidence=content.evidence_format(
                                "codeCount",
                                count=str(len(comparison.pdf_bom_codes)),
                            ),
                            api_evidence=content.evidence_format(
                                "codeCount",
                                count=str(len(comparison.api_codes)),
                            ),
                            pdf_scope=bom_scope_label,
                        )
                    )

        from app.domain.services.chat_drawing_multipage_coverage_service import (
            ChatDrawingMultipageCoverageService,
        )

        if ChatDrawingValidationRuleRegistryService.is_enabled(
            "multipage_coverage",
            product_code,
            group_code=group_code,
        ):
            items.extend(
                ChatDrawingMultipageCoverageService.build_check_items(
                    pdf_extract=pdf_extract,
                    comparison=comparison,
                )
            )

        if ChatDrawingValidationRuleRegistryService.is_enabled(
            "bom_quantity",
            product_code,
            group_code=group_code,
        ):
            from app.domain.services.chat_drawing_bom_quantity_validation_service import (
                ChatDrawingBomQuantityValidationService,
            )

            items.extend(
                ChatDrawingBomQuantityValidationService.build_check_items(
                    root=root,
                    pdf_extract=pdf_extract,
                    product_code=product_code,
                )
            )

        if ChatDrawingValidationRuleRegistryService.is_enabled(
            "balloon_presence",
            product_code,
            group_code=group_code,
        ):
            from app.domain.services.chat_drawing_balloon_validation_service import (
                ChatDrawingBalloonValidationService,
            )

            items.extend(
                ChatDrawingBalloonValidationService.build_check_items(
                    pdf_extract=pdf_extract,
                )
            )

        if ChatDrawingValidationRuleRegistryService.is_enabled(
            "intermediate_presence",
            product_code,
            group_code=group_code,
        ):
            items.extend(
                cls._intermediate_code_items(
                    root,
                    pdf_extract,
                    product_code,
                    comparison=comparison,
                )
            )

        if ChatDrawingValidationRuleRegistryService.is_enabled(
            "intermediate_length",
            product_code,
            group_code=group_code,
        ) or ChatDrawingValidationRuleRegistryService.is_enabled(
            "decape_per_intermediate",
            product_code,
            group_code=group_code,
        ):
            items.extend(
                cls._intermediate_dimension_items(
                    root,
                    pdf_extract,
                    product_code,
                    group_code=group_code,
                )
            )

        items.extend(
            cls._dimension_items(
                root,
                pdf_extract,
                bom_scope_label,
                product_code=product_code,
                group_code=group_code,
            )
        )

        return items

    @classmethod
    def _bom_scope(cls, pdf_extract: dict) -> dict[str, Any]:
        scopes = pdf_extract.get("validationScopes")

        if isinstance(scopes, dict):
            bom = scopes.get("bom")

            if isinstance(bom, dict):
                return bom

        source_metadata = pdf_extract.get("sourceMetadata")

        resolved = ChatDrawingRegionalScopeService.resolve(
            metadata=source_metadata if isinstance(source_metadata, dict) else {},
            full_text="",
        )

        bom = resolved.get("bom")

        return bom if isinstance(bom, dict) else {}

    @classmethod
    def _product_group_code(cls, root: dict) -> str | None:
        product = root.get("product") if isinstance(root.get("product"), dict) else {}
        group_code = str(product.get("group_code") or "").strip()

        return group_code or None

    @classmethod
    def _intermediate_code_items(
        cls,
        root: dict,
        pdf_extract: dict,
        product_code: str,
        *,
        comparison=None,
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        content = ChatDrawingValidationContentService
        pdf_intermediate = set(pdf_extract.get("intermediateCodes") or [])
        pdf_intermediate |= ChatDrawingBomComparisonService.intermediate_codes_matched_by_description(
            root=root,
            pdf_extract=pdf_extract,
        )
        api_intermediate = cls._collect_api_intermediate_codes(root, product_code)

        malformed = [
            code
            for code in pdf_intermediate
            if code and not ChatDrawingPatternsService.is_intermediate_family(str(code))
        ]

        if malformed:
            items.append(
                content.item_from_template(
                    "intermediate_malformed",
                    status="critical_error",
                    pdf_evidence=", ".join(malformed[:3]),
                    api_evidence=content.evidence("dash"),
                )
            )

        missing = sorted(api_intermediate - pdf_intermediate)

        if missing:
            default_status = "error" if pdf_intermediate else "critical_error"

            if comparison is not None:
                from app.domain.services.chat_drawing_multipage_coverage_service import (
                    ChatDrawingMultipageCoverageService,
                )

                status = ChatDrawingMultipageCoverageService.resolve_absence_check_status(
                    default_status,
                    pdf_extract=pdf_extract,
                    comparison=comparison,
                )
            else:
                status = default_status

            items.append(
                content.item_from_template(
                    "intermediate_missing",
                    status=status,
                    pdf_evidence=content.evidence("dash"),
                    api_evidence=", ".join(missing[:5]),
                )
            )

        extra_intermediate = sorted(
            code
            for code in (pdf_intermediate - api_intermediate)
            if ChatDrawingPatternsService.is_intermediate_family(code)
            and not any(
                ChatDrawingIntermediateCodeService.is_ocr_typo_duplicate(code, api_code)
                for api_code in api_intermediate
            )
        )

        if extra_intermediate:
            items.append(
                content.item_from_template(
                    "intermediate_extra",
                    status="critical_error",
                    pdf_evidence=", ".join(extra_intermediate[:5]),
                    api_evidence=content.evidence("dash"),
                )
            )

        if pdf_intermediate and api_intermediate and not missing and not extra_intermediate:
            items.append(
                content.item_from_template(
                    "intermediate_match_ok",
                    status="ok",
                    pdf_evidence=", ".join(sorted(pdf_intermediate)[:5]),
                    api_evidence=", ".join(sorted(api_intermediate)[:5]),
                )
            )

        return items

    @classmethod
    def _collect_api_intermediate_codes(cls, root: dict, product_code: str) -> set[str]:
        codes: set[str] = set()

        for code in ChatDrawingBomComparisonService.collect_structure_bom_codes(
            root,
            product_code,
        ):
            if ChatDrawingPatternsService.is_intermediate_family(str(code)):
                codes.add(code)

        return codes

    @classmethod
    def _intermediate_dimension_items(
        cls,
        root: dict,
        pdf_extract: dict,
        product_code: str,
        *,
        group_code: str | None = None,
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        content = ChatDrawingValidationContentService
        intermediate_rows = (
            ChatDrawingIntermediateSemanticsService.collect_structure_intermediates(root)
        )
        length_enabled = ChatDrawingValidationRuleRegistryService.is_enabled(
            "intermediate_length",
            product_code,
            group_code=group_code,
        )
        decape_enabled = ChatDrawingValidationRuleRegistryService.is_enabled(
            "decape_per_intermediate",
            product_code,
            group_code=group_code,
        )

        if length_enabled:
            for row in intermediate_rows:
                code = str(row.get("code") or "")
                length = row.get("lengthMm")
                cable_qty = row.get("cableQuantityMm")
                cable_unit = str(row.get("cableUnit") or "mm")

                if length is None or cable_qty is None:
                    continue

                within = ChatDrawingToleranceService.lengths_within_tolerance(length, cable_qty)

                if within is False:
                    items.append(
                        content.item_from_template(
                            "intermediate_length",
                            status="critical_error",
                            pdf_evidence=content.evidence_format(
                                "lengthFromDescription",
                                length=str(length),
                            ),
                            api_evidence=content.evidence_format(
                                "lengthFromStructure",
                                length=str(cable_qty),
                                unit=cable_unit,
                            ),
                            item_values={"code": code},
                        )
                    )

        if not decape_enabled:
            return items

        dimensions = pdf_extract.get("dimensions") if isinstance(
            pdf_extract.get("dimensions"), dict
        ) else {}
        pdf_left = dimensions.get("leftDecapeMm")
        pdf_right = dimensions.get("rightDecapeMm")
        decape_candidates = cls._pdf_decape_candidates(dimensions)

        if cls._should_skip_per_intermediate_decape_checks(
            pdf_extract,
            dimensions,
            root=root,
        ):
            return items

        if pdf_left is None and pdf_right is None and not decape_candidates:
            return items

        for row in intermediate_rows:
            left = row.get("leftDecapeMm")
            right = row.get("rightDecapeMm")
            code = str(row.get("code") or "")

            if left is None and right is None:
                continue

            for side_key, expected, pdf_ref in (
                ("left", left, pdf_left),
                ("right", right, pdf_right),
            ):
                if expected is None:
                    continue

                if not cls._decape_side_indicated(dimensions, side_key):
                    continue

                if pdf_ref is not None and cls._should_skip_intermediate_decape_for_profile(
                    pdf_ref,
                    expected,
                ):
                    continue

                within = cls._decape_matches_pdf(
                    expected,
                    pdf_ref=pdf_ref,
                    candidates=decape_candidates,
                )

                if within is False:
                    pdf_value = pdf_ref if pdf_ref is not None else cls._best_candidate(
                        expected,
                        decape_candidates,
                    )
                    items.append(
                        content.item_from_template(
                            "decape_mismatch",
                            status="error",
                            pdf_evidence=content.evidence_format(
                                "decapePdf",
                                value=str(pdf_value if pdf_value is not None else "—"),
                            ),
                            api_evidence=content.evidence_format(
                                "decapeFromIntermediate",
                                value=str(expected),
                            ),
                            item_values={
                                "side": content.decape_side(side_key),
                                "code": code,
                            },
                        )
                    )

        return items

    @classmethod
    def _pdf_decape_candidates(cls, dimensions: dict[str, Any]) -> list[float]:
        values: list[float] = []
        indication = dimensions.get("decapeIndication")
        side_indicated = (
            indication if isinstance(indication, dict) else {"left": False, "right": False}
        )
        typical = ChatDrawingPatternsService.typical_cable_decape_mm()

        for key in ("leftDecapeMm", "rightDecapeMm"):
            parsed = ChatDrawingToleranceService.parse_mm(dimensions.get(key))

            if parsed is None:
                continue

            side = "left" if key == "leftDecapeMm" else "right"

            if parsed > typical and not side_indicated.get(side):
                continue

            values.append(parsed)

        for raw in dimensions.get("cotaDecapeValuesMm") or []:
            parsed = ChatDrawingToleranceService.parse_mm(raw)

            if parsed is None or parsed > typical:
                continue

            values.append(parsed)

        return list(dict.fromkeys(values))

    @classmethod
    def _should_skip_per_intermediate_decape_checks(
        cls,
        pdf_extract: dict,
        dimensions: dict[str, Any],
        *,
        root: dict | None = None,
    ) -> bool:
        from app.domain.services.chat_drawing_dimensions_extraction_service import (
            ChatDrawingDimensionsExtractionService,
        )

        haystack = cls._dimension_note_haystack(pdf_extract)

        if ChatDrawingDimensionsExtractionService.detect_ambiguous_dimension_notes(
            haystack
        ):
            return True

        if ChatDrawingDimensionsExtractionService.only_implausible_global_decape(
            dimensions
        ):
            return True

        if cls._pdf_global_decape_unmatched_by_all_intermediates(dimensions, root):
            return True

        if root and cls._global_decape_conflicts_with_intermediate_profile(
            dimensions,
            root,
        ):
            return True

        return False

    @classmethod
    def _global_decape_conflicts_with_intermediate_profile(
        cls,
        dimensions: dict[str, Any],
        root: dict,
    ) -> bool:
        from app.domain.services.chat_drawing_intermediate_semantics_service import (
            ChatDrawingIntermediateSemanticsService,
        )

        pdf_left = ChatDrawingToleranceService.parse_mm(dimensions.get("leftDecapeMm"))

        if pdf_left is None:
            return False

        expected_lefts = [
            float(value)
            for row in ChatDrawingIntermediateSemanticsService.collect_structure_intermediates(
                root
            )
            if (value := row.get("leftDecapeMm")) is not None
        ]

        if not expected_lefts:
            return False

        max_expected = max(expected_lefts)
        ratio = ChatDrawingPatternsService.decape_global_mismatch_ratio()

        return pdf_left > max_expected * ratio

    @classmethod
    def _pdf_global_decape_unmatched_by_all_intermediates(
        cls,
        dimensions: dict[str, Any],
        root: dict,
    ) -> bool:
        rows = ChatDrawingIntermediateSemanticsService.collect_structure_intermediates(root)

        for side in ("left", "right"):
            pdf_key = f"{side}DecapeMm"
            pdf_val = ChatDrawingToleranceService.parse_mm(dimensions.get(pdf_key))

            if pdf_val is None or not cls._decape_side_indicated(dimensions, side):
                continue

            expected_key = f"{side}DecapeMm"
            expected_values = [
                float(value)
                for row in rows
                if (value := row.get(expected_key)) is not None
            ]

            if not expected_values:
                continue

            if not any(
                ChatDrawingToleranceService.decape_within_tolerance(pdf_val, expected)
                is True
                for expected in expected_values
            ):
                return True

        return False

    @classmethod
    def _should_skip_intermediate_decape_for_profile(
        cls,
        pdf_ref: float,
        expected: float,
    ) -> bool:
        if ChatDrawingToleranceService.decape_within_tolerance(pdf_ref, expected) is not False:
            return False

        gap = abs(float(pdf_ref) - float(expected))
        skip_gap = ChatDrawingPatternsService.validation_rule_float(
            "decapeProfileMismatchSkipMm",
            ChatDrawingPatternsService.decape_tolerance_mm() * 2,
        )

        return gap > skip_gap

    @classmethod
    def _decape_side_indicated(cls, dimensions: dict[str, Any], side: str) -> bool:
        indication = dimensions.get("decapeIndication")

        if isinstance(indication, dict):
            return bool(indication.get(side))

        key = "leftDecapeMm" if side == "left" else "rightDecapeMm"
        return dimensions.get(key) is not None

    @classmethod
    def _decape_matches_pdf(
        cls,
        expected: float,
        *,
        pdf_ref: float | None,
        candidates: list[float],
    ) -> bool | None:
        if pdf_ref is not None:
            result = ChatDrawingToleranceService.decape_within_tolerance(pdf_ref, expected)

            if result is True:
                return True

        for candidate in candidates:
            if ChatDrawingToleranceService.decape_within_tolerance(candidate, expected) is True:
                return True

        if pdf_ref is None and not candidates:
            return None

        return False

    @classmethod
    def _best_candidate(cls, expected: float, candidates: list[float]) -> float | None:
        best: float | None = None
        best_delta = float("inf")

        for candidate in candidates:
            delta = abs(candidate - expected)

            if delta < best_delta:
                best_delta = delta
                best = candidate

        return best

    @classmethod
    def _dimension_note_items(cls, pdf_extract: dict) -> list[dict[str, Any]]:
        from app.domain.services.chat_drawing_dimensions_extraction_service import (
            ChatDrawingDimensionsExtractionService,
        )

        if not ChatDrawingDimensionsExtractionService.detect_ambiguous_dimension_notes(
            cls._dimension_note_haystack(pdf_extract)
        ):
            return []

        content = ChatDrawingValidationContentService
        haystack = cls._dimension_note_haystack(pdf_extract)
        pdf_evidence = (
            ChatDrawingDimensionsExtractionService.summarize_ambiguous_dimension_notes(
                haystack
            )
            or content.evidence("pendingPdf")
        )

        return [
            content.item_from_template(
                ChatDrawingPatternsService.dimension_note_validation_rule(
                    "ambiguousTemplateKey",
                    "dimension_note_ambiguous",
                ),
                status=ChatDrawingPatternsService.dimension_note_validation_rule(
                    "ambiguousStatus",
                    "pending",
                ),
                pdf_evidence=pdf_evidence,
                api_evidence=content.evidence("dash"),
            )
        ]

    @classmethod
    def _dimension_note_haystack(cls, pdf_extract: dict) -> str:
        parts: list[str] = []
        dimensions = pdf_extract.get("dimensions")

        if isinstance(dimensions, dict):
            for key in ("notesText", "rawText"):
                value = dimensions.get(key)

                if value:
                    parts.append(str(value))

        source_metadata = pdf_extract.get("sourceMetadata")

        if isinstance(source_metadata, dict):
            for key in ChatDrawingPatternsService.pdf_haystack_source_metadata_keys():
                value = source_metadata.get(key)

                if value:
                    parts.append(str(value))

        full_text = pdf_extract.get("fullText")

        if full_text:
            parts.append(str(full_text))

        return "\n".join(parts)

    @classmethod
    def _dimension_items(
        cls,
        root: dict,
        pdf_extract: dict,
        bom_scope_label: str = "",
        *,
        product_code: str = "",
        group_code: str | None = None,
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        content = ChatDrawingValidationContentService
        dimensions = pdf_extract.get("dimensions") if isinstance(
            pdf_extract.get("dimensions"), dict
        ) else {}

        if ChatDrawingValidationRuleRegistryService.is_enabled(
            "dimension_note",
            product_code,
            group_code=group_code,
        ):
            items.extend(cls._dimension_note_items(pdf_extract))

        total_length = dimensions.get("totalLengthMm")
        left_decape = dimensions.get("leftDecapeMm")
        right_decape = dimensions.get("rightDecapeMm")
        segment_lengths = dimensions.get("segmentLengthsMm") or []
        intermediate_rows = (
            ChatDrawingIntermediateSemanticsService.collect_structure_intermediates(root)
        )

        if segment_lengths and ChatDrawingValidationRuleRegistryService.is_enabled(
            "segment_length",
            product_code,
            group_code=group_code,
        ):
            api_lengths = [
                row.get("lengthMm")
                for row in intermediate_rows
                if row.get("lengthMm") is not None
            ]
            structure_piece_quantities = (
                ChatDrawingBomQuantitySemanticsService.collect_structure_segment_reference_mm(
                    root
                )
            )
            failing_segments: list[float] = []

            for segment in segment_lengths[
                : ChatDrawingPatternsService.max_segment_length_checks()
            ]:
                if not api_lengths:
                    break

                if (
                    ChatDrawingPatternsService.bom_quantity_semantics_rule(
                        "rejectSegmentMatchingStructurePieceQuantity",
                        False,
                    )
                    and cls._segment_matches_structure_piece_quantity(
                        segment,
                        structure_piece_quantities,
                        api_lengths,
                    )
                ):
                    continue

                matched = any(
                    ChatDrawingToleranceService.lengths_within_tolerance(segment, api_len)
                    is True
                    for api_len in api_lengths
                )

                if matched is False:
                    failing_segments.append(segment)

            if failing_segments:
                pdf_evidence = content.evidence_format(
                    "segmentLengthsList",
                    values="; ".join(
                        content.evidence_format("segmentLength", value=str(value))
                        for value in failing_segments
                    ),
                )
                items.append(
                    content.item_from_template(
                        "segment_length_pending",
                        status="pending",
                        pdf_evidence=pdf_evidence,
                        api_evidence=", ".join(str(v) for v in api_lengths[:4]),
                    )
                )

        api_reference = ChatDrawingTotalLengthReferenceService.resolve(root)
        dimensions_scope = (pdf_extract.get("validationScopes") or {}).get("dimensions")
        dimensions_scope_label = ChatDrawingRegionalScopeService.scope_label(
            dimensions_scope.get("sourceKey")
            if isinstance(dimensions_scope, dict)
            else None
        )

        if (
            total_length is not None
            and api_reference is not None
            and ChatDrawingValidationRuleRegistryService.is_enabled(
                "total_length",
                product_code,
                group_code=group_code,
            )
        ):
            within = ChatDrawingToleranceService.lengths_within_tolerance(
                total_length,
                api_reference.length_mm,
            )

            if within is True:
                recommendation_field = "recommendationOk"
                status = "ok"
            elif within is False:
                recommendation_field = "recommendationCritical"
                status = "critical_error"
            else:
                recommendation_field = "recommendationPending"
                status = "pending"

            api_evidence = (
                content.evidence_format(
                    "lengthFromStructure",
                    length=str(api_reference.length_mm),
                    unit=str(api_reference.unit_label or "mm"),
                )
                if api_reference.unit_label
                else str(api_reference.length_mm)
            )

            items.append(
                content.item_from_template(
                    "total_length",
                    status=status,
                    pdf_evidence=content.evidence_format(
                        "totalLengthPdf",
                        value=str(total_length),
                    ),
                    api_evidence=api_evidence,
                    recommendation_field=recommendation_field,
                    pdf_scope=dimensions_scope_label or bom_scope_label,
                )
            )

        if (
            (left_decape is not None or right_decape is not None)
            and ChatDrawingValidationRuleRegistryService.is_enabled(
                "decapes_ed",
                product_code,
                group_code=group_code,
            )
        ):
            indication = dimensions.get("decapeIndication") if isinstance(
                dimensions.get("decapeIndication"), dict
            ) else {}
            left_indicated = bool(indication.get("left")) if indication else left_decape is not None
            right_indicated = bool(indication.get("right")) if indication else right_decape is not None
            decape_status = "ok"

            if left_indicated and left_decape is None:
                decape_status = "pending"

            if right_indicated and right_decape is None:
                decape_status = "pending"

            items.append(
                content.item_from_template(
                    "decapes_ed",
                    status=decape_status,
                    pdf_evidence=content.evidence_format(
                        "decapesPair",
                        left=str(left_decape or content.evidence("dash")),
                        right=str(right_decape or content.evidence("dash")),
                    ),
                    api_evidence=content.evidence_format("checkIntermediate50xx"),
                    recommendation_field=(
                        "recommendationOk"
                        if decape_status == "ok"
                        else "recommendationPending"
                    ),
                )
            )

        return items

    @classmethod
    def _segment_matches_structure_piece_quantity(
        cls,
        segment: float,
        structure_piece_quantities: set[float],
        api_lengths: list[Any],
    ) -> bool:
        if not structure_piece_quantities:
            return False

        matched_piece = any(
            ChatDrawingToleranceService.lengths_within_tolerance(segment, piece_qty) is True
            for piece_qty in structure_piece_quantities
        )

        if not matched_piece:
            return False

        matched_intermediate = any(
            ChatDrawingToleranceService.lengths_within_tolerance(segment, api_len) is True
            for api_len in api_lengths
            if api_len is not None
        )

        return not matched_intermediate
