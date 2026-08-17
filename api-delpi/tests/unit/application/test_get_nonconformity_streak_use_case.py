"""Unit — streak de NC TOTVS (QI2) com o mesmo filtro do dashboard."""

from __future__ import annotations

from datetime import date

import pytest

from app.application.use_cases.nonconformity.get_nonconformity_streak_use_case import (
    GetNonconformityStreakUseCase,
)


class _Repo:
    def __init__(self, dates: list[date]) -> None:
        self._dates = dates
        self.calls: list[tuple[str, str | None, str | None]] = []

    def list_occurrence_dates(
        self,
        *,
        filter_type: str,
        branch: str | None = None,
        product_prefix: str | None = None,
    ) -> list[date]:
        self.calls.append((filter_type, branch, product_prefix))
        return list(self._dates)


def test_streak_defaults_to_customer_and_exposes_value() -> None:
    """as_of=17 → fecha em 16; última NC 10/08 → 6 dias."""
    repo = _Repo([date(2026, 8, 10)])
    result = GetNonconformityStreakUseCase(repo).execute(as_of=date(2026, 8, 17))

    assert repo.calls == [("customer", None, None)]
    assert result["current_days_without_nc"] == 6
    assert result["value"] == 6
    assert result["as_of_date"] == "2026-08-16"
    assert result["type"] == "customer"
    assert result["branch"] == "all"
    assert result["product_prefix"] is None
    assert result["last_nc_date"] == "2026-08-10"


def test_streak_excludes_occurrences_on_as_of_day() -> None:
    """NC de «hoje» (as_of) não entra — só até o dia anterior."""
    repo = _Repo([date(2026, 8, 10), date(2026, 8, 17)])
    result = GetNonconformityStreakUseCase(repo).execute(as_of=date(2026, 8, 17))

    assert result["last_nc_date"] == "2026-08-10"
    assert result["value"] == 6
    assert result["as_of_date"] == "2026-08-16"


def test_streak_normalizes_branch_and_type() -> None:
    repo = _Repo([date(2026, 8, 17)])
    result = GetNonconformityStreakUseCase(repo).execute(
        filter_type="CUSTOMER",
        branch="01",
        as_of=date(2026, 8, 17),
    )

    assert repo.calls == [("customer", "01", None)]
    assert result["value"] == 0
    assert result["branch"] == "01"


def test_streak_treats_all_branch_as_unfiltered() -> None:
    repo = _Repo([])
    result = GetNonconformityStreakUseCase(repo).execute(
        filter_type="internal",
        branch="all",
        as_of=date(2026, 8, 17),
    )

    assert repo.calls == [("internal", None, None)]
    assert result["value"] == 0
    assert result["branch"] == "all"


def test_streak_forwards_product_prefix() -> None:
    repo = _Repo([date(2026, 8, 1)])
    result = GetNonconformityStreakUseCase(repo).execute(
        product_prefix="9048",
        as_of=date(2026, 8, 17),
    )

    assert repo.calls == [("customer", None, "9048")]
    assert result["product_prefix"] == "9048"
    assert result["value"] == 15


def test_streak_ignores_future_qi2_occurrence_for_product_prefix() -> None:
    """Caso real: filial 02 + 9026 com QI2_OCORRE=20260827 enquanto as_of=2026-08-17."""
    repo = _Repo([date(2026, 7, 9), date(2026, 8, 27)])
    result = GetNonconformityStreakUseCase(repo).execute(
        branch="02",
        product_prefix="9026",
        as_of=date(2026, 8, 17),
    )

    assert result["value"] == 38
    assert result["last_nc_date"] == "2026-07-09"
    assert result["as_of_date"] == "2026-08-16"
    assert result["branch"] == "02"
    assert result["product_prefix"] == "9026"


def test_streak_rejects_invalid_product_prefix() -> None:
    with pytest.raises(ValueError, match="product_prefix"):
        GetNonconformityStreakUseCase(_Repo([])).execute(product_prefix="9048*")
