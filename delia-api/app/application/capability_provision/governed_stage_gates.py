"""Shared governed-stage gate contract — doc 195.

Narrow Application-owned Protocol describing the governed primitives
a `SupportsGovernedCapabilityAttempt` implementation may consume for
sequencing: admission, typed confirmation, live-surface listing,
surface inquiry, the governed owner path and the bounded attempt
runner.

It exists so an alternative engine (e.g. the LangGraph infrastructure
adapter) can depend on a stable application contract instead of the
concrete `OperationalCapabilityOrchestrator` class. The primitives'
single implementation remains that orchestrator — this Protocol is
structural typing only; it carries no second implementation and no
new authority.

Residual note (accepted, doc 195 §F2): the sole runtime provider of
these gates today is Engine A itself. Splitting them into a separate
collaborator would require migrating a large coupled method set with
no behavior change to show for it — deferred to a bounded task only
if a genuine third consumer or owner-split need appears.
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
    ) -> GovernedCapabilityAttempt:
        """Post-admission governed owner path: surface → selection →
        invoke → judgment → recovery → synthesis."""
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
