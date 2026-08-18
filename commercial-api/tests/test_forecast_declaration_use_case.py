"""Unit tests for declared FCT use case (in-memory repository)."""

from __future__ import annotations

from commercial_app.application.use_cases.get_put_forecast_declaration import (
    NATURE_DECLARED_FCT,
    GetPutForecastDeclarationUseCase,
)


class _MemoryRepo:
    def __init__(self) -> None:
        self.rows: dict[tuple[int, int, str], dict] = {}

    def get(self, *, cycle_year: int, cycle_month: int, portfolio_id: str):
        return self.rows.get((cycle_year, cycle_month, portfolio_id))

    def upsert(
        self,
        *,
        cycle_year: int,
        cycle_month: int,
        portfolio_id: str,
        declared_value: float,
        updated_by: str,
    ) -> dict:
        row = {
            "cycleYear": cycle_year,
            "cycleMonth": cycle_month,
            "portfolioId": portfolio_id,
            "declaredValue": declared_value,
            "updatedBy": updated_by,
            "updatedAt": "2026-08-18T12:00:00+00:00",
        }
        self.rows[(cycle_year, cycle_month, portfolio_id)] = row
        return row


def test_get_empty_declaration() -> None:
    uc = GetPutForecastDeclarationUseCase(_MemoryRepo())
    data = uc.get(cycle_year=2026, cycle_month=8, portfolio_id="")
    assert data["empty"] is True
    assert data["declaredValue"] == 0.0
    assert data["nature"] == NATURE_DECLARED_FCT


def test_put_then_get_roundtrip() -> None:
    uc = GetPutForecastDeclarationUseCase(_MemoryRepo())
    saved = uc.put(
        declared_value=1500.5,
        updated_by="user-1",
        cycle_year=2026,
        cycle_month=8,
        portfolio_id="p1",
    )
    assert saved["empty"] is False
    assert saved["declaredValue"] == 1500.5
    loaded = uc.get(cycle_year=2026, cycle_month=8, portfolio_id="p1")
    assert loaded["declaredValue"] == 1500.5
    assert loaded["updatedBy"] == "user-1"


def test_put_rejects_negative() -> None:
    uc = GetPutForecastDeclarationUseCase(_MemoryRepo())
    try:
        uc.put(declared_value=-1, updated_by="x", cycle_year=2026, cycle_month=8)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
