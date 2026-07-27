"""Unit — use case de streak NC usa primeira OV quando não há NC."""

from __future__ import annotations

from datetime import date

from app.application.use_cases.lmp_nonconformity.get_lmp_nonconformity_streak_use_case import (
    GetLmpNonconformityStreakUseCase,
)


class _NcRepo:
    def __init__(self, dates: list[date]) -> None:
        self._dates = dates

    def list_occurrence_dates(self) -> list[date]:
        return list(self._dates)


class _LmpRepo:
    def __init__(self, first_ov: date | None) -> None:
        self._first_ov = first_ov
        self.calls = 0

    def get_earliest_ov_date(self) -> date | None:
        self.calls += 1
        return self._first_ov


def test_streak_use_case_fetches_first_ov_when_no_nc() -> None:
    lmp = _LmpRepo(date(2026, 1, 10))
    use_case = GetLmpNonconformityStreakUseCase(_NcRepo([]), lmp_repository=lmp)
    result = use_case.execute(as_of=date(2026, 7, 27))
    assert lmp.calls == 1
    assert result["current_days_without_nc"] == 198
    assert result["reference_start_date"] == "2026-01-10"


def test_streak_use_case_skips_totvs_when_nc_exists() -> None:
    lmp = _LmpRepo(date(2020, 1, 1))
    use_case = GetLmpNonconformityStreakUseCase(
        _NcRepo([date(2026, 7, 20)]),
        lmp_repository=lmp,
    )
    result = use_case.execute(as_of=date(2026, 7, 27))
    assert lmp.calls == 0
    assert result["current_days_without_nc"] == 7
    assert result["last_nc_date"] == "2026-07-20"
