"""Conteúdo JSON — validação de desenho (`drawing_validation.json`)."""

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_validation_content_service import (
    ChatDrawingValidationContentService,
)

configure_domain_infrastructure_ports()


def test_drawing_validation_structure_check_templates_exist():
    keys = [
        "bom_missing",
        "bom_extra",
        "bom_match_ok",
        "intermediate_missing",
        "intermediate_length",
        "decape_mismatch",
        "segment_length_pending",
        "total_length",
        "decapes_ed",
        "revision_cross_ok",
        "customer_reference_ok",
        "customer_reference_mismatch",
        "pdf_attached",
    ]

    for key in keys:
        item = ChatDrawingValidationContentService.item_from_template(
            key,
            status="ok",
            pdf_evidence="—",
            api_evidence="—",
        )
        assert item["section"]
        assert item["item"]
        assert item["rule"]
        assert item["recommendation"]


def test_drawing_validation_evidence_formats():
    assert "02" in ChatDrawingValidationContentService.evidence_format(
        "revisionInternalTable",
        revision="02",
    )
    assert ChatDrawingValidationContentService.decape_side("left") == "esquerdo"


def test_intermediate_length_item_uses_code_placeholder():
    item = ChatDrawingValidationContentService.item_from_template(
        "intermediate_length",
        status="critical_error",
        pdf_evidence="36 mm (descrição)",
        api_evidence="36 MT (SG1010)",
        item_values={"code": "50215425"},
    )

    assert "50215425" in item["item"]


def test_length_from_structure_evidence_includes_unit():
    text = ChatDrawingValidationContentService.evidence_format(
        "lengthFromStructure",
        length="240",
        unit="MT",
    )

    assert text == "240 MT (SG1010)"


def test_drawing_validation_rules_section_exists():
    from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService

    assert ChatDrawingPatternsService.length_tolerance_ratio() == 0.05
