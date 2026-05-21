from __future__ import annotations

import logging
import time

from tm_app.domain.services.dashboard_calculator import DashboardCalculatorService
from tm_app.infrastructure.persistence.repositories.dashboard_data_repository import (
    DashboardCalculoRepository,
    DashboardDataRepository,
)

logger = logging.getLogger(__name__)


class DashboardRecalcService:
    def __init__(self) -> None:
        self._calculator = DashboardCalculatorService()
        self._data_repo = DashboardDataRepository()
        self._dashboard_repo = DashboardCalculoRepository()

    def recalculate(self) -> dict:
        started = time.perf_counter()
        raw = self._data_repo.load_raw()
        rows = self._calculator.build_dashboard_rows(raw)
        inserted = self._dashboard_repo.replace_all(rows)
        elapsed_ms = (time.perf_counter() - started) * 1000

        logger.info(
            "transformometro_dashboard_recalc_ok rows=%d elapsed_ms=%.0f",
            inserted,
            elapsed_ms,
        )

        return {
            "rows_upserted": inserted,
            "elapsed_ms": round(elapsed_ms),
        }
