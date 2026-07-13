"""Regressão por categoria de regra — Fase C desacoplamento skill de desenho."""

from __future__ import annotations

import pytest

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_balloon_validation_service import (
    ChatDrawingBalloonValidationService,
)
from app.domain.services.chat_drawing_bom_comparison_service import (
    ChatDrawingBomComparisonService,
)
from app.domain.services.chat_drawing_bom_quantity_assertiveness_service import (
    ChatDrawingBomQuantityAssertivenessService,
)
from app.domain.services.chat_drawing_bom_quantity_validation_service import (
    ChatDrawingBomQuantityValidationService,
)
from app.domain.services.chat_drawing_guide_component_consistency_service import (
    ChatDrawingGuideComponentConsistencyService,
)
from app.domain.services.chat_drawing_guide_structure_consistency_service import (
    ChatDrawingGuideStructureConsistencyService,
)
from app.domain.services.chat_drawing_pdf_extraction_service import (
    ChatDrawingPdfExtractionService,
)
from app.domain.services.chat_drawing_structure_validation_service import (
    ChatDrawingStructureValidationService,
)
from app.domain.services.chat_drawing_validation_orchestration_service import (
    ChatDrawingValidationOrchestrationService,
)
from app.domain.services.chat_drawing_validation_rule_registry_service import (
    ChatDrawingValidationRuleRegistryService,
)
from tests.fixtures.drawing_validation_rule_regression_cases import (
    DRAWING_VALIDATION_RULE_CASES,
    cases_for_rule,
    payload_stamp_bom_nested_mp,
    pdf_extract_stamp_bom_nested_mp,
    rule_ids_with_cases,
)

configure_domain_infrastructure_ports()

_PRODUCT_CODE = "90262008"


def _root() -> dict:
    return payload_stamp_bom_nested_mp()


def _pdf_extract(**overrides: object) -> dict:
    payload = pdf_extract_stamp_bom_nested_mp()
    payload.update(overrides)

    return payload


@pytest.mark.parametrize(
    "case",
    DRAWING_VALIDATION_RULE_CASES,
    ids=[case.id for case in DRAWING_VALIDATION_RULE_CASES],
)
def test_rule_case_is_registered_in_catalog(case):
    catalog = ChatDrawingValidationRuleRegistryService._rule_catalog()

    assert case.rule_id in catalog


def test_all_catalog_rules_have_at_least_one_case():
    catalog = set(ChatDrawingValidationRuleRegistryService._rule_catalog())
    covered = rule_ids_with_cases()
    missing = catalog - covered

    assert not missing, f"Regras sem caso de regressão: {sorted(missing)}"


def test_revision_internal_table_capture():
    stamp = (
        "ES EXECUTADO VERIFICADO | LIBERADO | DATA\n"
        "| 20/08/24 04 |\n"
        "90262008 REV.08\n"
    )

    assert ChatDrawingPdfExtractionService._extract_internal_revision(stamp) == "04"


def test_revision_cross_check_ok_when_client_differs_from_totvs():
    payload = {
        "product": {
            "code": _PRODUCT_CODE,
            "current_revision": "004",
            "last_revision_date": "20260619",
        },
        "structure": _root()["structure"],
        "guide": {"items": [], "total": 0},
        "inspection": {"items": []},
    }

    package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code=_PRODUCT_CODE,
        payload=payload,
        has_pdf_attachment=True,
        api_ok=True,
        pdf_extract=_pdf_extract(revision="08", internalRevision="04"),
    )

    revision_items = [
        item
        for item in package["drawingAnalysis"]["items"]
        if str(item.get("templateKey") or "").startswith("revision_")
        and item.get("templateKey") != "revision_api"
    ]

    assert revision_items
    assert revision_items[0]["status"] == "ok"
    assert revision_items[0]["templateKey"] == "revision_client_not_comparable"


def test_bom_stamp_nested_mp_not_extra():
    result = ChatDrawingBomComparisonService.compare(
        root=_root(),
        pdf_extract=_pdf_extract(),
        product_code=_PRODUCT_CODE,
    )

    assert not result.extra_in_pdf


