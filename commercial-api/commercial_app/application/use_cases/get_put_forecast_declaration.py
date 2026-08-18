"""Get / put declared FCT for a calendar month (not TOTVS, not OP forecast)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from commercial_app.domain.ports.forecast_declaration_repository_port import (
    ForecastDeclarationRepositoryPort,
)

FORECAST_TZ = "America/Sao_Paulo"
NATURE_DECLARED_FCT = "declared_fct"


def current_cycle(*, as_of: datetime | None = None) -> tuple[int, int]:
    stamp = as_of or datetime.now(ZoneInfo(FORECAST_TZ))
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=ZoneInfo(FORECAST_TZ))
    else:
        stamp = stamp.astimezone(ZoneInfo(FORECAST_TZ))
    return stamp.year, stamp.month


class GetPutForecastDeclarationUseCase:
    def __init__(self, repository: ForecastDeclarationRepositoryPort) -> None:
        self._repo = repository

    def get(
        self,
        *,
        cycle_year: int | None = None,
        cycle_month: int | None = None,
        portfolio_id: str | None = None,
    ) -> dict[str, Any]:
        year, month = self._resolve_cycle(cycle_year, cycle_month)
        pid = (portfolio_id or "").strip()
        row = self._repo.get(cycle_year=year, cycle_month=month, portfolio_id=pid)
        if row is None:
            return {
                "cycleYear": year,
                "cycleMonth": month,
                "portfolioId": pid,
                "declaredValue": 0.0,
                "updatedBy": "",
                "updatedAt": None,
                "nature": NATURE_DECLARED_FCT,
                "empty": True,
            }
        return {**row, "nature": NATURE_DECLARED_FCT, "empty": False}

    def put(
        self,
        *,
        declared_value: float,
        updated_by: str,
        cycle_year: int | None = None,
        cycle_month: int | None = None,
        portfolio_id: str | None = None,
    ) -> dict[str, Any]:
        if declared_value < 0:
            raise ValueError("declared_value must be >= 0")
        year, month = self._resolve_cycle(cycle_year, cycle_month)
        pid = (portfolio_id or "").strip()
        row = self._repo.upsert(
            cycle_year=year,
            cycle_month=month,
            portfolio_id=pid,
            declared_value=round(float(declared_value), 2),
            updated_by=(updated_by or "").strip(),
        )
        return {**row, "nature": NATURE_DECLARED_FCT, "empty": False}

    def _resolve_cycle(
        self, cycle_year: int | None, cycle_month: int | None
    ) -> tuple[int, int]:
        if cycle_year is None or cycle_month is None:
            return current_cycle()
        if not (1 <= int(cycle_month) <= 12):
            raise ValueError("cycle_month must be 1..12")
        return int(cycle_year), int(cycle_month)
