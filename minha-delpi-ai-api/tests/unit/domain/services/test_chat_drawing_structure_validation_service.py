from app.domain.services.chat_drawing_structure_validation_service import (
    ChatDrawingStructureValidationService,
)
from tests.unit.domain.services.test_external_action_result_presenter_analyser_humanized import (
    _analyser_payload_with_guide_and_inspection,
)


def test_bom_match_ok():
    root = _analyser_payload_with_guide_and_inspection()
    pdf_extract = {
        "legible": True,
        "componentCodes": ["50212194"],
        "intermediateCodes": ["50212194"],
        "dimensions": {"totalLengthMm": 2.0, "leftDecapeMm": 10, "rightDecapeMm": 12},
    }

    items = ChatDrawingStructureValidationService.build_check_items(
        root=root,
        pdf_extract=pdf_extract,
        product_code="90260140",
    )

    assert any(
        item.get("item") == "Conjunto de componentes" and item.get("status") == "ok"
        for item in items
    )


def test_bom_missing_component_critical():
    root = _analyser_payload_with_guide_and_inspection()
    pdf_extract = {
        "legible": True,
        "componentCodes": [],
        "intermediateCodes": [],
        "dimensions": {},
    }

    items = ChatDrawingStructureValidationService.build_check_items(
        root=root,
        pdf_extract=pdf_extract,
        product_code="90260140",
    )

    assert any(
        item.get("status") == "critical_error" and "ausente" in item.get("item", "").lower()
        for item in items
    )
