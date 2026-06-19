from app.domain.services.chat_drawing_guide_structure_consistency_service import (
    ChatDrawingGuideStructureConsistencyService,
)
from app.domain.services.chat_drawing_inspection_validation_service import (
    ChatDrawingInspectionValidationService,
)
from app.domain.services.chat_drawing_validation_orchestration_service import (
    ChatDrawingValidationOrchestrationService,
)


def _payload_90262834_nested_pi() -> dict:
    return {
        "product": {
            "code": "90262834",
            "description": "MONTAGEM TESTE",
            "type": "PA",
        },
        "structure": {
            "items": [
                {
                    "code": "50230969",
                    "description": "PI PAI",
                    "type": "PI",
                    "components": [
                        {
                            "code": "50212870",
                            "description": "PI FILHO 70",
                            "type": "PI",
                            "components": [],
                        },
                        {
                            "code": "50212871",
                            "description": "PI FILHO 71",
                            "type": "PI",
                            "components": [],
                        },
                    ],
                },
            ]
        },
        "guide": {
            "items": [
                {"product_code": "90262834", "bom_level": 0},
                {"product_code": "50230969", "bom_level": 1},
                {"product_code": "50212870", "bom_level": 2},
                {"product_code": "50212871", "bom_level": 2},
            ]
        },
        "inspection": {
            "items": [
                {
                    "product": "90262834",
                    "measurable_tests": [{"test_code": "506", "nominal": "500"}],
                    "textual_tests": [],
                }
            ]
        },
    }


def test_nested_pi_in_guide_not_flagged_as_extra():
    root = _payload_90262834_nested_pi()

    comparison = ChatDrawingGuideStructureConsistencyService.compare(
        root=root,
        product_code="90262834",
    )

    assert "50212870" not in comparison.extra_in_guide
    assert "50212871" not in comparison.extra_in_guide
    assert not comparison.level_mismatches


def test_orchestration_inspection_ok_with_measurable_tests_contract():
    package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code="90262834",
        payload=_payload_90262834_nested_pi(),
        has_pdf_attachment=False,
        api_ok=True,
    )

    inspection_items = [
        item
        for item in package["drawingAnalysis"]["items"]
        if item.get("section") == "Inspeção"
    ]

    assert any(
        item.get("item") == "QP6 / QP7 / QP8"
        and item.get("status") == "ok"
        for item in inspection_items
    )


def test_inspection_validation_accepts_measurable_tests_without_legacy_qp_keys():
    inspection = {
        "items": [
            {
                "product": "90262834",
                "measurable_tests": [{"test_code": "506"}],
            }
        ]
    }

    assert ChatDrawingInspectionValidationService.has_inspection_plan(inspection)
