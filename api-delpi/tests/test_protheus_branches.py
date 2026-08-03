"""Testes — escopo de filial Protheus (all | 01 | 02)."""

from __future__ import annotations

import pytest

from app.domain.totvs.protheus_branches import (
    BRANCH_SCOPE_ALL,
    BRANCH_SCOPE_VALUES,
    append_branch_filter,
    branch_filter_sql,
    is_all_branches,
    normalize_branch_code,
    normalize_branch_scope,
)


def test_branch_scope_values_order() -> None:
    assert BRANCH_SCOPE_VALUES == ("all", "01", "02")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, BRANCH_SCOPE_ALL),
        ("", BRANCH_SCOPE_ALL),
        ("  ", BRANCH_SCOPE_ALL),
        ("all", BRANCH_SCOPE_ALL),
        ("All", BRANCH_SCOPE_ALL),
        ("Todas", BRANCH_SCOPE_ALL),
        ("todas", BRANCH_SCOPE_ALL),
        ("01", "01"),
        ("02", "02"),
    ],
)
def test_normalize_branch_scope(raw: str | None, expected: str) -> None:
    assert normalize_branch_scope(raw) == expected


@pytest.mark.parametrize("raw", ["03", "1", "everyone"])
def test_normalize_branch_scope_rejects_invalid(raw: str) -> None:
    with pytest.raises(ValueError, match="branch inválida"):
        normalize_branch_scope(raw)


def test_normalize_branch_code_requires_concrete() -> None:
    assert normalize_branch_code("01") == "01"
    with pytest.raises(ValueError):
        normalize_branch_code("all")
    with pytest.raises(ValueError):
        normalize_branch_code(None)


def test_branch_filter_sql_all_has_no_predicate() -> None:
    clause, params = branch_filter_sql("Filial", "all")
    assert clause == ""
    assert params == []
    clause2, params2 = branch_filter_sql("Filial", None)
    assert clause2 == ""
    assert params2 == []
    clause3, params3 = branch_filter_sql("Filial", "Todas")
    assert clause3 == ""
    assert params3 == []


def test_branch_filter_sql_concrete() -> None:
    clause, params = branch_filter_sql("Filial", "01")
    assert clause == "Filial = ?"
    assert params == ["01"]


def test_append_branch_filter_skips_all() -> None:
    clauses: list[str] = ["1=1"]
    params: list = []
    append_branch_filter(clauses, params, "Filial", "all")
    assert clauses == ["1=1"]
    assert params == []
    append_branch_filter(clauses, params, "Filial", "02")
    assert clauses == ["1=1", "Filial = ?"]
    assert params == ["02"]


def test_is_all_branches() -> None:
    assert is_all_branches("all") is True
    assert is_all_branches("Todas") is True
    assert is_all_branches("01") is False
