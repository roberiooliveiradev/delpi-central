"""Temporal goal semantics: level (snapshot/balance) vs flow (accumulating).

Cross-branch aggregation (sum 01+02) stays in consolidated_value_aggregation.
This module only decides whether period comparable applies day/month prorata.
"""

from __future__ import annotations

# Balance / snapshot indicators: comparable_goal = monthly level (no day prorata,
# no multi-month sum). Extend deliberately — do not treat all currency as level
# (negotiation savings, ROL, etc. remain flow).
LEVEL_GOAL_INDICATOR_IDS: frozenset[str] = frozenset(
    {
        "supplies-stock-value",
    }
)


def is_level_goal_indicator(indicator_id: str | None) -> bool:
    normalized = (indicator_id or "").strip()
    return normalized in LEVEL_GOAL_INDICATOR_IDS
