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


def test_rule_registry_star_enables_bom_comparison():
    enabled = ChatDrawingValidationRuleRegistryService.list_enabled_rules(
        "90262008",
        group_code="9026",
    )

    assert "bom_comparison" in enabled
    assert "revision_cross_check" in enabled


def test_rule_for_template_maps_bom_missing():
    assert (
        ChatDrawingValidationRuleRegistryService.rule_for_template("bom_missing")
        == "bom_comparison"
    )


def test_core_template_always_enabled():
    assert ChatDrawingValidationRuleRegistryService.is_template_enabled(
        "product_found",
        "70260048",
        group_code="7026",
    )


def test_filter_items_removes_balloon_for_7026():
    items = [
        {"templateKey": "product_found", "status": "ok"},
        {"templateKey": "balloon_presence_ok", "status": "ok"},
    ]

    filtered = ChatDrawingValidationRuleRegistryService.filter_items(
        items,
        "70260048",
        group_code="7026",
    )

    keys = {item.get("templateKey") for item in filtered}

    assert "product_found" in keys
    assert "balloon_presence_ok" not in keys


def test_template_keys_for_rule_bom_quantity():
    keys = ChatDrawingValidationRuleRegistryService.template_keys_for_rule("bom_quantity")

    assert "bom_quantity_mismatch" in keys
    assert "bom_quantity_ok" in keys


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
        "product": {"code": "90260140", "unit": "PC"},
        "structure": {
            "items": [
                {"code": "10081867", "quantity": 100.0, "unit": "PC", "components": []},
            ]
        },
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
        "product": {"code": "90260140", "unit": "PC"},
        "structure": {
            "items": [
                {"code": "10081867", "quantity": 100.0, "unit": "PC", "components": []},
            ]
        },
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


def test_guide_component_ok_when_legacy_pi_code_matches_structure_fingerprint():
    root = {
        "structure": {
            "items": [
                {
                    "code": "50225425",
                    "description": "CA0,75BRAN-00792/04/14-3800-0000",
                    "components": [],
                }
            ]
        },
        "guide": {
            "items": [
                {
                    "product_code": "90262008",
                    "component_code": "50221606",
                    "component_description": "CA18BRAN-00792/04/14-3800-0000",
                    "bom_level": 0,
                }
            ]
        },
    }

    mismatches = ChatDrawingGuideComponentConsistencyService.compare(
        root=root,
        product_code="90262008",
    )

    assert not mismatches


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


def test_balloon_ok_when_codes_only_in_structured_bom_table():
    pdf_extract = {
        "componentCodes": ["10080308", "10080843"],
        "bomRows": [
            {"code": "10080308", "quantity": "1", "quantitySource": "column"},
            {"code": "10080843", "quantity": "1", "quantitySource": "column"},
        ],
        "bomVisionRefinement": {"columnRowCount": 2},
        "sourceMetadata": {},
    }

    items = ChatDrawingBalloonValidationService.build_check_items(pdf_extract=pdf_extract)

    assert any(item.get("templateKey") == "balloon_presence_ok" for item in items)


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
