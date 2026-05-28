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
from si_app.shared.goal_scope import DEFAULT_PERIOD_SCORES_REFRESH_BRANCHES
from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_refresh_state_repository import (
    PostgresStrategicIndicatorsRefreshStateRepository,
)

logger = logging.getLogger("strategic_indicators.period_scores_refresh")


def _parse_branch_scopes() -> list[str | None]:
    raw = (settings.SI_PERIOD_SCORES_REFRESH_BRANCHES or "").strip()
    if not raw:
        return list(DEFAULT_PERIOD_SCORES_REFRESH_BRANCHES)

    scopes: list[str | None] = []
    for item in raw.split(","):
        normalized = item.strip()
        if normalized in {"", "consolidated", "all"}:
            if None not in scopes:
                scopes.append(None)
            continue
        scopes.append(normalized)

    return scopes or [None]


def _department_scopes(
    *,
    include_per_department: bool,
    reference_competence: str,
) -> list[str | None]:
    scopes: list[str | None] = [None]
    if not include_per_department:
        return scopes

    snapshot_service = build_strategic_indicators_snapshot_service()
    catalog = snapshot_service.get_catalog_snapshot(
        competence=reference_competence,
    )
    for department in catalog.departments_catalog:
        scopes.append(department.department_id)
    return scopes


def refresh_period_scores_materialized(
    *,
    reference_competence: str | None = None,
    trends_months: int | None = None,
    per_department: bool | None = None,
    invalidate_cache: bool = True,
) -> int:
    """
    Recalcula e persiste period_scores e calculation_snapshots para os escopos configurados.
    Retorna quantidade de períodos gravados (upserts).

    `reference_competence`: competência YYYY-MM de referência para a janela de tendência
    (default: mês atual do servidor).
    `trends_months` / `per_department`: sobrescrevem env (útil no script CLI sem recriar container).
    `invalidate_cache`: quando False, não apaga period_scores existentes (refresh incremental).
    """
    if not settings.SI_PERIOD_SCORES_ENABLED:
        logger.info("si_period_scores_refresh_skipped disabled")
        return 0

    resolved_trends_months = max(
        2,
        min(
            trends_months
            if trends_months is not None
            else settings.SI_PERIOD_SCORES_REFRESH_TRENDS_MONTHS,
            12,
        ),
    )
    resolved_per_department = (
        settings.SI_PERIOD_SCORES_REFRESH_PER_DEPARTMENT
        if per_department is None
        else per_department
    )

    state_repo = PostgresStrategicIndicatorsRefreshStateRepository()
    state_repo.mark_started()
    started = time.perf_counter()

    resolved_reference = (reference_competence or current_competence()).strip()
    resolve_period(
        competence=resolved_reference,
        start_date=None,
        end_date=None,
    )

    logger.info(
        (
            "si_period_scores_refresh_start competence=%s trends_months=%d "
            "per_department=%s invalidate_cache=%s"
        ),
        resolved_reference,
        resolved_trends_months,
        resolved_per_department,
        invalidate_cache,
    )

    try:
        if invalidate_cache:
            invalidate_strategic_indicators_snapshot_cache(
                schedule_materialized_refresh=False,
            )
        else:
            logger.info("si_period_scores_refresh_skip_invalidate")

        snapshot_service = build_strategic_indicators_snapshot_service()
        reference_competence = resolved_reference
        trend_periods = build_trend_periods(
            reference_competence=reference_competence,
            months=resolved_trends_months,
        )

        branch_scopes = _parse_branch_scopes()
        department_scopes = _department_scopes(
            include_per_department=resolved_per_department,
            reference_competence=reference_competence,
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
                if department_id and not resolved_per_department:
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
