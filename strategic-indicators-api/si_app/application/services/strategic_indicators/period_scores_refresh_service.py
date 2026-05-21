from __future__ import annotations

import logging
import time

from si_app.application.services.strategic_indicators.snapshot_shared_cache import (
    invalidate_strategic_indicators_snapshot_cache,
)
from si_app.application.use_cases.strategic_indicators.period_resolution import (
    build_trend_periods,
    current_competence,
    previous_period,
    resolve_period,
)
from si_app.composition.strategic_indicators_composer import (
    build_strategic_indicators_snapshot_service,
)
from si_app.config import settings
from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_refresh_state_repository import (
    PostgresStrategicIndicatorsRefreshStateRepository,
)

logger = logging.getLogger("strategic_indicators.period_scores_refresh")


def _parse_branch_scopes() -> list[str | None]:
    raw = (settings.SI_PERIOD_SCORES_REFRESH_BRANCHES or "").strip()
    if not raw:
        return [None]

    scopes: list[str | None] = []
    for item in raw.split(","):
        normalized = item.strip()
        if normalized in {"", "consolidated", "all"}:
            if None not in scopes:
                scopes.append(None)
            continue
        scopes.append(normalized)

    return scopes or [None]


def _department_scopes(*, include_per_department: bool) -> list[str | None]:
    scopes: list[str | None] = [None]
    if not include_per_department:
        return scopes

    snapshot_service = build_strategic_indicators_snapshot_service()
    catalog = snapshot_service.get_catalog_snapshot(
        competence=current_competence(),
    )
    for department in catalog.departments_catalog:
        scopes.append(department.department_id)
    return scopes


def refresh_period_scores_materialized() -> int:
    """
    Recalcula e persiste period_scores e calculation_snapshots para os escopos configurados.
    Retorna quantidade de períodos gravados (upserts).
    """
    if not settings.SI_PERIOD_SCORES_ENABLED:
        logger.info("si_period_scores_refresh_skipped disabled")
        return 0

    state_repo = PostgresStrategicIndicatorsRefreshStateRepository()
    state_repo.mark_started()
    started = time.perf_counter()

    try:
        invalidate_strategic_indicators_snapshot_cache()

        snapshot_service = build_strategic_indicators_snapshot_service()
        reference_competence = current_competence()
        trend_periods = build_trend_periods(
            reference_competence=reference_competence,
            months=settings.SI_PERIOD_SCORES_REFRESH_TRENDS_MONTHS,
        )

        branch_scopes = _parse_branch_scopes()
        department_scopes = _department_scopes(
            include_per_department=settings.SI_PERIOD_SCORES_REFRESH_PER_DEPARTMENT,
        )

        periods_by_competence: dict[str, object] = {
            period.competence: period for period in trend_periods
        }
        if settings.SI_PERIOD_SCORES_REFRESH_INCLUDE_PREVIOUS:
            current = resolve_period(
                competence=reference_competence,
                start_date=None,
                end_date=None,
            )
            prev = previous_period(current)
            periods_by_competence[prev.competence] = prev

        periods = list(periods_by_competence.values())
        upserted = 0

        for branch in branch_scopes:
            for department_id in department_scopes:
                if department_id and not settings.SI_PERIOD_SCORES_REFRESH_PER_DEPARTMENT:
                    continue

                target_periods = periods
                if department_id:
                    current = resolve_period(
                        competence=reference_competence,
                        start_date=None,
                        end_date=None,
                    )
                    target_periods = [current]

                snapshots = snapshot_service.get_series_snapshot_optimized(
                    periods=target_periods,
                    department_id=department_id,
                    branch=branch,
                    force_compute=True,
                )
                upserted += len(snapshots)

        duration_ms = int((time.perf_counter() - started) * 1000)
        state_repo.mark_completed(
            duration_ms=duration_ms,
            periods_upserted=upserted,
        )
        logger.info(
            (
                "si_period_scores_refresh_done competence=%s periods=%d branches=%d "
                "departments=%d ms=%d calculation_snapshots=%s"
            ),
            reference_competence,
            upserted,
            len(branch_scopes),
            len(department_scopes),
            duration_ms,
            settings.SI_CALCULATION_SNAPSHOTS_ENABLED,
        )
        return upserted
    except Exception as exc:
        state_repo.mark_failed(error_message=str(exc))
        logger.exception("si_period_scores_refresh_failed")
        raise
