from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeedbackInput:
    rating: int
    liked_most: str | None = None
    suggestions: str | None = None
