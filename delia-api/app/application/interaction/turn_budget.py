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


# Edge budget: the platform edge (Cloudflare proxy) terminates proxied
# requests at ~100s (observed as 524). The default turn budget keeps a
# >=20s margin below the edge deadline so the application always answers
# first with a deterministic bounded result.
DEFAULT_TURN_BUDGET_SECONDS = 80.0


@dataclass(frozen=True, slots=True)
class TurnDeadline:
    """Monotonic deadline shared by all stages of one turn."""

    ends_at: float
    clock: Callable[[], float] = field(
        default=time.monotonic, compare=False, repr=False
    )

    @classmethod
    def start(
        cls,
        total_seconds: float,
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> TurnDeadline:
        return cls(
            ends_at=clock() + max(0.0, float(total_seconds)),
            clock=clock,
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
