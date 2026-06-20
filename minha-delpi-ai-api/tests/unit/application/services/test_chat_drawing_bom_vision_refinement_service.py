from app.application.services.chat_drawing_bom_vision_refinement_service import (
    ChatDrawingBomVisionRefinementService,
)
from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_pdf_table_cell_refinement_service import (
    ChatPdfTableCellRefinementService,
)

configure_domain_infrastructure_ports()


def _sample_table() -> dict:
    return {
        "tableId": "region_bom_p0",
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
