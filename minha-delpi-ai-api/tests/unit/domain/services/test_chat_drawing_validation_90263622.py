from app.domain.services.chat_drawing_bom_comparison_service import BomComparisonResult
from app.domain.services.chat_drawing_multipage_coverage_service import (
    ChatDrawingMultipageCoverageService,
)
from app.domain.services.chat_drawing_structure_validation_service import (
    ChatDrawingStructureValidationService,
)
from app.domain.services.chat_drawing_validation_orchestration_service import (
    ChatDrawingValidationOrchestrationService,
)


def _comparison_90263622_scenario() -> BomComparisonResult:
    api_codes = tuple(f"5023{i:04d}" for i in range(60))
    pdf_codes = api_codes[:15]

    return BomComparisonResult(
        missing_in_pdf=tuple(api_codes[15:]),
        extra_in_pdf=(),
        pdf_bom_codes=pdf_codes,
        api_codes=api_codes,
    )


def test_multipage_partial_coverage_for_90263622_scenario():
    result = ChatDrawingMultipageCoverageService.evaluate(
        pdf_extract={"pageCount": 5, "legible": True},
        comparison=_comparison_90263622_scenario(),
    )

    assert result.applicable is True
    assert result.coverage_ratio == 0.25
    assert result.template_key == "multipage_bom_partial"
    assert result.status == "pending"


def test_multipage_low_coverage_between_thresholds():
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
    assert result.status == "error"


def test_multipage_not_applicable_for_single_page():
    result = ChatDrawingMultipageCoverageService.evaluate(
        pdf_extract={"pageCount": 1, "legible": True},
        comparison=_comparison_90263622_scenario(),
    )

    assert result.applicable is False
    assert result.template_key is None


def test_structure_validation_emits_multipage_item_for_partial_bom():
    api_codes = [f"5023{i:04d}" for i in range(60)]
    root = {
        "structure": {
            "items": [{"code": code, "components": []} for code in api_codes]
        }
    }
    pdf_extract = {
        "legible": True,
        "pageCount": 5,
        "componentCodes": list(api_codes[:15]),
        "validationScopes": {
            "bom": {"available": True, "sourceKey": "bom_region"}
        },
    }

    items = ChatDrawingStructureValidationService.build_check_items(
        root=root,
        pdf_extract=pdf_extract,
        product_code="90263622",
    )

    assert any(
        item.get("templateKey") == "multipage_bom_partial"
        for item in items
    )


def test_multipage_resolve_absence_check_status_demotes_critical():
    status = ChatDrawingMultipageCoverageService.resolve_absence_check_status(
        "critical_error",
        pdf_extract={"pageCount": 10, "legible": True},
        comparison=_comparison_90263622_scenario(),
    )

    assert status == "pending"


def test_structure_validation_demotes_intermediate_missing_on_multipage_partial():
    api_codes = [f"5023{i:04d}" for i in range(60)]
    root = {
        "structure": {
            "items": [
                {
                    "code": code,
                    "description": f"CT26VERM-00036/04/06-{code}",
                    "components": [],
                }
                for code in api_codes
            ]
        }
    }
    pdf_extract = {
        "legible": True,
        "pageCount": 10,
        "componentCodes": [],
        "intermediateCodes": [],
        "validationScopes": {
            "bom": {"available": False, "sourceKey": None, "charCount": 0}
        },
    }

    items = ChatDrawingStructureValidationService.build_check_items(
        root=root,
        pdf_extract=pdf_extract,
        product_code="90263622",
    )

    intermediate_items = [
        item for item in items if item.get("templateKey") == "intermediate_missing"
    ]

    assert intermediate_items
    assert intermediate_items[0]["status"] == "pending"
    assert any(item.get("templateKey") == "multipage_bom_partial" for item in items)


def test_orchestration_includes_multipage_metadata():
    api_codes = [f"5023{i:04d}" for i in range(60)]
    payload = {
        "product": {"code": "90263622", "description": "CHICOTE MULTIPAGINA", "type": "PA"},
        "structure": {
            "items": [{"code": code, "components": []} for code in api_codes]
        },
        "guide": {"items": [{"product_code": "90263622", "bom_level": 0}], "total": 1},
    }
    pdf_extract = {
        "legible": True,
        "pageCount": 5,
        "productCode": "90263622",
        "componentCodes": api_codes[:15],
        "validationScopes": {
            "bom": {"available": True, "sourceKey": "bom_region"}
        },
    }

    package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code="90263622",
        payload=payload,
        has_pdf_attachment=True,
        api_ok=True,
        pdf_extract=pdf_extract,
    )

    multipage = package["drawingAnalysis"].get("multipageCoverage")

    assert isinstance(multipage, dict)
    assert multipage.get("applicable") is True
    assert multipage.get("templateKey") == "multipage_bom_partial"
