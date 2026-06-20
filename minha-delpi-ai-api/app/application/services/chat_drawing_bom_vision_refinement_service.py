"""Loop skill desenho → port genérico de visão para refinamento de QTD BOM."""

from __future__ import annotations

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

        if root and code:
            payload = cls._refine_untrusted_rows(
                payload,
                root=root,
                product_code=code,
                storage_path=storage_path,
                structured_tables=structured_tables,
            )

        if structured_tables:
            refinement_meta = payload.get("bomVisionRefinement")

            if not isinstance(refinement_meta, dict):
                refinement_meta = {}

            payload["bomVisionRefinement"] = {
                **refinement_meta,
                "triggered": True,
                "tableCount": len(structured_tables),
                "columnRowCount": len(column_rows),
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
    def _refine_untrusted_rows(
        cls,
        pdf_extract: dict[str, Any],
        *,
        root: dict,
        product_code: str,
        storage_path: str,
        structured_tables: list[dict[str, Any]],
    ) -> dict[str, Any]:
        payload = dict(pdf_extract)
        triggers = ChatDrawingPatternsService.bom_quantity_refinement_triggers()
        evidences = ChatDrawingBomQuantityAssertivenessService.collect_evidences(
            root=root,
            pdf_extract=payload,
            product_code=product_code,
        )
        port = ChatPdfTableCellRefinementService()
        rows = {
            str(row.get("code") or ""): dict(row)
            for row in (payload.get("bomRows") or [])
            if isinstance(row, dict) and str(row.get("code") or "").strip()
        }
        attempts: list[dict[str, Any]] = []
        refined_codes: list[str] = []

        for code, evidence in evidences.items():
            reason = str(evidence.reason or "")

            if evidence.trusted or reason not in triggers:
                continue

            target = cls._locate_table_row(
                structured_tables,
                code=code,
            )

            if target is None:
                continue

            table_id, row_index, qty_col = target
            result = port.refine_cell(
                storage_path=storage_path,
                table_id=table_id,
                row_index=row_index,
                col_index=qty_col,
                fallback_text=str(evidence.quantity),
            )
            text = str(result.get("text") or "").strip()

            if not text:
                continue

            current = rows.get(code, {"code": code})
            current["quantity"] = text
            current["quantitySource"] = "refined_column"
            current["quantityTrusted"] = True
            current["quantityRefinement"] = {
                "attempted": True,
                "reason": reason,
                "tableId": table_id,
                "rowIndex": row_index,
                "colIndex": qty_col,
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

        if attempts:
            payload["bomVisionRefinement"] = {
                "triggered": True,
                "codesRefined": refined_codes,
                "attempts": attempts,
            }

        return payload

    @classmethod
    def _locate_table_row(
        cls,
        tables: list[dict[str, Any]],
        *,
        code: str,
    ) -> tuple[str, int, int] | None:
        for table in tables:
            if not isinstance(table, dict):
                continue

            columns = ChatDrawingBomTableInterpretationService.resolve_column_indices(table)
            code_col = columns.get("code")
            qty_col = columns.get("quantity")

            if code_col is None or qty_col is None:
                continue

            table_id = str(table.get("tableId") or "")

            for row in table.get("rows") or []:
                if not isinstance(row, dict):
                    continue

                cells = {
                    int(cell.get("col")): str(cell.get("text") or "").strip()
                    for cell in (row.get("cells") or [])
                    if isinstance(cell, dict)
                }
                cell_code = cells.get(int(code_col), "")
                match = ChatDrawingPatternsService.component_code().search(cell_code)

                if not match:
                    continue

                normalized = str(match.group(1))

                if normalized != code:
                    continue

                return table_id, int(row.get("index") or 0), int(qty_col)

        return None
