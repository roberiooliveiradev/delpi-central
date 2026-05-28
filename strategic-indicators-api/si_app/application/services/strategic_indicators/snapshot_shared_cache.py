from __future__ import annotations

from typing import Any

from si_app.application.services.strategic_indicators.measurement_snapshot_versions import (
    MeasurementSnapshotVersion,
)
from si_app.config import settings
from si_app.infrastructure.cache.ttl_cache import TtlCache

_measurements_cache: TtlCache[list[MeasurementSnapshotVersion]] = TtlCache(
    ttl_seconds=settings.SI_SNAPSHOT_CACHE_TTL_SECONDS,
)

_catalog_cache: TtlCache[Any] = TtlCache(
    ttl_seconds=settings.SI_SNAPSHOT_CACHE_TTL_SECONDS,
)

_catalog_fingerprint_cache: TtlCache[str] = TtlCache(
    ttl_seconds=settings.SI_SNAPSHOT_CACHE_TTL_SECONDS,
)

_rol_cache: TtlCache[dict] = TtlCache(
    ttl_seconds=settings.SI_SNAPSHOT_CACHE_TTL_SECONDS,
)


def measurements_cache_key(
    *,
    start_date: str,
    end_date: str,
    competence: str | None,
    department_id: str | None,
    branch: str | None,
) -> str:
    return "|".join(
        [
            "m",
            start_date,
            end_date,
            competence or "",
            department_id or "",
            branch or "",
        ]
    )


def get_catalog_fingerprint(cache_key: str) -> str | None:
    return _catalog_fingerprint_cache.get(cache_key)


def set_catalog_fingerprint(cache_key: str, fingerprint: str) -> None:
    _catalog_fingerprint_cache.set(cache_key, fingerprint)


def rol_cache_key(
    *,
    branch: str | None,
    start_date: str | None,
    end_date: str | None,
) -> str:
    return "|".join(
        [
            "rol",
            branch or "",
            start_date or "",
            end_date or "",
        ]
    )


def get_cached_rol(cache_key: str) -> dict | None:
    return _rol_cache.get(cache_key)


def set_cached_rol(cache_key: str, payload: dict) -> None:
    _rol_cache.set(cache_key, payload)


def catalog_cache_key(
    *,
    competence: str | None,
    start_date: str | None,
    end_date: str | None,
    department_id: str | None,
    branch: str | None,
) -> str:
    return "|".join(
        [
            "c",
            competence or "",
            start_date or "",
            end_date or "",
            department_id or "",
            branch or "",
        ]
    )


def clear_in_process_snapshot_cache() -> None:
    """Limpa apenas caches em memória (TTL). Não altera period_scores no Postgres."""
    from si_app.application.services.lmp.lmp_dashboard_cache import (
        invalidate_lmp_dashboard_cache,
    )
    from si_app.application.services.lmp.lmp_dashboard_summary_cache import (
        invalidate_lmp_dashboard_summary_cache,
    )

    _measurements_cache.invalidate_all()
    _rol_cache.invalidate_all()
    _catalog_cache.invalidate_all()
    _catalog_fingerprint_cache.invalidate_all()
    invalidate_lmp_dashboard_cache()
    invalidate_lmp_dashboard_summary_cache()


def invalidate_strategic_indicators_snapshot_cache(
    *,
    schedule_materialized_refresh: bool = True,
) -> None:
    from si_app.application.services.strategic_indicators.snapshot_refresh_coordinator import (
        schedule_period_scores_refresh_after_config_change,
    )
    from si_app.config import settings
    from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_calculation_snapshots_repository import (
        PostgresStrategicIndicatorsCalculationSnapshotsRepository,
    )
    from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_period_scores_repository import (
        PostgresStrategicIndicatorsPeriodScoresRepository,
    )

    clear_in_process_snapshot_cache()

    if settings.SI_PERIOD_SCORES_ENABLED:
        PostgresStrategicIndicatorsPeriodScoresRepository().delete_all()

    if settings.SI_CALCULATION_SNAPSHOTS_ENABLED:
        PostgresStrategicIndicatorsCalculationSnapshotsRepository().delete_all()

    if schedule_materialized_refresh:
        schedule_period_scores_refresh_after_config_change()
