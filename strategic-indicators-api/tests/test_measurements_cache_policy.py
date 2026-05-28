from __future__ import annotations

from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicIndicatorMeasuredValue,
)
from si_app.application.services.strategic_indicators.measurements_cache_policy import (
    FULL_MEASUREMENT_DEPARTMENT_IDS,
    MISSING_DEPARTMENT_ERROR_CODE,
    enrich_measurement_errors,
    has_measurement_errors,
    should_cache_measurements,
    should_cache_rol_payload,
)


def _item(department_id: str) -> StrategicIndicatorMeasuredValue:
    return StrategicIndicatorMeasuredValue(
        department_id=department_id,
        indicator_id=f"{department_id}-x",
        value=1.0,
        source="test",
    )


def test_has_measurement_errors_is_true_for_any_error_entry() -> None:
    assert has_measurement_errors([]) is False
    assert has_measurement_errors(None) is False
    assert has_measurement_errors([{"message": "timeout"}]) is True
    assert has_measurement_errors([{}]) is True


def test_enrich_adds_missing_department_errors() -> None:
    items = [_item("hr")]
    errors = enrich_measurement_errors(
        items,
        [],
        department_id=None,
        competence="2026-05",
    )
    assert has_measurement_errors(errors)
    missing = [
        e for e in errors if e.get("code") == MISSING_DEPARTMENT_ERROR_CODE
    ]
    assert len(missing) == len(FULL_MEASUREMENT_DEPARTMENT_IDS) - 1
    assert any("Engenharia" in e["message"] for e in missing)


def test_enrich_preserves_fetch_errors_with_context() -> None:
    items = [_item(d) for d in FULL_MEASUREMENT_DEPARTMENT_IDS]
    errors = enrich_measurement_errors(
        items,
        [
            {
                "department_id": "commercial",
                "source": "commercial_snapshot",
                "message": "HTTP 504",
            }
        ],
        department_id=None,
        competence="2026-05",
        branch="01",
    )
    assert any("HTTP 504" in e["message"] for e in errors)
    assert any("competência 2026-05" in e["message"] for e in errors)


def test_should_not_cache_full_load_with_only_hr() -> None:
    items = [_item("hr")]
    errors = enrich_measurement_errors(items, [], department_id=None)
    assert should_cache_measurements(items, errors, department_id=None) is False


def test_should_cache_full_load_only_with_all_departments_and_zero_errors() -> None:
    items = [_item(d) for d in FULL_MEASUREMENT_DEPARTMENT_IDS]
    assert should_cache_measurements(items, [], department_id=None) is True


def test_should_not_cache_when_any_error_even_with_full_coverage() -> None:
    items = [_item(d) for d in FULL_MEASUREMENT_DEPARTMENT_IDS]
    errors = enrich_measurement_errors(
        items,
        [{"department_id": "commercial", "message": "504"}],
        department_id=None,
    )
    assert should_cache_measurements(items, errors, department_id=None) is False


def test_should_cache_department_scoped_load_without_errors() -> None:
    items = [_item("financial")]
    assert should_cache_measurements(items, [], department_id="financial") is True


def test_should_cache_rol_payload_with_rol_key() -> None:
    assert should_cache_rol_payload({"rol": 0}) is True
    assert should_cache_rol_payload({}) is False
