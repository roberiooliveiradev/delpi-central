from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_bom_table_interpretation_service import (
    ChatDrawingBomTableInterpretationService,
)

configure_domain_infrastructure_ports()


def _sample_bom_table() -> dict:
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
            },
            {
                "index": 1,
                "cells": [
                    {"col": 0, "text": "2"},
                    {"col": 1, "text": "10080044"},
                    {"col": 2, "text": "2"},
                    {"col": 3, "text": "TERM. FASTON 2,80X0,50"},
                ],
            },
        ],
    }


def test_bom_rows_from_tables_maps_quantity_column():
    rows = ChatDrawingBomTableInterpretationService.bom_rows_from_tables(
        [_sample_bom_table()],
        product_code="90263149",
    )
    by_code = {row["code"]: row for row in rows}

    assert by_code["10090050"]["quantity"] == "1"
    assert by_code["10090050"]["quantitySource"] == "column"
    assert by_code["10090050"]["quantityTrusted"] is True


def test_resolve_column_indices_matches_bom_headers():
    columns = ChatDrawingBomTableInterpretationService.resolve_column_indices(
        _sample_bom_table()
    )

    assert columns["code"] == 1
    assert columns["quantity"] == 2
    assert columns["description"] == 3
