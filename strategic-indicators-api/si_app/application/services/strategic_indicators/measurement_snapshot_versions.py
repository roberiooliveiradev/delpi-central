from __future__ import annotations

import time
from dataclasses import dataclass

from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicIndicatorMeasuredValue,
)
from si_app.application.services.strategic_indicators.measurements_cache_policy import (
    has_measurement_errors,
    should_cache_measurements,
)

MAX_MEASUREMENT_SNAPSHOT_VERSIONS = 3


@dataclass(frozen=True)
class MeasurementSnapshotVersion:
    """Uma tentativa de coleta de medições para um escopo/período."""

    items: tuple[StrategicIndicatorMeasuredValue, ...]
    errors: tuple[dict, ...]
    is_clean: bool
    recorded_at: float
    version_number: int


@dataclass(frozen=True)
class MeasurementSnapshotServeResult:
    """Resultado exposto ao pipeline após resolver versões."""

    items: list[StrategicIndicatorMeasuredValue]
    errors: list[dict]
    is_clean: bool
    version_count: int
    serving_version_number: int
    latest_version_number: int
    serving_fallback_from_previous_clean: bool


def _version_fingerprint(
    items: list[StrategicIndicatorMeasuredValue],
    errors: list[dict],
) -> tuple:
    item_sig = tuple(
        sorted(
            (
                item.indicator_id,
                item.department_id,
                item.value,
                tuple(sorted((item.unit_values or {}).items())),
            )
            for item in items
        )
    )
    error_sig = tuple(
        sorted(
            (
                str(error.get("department_id") or ""),
                str(error.get("source") or ""),
                str(error.get("message") or ""),
                str(error.get("code") or ""),
            )
            for error in errors
        )
    )
    return item_sig, error_sig


def append_measurement_snapshot_version(
    versions: list[MeasurementSnapshotVersion],
    *,
    items: list[StrategicIndicatorMeasuredValue],
    errors: list[dict],
    department_id: str | None,
) -> list[MeasurementSnapshotVersion]:
    is_clean = should_cache_measurements(items, errors, department_id=department_id)
    next_number = versions[-1].version_number + 1 if versions else 1

    if versions:
        latest = versions[-1]
        if _version_fingerprint(items, errors) == _version_fingerprint(
            list(latest.items),
            list(latest.errors),
        ):
            return versions

    new_version = MeasurementSnapshotVersion(
        items=tuple(items),
        errors=tuple(errors),
        is_clean=is_clean,
        recorded_at=time.monotonic(),
        version_number=next_number,
    )
    merged = [*versions, new_version]
    if len(merged) <= MAX_MEASUREMENT_SNAPSHOT_VERSIONS:
        return merged
    return merged[-MAX_MEASUREMENT_SNAPSHOT_VERSIONS:]


def resolve_measurement_snapshot_serve(
    versions: list[MeasurementSnapshotVersion],
    *,
    department_id: str | None,
) -> MeasurementSnapshotServeResult | None:
    if not versions:
        return None

    latest = versions[-1]
    clean_versions = [version for version in versions if version.is_clean]
    serving = clean_versions[-1] if clean_versions else latest

    latest_has_issues = (
        not latest.is_clean or has_measurement_errors(list(latest.errors))
    )
    serving_fallback = serving.version_number != latest.version_number and latest_has_issues

    if serving_fallback:
        display_errors = list(latest.errors)
    else:
        display_errors = list(serving.errors)

    return MeasurementSnapshotServeResult(
        items=list(serving.items),
        errors=display_errors,
        is_clean=serving.is_clean and not serving_fallback,
        version_count=len(versions),
        serving_version_number=serving.version_number,
        latest_version_number=latest.version_number,
        serving_fallback_from_previous_clean=serving_fallback,
    )


def failed_department_ids_from_errors(errors: list[dict]) -> set[str]:
    departments: set[str] = set()
    for entry in errors:
        if not isinstance(entry, dict):
            continue
        department_id = str(entry.get("department_id") or "").strip()
        if department_id:
            departments.add(department_id)
    return departments
