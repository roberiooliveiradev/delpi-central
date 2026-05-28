from __future__ import annotations

from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicIndicatorMeasuredValue,
)
from si_app.application.services.strategic_indicators.measurement_snapshot_versions import (
    MAX_MEASUREMENT_SNAPSHOT_VERSIONS,
    append_measurement_snapshot_version,
    resolve_measurement_snapshot_serve,
)
from si_app.application.services.strategic_indicators.versioned_measurements_cache import (
    get_versioned_measurements,
    record_versioned_measurements,
)
from si_app.application.services.strategic_indicators import snapshot_shared_cache


def _item(department_id: str, value: float = 1.0) -> StrategicIndicatorMeasuredValue:
    return StrategicIndicatorMeasuredValue(
        department_id=department_id,
        indicator_id=f"{department_id}-x",
        value=value,
        source="test",
    )


def _all_departments_items() -> list[StrategicIndicatorMeasuredValue]:
    departments = (
        "engineering",
        "production",
        "commercial",
        "quality",
        "hr",
        "financial",
        "supplies",
    )
    return [_item(department_id) for department_id in departments]


def test_append_keeps_at_most_three_versions() -> None:
    versions = []
    for index in range(5):
        versions = append_measurement_snapshot_version(
            versions,
            items=[_item("hr", float(index))],
            errors=[],
            department_id="hr",
        )

    assert len(versions) == MAX_MEASUREMENT_SNAPSHOT_VERSIONS
    assert versions[0].version_number == 3
    assert versions[-1].version_number == 5


def test_serves_latest_clean_version_when_latest_has_errors() -> None:
    clean_items = _all_departments_items()
    versions = append_measurement_snapshot_version(
        [],
        items=clean_items,
        errors=[],
        department_id=None,
    )
    versions = append_measurement_snapshot_version(
        versions,
        items=[_item("hr")],
        errors=[
            {
                "department_id": "commercial",
                "source": "commercial_snapshot",
                "message": "Connection refused",
            }
        ],
        department_id=None,
    )

    served = resolve_measurement_snapshot_serve(versions, department_id=None)
    assert served is not None
    assert served.serving_fallback_from_previous_clean is True
    assert len(served.items) == len(clean_items)
    assert any("Connection refused" in e["message"] for e in served.errors)


def test_versioned_cache_records_and_resolves() -> None:
    snapshot_shared_cache._measurements_cache.invalidate_all()
    cache_key = "m|01-05-2026|31-05-2026|2026-05|||"

    record_versioned_measurements(
        cache_key,
        items=_all_departments_items(),
        errors=[],
        department_id=None,
    )
    record_versioned_measurements(
        cache_key,
        items=[_item("hr")],
        errors=[{"department_id": "production", "message": "timeout", "source": "x"}],
        department_id=None,
    )

    resolved = get_versioned_measurements(cache_key, department_id=None)
    assert resolved is not None
    assert resolved.serving_fallback_from_previous_clean is True
    assert len(resolved.items) == 7
