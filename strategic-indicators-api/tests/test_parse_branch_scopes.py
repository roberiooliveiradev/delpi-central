"""parse_branch_scopes — escopos de filial do refresh period_scores."""

from __future__ import annotations

from si_app.application.services.strategic_indicators.period_scores_refresh_service import (
    parse_branch_scopes,
)
from si_app.shared.goal_scope import DEFAULT_PERIOD_SCORES_REFRESH_BRANCHES


def test_parse_branch_scopes_empty_uses_default_three() -> None:
    assert parse_branch_scopes("") == list(DEFAULT_PERIOD_SCORES_REFRESH_BRANCHES)


def test_parse_branch_scopes_consolidated_only() -> None:
    assert parse_branch_scopes("consolidated") == [None]
    assert parse_branch_scopes("all") == [None]


def test_parse_branch_scopes_explicit_filiais() -> None:
    assert parse_branch_scopes("01,02") == ["01", "02"]
    assert parse_branch_scopes(" 01 , 02 ") == ["01", "02"]
