"""C3-T8 conversation/session interaction foundation value objects.

InteractionSession + InteractionTurn model a bounded interaction surface
only. session != authorization; session != Personal Memory;
conversation history != source of truth; interaction result != FACT;
planned PREPARE/ACT/VERIFY remain descriptive (no execution).

Canonical semantics: 16 C3 DAG, 21 §8, 50 product boundary, 17.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.domain.decision_path.model import DecisionPath, DecisionPathResult
from app.domain.evidence.model import (
    EntityRef,
    EpistemicClass,
    EvidenceRef,
    SourceRef,
    UserRef,
)
from app.domain.planning.model import PlanCandidate


class SessionStatus(str, Enum):
    """Minimal lifecycle. Retention/expiration are separate concerns."""

    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"  # interaction context inactive; != revoked AuthZ


class TurnKind(str, Enum):
    """DÉLIA interaction semantics — not provider roles (system/tool)."""

    USER_INPUT = "USER_INPUT"
    DELIA_RESULT = "DELIA_RESULT"


class GroundingStatus(str, Enum):
    """C4-MCP-GOVERNED-READS-01: whether the result is backed by a
    governed authoritative DELPI source read.

    GROUNDED != FACT — grounding states provenance, not epistemic
    truth elevation. NON_GROUNDED results must not claim current DELPI
    data.
    """

    GROUNDED = "GROUNDED"
    NON_GROUNDED = "NON_GROUNDED"


class InteractionValidationCode(str, Enum):
    """Bounded deterministic validation codes — never CoT."""

    SESSION_CLOSED = "session_closed"
    CROSS_SESSION_REFERENCE = "cross_session_reference"
    EMPTY_CONTENT = "empty_content"


@dataclass(frozen=True, slots=True)
class SessionContext:
    """Bounded typed context for a session. Never an arbitrary bag.

    All references are descriptive: entity_refs are typed business refs,
    not resolutions; active_plan is a PlanCandidate, not authorization;
    Portal-published context enters only through typed ref fields.
    """

    entity_refs: tuple[EntityRef, ...] = ()
    evidence_refs: tuple[EvidenceRef, ...] = ()
    source_refs: tuple[SourceRef, ...] = ()
    active_intent: str | None = None
    selected_decision_path: DecisionPath | None = None
    active_plan: PlanCandidate | None = None

    def grants_authorization(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class InteractionSession:
    """DÉLIA-owned bounded session identity + context.

    session exists != user authorized. actor_ref is identity correlation
    only, never a permission snapshot. No permission cache, no secrets,
    no credential fields.
    """

    session_id: str
    actor_ref: UserRef | None = None
    status: SessionStatus = SessionStatus.ACTIVE
    started_at: str = ""
    last_interaction_at: str | None = None
    context: SessionContext = SessionContext()

    def __post_init__(self) -> None:
        if not self.session_id.strip():
            raise ValueError("InteractionSession.session_id is required")
        if not self.started_at.strip():
            raise ValueError("InteractionSession.started_at is required")
        if self.actor_ref is not None and not isinstance(
            self.actor_ref, UserRef
        ):
            raise ValueError(
                "InteractionSession.actor_ref must be canonical UserRef"
            )
        if not isinstance(self.status, SessionStatus):
            raise ValueError(
                "InteractionSession.status must be SessionStatus"
            )

    def grants_authorization(self) -> bool:
        return False

    def is_personal_memory(self) -> bool:
        return False

    def is_organizational_knowledge(self) -> bool:
        return False

    def is_source_of_truth(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class InteractionTurn:
    """One bounded turn. User input is untrusted data; DÉLIA result is
    not FACT by default and carries explicit epistemic classification."""

    turn_id: str
    session_id: str
    kind: TurnKind
    content: str
    occurred_at: str
    epistemic_class: EpistemicClass | None = None
    evidence_refs: tuple[EvidenceRef, ...] = ()
    source_refs: tuple[SourceRef, ...] = ()
    decision_path_result: DecisionPathResult | None = None
    plan_candidate: PlanCandidate | None = None
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name, value in (
            ("turn_id", self.turn_id),
            ("session_id", self.session_id),
            ("occurred_at", self.occurred_at),
        ):
            if not value.strip():
                raise ValueError(f"InteractionTurn.{name} is required")
        if not isinstance(self.kind, TurnKind):
            raise ValueError("InteractionTurn.kind must be TurnKind")
        if self.epistemic_class is not None and not isinstance(
            self.epistemic_class, EpistemicClass
        ):
            raise ValueError(
                "InteractionTurn.epistemic_class must be EpistemicClass"
            )
        if self.epistemic_class is EpistemicClass.FACT:
            raise ValueError(
                "InteractionTurn.epistemic_class=FACT requires a qualified-Fact "
                "contract that C3-T8 does not provide; fail closed"
            )
        if (
            self.kind is TurnKind.USER_INPUT
            and self.epistemic_class is not None
            and self.epistemic_class is not EpistemicClass.OBSERVATION
        ):
            raise ValueError(
                "USER_INPUT epistemic_class must be None or OBSERVATION; "
                "untrusted input cannot self-classify above observation"
            )

    def grants_authorization(self) -> bool:
        return False

    def is_execution(self) -> bool:
        return False

    def is_authoritative_fact(self) -> bool:
        return False

    def is_personal_memory(self) -> bool:
        return False

    def is_organizational_knowledge(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class InteractionValidationResult:
    """Bounded deterministic validation outcome — not an execution status."""

    valid: bool
    error_codes: tuple[InteractionValidationCode, ...] = ()
    limitations: tuple[str, ...] = ()

    def grants_authorization(self) -> bool:
        return False
