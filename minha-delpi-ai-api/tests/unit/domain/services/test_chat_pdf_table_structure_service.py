from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_bom_table_interpretation_service import (
    ChatDrawingBomTableInterpretationService,
)
from app.domain.services.chat_pdf_table_structure_service import (
    ChatPdfTableStructureService,
)

configure_domain_infrastructure_ports()

_BOM_90263149_SNIPPET = """
1
|| cóvico | vescrição — |iremjarD| CÓDIGO | DESCRIÇÃO
Ojujo o
D | o1 |1 0 0
ololololo|lo|lo/o|o/o|o
10080010 _|TERM. LINGUETA 6,30X0,80 0,30-0,80MM2 NU S/ISOLACAO FITADO CURTO UL ROHS
A |B | 2 | 10080044 |TERM. FASTON 2,80X0,50 0,50-1,65MM2 NU S/ISOLACAO FITADO ROHS UL
. 10090050 |ISOLADOR NYLON RETO 6,35 NU UL94V-2
D | 1 | 10140155 [CHAVE HH 10A 6 PINOS GRAVACAO 127/220 2 PINOS JAMPEADA
10500020 |TERMOENCOLHIVEL 3,20X0,40 1/8POL (1,6) PT 125°C POLIOLEFINA COMP 33MM UL-ROHS
"""


def test_extract_from_region_text_parses_pipe_delimited_table():
    text = (
        "| POS | CÓDIGO | QTD | DESCRIÇÃO |\n"
        "| 1 | 10080010 | 1 | TERM. LINGUETA |\n"
        "| 2 | 10080044 | 2 | TERM. FASTON |\n"
    )
    table = ChatPdfTableStructureService.extract_from_region_text(
        text,
        table_id="region_bom_p0",
        source_region="bom",
        source_bbox=[0.0, 0.0, 0.55, 0.35],
    )

    assert table is not None
    assert table["rowCount"] == 2
    assert ChatPdfTableStructureService.cell_text(table, row_index=0, col_index=2) == "1"
    assert ChatPdfTableStructureService.cell_text(table, row_index=1, col_index=1) == "10080044"
    bbox = ChatPdfTableStructureService.cell_bbox(table, row_index=0, col_index=2)

    assert isinstance(bbox, list)
    assert len(bbox) == 4


def test_extract_from_region_text_reanchors_after_ocr_noise():
    table = ChatPdfTableStructureService.extract_from_region_text(
        _BOM_90263149_SNIPPET,
        table_id="region_bom_p0",
        source_region="bom",
        source_bbox=[0.0, 0.0, 0.55, 0.35],
    )

    assert table is not None
    assert table["rowCount"] >= 4
    assert ChatPdfTableStructureService.cell_text(table, row_index=0, col_index=3) == "10080044"
    assert ChatPdfTableStructureService.cell_text(table, row_index=0, col_index=2) == "2"


def test_bom_interpretation_from_reanchored_90263149_snippet():
    table = ChatPdfTableStructureService.extract_from_region_text(
        _BOM_90263149_SNIPPET,
        table_id="region_bom_p0",
        source_region="bom",
    )

    assert table is not None

    rows = ChatDrawingBomTableInterpretationService.bom_rows_from_tables(
        [table],
        product_code="90263149",
    )
    by_code = {row["code"]: row for row in rows}

    assert by_code["10080044"]["quantity"] == "2"
    assert "10090050" in by_code
    assert by_code["10090050"]["quantityTrusted"] is False
    assert by_code["10140155"]["quantity"] == "1"


def test_extract_from_metadata_prefers_richer_cached_table():
    metadata = {
        "regionTexts": {
            "bom": "CÓDIGO | DESCRIÇÃO\nD | o1 | 1 0 0",
        },
        "structuredTables": [
            {
                "tableId": "region_bom_p0",
                "sourceRegion": "bom",
                "columns": [
                    {"index": 0, "headerText": "POS"},
                    {"index": 1, "headerText": "CÓDIGO"},
                    {"index": 2, "headerText": "QTD"},
                ],
                "rows": [
                    {
                        "index": 0,
                        "cells": [
                            {"col": 0, "text": "1"},
                            {"col": 1, "text": "10090050"},
                            {"col": 2, "text": "1"},
                        ],
                    }
                ],
                "rowCount": 1,
            }
        ],
    }
    tables = ChatPdfTableStructureService.extract_from_metadata(metadata)
    bom_table = next(table for table in tables if table.get("tableId") == "region_bom_p0")

    assert ChatPdfTableStructureService.cell_text(bom_table, row_index=0, col_index=1) == "10090050"


def test_extract_from_metadata_merges_structured_tables():
    metadata = {
        "structuredTables": [
            {
                "tableId": "cached_table",
                "columns": [{"index": 0, "headerText": "QTD"}],
                "rows": [],
            }
        ]
    }
    tables = ChatPdfTableStructureService.extract_from_metadata(metadata)

    assert any(table.get("tableId") == "cached_table" for table in tables)
