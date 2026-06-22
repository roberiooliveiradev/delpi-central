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


def test_all_catalog_rules_have_at_least_one_case_or_service_test():
    catalog = set(ChatDrawingValidationRuleRegistryService._rule_catalog())
    covered = rule_ids_with_cases()
    service_only = {
        "product_code_cross_check",
        "guide_structure",
        "multipage_coverage",
        "intermediate_presence",
        "intermediate_length",
        "total_length",
        "decapes_ed",
        "dimension_note",
    }
    missing = catalog - covered - service_only

    assert not missing, f"Regras sem caso de regressão: {sorted(missing)}"


def test_revision_internal_table_capture():
    stamp = (
        "ES EXECUTADO VERIFICADO | LIBERADO | DATA\n"
        "| 20/08/24 04 |\n"
        "90262008 REV.08\n"
    )

    assert ChatDrawingPdfExtractionService._extract_internal_revision(stamp) == "04"


def test_revision_cross_check_ok_when_internal_matches_api():
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
        if item.get("item") == "Revisão"
    ]

    assert revision_items
    assert revision_items[0]["status"] == "ok"


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
