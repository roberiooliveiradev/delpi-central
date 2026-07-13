"""Evidência de quantidade BOM — rejeita ruído OCR antes de crítico PDF × SG1010."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_drawing_bom_quantity_semantics_service import (
    ChatDrawingBomQuantitySemanticsService,
    StructureQuantityRow,
)
from app.domain.services.chat_drawing_intermediate_semantics_service import (
    ChatDrawingIntermediateSemanticsService,
)
from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_drawing_tolerance_service import ChatDrawingToleranceService
from app.domain.services.chat_drawing_structure_index_service import (
    ChatDrawingStructureIndexService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


@dataclass(frozen=True)
class BomQuantityEvidence:
    code: str
    quantity: float
    trusted: bool
    reason: str | None = None


class ChatDrawingBomQuantityAssertivenessService:
    @classmethod
    def collect_evidences(
        cls,
        *,
        root: dict,
        pdf_extract: dict,
        product_code: str,
    ) -> dict[str, BomQuantityEvidence]:
        api_quantities = ChatDrawingBomQuantitySemanticsService.collect_structure_quantities(
            root,
            product_code,
        )
        grouped: dict[str, list[BomQuantityEvidence]] = {}

        for row in pdf_extract.get("bomRows") or []:
            if not isinstance(row, dict):
                continue

            code = ChatProductQueryIntentService.normalize_product_code(
                str(row.get("code") or "")
            )
            quantity = ChatDrawingToleranceService.parse_mm(row.get("quantity"))

            if not code or quantity is None:
                continue

            api_row = api_quantities.get(code)
            reason = cls._untrusted_reason(
                row=row,
                code=code,
                quantity=quantity,
                api_row=api_row,
                root=root,
                pdf_extract=pdf_extract,
            )
            grouped.setdefault(code, []).append(
                BomQuantityEvidence(
                    code=code,
                    quantity=quantity,
                    trusted=reason is None,
                    reason=reason,
                )
            )

        return {
            code: cls._pick_best_evidence(
                code,
                candidates,
                api_row=api_quantities.get(code),
                root=root,
                pdf_extract=pdf_extract,
            )
            for code, candidates in grouped.items()
        }

    @classmethod
    def collect_trusted_quantities(
        cls,
        *,
        root: dict,
        pdf_extract: dict,
        product_code: str,
    ) -> dict[str, float]:
        return {
            code: evidence.quantity
            for code, evidence in cls.collect_evidences(
                root=root,
                pdf_extract=pdf_extract,
                product_code=product_code,
            ).items()
            if evidence.trusted
        }

    @classmethod
    def mismatch_status(
        cls,
        *,
        trusted: bool,
        pdf_extract: dict | None = None,
        code: str = "",
    ) -> str:
        if not trusted:
            return str(
                ChatDrawingPatternsService.bom_quantity_semantics_rule(
                    "mismatchStatusWhenUncertain",
                    "pending",
                )
            )

        required_sources = ChatDrawingPatternsService.bom_quantity_critical_requires_sources()

        if required_sources:
            row = cls._bom_row(pdf_extract, code)
            source = str(row.get("quantitySource") or "").strip().lower()

            if source not in required_sources:
                if ChatDrawingPatternsService.bom_quantity_refinement_exhausted_pending():
                    return str(
                        ChatDrawingPatternsService.bom_quantity_semantics_rule(
                            "mismatchStatusWhenUncertain",
                            "pending",
                        )
                    )

        return str(
            ChatDrawingPatternsService.bom_quantity_semantics_rule(
                "mismatchStatusWhenTrusted",
                "critical_error",
            )
        )

    @classmethod
    def _bom_row(cls, pdf_extract: dict | None, code: str) -> dict[str, Any]:
        normalized = str(code or "").strip()

        if not normalized or not isinstance(pdf_extract, dict):
            return {}

        for row in pdf_extract.get("bomRows") or []:
            if not isinstance(row, dict):
                continue

            row_code = str(row.get("code") or "").strip()

            if row_code == normalized:
                return row

        return {}

    @classmethod
    def _pick_best_evidence(
        cls,
        code: str,
        candidates: list[BomQuantityEvidence],
        *,
        api_row: StructureQuantityRow | None,
        root: dict,
        pdf_extract: dict,
    ) -> BomQuantityEvidence:
        if not candidates:
            return BomQuantityEvidence(code=code, quantity=0.0, trusted=False, reason="missing")

        if api_row is not None:
            matching = [
                candidate
                for candidate in candidates
                if cls._matches_api(
                    quantity=candidate.quantity,
                    api_row=api_row,
                    root=root,
                    pdf_extract=pdf_extract,
                )
            ]

            if matching:
                preferred = next(
                    (candidate for candidate in matching if candidate.trusted),
                    matching[0],
                )
                return BomQuantityEvidence(
                    code=code,
                    quantity=preferred.quantity,
                    trusted=True,
                )

        trusted = [candidate for candidate in candidates if candidate.trusted]

        if trusted:
            return trusted[0]

        return candidates[0]

    @classmethod
    def _matches_api(
        cls,
        *,
        quantity: float,
        api_row: StructureQuantityRow,
        root: dict,
        pdf_extract: dict,
    ) -> bool:
        normalization = ChatDrawingBomQuantitySemanticsService.normalize_pdf_quantity(
            pdf_quantity=quantity,
            api_row=api_row,
            root=root,
            pdf_extract=pdf_extract,
        )

        if not normalization.comparable or normalization.pdf_value is None:
            return False

        within = ChatDrawingToleranceService.lengths_within_tolerance(
            normalization.pdf_value,
            api_row.quantity,
            ratio=ChatDrawingPatternsService.quantity_tolerance_ratio(),
        )

        return within is not False

    @classmethod
    def _untrusted_reason(
        cls,
        *,
        row: dict[str, Any],
        code: str,
        quantity: float,
        api_row: StructureQuantityRow | None,
        root: dict,
        pdf_extract: dict,
    ) -> str | None:
        if quantity <= 0 and ChatDrawingPatternsService.bom_quantity_semantics_rule(
            "rejectZeroQuantity",
            True,
        ):
            return "zero_quantity"

        if ChatDrawingPatternsService.is_intermediate_family(code):
            intermediate_reason = cls._intermediate_quantity_reason(
                row=row,
                code=code,
                quantity=quantity,
            )

            if intermediate_reason:
                return intermediate_reason

        if ChatDrawingPatternsService.bom_quantity_semantics_rule(
            "rejectQuantityMatchingDescriptionNumber",
            True,
        ) and cls._quantity_matches_description(
            row,
            quantity,
            code=code,
            pdf_extract=pdf_extract,
            root=root,
        ):
            return "quantity_from_description"

        source = str(row.get("quantitySource") or "").strip().lower()
        trusted_column_source = bool(row.get("quantityTrusted")) and source in {
            "column",
            "column_inferred",
            "refined_column",
        }

        piece_units = ChatDrawingPatternsService.piece_count_units()
        api_unit = (api_row.unit if api_row else "").upper()

        if api_unit in piece_units or not api_row:
            max_qty = int(
                ChatDrawingPatternsService.bom_quantity_semantics_rule(
                    "maxTrustedPieceQuantity",
                    99,
                )
            )

            if quantity > max_qty:
                return "piece_quantity_implausible"

            if (
                ChatDrawingPatternsService.bom_quantity_semantics_rule(
                    "rejectDecimalPieceQuantity",
                    True,
                )
                and not float(quantity).is_integer()
            ):
                return "decimal_piece_quantity"

        # OCR de célula (refined_column) em PDF ODA/fonte colada: decimais que não
        # batem com a SG1010 são ruído (ex.: 0.756 lido no lugar de 01 / 750 mm).
        if (
            source == "refined_column"
            and ChatDrawingPatternsService.bom_quantity_semantics_rule(
                "rejectDecimalPieceQuantity",
                True,
            )
            and not float(quantity).is_integer()
            and (
                api_row is None
                or not cls._matches_api(
                    quantity=quantity,
                    api_row=api_row,
                    root=root,
                    pdf_extract=pdf_extract,
                )
            )
        ):
            return "decimal_piece_quantity"

        if api_row is not None and not cls._matches_api(
            quantity=quantity,
            api_row=api_row,
            root=root,
            pdf_extract=pdf_extract,
        ):
            batch_scale = ChatDrawingBomQuantitySemanticsService.batch_scale_for_root(root)

            if (
                batch_scale > 1
                and cls._alternate_piece_quantity_matches_api(
                    quantity=quantity,
                    api_row=api_row,
                    root=root,
                    pdf_extract=pdf_extract,
                )
            ):
                return "quantity_api_crosscheck"

        return None

    @classmethod
    def _alternate_piece_quantity_matches_api(
        cls,
        *,
        quantity: float,
        api_row: StructureQuantityRow,
        root: dict,
        pdf_extract: dict,
    ) -> bool:
        if api_row.unit.upper() not in ChatDrawingPatternsService.piece_count_units():
            return False

        max_qty = int(
            ChatDrawingPatternsService.bom_quantity_semantics_rule(
                "maxAlternateCrosscheckQuantity",
                20,
            )
        )

        for alt in range(1, max_qty + 1):
            if float(alt) == float(quantity):
                continue

            if cls._matches_api(
                quantity=float(alt),
                api_row=api_row,
                root=root,
                pdf_extract=pdf_extract,
            ):
                return True

        return False

    @classmethod
    def _intermediate_quantity_reason(
        cls,
        *,
        row: dict[str, Any],
        code: str,
        quantity: float,
    ) -> str | None:
        if not ChatDrawingPatternsService.bom_quantity_semantics_rule(
            "rejectIntermediateLengthAsQuantity",
            True,
        ):
            return None

        min_length_mm = float(
            ChatDrawingPatternsService.bom_quantity_semantics_float(
                "intermediateLengthQuantityMinMm",
                50.0,
            )
        )
        description = str(row.get("description") or "")
        qty_raw = str(row.get("quantity") or "").strip()
        parsed = ChatDrawingIntermediateSemanticsService.parse_description(description)

        length_mm = parsed.get("lengthMm")

        if length_mm is not None and abs(float(length_mm) - quantity) < 0.01:
            return "intermediate_length_as_quantity"

        if qty_raw.startswith("0") and len(qty_raw) >= 4:
            padded = ChatDrawingToleranceService.parse_mm(qty_raw)

            if padded is not None and padded >= min_length_mm:
                return "intermediate_length_as_quantity"

        if quantity >= min_length_mm and float(quantity).is_integer():
            segment = ChatDrawingPatternsService.intermediate_segment().search(description)

            if segment:
                return "intermediate_length_as_quantity"

        if quantity > 1 and ChatDrawingPatternsService.is_intermediate_family(code):
            return "intermediate_quantity_implausible"

        return None

    @classmethod
    def _quantity_matches_description(
        cls,
        row: dict[str, Any],
        quantity: float,
        *,
        code: str = "",
        pdf_extract: dict | None = None,
        root: dict | None = None,
    ) -> bool:
        description = cls._resolved_row_description(
            row,
            code=code,
            pdf_extract=pdf_extract or {},
            root=root or {},
        )

        if not description.strip():
            return False

        for token in cls._description_numeric_tokens(description):
            if abs(token - quantity) < 0.001:
                return True

        return False

    @classmethod
    def _resolved_row_description(
        cls,
        row: dict[str, Any],
        *,
        code: str,
        pdf_extract: dict,
        root: dict | None = None,
    ) -> str:
        parts = [str(row.get("description") or "")]
        normalized_code = ChatProductQueryIntentService.normalize_product_code(code)

        if normalized_code and isinstance(root, dict):
            structure = root.get("structure") if isinstance(root.get("structure"), dict) else {}

            for index_row in ChatDrawingStructureIndexService.flatten_items(structure):
                if index_row.code == normalized_code and index_row.description.strip():
                    parts.append(index_row.description)
                    break

        if not normalized_code:
            return " ".join(part for part in parts if part).strip()

        source_metadata = pdf_extract.get("sourceMetadata")

        if isinstance(source_metadata, dict):
            stamp_text = str(source_metadata.get("stampText") or "")

            for line in stamp_text.splitlines():
                compact = line.replace(" ", "")

                if normalized_code not in compact:
                    continue

                parts.append(line.strip())

        return " ".join(part for part in parts if part).strip()

    @classmethod
    def _description_numeric_tokens(cls, description: str) -> set[float]:
        tokens: set[float] = set()
        blob = str(description or "")

        for pattern in ChatDrawingPatternsService.bom_description_quantity_noise_patterns():
            for match in pattern.finditer(blob):
                for group_index in range(1, (match.lastindex or 0) + 1):
                    parsed = ChatDrawingToleranceService.parse_mm(match.group(group_index))

                    if parsed is not None:
                        tokens.add(parsed)

        return tokens
