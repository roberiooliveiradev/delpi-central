"""Unit tests for level vs flow goal temporal policy."""

from si_app.domain.services.goal_temporal_policy import (
    LEVEL_GOAL_INDICATOR_IDS,
    is_level_goal_indicator,
)


def test_stock_value_is_level_goal() -> None:
    assert "supplies-stock-value" in LEVEL_GOAL_INDICATOR_IDS
    assert is_level_goal_indicator("supplies-stock-value") is True


def test_flow_currency_sibling_is_not_level() -> None:
    assert is_level_goal_indicator("supplies-negotiation-savings") is False
    assert is_level_goal_indicator("supplies-otd") is False
    assert is_level_goal_indicator(None) is False
    assert is_level_goal_indicator("  ") is False
