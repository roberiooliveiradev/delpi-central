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
    repo = _Repo([date(2026, 8, 10)])
    result = GetNonconformityStreakUseCase(repo).execute(as_of=date(2026, 8, 17))

    assert repo.calls == [("customer", None, None)]
    assert result["current_days_without_nc"] == 7
    assert result["value"] == 7
    assert result["type"] == "customer"
    assert result["branch"] == "all"
    assert result["product_prefix"] is None
    assert result["last_nc_date"] == "2026-08-10"


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
    assert result["value"] == 16


def test_streak_rejects_invalid_product_prefix() -> None:
    with pytest.raises(ValueError, match="product_prefix"):
        GetNonconformityStreakUseCase(_Repo([])).execute(product_prefix="9048*")
