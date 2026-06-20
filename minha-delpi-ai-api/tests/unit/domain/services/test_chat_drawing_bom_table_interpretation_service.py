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


def _corrupted_header_bom_table() -> dict:
    return {
        "tableId": "region_bom_p0",
        "sourceRegion": "bom",
        "columns": [
            {"index": 0, "headerText": "cóvico"},
            {"index": 1, "headerText": "vescrição —"},
            {"index": 2, "headerText": "iremjarD"},
            {"index": 3, "headerText": "CÓDIGO"},
            {"index": 4, "headerText": "DESCRIÇÃO"},
        ],
        "rows": [
            {
                "index": 0,
                "cells": [
                    {"col": 0, "text": "1"},
                    {"col": 1, "text": "PC"},
                    {"col": 2, "text": "1"},
                    {"col": 3, "text": "10090050"},
                    {"col": 4, "text": "ISOLADOR NYLON RETO 6,35 NU UL94V-2"},
                ],
            },
            {
                "index": 1,
                "cells": [
                    {"col": 0, "text": "2"},
                    {"col": 1, "text": "PC"},
                    {"col": 2, "text": "2"},
                    {"col": 3, "text": "10080044"},
                    {"col": 4, "text": "TERM. FASTON 2,80X0,50"},
                ],
            },
            {
                "index": 2,
                "cells": [
                    {"col": 0, "text": "3"},
                    {"col": 1, "text": "PC"},
                    {"col": 2, "text": "1"},
                    {"col": 3, "text": "10140155"},
                    {"col": 4, "text": "CHAVE HH 10A 6 PINOS"},
                ],
            },
        ],
    }


def test_resolve_column_indices_infers_quantity_when_header_ocr_corrupted():
    table = _corrupted_header_bom_table()
    columns = ChatDrawingBomTableInterpretationService.resolve_column_indices(table)

    assert columns["code"] == 3
    assert columns["description"] == 4
    assert columns["quantity"] is not None


def test_bom_rows_from_corrupted_header_table_90263149_layout():
    rows = ChatDrawingBomTableInterpretationService.bom_rows_from_tables(
        [_corrupted_header_bom_table()],
        product_code="90263149",
    )
    by_code = {row["code"]: row for row in rows}

    assert by_code["10090050"]["quantity"] == "1"
    assert by_code["10090050"]["quantitySource"] in {"column", "column_inferred"}
    assert by_code["10090050"]["quantityTrusted"] is True
    assert by_code["10080044"]["quantity"] == "2"


def test_locate_quantity_cell_finds_misaligned_partial_row():
    table = {
        "tableId": "region_bom_p0",
        "sourceRegion": "bom",
        "columns": [
            {"index": 0, "headerText": "cóvico"},
            {"index": 1, "headerText": "vescrição —"},
            {"index": 2, "headerText": "iremjarD"},
            {"index": 3, "headerText": "CÓDIGO"},
            {"index": 4, "headerText": "DESCRIÇÃO"},
        ],
        "rows": [
            {
                "index": 1,
                "cells": [
                    {"col": 0, "text": "10090050"},
                    {"col": 1, "text": "ISOLADOR NYLON RETO 6,35 NU UL94V-2"},
                ],
            }
        ],
    }
    located = ChatDrawingBomTableInterpretationService.locate_quantity_cell(
        [table],
        code="10090050",
    )

    assert located == ("region_bom_p0", 1, 2)
