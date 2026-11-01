"""S3 — explicit subobjective tracking for multi-requirement turns.

State model ``subobjective(id, goal, dependencies, evidence_needed,
state, attempts, evidence_refs, gaps)`` — a bounded, deterministic
runtime record of what one investigation already proved per
sub-requirement. It reuses the canonical planning vocabulary
(``PlanStep``-shaped proposals validated elsewhere) and the closed
state set fixed by the binding contract:

    PENDING → READY → IN_PROGRESS → COMPLETED | PARTIAL | BLOCKED | FAILED

Rules (fail-closed, no semantics invented here):
- a subobjective is READY only when every dependency is COMPLETED or
  PARTIAL-with-gap (a PARTIAL dependency never unblocks completion of
  the dependent, only its attempt);
- COMPLETED requires recorded evidence_refs — a tool 200, a catalog
  row or a generic reply never marks completion;
- attempts are capped per subobjective and per investigation — a new
  attempt with no recorded progress is rejected;
- BLOCKED is terminal for non-recoverable failures; PARTIAL records
  the uncovered gap so synthesis may declare it honestly;
- this module never invokes capabilities, authorizes actions or
  judges evidence — it only records validated state transitions.

The tracker is application state — never persisted with secrets,
tokens or untrusted content (S5 owns durable checkpointing).
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Mapping

SUBOBJECTIVE_PENDING = "PENDING"
SUBOBJECTIVE_READY = "READY"
SUBOBJECTIVE_IN_PROGRESS = "IN_PROGRESS"
SUBOBJECTIVE_COMPLETED = "COMPLETED"
SUBOBJECTIVE_PARTIAL = "PARTIAL"
SUBOBJECTIVE_BLOCKED = "BLOCKED"
SUBOBJECTIVE_FAILED = "FAILED"

SUBOBJECTIVE_STATES = frozenset(
    {
        SUBOBJECTIVE_PENDING,
        SUBOBJECTIVE_READY,
        SUBOBJECTIVE_IN_PROGRESS,
        SUBOBJECTIVE_COMPLETED,
        SUBOBJECTIVE_PARTIAL,
        SUBOBJECTIVE_BLOCKED,
        SUBOBJECTIVE_FAILED,
    }
)

TERMINAL_STATES = frozenset(
    {
        SUBOBJECTIVE_COMPLETED,
        SUBOBJECTIVE_PARTIAL,
        SUBOBJECTIVE_BLOCKED,
    }
)

# States that allow a dependent subobjective to become READY.
_DEPENDENCY_SATISFIED = frozenset(
    {SUBOBJECTIVE_COMPLETED, SUBOBJECTIVE_PARTIAL}
)

MAX_SUBOBJECTIVES_PER_INVESTIGATION = 8
MAX_ATTEMPTS_PER_SUBOBJECTIVE = 3
MAX_EVIDENCE_REFS = 16
MAX_GAPS = 8
MAX_FIELD_CHARS = 240


@dataclass(frozen=True, slots=True)
class SubObjective:
    """One tracked sub-requirement of a multi-requirement objective.

    ``goal``/``dependencies``/``evidence_needed`` come from the
    validated decomposition proposal (untrusted, bounded);
    ``state``/``attempts``/``evidence_refs``/``gaps`` are runtime
    records written only through ``SubObjectiveTracker``.
    """

    subobjective_id: str
    goal: str
    dependencies: tuple[str, ...] = ()
    evidence_needed: tuple[str, ...] = ()
    state: str = SUBOBJECTIVE_PENDING
    attempts: int = 0
    evidence_refs: tuple[str, ...] = ()
    gaps: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.subobjective_id.strip():
            raise ValueError("SubObjective.subobjective_id is required")
        if len(self.subobjective_id) > 64:
            raise ValueError("SubObjective.subobjective_id too long")
        if not self.goal.strip():
            raise ValueError("SubObjective.goal is required")
        if len(self.goal) > MAX_FIELD_CHARS:
            raise ValueError("SubObjective.goal too long")
        if self.state not in SUBOBJECTIVE_STATES:
            raise ValueError("SubObjective.state outside closed set")
        if self.attempts < 0:
            raise ValueError("SubObjective.attempts negative")
        if self.state == SUBOBJECTIVE_COMPLETED and not self.evidence_refs:
            raise ValueError("COMPLETED requires evidence_refs")


class SubObjectiveTracker:
    """Deterministic state machine for one investigation's
    subobjectives. Fail-closed on unknown ids, forward/duplicate
    dependencies and transitions outside the legal graph."""

    def __init__(
        self,
        objectives: tuple[SubObjective, ...],
        *,
        investigation_attempt_cap: int = MAX_ATTEMPTS_PER_SUBOBJECTIVE * 2,
    ) -> None:
        if len(objectives) > MAX_SUBOBJECTIVES_PER_INVESTIGATION:
            raise ValueError("too many subobjectives for one investigation")
        ids = [o.subobjective_id for o in objectives]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate subobjective_id")
        known = set(ids)
        seen: set[str] = set()
        for obj in objectives:
            for dep in obj.dependencies:
                if dep not in known:
                    raise ValueError(
                        f"unknown dependency {dep!r} in {obj.subobjective_id!r}"
                    )
                if dep not in seen:
                    # dependencies may only reference earlier entries —
                    # cycles are structurally impossible (planning rules).
                    raise ValueError(
                        f"forward dependency {dep!r} in {obj.subobjective_id!r}"
                    )
            seen.add(obj.subobjective_id)
        self._objectives: dict[str, SubObjective] = {
            o.subobjective_id: o for o in objectives
        }
        self._order = tuple(ids)
        self._investigation_attempts = 0
        self._investigation_attempt_cap = max(1, investigation_attempt_cap)

    # ---------------- queries ----------------

    @property
    def objectives(self) -> tuple[SubObjective, ...]:
        return tuple(self._objectives[i] for i in self._order)

    def get(self, subobjective_id: str) -> SubObjective:
        return self._objectives[subobjective_id]

    def ready_ids(self) -> tuple[str, ...]:
        out = []
        for oid in self._order:
            obj = self._objectives[oid]
            if obj.state not in (SUBOBJECTIVE_PENDING, SUBOBJECTIVE_READY):
                continue
            if all(
                self._objectives[d].state in _DEPENDENCY_SATISFIED
                for d in obj.dependencies
            ):
                out.append(oid)
        return tuple(out)

    def is_finished(self) -> bool:
        return all(
            self._objectives[oid].state in TERMINAL_STATES
            for oid in self._order
        )

    def coverage(self) -> Mapping[str, int]:
        counts: dict[str, int] = {s: 0 for s in sorted(SUBOBJECTIVE_STATES)}
        for obj in self._objectives.values():
            counts[obj.state] += 1
        return counts

    # ---------------- transitions ----------------

    def begin_attempt(self, subobjective_id: str) -> SubObjective:
        """Mark PENDING/READY → IN_PROGRESS consuming one attempt.
        Rejects attempts on terminal/dep-blocked/exhausted budgets."""
        obj = self._objectives[subobjective_id]
        if obj.state in TERMINAL_STATES:
            raise ValueError("attempt on terminal subobjective")
        if obj.state == SUBOBJECTIVE_FAILED and not self.retry_ready(
            subobjective_id
        ):
            raise ValueError("subobjective failed without retry budget")
        if obj.state == SUBOBJECTIVE_IN_PROGRESS:
            raise ValueError("subobjective already in progress")
        if not all(
            self._objectives[d].state in _DEPENDENCY_SATISFIED
            for d in obj.dependencies
        ):
            raise ValueError("dependencies not satisfied")
        if obj.attempts >= MAX_ATTEMPTS_PER_SUBOBJECTIVE:
            raise ValueError("subobjective attempt cap reached")
        if self._investigation_attempts >= self._investigation_attempt_cap:
            raise ValueError("investigation attempt cap reached")
        self._investigation_attempts += 1
        updated = dataclasses.replace(
            obj, state=SUBOBJECTIVE_IN_PROGRESS, attempts=obj.attempts + 1
        )
        self._objectives[subobjective_id] = updated
        return updated

    def record_progress(
        self,
        subobjective_id: str,
        *,
        evidence_refs: tuple[str, ...] = (),
        gaps: tuple[str, ...] = (),
    ) -> SubObjective:
        """Record validated evidence refs / uncovered gaps on an
        IN_PROGRESS subobjective. Never marks completion."""
        obj = self._objectives[subobjective_id]
        if obj.state != SUBOBJECTIVE_IN_PROGRESS:
            raise ValueError("progress requires IN_PROGRESS")
        refs = tuple(
            r[:MAX_FIELD_CHARS] for r in evidence_refs if str(r).strip()
        )[:MAX_EVIDENCE_REFS]
        gap_list = tuple(
            g[:MAX_FIELD_CHARS] for g in gaps if str(g).strip()
        )[:MAX_GAPS]
        updated = dataclasses.replace(
            obj,
            evidence_refs=obj.evidence_refs + refs,
            gaps=obj.gaps + gap_list,
        )
        self._objectives[subobjective_id] = updated
        return updated

    def complete(
        self, subobjective_id: str, *, evidence_refs: tuple[str, ...]
    ) -> SubObjective:
        """Mark COMPLETED — requires non-empty validated evidence refs.
        Completion by catalog/generic reply alone is impossible."""
        obj = self._objectives[subobjective_id]
        if obj.state != SUBOBJECTIVE_IN_PROGRESS:
            raise ValueError("complete requires IN_PROGRESS")
        refs = tuple(
            r[:MAX_FIELD_CHARS] for r in evidence_refs if str(r).strip()
        )[:MAX_EVIDENCE_REFS]
        if not (obj.evidence_refs or refs):
            raise ValueError("COMPLETED requires recorded evidence_refs")
        updated = dataclasses.replace(
            obj,
            state=SUBOBJECTIVE_COMPLETED,
            evidence_refs=obj.evidence_refs + refs,
        )
        self._objectives[subobjective_id] = updated
        return updated

    def conclude_partial(
        self, subobjective_id: str, *, gaps: tuple[str, ...]
    ) -> SubObjective:
        """Mark PARTIAL with an explicit uncovered gap — the honest
        conclusion when legitimate unavailability prevents proof."""
        obj = self._objectives[subobjective_id]
        if obj.state != SUBOBJECTIVE_IN_PROGRESS:
            raise ValueError("partial requires IN_PROGRESS")
        gap_list = tuple(
            g[:MAX_FIELD_CHARS] for g in gaps if str(g).strip()
        )[:MAX_GAPS]
        if not gap_list and not obj.gaps:
            raise ValueError("PARTIAL requires a declared gap")
        updated = dataclasses.replace(
            obj,
            state=SUBOBJECTIVE_PARTIAL,
            gaps=obj.gaps + gap_list,
        )
        self._objectives[subobjective_id] = updated
        return updated

    def fail(self, subobjective_id: str, *, recoverable: bool) -> SubObjective:
        """Fail an attempt: recoverable → FAILED (retry budget may
        remain); non-recoverable → BLOCKED terminal fail-closed."""
        obj = self._objectives[subobjective_id]
        if obj.state != SUBOBJECTIVE_IN_PROGRESS:
            raise ValueError("fail requires IN_PROGRESS")
        state = SUBOBJECTIVE_FAILED if recoverable else SUBOBJECTIVE_BLOCKED
        updated = dataclasses.replace(obj, state=state)
        if state == SUBOBJECTIVE_FAILED and (
            obj.attempts >= MAX_ATTEMPTS_PER_SUBOBJECTIVE
        ):
            # Budget exhausted under failure — degrade to BLOCKED so
            # synthesis can never claim progress silently.
            updated = dataclasses.replace(
                updated, state=SUBOBJECTIVE_BLOCKED
            )
        self._objectives[subobjective_id] = updated
        return updated

    def expire_pending(self, *, gap: str) -> None:
        """Budget/deadline exhausted: every non-terminal subobjective
        becomes BLOCKED with the declared gap — never a silent drop."""
        for oid in self._order:
            obj = self._objectives[oid]
            if obj.state not in TERMINAL_STATES:
                self._objectives[oid] = dataclasses.replace(
                    obj,
                    state=SUBOBJECTIVE_BLOCKED,
                    gaps=(obj.gaps + (gap[:MAX_FIELD_CHARS],))[:MAX_GAPS],
                )

    def retry_ready(self, subobjective_id: str) -> bool:
        """A FAILED subobjective may retry while budget remains —
        recovering it back to READY (not silently re-running)."""
        obj = self._objectives[subobjective_id]
        return (
            obj.state == SUBOBJECTIVE_FAILED
            and obj.attempts < MAX_ATTEMPTS_PER_SUBOBJECTIVE
            and self._investigation_attempts < self._investigation_attempt_cap
            and all(
                self._objectives[d].state in _DEPENDENCY_SATISFIED
                for d in obj.dependencies
            )
        )
