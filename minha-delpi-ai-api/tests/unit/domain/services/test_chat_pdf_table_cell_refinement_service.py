from unittest.mock import patch

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_pdf_table_cell_refinement_service import (
    ChatPdfTableCellRefinementService,
)
from app.domain.services.chat_pdf_table_structure_service import (
    ChatPdfTableStructureService,
)

configure_domain_infrastructure_ports()


def _table_with_bbox() -> dict:
    table = ChatPdfTableStructureService.extract_from_region_text(
        "| POS | CÓDIGO | QTD |\n| 1 | 10090050 | 2 |\n",
        table_id="region_bom_p0",
        source_region="bom",
        source_bbox=[0.0, 0.0, 0.5, 0.4],
    )

    assert table is not None
    return table


def test_refine_cell_prefers_ocr_over_cached_text():
    ChatPdfTableCellRefinementService.clear_cache()
    table = _table_with_bbox()
    storage_path = "/tmp/test_cell_ocr.pdf"
    ChatPdfTableCellRefinementService.register_tables(storage_path, [table])
    cell_bbox = ChatPdfTableStructureService.cell_bbox(table, row_index=0, col_index=2)

    assert cell_bbox is not None

    with patch.object(
        ChatPdfTableCellRefinementService,
        "_ocr_cell_bbox",
        return_value={"text": "2", "engines": ["tesseract"], "engine": "tesseract"},
    ):
        result = ChatPdfTableCellRefinementService().refine_cell(
            storage_path=storage_path,
            table_id="region_bom_p0",
            row_index=0,
            col_index=2,
            fallback_text="6.35",
        )

    assert result["text"] == "2"
    assert result["engine"] == "tesseract"
    assert result.get("bbox") == cell_bbox


def test_refine_cell_falls_back_to_cached_table_text():
    ChatPdfTableCellRefinementService.clear_cache()
    table = _table_with_bbox()
    storage_path = "/tmp/test_cell_cache.pdf"
    ChatPdfTableCellRefinementService.register_tables(storage_path, [table])

    with patch.object(
        ChatPdfTableCellRefinementService,
        "_ocr_cell_bbox",
        return_value={"text": "", "engines": [], "engine": ""},
    ):
        result = ChatPdfTableCellRefinementService().refine_cell(
            storage_path=storage_path,
            table_id="region_bom_p0",
            row_index=0,
            col_index=2,
            fallback_text="6.35",
        )

    assert result["text"] == "2"
    assert result["engine"] == "structured_table"