def test_bom_root_mp_found_in_stamp_haystack():
    result = ChatDrawingBomComparisonService.compare(
        root=_root(),
        pdf_extract=_pdf_extract(),
        product_code=_PRODUCT_CODE,
    )

    assert "10090062" not in result.missing_in_pdf


def test_guide_legacy_pi_fingerprint_ok():
    mismatches = ChatDrawingGuideComponentConsistencyService.compare(
        root=_root(),
        product_code=_PRODUCT_CODE,
    )

    assert not mismatches


def test_decape_global_misassigned_no_false_error():
    items = ChatDrawingStructureValidationService.build_check_items(
        root=_root(),
        pdf_extract=_pdf_extract(),
        product_code=_PRODUCT_CODE,
    )

    decape_errors = [
        item
        for item in items
        if item.get("templateKey") == "decape_mismatch"
        and item.get("status") == "error"
    ]

    assert not decape_errors


def test_quantity_from_description_untrusted():
    evidence = ChatDrawingBomQuantityAssertivenessService.collect_evidences(
        root=_root(),
        pdf_extract=_pdf_extract(),
        product_code=_PRODUCT_CODE,
    ).get("10120073")

    assert evidence is not None
    assert evidence.trusted is False
    assert evidence.reason == "quantity_from_description"


def test_quantity_from_description_not_pending_critical():
    pending = ChatDrawingBomQuantityValidationService.collect_pending(
        root=_root(),
        pdf_extract=_pdf_extract(),
        product_code=_PRODUCT_CODE,
    )

    assert "10120073" not in {item.code for item in pending}


def test_segment_length_rejects_structure_piece_quantity_false_positive():
    items = ChatDrawingStructureValidationService.build_check_items(
        root=_root(),
        pdf_extract=_pdf_extract(),
        product_code=_PRODUCT_CODE,
    )

    segment_pending = [
        item
        for item in items
        if item.get("templateKey") == "segment_length_pending"
    ]

    assert not segment_pending


def test_bom_quantity_within_tolerance():
    root = {
        "product": {"code": "90260140", "unit": "PC"},
        "structure": {
            "items": [
                {"code": "10081867", "quantity": 100.0, "unit": "PC", "components": []},
            ]
        },
    }
    pdf_extract = {"bomRows": [{"code": "10081867", "quantity": "95"}]}

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


def test_balloon_ok_from_structured_bom_table():
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


def test_registry_7026_disables_balloon_template():
    items = [
        {"templateKey": "balloon_presence_ok", "status": "ok"},
    ]

    filtered = ChatDrawingValidationRuleRegistryService.filter_items(
        items,
        "70260048",
        group_code="7026",
    )

    assert not filtered


def test_rule_case_ids_unique_per_rule():
    for rule_id in rule_ids_with_cases():
        ids = [case.id for case in cases_for_rule(rule_id)]

        assert len(ids) == len(set(ids))


def test_product_code_cross_check_mismatch():
    from app.domain.services.chat_drawing_validation_orchestration_service import (
        ChatDrawingValidationOrchestrationService,
    )

    package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code="90260140",
        payload={
            "product": {"code": "90260140"},
            "structure": {"items": []},
            "guide": {"items": []},
            "inspection": {"items": []},
        },
        has_pdf_attachment=True,
        api_ok=True,
        pdf_extract={
            "legible": True,
            "productCode": "90260999",
            "componentCodes": [],
        },
    )

    mismatches = [
        item
        for item in package["drawingAnalysis"]["items"]
        if item.get("templateKey") == "product_code_mismatch"
    ]

    assert mismatches


def test_guide_structure_flags_extra_product():
    from tests.unit.domain.services.test_chat_drawing_bom_comparison_service import (
        _payload_90264227,
    )

    items = ChatDrawingGuideStructureConsistencyService.build_check_items(
        root=_payload_90264227(),
        product_code="90264227",
    )

    assert any(item.get("templateKey") == "guide_structure_extra" for item in items)


