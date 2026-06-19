"""Regressão — PAs 7026 (montagem) com chicotes 9026 na BOM."""

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_document_vision_bom_service import ChatDocumentVisionBomService
from app.domain.services.chat_drawing_bom_row_sanitization_service import (
    ChatDrawingBomRowSanitizationService,
)
from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_drawing_product_code_resolution_service import (
    ChatDrawingProductCodeResolutionService,
)

configure_domain_infrastructure_ports()


def test_filename_extracts_7026_pa_code():
    code = ChatDrawingProductCodeResolutionService.extract_product_code_from_filename(
        "70260048.pdf"
    )

    assert code == "70260048"


def test_is_finished_product_accepts_7026_and_9026():
    assert ChatDrawingPatternsService.is_finished_product("70260048") is True
    assert ChatDrawingPatternsService.is_finished_product("90263188") is True
    assert ChatDrawingPatternsService.is_assembly_pa("70260048") is True
    assert ChatDrawingPatternsService.is_assembly_pa("90263188") is False


def test_nested_chicote_9026_counts_in_7026_bom():
    rows = [
        {"code": "90263188", "quantity": "01", "description": "CHICOTE DE LIGACAO"},
        {"code": "10080591", "quantity": "02", "description": "TERM. PINO"},
    ]

    codes = ChatDocumentVisionBomService.meaningful_bom_component_codes(
        rows,
        exclude_product_code="70260048",
    )

    assert codes == ["90263188", "10080591"]


def test_nested_chicote_not_ghost_when_pa_is_7026():
    rows = [
        {"code": "90263188", "description": "CHICOTE DE LIGACAO"},
        {"code": "10080591", "description": "TERM. PINO"},
    ]

    sanitized = ChatDrawingBomRowSanitizationService.sanitize_rows(
        rows,
        product_code="70260048",
    )

    assert [row["code"] for row in sanitized] == ["90263188", "10080591"]


def test_resolve_with_pdf_attachment_prefers_7026_filename_over_9026_stamp():
    code, source = ChatDrawingProductCodeResolutionService._resolve_with_pdf_attachment(
        pdf_extract={
            "productCode": "90263188",
            "productCodeSource": "stamp_labeled",
        },
        attachment_filename="70260048.pdf",
    )

    assert code == "70260048"
    assert source == "filename"


def test_extract_bom_rows_keeps_9026_chicote_with_quantity_in_7026_pa():
    text = """
    QTD. | CÓDIGO | DESCRIÇÃO
    A | 01 | 90263188 | CHICOTE DE LIGACAO
    B | 02 | 10080591 | TERM. PINO
    """

    rows = ChatDocumentVisionBomService.extract_bom_rows(
        text,
        exclude_product_code="70260048",
        region_scoped=True,
    )

    assert [row["code"] for row in rows] == ["90263188", "10080591"]


def test_filename_extracts_8000_and_8001_pa_codes():
    assert (
        ChatDrawingProductCodeResolutionService.extract_product_code_from_filename(
            "80001234.pdf"
        )
        == "80001234"
    )
    assert (
        ChatDrawingProductCodeResolutionService.extract_product_code_from_filename(
            "80016332.pdf"
        )
        == "80016332"
    )


def test_sample_pa_is_chicote_like_not_assembly():
    assert ChatDrawingPatternsService.is_assembly_pa("80001234") is False
    assert ChatDrawingPatternsService.is_assembly_pa("80016332") is False
    assert ChatDrawingPatternsService.is_sample_pa("80001234") is True
    assert ChatDrawingPatternsService.is_sample_pa("80016332") is True
    assert ChatDrawingPatternsService.is_chicote_leaf_pa("80016332") is True
    assert ChatDrawingPatternsService.is_chicote_leaf_pa("90263188") is True
    assert ChatDrawingPatternsService.is_chicote_leaf_pa("70260048") is False
    assert ChatDrawingPatternsService.is_finished_product("80016332") is True
    assert ChatDrawingPatternsService.is_finished_product("10080001") is False


def test_sample_pa_bom_does_not_treat_9026_as_nested_chicote():
    rows = [
        {"code": "90264130", "quantity": "01", "description": "CHICOTE DE LIGACAO"},
        {"code": "10081073", "quantity": "02", "description": "TERM."},
    ]

    codes = ChatDocumentVisionBomService.meaningful_bom_component_codes(
        rows,
        exclude_product_code="80016332",
    )

    assert codes == ["10081073"]
    assert ChatDrawingPatternsService.is_nested_chicote_in_assembly_bom(
        "90264130",
        "80016332",
    ) is False


def test_resolve_prefers_8001_filename_over_9026_stamp():
    code, source = ChatDrawingProductCodeResolutionService._resolve_with_pdf_attachment(
        pdf_extract={
            "productCode": "90264130",
            "productCodeSource": "stamp_labeled",
        },
        attachment_filename="80016332.pdf",
    )

    assert code == "80016332"
    assert source == "filename"
