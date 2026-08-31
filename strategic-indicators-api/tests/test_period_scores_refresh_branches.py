"""Refresh period_scores — escopos consolidados + filiais no default Compose."""

from __future__ import annotations

from si_app.application.services.strategic_indicators.period_scores_refresh_service import (
    parse_branch_scopes,
)
from si_app.shared.goal_scope import DEFAULT_PERIOD_SCORES_REFRESH_BRANCHES


def test_parse_branch_scopes_compose_default_includes_filiais() -> None:
    assert parse_branch_scopes("consolidated,01,02") == [None, "01", "02"]
    assert parse_branch_scopes("consolidated,01,02") == list(
        DEFAULT_PERIOD_SCORES_REFRESH_BRANCHES
    )


def test_operations_docs_document_filial_refresh_default() -> None:
    from pathlib import Path

    operations = (
        Path(__file__).resolve().parents[1] / "docs" / "OPERATIONS.md"
    ).read_text(encoding="utf-8")
    assert "consolidated,01,02" in operations
    assert "SI_PERIOD_SCORES_MAX_AGE_SECONDS" in operations