def test_multipage_coverage_low_signal():
    from app.domain.services.chat_drawing_bom_comparison_service import BomComparisonResult
    from app.domain.services.chat_drawing_multipage_coverage_service import (
        ChatDrawingMultipageCoverageService,
    )

    api_codes = tuple(f"5023{i:04d}" for i in range(10))
    pdf_codes = api_codes[:5]
    comparison = BomComparisonResult(
        missing_in_pdf=tuple(api_codes[5:]),
        extra_in_pdf=(),
        pdf_bom_codes=pdf_codes,
        api_codes=api_codes,
    )

    result = ChatDrawingMultipageCoverageService.evaluate(
        pdf_extract={"pageCount": 3, "legible": True},
        comparison=comparison,
    )

    assert result.template_key == "multipage_low_coverage"


def test_intermediate_presence_missing():
    root = {
        "structure": {
            "items": [
                {
                    "code": "50225425",
                    "description": "CA0,75BRAN-00792/04/14-3800-0000",
                    "components": [],
                }
            ]
        }
    }
    pdf_extract = {"legible": True, "intermediateCodes": [], "componentCodes": []}

    items = ChatDrawingStructureValidationService.build_check_items(
        root=root,
        pdf_extract=pdf_extract,
        product_code="90262008",
    )

    assert any(item.get("templateKey") == "intermediate_missing" for item in items)


def test_intermediate_length_mismatch():
    root = {
        "structure": {
            "items": [
                {
                    "code": "50225425",
                    "description": "CA0,75BRAN-00792/04/14-3800-0000",
                    "components": [{"code": "10020043", "quantity": 100.0, "unit": "MT"}],
                }
            ]
        }
    }
    pdf_extract = {
        "legible": True,
        "intermediateCodes": ["50225425"],
        "componentCodes": ["50225425"],
        "bomRows": [{"code": "50225425"}],
        "dimensions": {},
    }

    items = ChatDrawingStructureValidationService.build_check_items(
        root=root,
        pdf_extract=pdf_extract,
        product_code="90262008",
    )

    assert any(item.get("templateKey") == "intermediate_length" for item in items)


def test_total_length_within_tolerance_ok():
    root = {
        "structure": {
            "items": [
                {
                    "code": "50225425",
                    "description": "CA0,75BRAN-00792/04/14-3800-0000",
                    "components": [{"code": "10020043", "quantity": 1000.0, "unit": "MT"}],
                }
            ]
        }
    }
    pdf_extract = {
        "legible": True,
        "componentCodes": ["50225425"],
        "bomRows": [{"code": "50225425"}],
        "dimensions": {"totalLengthMm": 792.0},
    }

    items = ChatDrawingStructureValidationService.build_check_items(
        root=root,
        pdf_extract=pdf_extract,
        product_code="90262008",
    )

    assert any(
        item.get("templateKey") == "total_length" and item.get("status") == "ok"
        for item in items
    )


def test_decapes_ed_pending_when_side_missing():
    root = {"structure": {"items": []}}
    pdf_extract = {
        "legible": True,
        "componentCodes": [],
        "dimensions": {
            "leftDecapeMm": 14.0,
            "rightDecapeMm": None,
            "decapeIndication": {"left": True, "right": True},
        },
    }

    items = ChatDrawingStructureValidationService.build_check_items(
        root=root,
        pdf_extract=pdf_extract,
        product_code="90262008",
    )

    assert any(
        item.get("templateKey") == "decapes_ed" and item.get("status") == "pending"
        for item in items
    )


def test_dimension_note_ambiguous_detected():
    from app.domain.services.chat_drawing_dimensions_extraction_service import (
        ChatDrawingDimensionsExtractionService,
    )

    text = "TERMO ENCOLHÍVEL 25 MM DECAPE 14 MM"

    assert ChatDrawingDimensionsExtractionService.detect_ambiguous_dimension_notes(text)
