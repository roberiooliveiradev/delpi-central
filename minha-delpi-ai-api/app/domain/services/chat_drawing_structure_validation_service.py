"""Validação BOM, 50xx e cotas (PDF × estrutura API) — Onda 12.3+."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_drawing_bom_comparison_service import (
    ChatDrawingBomComparisonService,
)
from app.domain.services.chat_drawing_intermediate_semantics_service import (
    ChatDrawingIntermediateSemanticsService,
)
from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_drawing_tolerance_service import ChatDrawingToleranceService
from app.domain.services.chat_drawing_validation_content_service import (
    ChatDrawingValidationContentService,
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
        comparison = ChatDrawingBomComparisonService.compare(
            root=root,
            pdf_extract=pdf_extract,
            product_code=product_code,
        )

        if comparison.missing_in_pdf:
            items.append(
                content.item_from_template(
                    "bom_missing",
                    status="critical_error",
                    pdf_evidence=content.evidence("dash"),
                    api_evidence=", ".join(comparison.missing_in_pdf[:5]),
                )
            )

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
                )
            )

        items.extend(cls._intermediate_code_items(root, pdf_extract, product_code))
        items.extend(cls._intermediate_dimension_items(root, pdf_extract))
        items.extend(cls._dimension_items(root, pdf_extract))

        return items

    @classmethod
    def _intermediate_code_items(
        cls,
        root: dict,
        pdf_extract: dict,
        product_code: str,
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
            items.append(
                content.item_from_template(
                    "intermediate_missing",
                    status="error" if pdf_intermediate else "critical_error",
                    pdf_evidence=content.evidence("dash"),
                    api_evidence=", ".join(missing[:5]),
                )
            )

        extra_intermediate = sorted(
            code
            for code in (pdf_intermediate - api_intermediate)
            if ChatDrawingPatternsService.is_intermediate_family(code)
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
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        content = ChatDrawingValidationContentService
        intermediate_rows = (
            ChatDrawingIntermediateSemanticsService.collect_structure_intermediates(root)
        )

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

        dimensions = pdf_extract.get("dimensions") if isinstance(
            pdf_extract.get("dimensions"), dict
        ) else {}
        pdf_left = dimensions.get("leftDecapeMm")
        pdf_right = dimensions.get("rightDecapeMm")
        decape_candidates = cls._pdf_decape_candidates(dimensions)

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

        for key in ("leftDecapeMm", "rightDecapeMm"):
            parsed = ChatDrawingToleranceService.parse_mm(dimensions.get(key))

            if parsed is not None:
                values.append(parsed)

        for raw in dimensions.get("cotaDecapeValuesMm") or []:
            parsed = ChatDrawingToleranceService.parse_mm(raw)

            if parsed is not None:
                values.append(parsed)

        return list(dict.fromkeys(values))

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

            if result is not None:
                return result

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
    def _dimension_items(cls, root: dict, pdf_extract: dict) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        content = ChatDrawingValidationContentService
        dimensions = pdf_extract.get("dimensions") if isinstance(
            pdf_extract.get("dimensions"), dict
        ) else {}

        total_length = dimensions.get("totalLengthMm")
        left_decape = dimensions.get("leftDecapeMm")
        right_decape = dimensions.get("rightDecapeMm")
        segment_lengths = dimensions.get("segmentLengthsMm") or []
        intermediate_rows = (
            ChatDrawingIntermediateSemanticsService.collect_structure_intermediates(root)
        )

        if segment_lengths:
            api_lengths = [
                row.get("lengthMm")
                for row in intermediate_rows
                if row.get("lengthMm") is not None
            ]
            failing_segments: list[float] = []

            for segment in segment_lengths[
                : ChatDrawingPatternsService.max_segment_length_checks()
            ]:
                if not api_lengths:
                    break

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

        api_quantity = cls._root_structure_quantity(root)

        if total_length is not None and api_quantity is not None:
            within = ChatDrawingToleranceService.lengths_within_tolerance(
                total_length,
                api_quantity,
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

            items.append(
                content.item_from_template(
                    "total_length",
                    status=status,
                    pdf_evidence=content.evidence_format(
                        "totalLengthPdf",
                        value=str(total_length),
                    ),
                    api_evidence=str(api_quantity),
                    recommendation_field=recommendation_field,
                )
            )

        if left_decape is not None or right_decape is not None:
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
    def _root_structure_quantity(cls, root: dict) -> float | None:
        structure = root.get("structure") if isinstance(root.get("structure"), dict) else {}
        items = structure.get("items") or []

        if len(items) != 1:
            return None

        item = items[0]

        if not isinstance(item, dict):
            return None

        quantity = item.get("quantity")

        if quantity is None:
            return None

        try:
            value = float(quantity)
        except (TypeError, ValueError):
            return None

        if value <= 0 or value > ChatDrawingPatternsService.max_root_structure_quantity_mm():
            return None

        return value
