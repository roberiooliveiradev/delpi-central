from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_pdf_table_structure_service import (
    ChatPdfTableStructureService,
)

configure_domain_infrastructure_ports()


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
