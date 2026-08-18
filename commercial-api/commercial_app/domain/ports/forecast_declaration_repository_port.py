"""Port for declared monthly forecast (FCT)."""

from __future__ import annotations

from typing import Protocol


class ForecastDeclarationRecord(dict):
    """Typed dict-shaped record: cycleYear, cycleMonth, portfolioId, declaredValue, updatedBy, updatedAt."""


class ForecastDeclarationRepositoryPort(Protocol):
    def get(
        self,
        *,
        cycle_year: int,
        cycle_month: int,
        portfolio_id: str,
    ) -> dict | None: ...

    def upsert(
        self,
        *,
        cycle_year: int,
        cycle_month: int,
        portfolio_id: str,
        declared_value: float,
        updated_by: str,
    ) -> dict: ...
