"""Shared governed-stage gate contract — docs 195 / 231.

Narrow Application-owned Protocol describing the governed primitives
a `SupportsGovernedCapabilityAttempt` implementation may consume for
sequencing: admission, typed confirmation, live-surface listing,
surface inquiry, semantic tool catalog/invoke, the governed owner
path and the bounded attempt runner.

It exists so an infrastructure investigation runtime (Pydantic AI
adapter, historically LangGraph) can depend on a stable application
contract instead of the concrete `OperationalCapabilityOrchestrator`
class. The primitives' single implementation remains that
orchestrator — this Protocol is structural typing only; it carries no
second implementation and no new authority.

Residual note (accepted, doc 195 §F2 / retained doc 231): the sole
runtime provider of these gates today is the Application orchestrator
itself.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping, Protocol

from app.application.capability_provision.contracts import (
    CapabilityGroup,
)
from app.application.interaction.activity import ActivityEventSink
from app.application.interaction.capability_attempt import (
    GovernedCapabilityAttempt,
)
from app.application.interaction.turn_budget import TurnDeadline
from app.application.interaction.workspace_context import (
    WorkspaceContext,
)
from app.application.model_invocation.contracts import (
    ConversationContextTurn,
)


class SupportsGovernedStageGates(Protocol):
    """Governed stage primitives an orchestration engine may sequence.

    Every member is an invariant control (admission, confirmation,
    surface, owner path, attempt runner) — the sequencing *between*
    them is the engine's variable. An implementation of this protocol
    owns the gates' semantics; an engine owns their order.
    """

    def _admit_conversational_turn(
        self,
        input_text: str,
        *,
        workspace_context: WorkspaceContext | None,
        prior_turns: tuple[ConversationContextTurn, ...],
        correlation: str,
        deadline: TurnDeadline,
    ) -> tuple[str | None, bool]:
        """Classify the turn; returns (class | None, owner_required)."""
        ...

    def _attempt_confirmation(
        self,
        confirmation_payload: Mapping[str, Any],
        *,
        actor_user_id: str | None,
        correlation: str,
        prepare_only: bool = False,
        deadline: TurnDeadline | None = None,
    ) -> GovernedCapabilityAttempt:
        """Resume a pending owner proposal under typed confirmation."""
        ...

    def _groups(
        self,
        correlation: str,
        deadline: TurnDeadline | None = None,
    ) -> tuple[dict[str, CapabilityGroup], list[str]]:
        """Live capability surface from providers, with failures."""
        ...

    def _surface_inquiry_attempt(
        self,
        groups: Mapping[str, CapabilityGroup],
        failures: list[str],
        correlation: str,
    ) -> GovernedCapabilityAttempt:
        """Deterministic surface-inquiry answer attempt."""
        ...

    def _decompose_objective(
        self,
        input_text: str,
        *,
        correlation: str,
        workspace_context: WorkspaceContext | None,
        deadline: TurnDeadline,
        prior_turns: tuple[ConversationContextTurn, ...] = (),
        goal: Any | None = None,
    ) -> tuple["SubObjective", ...] | None:
        """Bounded decomposition proposal for a compound objective —
        validated fail-closed; ``None`` keeps the single-capability
        path. ``prior_turns``/``goal`` carry untrusted referent
        candidates and the validated semantic goal for referent
        binding — they never grant authority or evidence."""
        ...

    def _governed_owner_path(
        self,
        input_text: str,
        *,
        correlation: str,
        actor_user_id: str | None,
        session_id: str | None,
        workspace_context: WorkspaceContext | None,
        prior_turns: tuple[ConversationContextTurn, ...],
        prepare_only: bool,
        unbound_outcome: str | None,
        deadline: TurnDeadline,
        depth: int = 0,
    ) -> GovernedCapabilityAttempt:
        """Post-admission governed owner path: surface → selection →
        invoke → judgment → recovery → synthesis."""
        ...

    def _project_semantic_tool_catalog(
        self,
        *,
        correlation: str,
        deadline: TurnDeadline,
        actor_user_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Bounded live READ/DISCOVERY/ANALYSIS catalog for Agent tools.

        Metadata only — never authorization. Write classes omitted.
        ``actor_user_id`` is accepted for audit lineage; live surface
        already reflects Core AuthZ via ``_groups``.
        """
        ...

    def _governed_semantic_tool_invoke(
        self,
        *,
        capability_id: str,
        arguments: Mapping[str, Any],
        input_text: str,
        correlation: str,
        actor_user_id: str | None,
        session_id: str | None,
        workspace_context: WorkspaceContext | None,
        prior_turns: tuple[ConversationContextTurn, ...],
        prepare_only: bool,
        deadline: TurnDeadline,
    ) -> GovernedCapabilityAttempt:
        """Invoke one catalog capability under live AuthZ/schema gates.

        Discovery-first candidate binding stays inside Application.
        PREPARE/ACT are rejected on this tool surface.
        """
        ...

    def _accept_semantic_investigation_plan(
        self,
        *,
        goal_class: str,
        comparison_requested: bool,
        target_identities: object,
        evidence_needed: object = (),
        business_subject: str | None = None,
        correlation: str,
    ) -> object | None:
        """Validate Agent-declared typed investigation plan.

        Semantic proposal only — never authorization. Returns None when
        the declaration is invalid.
        """
        ...

    def _compose_observation_pair(
        self,
        *,
        left: GovernedCapabilityAttempt,
        right: GovernedCapabilityAttempt,
        correlation: str,
        workspace_context: WorkspaceContext | None,
        deadline: TurnDeadline,
    ) -> GovernedCapabilityAttempt | None:
        """Optional deterministic composition of two verified observations."""
        ...

    def _finalize_semantic_investigation(
        self,
        *,
        input_text: str,
        collected: tuple[GovernedCapabilityAttempt, ...],
        correlation: str,
        workspace_context: WorkspaceContext | None,
        deadline: TurnDeadline,
        unbound_outcome: str | None,
        plan: object | None = None,
        clarification_question: str | None = None,
        composed_attempt: GovernedCapabilityAttempt | None = None,
    ) -> GovernedCapabilityAttempt:
        """Goal-coverage finalizer for Agent-collected tool attempts.

        Clarification and agent-requested composition are first-class.
        Typed plan is optional for simple READ. Material obligations and
        authoritative identity binding remain Application-owned.
        """
        ...

    def _run_governed_attempts(
        self,
        attempt_once: Callable[
            [str, TurnDeadline], GovernedCapabilityAttempt
        ],
        *,
        correlation_id: str | None,
        confirmation: Mapping[str, Any] | None,
        activity_sink: ActivityEventSink | None,
        cancel_check: Callable[[], bool] | None,
        turn_deadline: TurnDeadline | None,
    ) -> GovernedCapabilityAttempt:
        """Bounded attempt runner: request-scoped context binding,
        monotonic budget anchoring, resume loop, terminal mapping."""
        ...
