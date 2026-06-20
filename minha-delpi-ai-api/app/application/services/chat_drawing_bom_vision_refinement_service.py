"""Loop skill desenho → port genérico de visão para refinamento de QTD BOM."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_drawing_bom_quantity_assertiveness_service import (
    ChatDrawingBomQuantityAssertivenessService,
)
from app.domain.services.chat_drawing_bom_table_interpretation_service import (
    ChatDrawingBomTableInterpretationService,
)
from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_pdf_table_cell_refinement_service import (
    ChatPdfTableCellRefinementService,
)
from app.domain.services.chat_pdf_table_structure_service import (
    ChatPdfTableStructureService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


class ChatDrawingBomVisionRefinementService:
    @classmethod
    def refine_if_needed(
        cls,
        pdf_extract: dict[str, Any],
        *,
        storage_path: str = "",
        analyser_root: dict | None = None,
        product_code: str | None = None,
    ) -> dict[str, Any]:
        return cls.apply(
            pdf_extract,
            storage_path=storage_path,
            analyser_root=analyser_root,
            product_code=product_code,
        )

    @classmethod
    def apply(
        cls,
        pdf_extract: dict[str, Any],
        *,
        storage_path: str = "",
        analyser_root: dict | None = None,
        product_code: str | None = None,
    ) -> dict[str, Any]:
        if not cls.enabled():
            return pdf_extract

        payload = dict(pdf_extract)
        code = str(product_code or payload.get("productCode") or "").strip()
        metadata = payload.get("sourceMetadata")

        if not isinstance(metadata, dict):
            metadata = {}

        if not storage_path:
            storage_path = str(metadata.get("storagePath") or "").strip()

        structured_tables = cls._structured_tables(payload, metadata)

        if storage_path and structured_tables:
            ChatPdfTableCellRefinementService.register_tables(
                storage_path,
                structured_tables,
            )

        column_rows = ChatDrawingBomTableInterpretationService.bom_rows_from_tables(
            structured_tables,
            product_code=code,
        )

        if column_rows:
            payload["bomRows"] = cls._merge_bom_rows(
                payload.get("bomRows") if isinstance(payload.get("bomRows"), list) else [],
                column_rows,
            )

        root = analyser_root if isinstance(analyser_root, dict) else {}

        if storage_path and structured_tables:
            payload = cls._refine_quantities(
                payload,
                storage_path=storage_path,
                structured_tables=structured_tables,
                product_code=code,
                analyser_root=root,
            )

        if structured_tables:
            refinement_meta = payload.get("bomVisionRefinement")

            if not isinstance(refinement_meta, dict):
                refinement_meta = {}

            prior_codes = [
                str(code).strip()
                for code in (refinement_meta.get("codesRefined") or [])
                if str(code).strip()
            ]

            payload["bomVisionRefinement"] = {
                **refinement_meta,
                "triggered": True,
                "tableCount": len(structured_tables),
                "columnRowCount": len(column_rows),
                "resolved": len(prior_codes),
                "codesRefined": prior_codes,
            }

        return payload

    @classmethod
    def enabled(cls) -> bool:
        return bool(
            ChatDrawingPatternsService.bom_row_refinement_rule("enabled", True)
        )

    @classmethod
    def _structured_tables(
        cls,
        pdf_extract: dict[str, Any],
        metadata: dict[str, Any],
    ) -> list[dict[str, Any]]:
        combined = {**metadata}

        if isinstance(pdf_extract.get("structuredTables"), list):
            combined["structuredTables"] = pdf_extract["structuredTables"]

        return ChatPdfTableStructureService.extract_from_metadata(combined)

    @classmethod
    def _merge_bom_rows(
        cls,
        existing: list[dict[str, Any]],
        preferred: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        by_code = {
            str(row.get("code") or ""): dict(row)
            for row in existing
            if isinstance(row, dict) and str(row.get("code") or "").strip()
        }

        for row in preferred:
            if not isinstance(row, dict):
                continue

            code = str(row.get("code") or "").strip()

            if not code:
                continue

            prior = by_code.get(code)

            if prior is None:
                by_code[code] = row
                continue

            by_code[code] = ChatDrawingBomTableInterpretationService.prefer_row(prior, row)

        return list(by_code.values())

    @classmethod
    def _refine_quantities(
        cls,
        pdf_extract: dict[str, Any],
        *,
        storage_path: str,
        structured_tables: list[dict[str, Any]],
        product_code: str,
        analyser_root: dict[str, Any],
    ) -> dict[str, Any]:
        payload = dict(pdf_extract)
        triggers = ChatDrawingPatternsService.bom_quantity_refinement_triggers()
        targets = cls._collect_refinement_targets(
            payload,
            analyser_root=analyser_root,
            product_code=product_code,
            triggers=triggers,
        )

        if not targets:
            return payload

        port = ChatPdfTableCellRefinementService()
        rows = {
            str(row.get("code") or ""): dict(row)
            for row in (payload.get("bomRows") or [])
            if isinstance(row, dict) and str(row.get("code") or "").strip()
        }
        attempts: list[dict[str, Any]] = []
        refined_codes: list[str] = []
        attempt_count = 0

        for code, reason in targets.items():
            if reason not in triggers:
                continue

            target = ChatDrawingBomTableInterpretationService.locate_quantity_cell(
                structured_tables,
                code=code,
            )

            if target is None:
                continue

            table_id, row_index, qty_col = target
            current = rows.get(code, {"code": code})
            attempt_count += 1
            result, used_col = cls._refine_quantity_cell(
                port,
                storage_path=storage_path,
                table_id=table_id,
                row_index=row_index,
                qty_col=qty_col,
                fallback_text=str(current.get("quantity") or ""),
            )
            text = str(result.get("text") or "").strip()

            if not text:
                attempts.append(
                    {
                        "code": code,
                        "reason": reason,
                        "tableId": table_id,
                        "success": False,
                    }
                )
                continue

            current["quantity"] = text
            current["quantitySource"] = "refined_column"
            current["quantityTrusted"] = True
            current["quantityRefinement"] = {
                "attempted": True,
                "reason": reason,
                "tableId": table_id,
                "rowIndex": row_index,
                "colIndex": used_col,
                "engine": result.get("engine"),
                "engines": list(result.get("engines") or []),
                "cellBbox": result.get("bbox"),
            }
            rows[code] = current
            refined_codes.append(code)
            attempts.append(
                {
                    "code": code,
                    "reason": reason,
                    "tableId": table_id,
                    "success": True,
                }
            )

        if rows:
            payload["bomRows"] = list(rows.values())

        if attempts or refined_codes:
            prior_meta = payload.get("bomVisionRefinement")

            if not isinstance(prior_meta, dict):
                prior_meta = {}

            prior_codes = [
                str(item).strip()
                for item in (prior_meta.get("codesRefined") or [])
                if str(item).strip()
            ]
            merged_codes = list(dict.fromkeys(prior_codes + refined_codes))
            prior_attempts = [
                item
                for item in (prior_meta.get("attempts") or [])
                if isinstance(item, dict)
            ]
            prior_attempt_count = int(prior_meta.get("attemptCount") or len(prior_attempts))

            payload["bomVisionRefinement"] = {
                **prior_meta,
                "triggered": True,
                "attempted": True,
                "attemptCount": prior_attempt_count + attempt_count,
                "resolved": len(merged_codes),
                "codesRefined": merged_codes,
                "attempts": prior_attempts + attempts,
            }

        return payload

    @classmethod
    def _refine_quantity_cell(
        cls,
        port: ChatPdfTableCellRefinementService,
        *,
        storage_path: str,
        table_id: str,
        row_index: int,
        qty_col: int,
        fallback_text: str,
    ) -> tuple[dict[str, Any], int]:
        empty: dict[str, Any] = {"text": "", "engines": [], "engine": "", "bbox": None}

        for offset in ChatDrawingPatternsService.bom_quantity_column_retry_offsets():
            col_index = qty_col if offset == 0 else qty_col + offset

            if col_index < 0:
                continue

            result = port.refine_cell(
                storage_path=storage_path,
                table_id=table_id,
                row_index=row_index,
                col_index=col_index,
                fallback_text=fallback_text if offset == 0 else "",
            )
            text = str(result.get("text") or "").strip()

            if text and cls._accepts_quantity_text(text):
                return dict(result), col_index

        return empty, qty_col

    @classmethod
    def _accepts_quantity_text(cls, text: str) -> bool:
        cleaned = str(text or "").strip()

        if not cleaned or not ChatDrawingPatternsService.bom_quantity().match(cleaned):
            return False

        max_digits = int(
            ChatDrawingPatternsService.bom_column_inference_rule("quantityMaxDigits", 4) or 4
        )
        digits = re.sub(r"\D", "", cleaned.split(",")[0].split(".")[0])

        return 0 < len(digits) <= max_digits

    @classmethod
    def _collect_refinement_targets(
        cls,
        pdf_extract: dict[str, Any],
        *,
        analyser_root: dict[str, Any],
        product_code: str,
        triggers: frozenset[str],
    ) -> dict[str, str]:
        targets: dict[str, str] = {}

        for row in pdf_extract.get("bomRows") or []:
            if not isinstance(row, dict):
                continue

            code = ChatProductQueryIntentService.normalize_product_code(
                str(row.get("code") or "")
            )

            if not code:
                continue

            if str(row.get("quantitySource") or "") == "refined_column" and row.get(
                "quantityTrusted"
            ):
                continue

            quantity = str(row.get("quantity") or "").strip()

            if not quantity or not row.get("quantityTrusted"):
                targets[code] = "missing_quantity"
                continue

            source = str(row.get("quantitySource") or "").strip().lower()

            if source == "column_inferred" and not row.get("quantityTrusted"):
                targets[code] = "untrusted_column_quantity"

        if analyser_root and product_code:
            evidences = ChatDrawingBomQuantityAssertivenessService.collect_evidences(
                root=analyser_root,
                pdf_extract=pdf_extract,
                product_code=product_code,
            )

            for code, evidence in evidences.items():
                reason = str(evidence.reason or "")

                if evidence.trusted or reason not in triggers:
                    continue

                targets[code] = reason

        return targets
