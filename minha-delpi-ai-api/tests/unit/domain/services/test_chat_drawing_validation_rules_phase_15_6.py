from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_balloon_validation_service import (
    ChatDrawingBalloonValidationService,
)
from app.domain.services.chat_drawing_bom_quantity_validation_service import (
    ChatDrawingBomQuantityValidationService,
)
from app.domain.services.chat_drawing_guide_component_consistency_service import (
    ChatDrawingGuideComponentConsistencyService,
)
from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_drawing_validation_rule_registry_service import (
    ChatDrawingValidationRuleRegistryService,
)

configure_domain_infrastructure_ports()


def test_rule_registry_default_family_enables_bom_quantity():
    assert ChatDrawingValidationRuleRegistryService.is_enabled(
        "bom_quantity",
        "90260140",
        group_code="9026",
    )


def test_rule_registry_7026_disables_balloon_presence():
    assert not ChatDrawingValidationRuleRegistryService.is_enabled(
        "balloon_presence",
        "70260048",
        group_code="7026",
    )
    assert ChatDrawingValidationRuleRegistryService.is_enabled(
        "bom_quantity",
        "70260048",
        group_code="7026",
    )


def test_bom_quantity_flags_mismatch_outside_tolerance():
    root = {
        "structure": {
            "items": [
                {"code": "10081867", "quantity": 100.0, "components": []},
            ]
        }
    }
    pdf_extract = {
        "bomRows": [{"code": "10081867", "quantity": "50"}],
    }

    mismatches = ChatDrawingBomQuantityValidationService.compare(
        root=root,
        pdf_extract=pdf_extract,
        product_code="90260140",
    )

    assert mismatches
    assert mismatches[0].code == "10081867"


def test_bom_quantity_ok_within_tolerance():
    root = {
        "structure": {
            "items": [
                {"code": "10081867", "quantity": 100.0, "components": []},
            ]
        }
    }
    pdf_extract = {
        "bomRows": [{"code": "10081867", "quantity": "95"}],
    }

    mismatches = ChatDrawingBomQuantityValidationService.compare(
        root=root,
        pdf_extract=pdf_extract,
        product_code="90260140",
    )

    assert not mismatches


def test_guide_component_mismatch_when_mp_not_under_pi():
    root = {
        "structure": {
            "items": [
                {
                    "code": "50230969",
                    "type": "PI",
                    "components": [{"code": "10081867", "quantity": 1.0}],
                }
            ]
        },
        "guide": {
            "items": [
                {
                    "product_code": "50230969",
                    "component_code": "10091640",
                    "bom_level": 1,
                }
            ]
        },
    }

    mismatches = ChatDrawingGuideComponentConsistencyService.compare(
        root=root,
        product_code="90262834",
    )

    assert mismatches
    assert mismatches[0].component_code == "10091640"


def test_guide_component_ok_for_pa_root_when_mp_in_structure():
    root = {
        "structure": {
            "items": [
                {"code": "10080044", "quantity": 1.0, "components": []},
            ]
        },
        "guide": {
            "items": [
                {
                    "product_code": "90262834",
                    "component_code": "10080044",
                    "bom_level": 0,
                }
            ]
        },
    }

    mismatches = ChatDrawingGuideComponentConsistencyService.compare(
        root=root,
        product_code="90262834",
    )

    assert not mismatches


def test_balloon_missing_codes_when_annotations_partial():
    pdf_extract = {
        "componentCodes": ["10081867", "10091640"],
        "sourceMetadata": {
            "annotationText": "BALÃO 10081867",
        },
    }

    result = ChatDrawingBalloonValidationService.evaluate(pdf_extract=pdf_extract)

    assert "10091640" in result.missing_in_annotations


def test_quantity_tolerance_ratio_from_json():
    assert ChatDrawingPatternsService.quantity_tolerance_ratio() == 0.1
