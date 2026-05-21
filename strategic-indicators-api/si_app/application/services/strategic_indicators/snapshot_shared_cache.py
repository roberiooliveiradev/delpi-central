from __future__ import annotations

from typing import Any

from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicIndicatorMeasuredValue,
)
from si_app.config import settings
from si_app.infrastructure.cache.ttl_cache import TtlCache

_measurements_cache: TtlCache[
    tuple[list[StrategicIndicatorMeasuredValue], list[dict]]
] = TtlCache(ttl_seconds=settings.SI_SNAPSHOT_CACHE_TTL_SECONDS)

_catalog_cache: TtlCache[Any] = TtlCache(
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


def invalidate_strategic_indicators_snapshot_cache() -> None:
    from si_app.application.services.lmp.lmp_dashboard_cache import (
        invalidate_lmp_dashboard_cache,
    )
    from si_app.application.services.lmp.lmp_dashboard_summary_cache import (
        invalidate_lmp_dashboard_summary_cache,
    )
    from si_app.config import settings
    from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_period_scores_repository import (
        PostgresStrategicIndicatorsPeriodScoresRepository,
    )

    _measurements_cache.invalidate_all()
    _catalog_cache.invalidate_all()
    invalidate_lmp_dashboard_cache()
    invalidate_lmp_dashboard_summary_cache()

    if settings.SI_PERIOD_SCORES_ENABLED:
        PostgresStrategicIndicatorsPeriodScoresRepository().delete_all()
