from app.domain.services.chat_drawing_guide_structure_consistency_service import (
    ChatDrawingGuideStructureConsistencyService,
)
from app.domain.services.chat_drawing_validation_orchestration_service import (
    ChatDrawingValidationOrchestrationService,
)
from tests.unit.domain.services.test_chat_drawing_bom_comparison_service import (
    _payload_90264227,
)
from tests.unit.domain.services.test_external_action_result_presenter_analyser_humanized import (
    _analyser_payload_with_guide_and_inspection,
)


def test_guide_structure_ok_when_pa_and_intermediate_match():
    root = _analyser_payload_with_guide_and_inspection()

    items = ChatDrawingGuideStructureConsistencyService.build_check_items(
        root=root,
        product_code="90260140",
    )

    assert any(
        item.get("item") == "Roteiro × estrutura" and item.get("status") == "ok"
        for item in items
    )


def test_guide_structure_flags_extra_and_missing_for_90264227():
    root = _payload_90264227()

    items = ChatDrawingGuideStructureConsistencyService.build_check_items(
        root=root,
        product_code="90264227",
    )

    assert any(
        item.get("item") == "Produto no roteiro fora da estrutura"
        and "50225933" in str(item.get("apiEvidence"))
        for item in items
    )
    assert any(
        item.get("item") == "Produto da estrutura sem roteiro"
        and "50215425" in str(item.get("apiEvidence"))
        for item in items
    )


def test_guide_structure_level_mismatch_for_pa_at_wrong_level():
    root = _analyser_payload_with_guide_and_inspection()
    root["guide"]["items"][0]["bom_level"] = 1

    items = ChatDrawingGuideStructureConsistencyService.build_check_items(
        root=root,
        product_code="90260140",
    )

    assert any(
        item.get("item") == "Nível BOM do produto 90260140"
        and item.get("status") == "critical_error"
        for item in items
    )


def test_guide_structure_ignores_mp_and_consumable_in_sg2010():
    """Matéria-prima/consumível no roteiro não gera guide_structure_extra."""
    root = {
        "structure": {
            "items": [
                {
                    "code": "50215425",
                    "type": "PI",
                    "description": "CT26VERM-00036/04/06-0000-0000",
                    "components": [{"code": "10440133", "type": "MP"}],
                }
            ]
        },
        "guide": {
            "items": [
                {"product_code": "90264227", "bom_level": 0},
                {"product_code": "50215425", "bom_level": 1},
                {"product_code": "10080063", "bom_level": 2},
                {"product_code": "10130091", "bom_level": 2},
            ]
        },
    }

    comparison = ChatDrawingGuideStructureConsistencyService.compare(
        root=root,
        product_code="90264227",
    )

    assert "10080063" not in comparison.extra_in_guide
    assert "10130091" not in comparison.extra_in_guide
    assert "50215425" not in comparison.extra_in_guide
    assert "50215425" in comparison.expected_codes


def test_orchestration_includes_guide_structure_checks_without_pdf():
    package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code="90260140",
        payload=_analyser_payload_with_guide_and_inspection(),
        has_pdf_attachment=False,
        api_ok=True,
    )

    items = package["drawingAnalysis"]["items"]

    assert any(item.get("item") == "Roteiro × estrutura" for item in items)
