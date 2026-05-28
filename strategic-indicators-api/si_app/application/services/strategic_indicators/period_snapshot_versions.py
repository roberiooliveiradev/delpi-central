from __future__ import annotations

from dataclasses import replace

from si_app.application.services.strategic_indicators.measurements_cache_policy import (
    has_measurement_errors,
)
from si_app.application.services.strategic_indicators.measurement_snapshot_versions import (
    MAX_MEASUREMENT_SNAPSHOT_VERSIONS,
)
from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_models import (
    PeriodScoresCacheEntry,
    StrategicIndicatorsPeriodSnapshot,
)


def resolve_period_scores_serve(
    entries: list[PeriodScoresCacheEntry],
) -> PeriodScoresCacheEntry | None:
    if not entries:
        return None

    ordered = sorted(entries, key=lambda entry: entry.version_number)
    latest = ordered[-1]
    clean_entries = [entry for entry in ordered if entry.is_clean]
    serving = clean_entries[-1] if clean_entries else latest

    latest_has_issues = not latest.is_clean or has_measurement_errors(
        list(latest.snapshot.measurement_errors)
    )
    serving_fallback = (
        serving.version_number != latest.version_number and latest_has_issues
    )

    if not serving_fallback:
        return serving

    snapshot = replace(
        serving.snapshot,
        measurement_errors=list(latest.snapshot.measurement_errors),
    )
    return PeriodScoresCacheEntry(
        snapshot=snapshot,
        catalog_inputs_hash=serving.catalog_inputs_hash,
        version_number=serving.version_number,
        is_clean=serving.is_clean,
    )


def prune_period_score_version_numbers(
    version_numbers: list[int],
) -> list[int]:
    if len(version_numbers) <= MAX_MEASUREMENT_SNAPSHOT_VERSIONS:
        return version_numbers
    return sorted(version_numbers)[-MAX_MEASUREMENT_SNAPSHOT_VERSIONS:]
