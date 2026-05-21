from __future__ import annotations

from typing import Any


def indicator_has_score(indicator: Any) -> bool:
    return getattr(indicator, "score", None) is not None


def iter_scored_indicators(indicators: list[Any]) -> list[Any]:
    return [item for item in indicators if indicator_has_score(item)]
