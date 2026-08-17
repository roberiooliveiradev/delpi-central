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


def test_cli_parser_exposes_branches_flag() -> None:
    import importlib.util
    from pathlib import Path

    script = (
        Path(__file__).resolve().parents[1] / "scripts" / "refresh_period_scores.py"
    )
    spec = importlib.util.spec_from_file_location("refresh_period_scores_cli", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    parser = module.build_parser()
    args = parser.parse_args(["--branches", "01,02", "--no-invalidate"])
    assert args.branches == "01,02"
    assert args.no_invalidate is True
    assert "--branches" in parser.format_help()
    assert parse_branch_scopes(args.branches) == ["01", "02"]
