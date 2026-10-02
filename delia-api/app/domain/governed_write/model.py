"""Governed-write semantic model — provider-neutral orchestration.

ARCH-DRIFT-MCP-FULL-CAPABILITY-ORCHESTRATION-03 (ledger §6.126): the
static DÉLIA-owned write-binding registry (``GovernedWriteBinding`` /
``GOVERNED_WRITE_BINDINGS`` / ``write_binding_for``) is SUPERSEDED — the
specialist owns its capability surface and DÉLIA keeps no MCP capability
catalog, pair registry, or per-capability enable flags. What remains
DÉLIA-owned is generic write *governance*: preview, structured
confirmation, gate decision, outcome projection and audit — all bound
to the live capability identity (``capability_ref`` =
``specialist_id.remote_name``), never to a local registry row.

Permanent semantics:

- A preview/confirmation/decision/audit record never grants business
  authorization. ``authorizes_act()`` is always False.
- ``proposal_ref`` is an opaque owner-issued proposal handle. DÉLIA must
  never decode, re-sign, mutate, reinterpret, or invent it; only a
  non-reversible digest may be used for correlation/audit.
- Confirmation means USER_CONFIRMED_EXACT_PREVIEW only — it is never
  Core/Domain AuthZ and never ACT authorization.
- The strongest DÉLIA-side decision is READY_FOR_LIVE_REVALIDATION —
  never ACT_AUTHORIZED. Live Core/Domain revalidation happens at the
  ACT call, enforced by the owner.
- A technical 2xx is never a business VERIFIED outcome; only the owner's
  authoritative postcondition verification may project VERIFIED.

Canonical semantics: 16 C5 gates, 17, 21, 57, 60; ledger §6.106/§6.126.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from app.domain.evidence.model import SourceRef


class ProposalReadiness(str, Enum):
    """Bounded readiness of an owner PREPARE result as projected by DÉLIA.

    Never inferred from natural-language text; missing mandatory
    governance fields fail closed to INVALID/UNKNOWN.
    """

    READY = "READY"
    NOT_READY = "NOT_READY"
    EXPIRED = "EXPIRED"
    INVALID = "INVALID"
    UNKNOWN = "UNKNOWN"


class ConfirmationDecision(str, Enum):
    """Explicit structured decision in a confirmation event."""

    CONFIRM = "CONFIRM"
    REJECT = "REJECT"


class ConfirmationState(str, Enum):
    """Bounded state of a confirmation binding."""

    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    INVALIDATED = "INVALIDATED"


class ConfirmationReason(str, Enum):
    """Deterministic reason codes for confirmation binding outcomes."""

    EXACT_PREVIEW_CONFIRMED = "exact_preview_confirmed"
    USER_REJECTED = "user_rejected"
    ACTOR_MISMATCH = "actor_mismatch"
    SESSION_MISMATCH = "session_mismatch"
    BINDING_MISMATCH = "binding_mismatch"
    PROPOSAL_MISMATCH = "proposal_mismatch"
    PREVIEW_CHANGED = "preview_changed"
    PROPOSAL_EXPIRED = "proposal_expired"
    PROPOSAL_NOT_READY = "proposal_not_ready"


class WriteGateStatus(str, Enum):
    """Bounded decision of whether a write may continue toward an ACT
    attempt. No state authorizes execution."""

    BLOCKED = "BLOCKED"
    REQUIRES_CONFIRMATION = "REQUIRES_CONFIRMATION"
    READY_FOR_LIVE_REVALIDATION = "READY_FOR_LIVE_REVALIDATION"
    REJECTED = "REJECTED"


class WriteGateReason(str, Enum):
    """Bounded reason codes for the write continuation decision."""

    CAPABILITY_NOT_LIVE = "capability_not_live"
    PROPOSAL_NOT_READY = "proposal_not_ready"
    PROPOSAL_EXPIRED = "proposal_expired"
    CONFIRMATION_MISSING = "confirmation_missing"
    CONFIRMATION_MISMATCH = "confirmation_mismatch"
    USER_REJECTED = "user_rejected"
    LIVE_AUTHZ_REQUIRED = "live_authz_required"
    DOMAIN_REVALIDATION_REQUIRED = "domain_revalidation_required"


class WriteOutcomeStatus(str, Enum):
    """Truthful classification of an owner ACT result."""

    EXECUTION_REPORTED = "EXECUTION_REPORTED"
    VERIFIED = "VERIFIED"
    OUTCOME_VERIFICATION_FAILED = "OUTCOME_VERIFICATION_FAILED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


class WriteAuditStage(str, Enum):
    """Bounded lifecycle stages for a governed-write decision record."""

    PREPARE_PROJECTED = "PREPARE_PROJECTED"
    CONFIRMATION_BOUND = "CONFIRMATION_BOUND"
    DECISION_GATE = "DECISION_GATE"
    ACT_ATTEMPT = "ACT_ATTEMPT"
    OUTCOME_VERIFIED = "OUTCOME_VERIFIED"


@dataclass(frozen=True, slots=True)
class WriteProposalPreview:
    """Bounded provider-neutral projection of an owner PREPARE result.

    ``capability_ref`` is the live capability identity
    (``specialist_id.remote_name``) — a correlation reference to the
    capability that produced the preview, not a registry lookup.

    ``proposal_ref`` is the opaque owner handle kept only so a future
    authorized ACT call can pass it back verbatim to the owner. It is
    security-sensitive: never logged raw — audit/correlation uses
    ``proposal_digest()`` only. Business fingerprint/TOCTOU/idempotency
    remain owner-owned; DÉLIA does not reimplement them.
    """

    capability_ref: str
    owner_capability: str
    proposal_ref: str
    readiness: ProposalReadiness
    specialist_id: str
    correlation_id: str
    observed_at: str
    resource_ref: str | None = None
    exact_change: Mapping[str, Any] | None = None
    validation_summary: Mapping[str, Any] | None = None
    consequential_impact: Mapping[str, Any] | None = None
    confirmation_requirement: Mapping[str, Any] | None = None
    expected_postcondition: Mapping[str, Any] | None = None
    expires_at_epoch: float | None = None
    limitations: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        for name in (
            "capability_ref",
            "owner_capability",
            "specialist_id",
            "correlation_id",
            "observed_at",
        ):
            if not str(getattr(self, name) or "").strip():
                raise ValueError(f"WriteProposalPreview.{name} is required")
        # ``proposal_ref`` may be absent on INVALID projections (the
        # owner returned no usable handle). A READY preview can never
        # exist without the opaque handle needed for a future commit.
        if self.readiness is ProposalReadiness.READY and not str(
            self.proposal_ref or ""
        ).strip():
            raise ValueError(
                "WriteProposalPreview.proposal_ref is required when READY"
            )

    def authorizes_act(self) -> bool:
        return False

    def grants_authorization(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class StructuredConfirmation:
    """Explicit structured confirmation event — future UI/runtime input.

    This is the ONLY admissible confirmation shape. Arbitrary chat text
    ("sim"), model output, or a handle pasted as ordinary text never
    constitute a confirmation.
    """

    actor_user_id: str
    session_id: str
    capability_ref: str
    proposal_digest: str
    preview_fingerprint: str
    decision: ConfirmationDecision
    occurred_at_epoch: float

    def __post_init__(self) -> None:
        for name in (
            "actor_user_id",
            "session_id",
            "capability_ref",
            "proposal_digest",
            "preview_fingerprint",
        ):
            if not str(getattr(self, name) or "").strip():
                raise ValueError(f"StructuredConfirmation.{name} is required")

    def authorizes_act(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class ConfirmationRecord:
    """Result of binding a StructuredConfirmation to an exact preview.

    CONFIRMED means USER_CONFIRMED_EXACT_PREVIEW=YES only — it never
    means Core AuthZ, Domain AuthZ, ACT_ALLOWED, or execution success.
    """

    state: ConfirmationState
    reason_codes: tuple[ConfirmationReason, ...] = ()
    confirmation: StructuredConfirmation | None = None

    def authorizes_act(self) -> bool:
        return False

    def grants_authorization(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class WriteGateDecision:
    """Decision on whether a governed write may continue.

    READY_FOR_LIVE_REVALIDATION is the strongest possible state and still
    requires live Core + Domain authorization at the ACT request —
    ``live_core_authz_required`` and ``domain_revalidation_required`` are
    always True on that state by construction.
    """

    status: WriteGateStatus
    reason_codes: tuple[WriteGateReason, ...] = ()
    capability_ref: str | None = None
    live_core_authz_required: bool = False
    domain_revalidation_required: bool = False

    def __post_init__(self) -> None:
        if self.status is WriteGateStatus.READY_FOR_LIVE_REVALIDATION:
            if not (
                self.live_core_authz_required
                and self.domain_revalidation_required
            ):
                raise ValueError(
                    "READY_FOR_LIVE_REVALIDATION requires live_core_authz_"
                    "required and domain_revalidation_required"
                )

    def authorizes_act(self) -> bool:
        return False

    def grants_authorization(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class WriteOutcomeProjection:
    """Bounded provider-neutral projection of an owner ACT result.

    VERIFIED requires owner-authoritative postcondition evidence; a
    technical transport success alone can only produce
    EXECUTION_REPORTED/OUTCOME_VERIFICATION_FAILED — never VERIFIED.
    """

    status: WriteOutcomeStatus
    capability_ref: str
    specialist_id: str
    owner_capability: str
    correlation_id: str
    occurred_at: str
    verified: bool = False
    source_refs: tuple[SourceRef, ...] = ()
    postcondition_summary: Mapping[str, Any] | None = None
    limitations: tuple[str, ...] = field(default_factory=tuple)

    def is_fact(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class WriteDecisionAuditRecord:
    """Audit data contract for governed-write decisions.

    Correlation-only references: proposal identity is carried as a
    non-reversible digest, never as the raw handle. The record must never
    contain tokens, secrets, authorization headers, provider payloads,
    prompts, or chain-of-thought.
    """

    audit_id: str
    correlation_id: str
    actor_user_id: str
    capability_ref: str
    specialist_id: str
    owner_capability: str
    stage: WriteAuditStage
    decision: str
    occurred_at: str
    proposal_digest: str | None = None
    preview_fingerprint: str | None = None
    confirmation_state: ConfirmationState | None = None
    outcome_status: WriteOutcomeStatus | None = None
    reason_codes: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "audit_id",
            "correlation_id",
            "actor_user_id",
            "capability_ref",
            "specialist_id",
            "owner_capability",
            "decision",
            "occurred_at",
        ):
            if not str(getattr(self, name) or "").strip():
                raise ValueError(f"WriteDecisionAuditRecord.{name} is required")

    def authorizes_act(self) -> bool:
        return False

    def to_dict(self) -> dict[str, Any]:
        """Deterministic bounded serialization — digest refs only."""
        return {
            "audit_id": self.audit_id,
            "correlation_id": self.correlation_id,
            "actor_user_id": self.actor_user_id,
            "capability_ref": self.capability_ref,
            "specialist_id": self.specialist_id,
            "owner_capability": self.owner_capability,
            "stage": self.stage.value,
            "decision": self.decision,
            "occurred_at": self.occurred_at,
            "proposal_digest": self.proposal_digest,
            "preview_fingerprint": self.preview_fingerprint,
            "confirmation_state": (
                self.confirmation_state.value
                if self.confirmation_state is not None
                else None
            ),
            "outcome_status": (
                self.outcome_status.value
                if self.outcome_status is not None
                else None
            ),
            "reason_codes": list(self.reason_codes),
            "limitations": list(self.limitations),
        }
