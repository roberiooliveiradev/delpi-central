from app.domain.services.chat_drawing_validation_orchestration_service import (
    ChatDrawingValidationOrchestrationService,
)
from tests.unit.domain.services.test_external_action_result_presenter_analyser_humanized import (
    _analyser_payload_with_guide_and_inspection,
)


def test_build_from_analyser_payload_ok_with_guide_and_inspection():
    package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code="90260140",
        payload=_analyser_payload_with_guide_and_inspection(),
        has_pdf_attachment=False,
        api_ok=True,
    )

    analysis = package["drawingAnalysis"]

    assert analysis["status"] in {"incomplete", "approved_with_notes", "approved"}
    assert analysis["criticalErrors"] == 0
    assert any(item["section"] == "Roteiro" for item in analysis["items"])
    assert any(item["section"] == "Inspeção" for item in analysis["items"])


def test_build_from_analyser_product_not_found_critical():
    package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code="99999999",
        payload=None,
        has_pdf_attachment=True,
        api_ok=False,
        api_status_code=404,
    )

    assert package["drawingAnalysis"]["status"] == "rejected"
    assert package["drawingAnalysis"]["criticalErrors"] >= 1


def test_pdf_code_divergence_critical():
    package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code="90260140",
        payload=_analyser_payload_with_guide_and_inspection(),
        has_pdf_attachment=True,
        api_ok=True,
        pdf_extract={
            "productCode": "90264130",
            "revision": "00",
            "legible": True,
        },
    )

    critical = [
        item
        for item in package["drawingAnalysis"]["items"]
        if item.get("status") == "critical_error"
    ]

    assert any(item.get("item") == "Código DELPI" for item in critical)


def test_format_report_uses_status_symbols():
    package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code="90260140",
        payload=_analyser_payload_with_guide_and_inspection(),
        has_pdf_attachment=True,
        api_ok=True,
        pdf_extract={
            "productCode": "90260140",
            "revision": "01",
            "legible": True,
            "componentCodes": ["50212194"],
            "intermediateCodes": ["50212194"],
            "dimensions": {"totalLengthMm": 2.0},
        },
    )

    report = ChatDrawingValidationOrchestrationService.format_report_markdown(package)

    assert "✅" in report or "⚠️" in report or "❌" in report


def test_format_report_contains_sections():
    package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code="90260140",
        payload=_analyser_payload_with_guide_and_inspection(),
        has_pdf_attachment=True,
        api_ok=True,
    )

    report = ChatDrawingValidationOrchestrationService.format_report_markdown(package)

    assert "Relatório de Análise de Desenho DELPI" in report
    assert "Checklist completo" in report
    assert "Status geral" in report


def test_format_report_lists_structure_guide_and_inspection():
    package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code="90260140",
        payload=_analyser_payload_with_guide_and_inspection(),
        has_pdf_attachment=True,
        api_ok=True,
        pdf_extract={
            "productCode": "90260140",
            "revision": "01",
            "legible": True,
        },
    )

    report = ChatDrawingValidationOrchestrationService.format_report_markdown(package)

    assert "Estrutura (SG1010)" in report
    assert "50212194" in report
    assert "Roteiro (SG2010)" in report
    assert "CORTAR TUBO MAIOR E MENOR" in report
    assert "Inspeções (QP6" in report


def test_format_report_pdf_section_uses_pdf_product_code():
    package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code="10070077",
        payload=_analyser_payload_with_guide_and_inspection(),
        has_pdf_attachment=True,
        api_ok=True,
        pdf_extract={
            "productCode": "90262511",
            "revision": "04",
            "legible": True,
        },
    )

    report = ChatDrawingValidationOrchestrationService.format_report_markdown(package)

    assert "## 2. Dados identificados no PDF" in report
    assert "| Código | 90262511 |" in report
    assert "| Código | 90260140 |" in report
