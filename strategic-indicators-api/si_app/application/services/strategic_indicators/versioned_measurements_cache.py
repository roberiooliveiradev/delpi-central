from __future__ import annotations

import logging

from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicIndicatorMeasuredValue,
)
from si_app.application.services.strategic_indicators.measurement_snapshot_versions import (
    MeasurementSnapshotServeResult,
    MeasurementSnapshotVersion,
    append_measurement_snapshot_version,
    resolve_measurement_snapshot_serve,
)
from si_app.application.services.strategic_indicators.snapshot_shared_cache import (
    _measurements_cache as shared_measurements_version_store,
)

logger = logging.getLogger("strategic_indicators.snapshot_versions")


def get_versioned_measurements(
    cache_key: str,
    *,
    department_id: str | None,
) -> MeasurementSnapshotServeResult | None:
    versions = shared_measurements_version_store.get(cache_key)
    if not versions:
        return None
    return resolve_measurement_snapshot_serve(versions, department_id=department_id)


def record_versioned_measurements(
    cache_key: str,
    *,
    items: list[StrategicIndicatorMeasuredValue],
    errors: list[dict],
    department_id: str | None,
) -> MeasurementSnapshotServeResult:
    versions: list[MeasurementSnapshotVersion] = list(
        shared_measurements_version_store.get(cache_key) or []
    )
    versions = append_measurement_snapshot_version(
        versions,
        items=items,
        errors=errors,
        department_id=department_id,
    )
    shared_measurements_version_store.set(cache_key, versions)

    resolved = resolve_measurement_snapshot_serve(versions, department_id=department_id)
    if resolved is None:
        return MeasurementSnapshotServeResult(
            items=items,
            errors=errors,
            is_clean=False,
            version_count=1,
            serving_version_number=1,
            latest_version_number=1,
            serving_fallback_from_previous_clean=False,
        )

    if resolved.serving_fallback_from_previous_clean:
        logger.warning(
            (
                "si_measurements_serving_clean_version cache_key=%s "
                "serving_v=%d latest_v=%d versions=%d latest_errors=%d"
            ),
            cache_key,
            resolved.serving_version_number,
            resolved.latest_version_number,
            resolved.version_count,
            len(errors),
        )
    elif not resolved.is_clean:
        logger.warning(
            (
                "si_measurements_no_clean_version cache_key=%s "
                "versions=%d latest_errors=%d"
            ),
            cache_key,
            resolved.version_count,
            len(errors),
        )

    return resolved
