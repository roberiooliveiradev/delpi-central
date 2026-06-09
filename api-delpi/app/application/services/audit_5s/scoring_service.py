from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class CriterionScoreInput:
    senso_order: int
    score: int | None
    is_not_applicable: bool


def calculate_senso_percentual(scores: Iterable[CriterionScoreInput]) -> float | None:
    applicable = [
        item.score
        for item in scores
        if not item.is_not_applicable and item.score is not None
    ]
    if not applicable:
        return None

    total = sum(applicable)
    maximum = len(applicable) * 5
    return round((total / maximum) * 100, 2)


def calculate_overall_percentual(senso_percentuals: Iterable[float | None]) -> float | None:
    valid = [value for value in senso_percentuals if value is not None]
    if not valid:
        return None
    return round(sum(valid) / len(valid), 2)


def is_evaluation_complete(
    *,
    total_criteria: int,
    scored_criteria: int,
) -> bool:
    return total_criteria > 0 and scored_criteria >= total_criteria


def is_nc_candidate(score: int | None, is_not_applicable: bool) -> bool:
    return not is_not_applicable and score in (1, 3)
