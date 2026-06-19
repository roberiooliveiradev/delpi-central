"""Apresentação do relatório de validação de desenho."""

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_validation_content_service import (
    ChatDrawingValidationContentService,
)
from app.domain.services.chat_drawing_validation_presentation_service import (
    ChatDrawingValidationPresentationService,
)

configure_domain_infrastructure_ports()


def test_status_display_from_json():
    assert "OK" in ChatDrawingValidationPresentationService.status_display("ok")
    assert ChatDrawingValidationPresentationService.status_label("error") == "Erro"


def test_consolidate_segment_length_items():
    items = [
        ChatDrawingValidationContentService.item_from_template(
            "segment_length_pending",
            status="pending",
            pdf_evidence="140 mm",
            api_evidence="36 mm",
        ),
        ChatDrawingValidationContentService.item_from_template(
            "segment_length_pending",
            status="pending",
            pdf_evidence="150 mm",
            api_evidence="36 mm",
        ),
    ]

    consolidated = ChatDrawingValidationPresentationService.consolidate_items(items)

    assert len(consolidated) == 1
    assert consolidated[0]["item"] == "Comprimentos de trecho (cotas)"
    assert "140 mm" in consolidated[0]["pdfEvidence"]
    assert "150 mm" in consolidated[0]["pdfEvidence"]


def test_expand_bom_extra_into_per_code_rows():
    items = [
        ChatDrawingValidationContentService.item_from_template(
            "bom_extra",
            status="critical_error",
            pdf_evidence="10140027, 10440133",
            api_evidence="—",
        ),
    ]

    expanded = ChatDrawingValidationPresentationService.expand_items(items)

    assert len(expanded) == 2
    assert expanded[0]["item"] == "Componente 10140027 extra no PDF"
    assert expanded[1]["item"] == "Componente 10440133 extra no PDF"


def test_format_code_wraps_product_codes():
    assert ChatDrawingValidationPresentationService.format_code("90264227") == "`90264227`"
    assert ChatDrawingValidationPresentationService.format_code_list("10140027, 10440133") == (
        "`10140027`, `10440133`"
    )


def test_resolve_pdf_product_code_falls_back_to_context():
    assert (
        ChatDrawingValidationPresentationService.resolve_pdf_product_code(
            pdf_product_code="",
            resolved_product_code="90264227",
        )
        == "90264227"
    )


def test_divergence_items_include_error_status():
    items = [
        ChatDrawingValidationContentService.item_from_template(
            "bom_missing_item",
            status="error",
            pdf_evidence="—",
            api_evidence="50215434",
            item_values={"code": "50215434"},
        ),
        ChatDrawingValidationContentService.item_from_template(
            "product_found",
            status="ok",
            pdf_evidence="—",
            api_evidence="90260140",
        ),
    ]

    divergences = ChatDrawingValidationPresentationService.divergence_items(items)

    assert len(divergences) == 1
    assert divergences[0]["status"] == "error"


def test_export_inspection_rows_measurable_textual_contract():
    root = {
        "inspection": {
            "items": [
                {
                    "product_code": "90261647",
                    "bom_level": 0,
                    "header": {"product_code": "90261647", "revision": "02"},
                    "measurable_tests": [{"test_code": "01"}] * 4,
                    "textual_tests": [{"test_code": "504"}] * 21,
                }
            ]
        }
    }

    rows = ChatDrawingValidationPresentationService._export_inspection_rows(root)

    assert len(rows) == 1
    assert rows[0]["product"] == "`90261647`"
    assert rows[0]["level"] == "0"
    assert rows[0]["qp6"] == "1"
    assert rows[0]["qp7"] == "4"
    assert rows[0]["qp8"] == "21"


def test_format_inspection_section_measurable_textual_contract():
    root = {
        "inspection": {
            "items": [
                {
                    "product_code": "90261647",
                    "bom_level": 0,
                    "header": {"product_code": "90261647", "revision": "02"},
                    "measurable_tests": [{"test_code": "01"}],
                    "textual_tests": [{"test_code": "504"}],
                }
            ]
        }
    }

    lines = ChatDrawingValidationPresentationService._format_inspection_section(root)

    assert any("Inspeções (QP6" in line for line in lines)
    assert any("90261647" in line and "| 1 |" in line for line in lines)
