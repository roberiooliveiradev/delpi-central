from unittest.mock import patch

from app.application.services.chat_drawing_bom_vision_refinement_service import (
    ChatDrawingBomVisionRefinementService,
)
from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_pdf_table_cell_refinement_service import (
    ChatPdfTableCellRefinementService,
)
from app.domain.services.chat_pdf_table_structure_service import (
    ChatPdfTableStructureService,
)

configure_domain_infrastructure_ports()


def _sample_table() -> dict:
    return {
        "tableId": "region_bom_p0",
        "sourceRegion": "bom",
        "columns": [
            {"index": 0, "headerText": "POS"},
            {"index": 1, "headerText": "CÓDIGO"},
            {"index": 2, "headerText": "QTD"},
            {"index": 3, "headerText": "DESCRIÇÃO"},
        ],
        "rows": [
            {
                "index": 0,
                "cells": [
                    {"col": 0, "text": "1"},
                    {"col": 1, "text": "10090050"},
                    {"col": 2, "text": "1"},
                    {"col": 3, "text": "ISOLADOR NYLON RETO 6,35 NU UL94V-2"},
                ],
            }
        ],
    }


def test_apply_prefers_column_rows_over_noisy_text_parse():
    ChatPdfTableCellRefinementService.clear_cache()
    storage_path = "/tmp/test_90263149.pdf"
    table = _sample_table()
    ChatPdfTableCellRefinementService.register_tables(storage_path, [table])

    pdf_extract = {
        "productCode": "90263149",
        "bomRows": [
            {
                "code": "10090050",
                "quantity": "6.35",
                "description": "ISOLADOR NYLON RETO 6,35 NU UL94V-2",
            }
        ],
        "sourceMetadata": {
            "structuredTables": [table],
            "storagePath": storage_path,
        },
    }

    refined = ChatDrawingBomVisionRefinementService.apply(
        pdf_extract,
        storage_path=storage_path,
        product_code="90263149",
    )
    by_code = {
        row["code"]: row for row in refined.get("bomRows") or [] if isinstance(row, dict)
    }

    assert by_code["10090050"]["quantity"] == "1"
    assert by_code["10090050"]["quantitySource"] == "column"
    assert refined.get("bomVisionRefinement", {}).get("triggered") is True


def test_apply_refines_missing_quantity_via_cell_ocr_on_partial_row():
    ChatPdfTableCellRefinementService.clear_cache()
    storage_path = "/tmp/test_90263149_partial.pdf"
    table = ChatPdfTableStructureService.extract_from_region_text(
        "|| cóvico | vescrição — |iremjarD| CÓDIGO | DESCRIÇÃO\n"
        ". 10090050 |ISOLADOR NYLON RETO 6,35 NU UL94V-2\n",
        table_id="region_bom_p0",
        source_region="bom",
        source_bbox=[0.0, 0.0, 0.55, 0.35],
    )

    assert table is not None
    ChatPdfTableCellRefinementService.register_tables(storage_path, [table])

    pdf_extract = {
        "productCode": "90263149",
        "bomRows": [
            {
                "code": "10090050",
                "quantity": None,
                "description": "ISOLADOR NYLON RETO 6,35 NU UL94V-2",
                "quantitySource": "column_inferred",
                "quantityTrusted": False,
            }
        ],
        "sourceMetadata": {
            "structuredTables": [table],
            "storagePath": storage_path,
        },
    }

    with patch.object(
        ChatPdfTableCellRefinementService,
        "_ocr_cell_bbox",
        return_value={"text": "1", "engines": ["tesseract"], "engine": "tesseract"},
    ):
        refined = ChatDrawingBomVisionRefinementService.apply(
            pdf_extract,
            storage_path=storage_path,
            product_code="90263149",
        )

    by_code = {
        row["code"]: row for row in refined.get("bomRows") or [] if isinstance(row, dict)
    }

    assert by_code["10090050"]["quantity"] == "1"
    assert by_code["10090050"]["quantitySource"] == "refined_column"
    assert by_code["10090050"]["quantityTrusted"] is True
    assert refined.get("bomVisionRefinement", {}).get("resolved") == 1


def test_apply_preserves_prior_codes_refined_when_second_pass_resolves_zero():
    ChatPdfTableCellRefinementService.clear_cache()
    storage_path = "/tmp/test_90263149_preserve.pdf"
    table = _sample_table()
    ChatPdfTableCellRefinementService.register_tables(storage_path, [table])

    pdf_extract = {
        "productCode": "90263149",
        "bomRows": [
            {
                "code": "10090050",
                "quantity": "1",
                "quantitySource": "refined_column",
                "quantityTrusted": True,
            }
        ],
        "bomVisionRefinement": {
            "triggered": True,
            "codesRefined": ["10090050", "10080010"],
            "resolved": 2,
            "attemptCount": 2,
        },
        "sourceMetadata": {
            "structuredTables": [table],
            "storagePath": storage_path,
        },
    }

    refined = ChatDrawingBomVisionRefinementService.apply(
        pdf_extract,
        storage_path=storage_path,
        product_code="90263149",
    )
    meta = refined.get("bomVisionRefinement") or {}

    assert meta.get("resolved") == 2
    assert meta.get("codesRefined") == ["10090050", "10080010"]


def test_refine_quantity_cell_retries_adjacent_column():
    ChatPdfTableCellRefinementService.clear_cache()
    port = ChatPdfTableCellRefinementService()

    with patch.object(
        port,
        "refine_cell",
        side_effect=[
            {"text": "", "engines": [], "engine": "", "bbox": None},
            {"text": "2", "engines": ["tesseract"], "engine": "tesseract", "bbox": [0, 0, 1, 1]},
        ],
    ) as refine_mock:
        result, col = ChatDrawingBomVisionRefinementService._refine_quantity_cell(
            port,
            storage_path="/tmp/x.pdf",
            table_id="t1",
            row_index=0,
            qty_col=2,
            fallback_text="",
        )

    assert result.get("text") == "2"
    assert col == 1
    assert refine_mock.call_count == 2


def test_accepts_quantity_text_rejects_implausible_digit_count():
    assert ChatDrawingBomVisionRefinementService._accepts_quantity_text("2") is True
    assert ChatDrawingBomVisionRefinementService._accepts_quantity_text("2810522") is False
