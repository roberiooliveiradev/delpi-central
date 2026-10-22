"""TurnDeadline — one total wall-clock budget for an interaction turn.

C3-INTELLIGENCE-LOOP-03R2A: production proved the edge (Cloudflare 524)
can fire mid-turn while governed stages keep running. One monotonic
deadline is computed at the start of the turn and shared by every
expensive stage — each stage receives at most
``min(configured stage max, remaining budget)`` and no stage may start
once the deadline passed.

This is a reduction-only ceiling over the existing per-stage
``timeout_seconds`` contract — it can shorten, never lengthen, any
stage timeout. It is not a second budget system: it reuses the same
semantic timeout contract already carried by ModelInvocationRequest.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field


# Global conversational turn budget (Stage 05). The platform edge
# (Cloudflare proxy) terminates proxied requests at ~100s (observed as
# 524); 30s keeps a large edge margin while bounding end-to-end UX.
# Per-stage timeouts remain reduction-clamped by this ceiling.
DEFAULT_TURN_BUDGET_SECONDS = 30.0


@dataclass(frozen=True, slots=True)
class TurnDeadline:
    """Monotonic deadline shared by all stages of one turn."""

    ends_at: float
    clock: Callable[[], float] = field(
        default=time.monotonic, compare=False, repr=False
    )
    # CP5/R2: the instant this deadline's clock started — lets an
    # outer monotonic budget anchor at the REAL interaction start
    # instead of being recomputed at a downstream seam. ``None`` for
    # directly-constructed deadlines (callers keep the legacy anchor).
    started_at: float | None = None

    @classmethod
    def start(
        cls,
        total_seconds: float,
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> TurnDeadline:
        now = clock()
        return cls(
            ends_at=now + max(0.0, float(total_seconds)),
            clock=clock,
            started_at=now,
        )

    def remaining_seconds(self) -> float:
        return max(0.0, self.ends_at - self.clock())

    def exhausted(self) -> bool:
        return self.clock() >= self.ends_at

    def stage_timeout(self, configured_max: float) -> float:
        """Per-stage timeout bounded by both the configured cap and the
        remaining turn budget — never exceeds the configured maximum."""
        return max(0.0, min(float(configured_max), self.remaining_seconds()))

    def check(self, stage: str) -> None:
        """Fail fast when the turn budget is already exhausted.

        Raises TurnBudgetExhausted so the orchestration boundary can
        render the canonical deterministic terminal result — no stage
        may start once the deadline passed.
        """
        if self.exhausted():
            raise TurnBudgetExhausted(stage)


class TurnBudgetExhausted(Exception):
    """The shared turn deadline passed before the stage could start."""

    def __init__(self, stage: str) -> None:
        super().__init__(stage)
        self.stage = stage


def remaining_budget(
    started: float, total_seconds: float | None
) -> float | None:
    """Remaining budget for the next bounded call inside a fan-out.

    Providers that fan out to several sources/specialists under one
    ``timeout_seconds`` split the budget per call so the total cannot
    exceed the caller's bound. ``None`` means unbounded by the caller
    (the callee's own configured stage max still applies).
    """
    if total_seconds is None:
        return None
    return max(0.0, float(total_seconds) - (time.monotonic() - started))
