"""Engine B — LangGraph sequencing adapter over shared governed gates.

DELIA-C3-PLUGGABLE-ORCHESTRATION-LANGGRAPH-ENGINE-B-01 + isolation
remediation (docs 192/193/194/195) — experimental, LOCAL EVALUATION
ONLY. Infrastructure adapter: this module is the ONLY place LangGraph
may be imported. Never wired into the production composition root;
the dependency is an opt-in eval fixture, not a runtime requirement.

Layer position:

    Application contract   SupportsGovernedCapabilityAttempt
    Application contract   SupportsGovernedStageGates
            ^                       ^
            |                       | (implements, structurally)
    THIS ADAPTER ──────────── LangGraph SDK (framework, infra-only)

What this engine is:
  a ``SupportsGovernedCapabilityAttempt`` implementation whose stage
  SEQUENCING is expressed as a LangGraph ``StateGraph`` — typed state,
  real nodes, conditional edges — routing between confirmation,
  admission classes, surface inquiry and the governed owner path.

What this engine is NOT:
  - not a wrapper: ``OperationalCapabilityOrchestrator.attempt`` and
    ``._attempt`` are never called; the complete flow is re-sequenced
    by the graph (proven by the non-delegation spy test).
  - not coupled to Engine A: the adapter never imports or constructs
    ``OperationalCapabilityOrchestrator`` — it receives the shared
    governed primitives through the narrow
    ``SupportsGovernedStageGates`` application contract (injected).
    Residual: the contract's sole provider today is Engine A itself;
    ``_emit_activity`` is a shared module-level application helper.
  - not a second authority: every governed gate (admission, selection
    validation, candidate binding, invoke, judgment, write governance,
    budgets, cancellation, provenance) executes inside the SAME
    methods the gates provider runs — the engine supplies ordering
    only.
  - not a planner/tool-calling agent: no LangGraph tools, agents,
    handoffs, checkpointing or model access are used — the framework
    provides the graph runtime exclusively (FRAMEWORK_ROLE=
    STAGE_SEQUENCING_ONLY).

Graph (v1 mirrors the governed order for A/B comparability; the
sequencing variable lives in the edges, not in duplicated gates):

    START -> preflight --+--> confirmation -> END
                         |
                         +--> admission --+--> surface_inquiry -> END
                                          +--> conversational -> END
                                          +--> owner_path -> END
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Mapping, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.application.capability_provision.governed_stage_gates import (
    SupportsGovernedStageGates,
)
from app.application.capability_provision.orchestration import (
    _emit_activity,
)
from app.application.interaction.activity import (
    ActivityEventSink,
    ActivityPhase,
)
from app.application.interaction.capability_attempt import (
    EARLY_CONVERSATIONAL_ADMISSION,
    OWNER_PATH_UNBOUND,
    GovernedCapabilityAttempt,
    GovernedCapabilityStatus,
)
from app.application.interaction.turn_budget import TurnDeadline
from app.application.interaction.workspace_context import WorkspaceContext
from app.application.model_invocation.contracts import (
    ConversationContextTurn,
)

_logger = logging.getLogger(__name__)


class _GovernedTurnState(TypedDict, total=False):
    """Bounded per-attempt graph state. Every field is either a
    contract input, a stage decision produced by a governed primitive,
    or the terminal attempt — no free-form framework state."""

    input_text: str
    correlation: str
    actor_user_id: str | None
    session_id: str | None
    confirmation: Mapping[str, Any] | None
    workspace_context: WorkspaceContext | None
    prior_turns: tuple[ConversationContextTurn, ...]
    prepare_only: bool
    deadline: TurnDeadline
    admission_class: str | None
    admission_owner_required: bool
    attempt: GovernedCapabilityAttempt
    trace: list[str]


class LangGraphCapabilityOrchestrator:
    """``SupportsGovernedCapabilityAttempt`` via a LangGraph graph.

    The shared governed primitives arrive injected as the
    ``SupportsGovernedStageGates`` application contract — the adapter
    never learns which class provides them. Composition (today: an
    ``OperationalCapabilityOrchestrator`` instance built with the
    production-identical providers/model/budgets/instructions) is the
    caller's concern — the test harness and any future wiring decide
    which gates provider to hand over.
    """

    def __init__(self, gates: SupportsGovernedStageGates) -> None:
        # Shared governed primitives — the SAME gates Engine A runs;
        # the engine calls its stage-phase methods, never attempt()
        # or _attempt() flow entrypoints on any engine.
        self._gates = gates
        self._compiled_graph: CompiledStateGraph = self._build_graph()
        # Evaluation observability only — the executed node list of
        # the most recent invocation (proves real sequencing in the
        # conformance suite). Single-threaded local eval only.
        self.last_node_trace: list[str] = []

    # ---------------- graph construction ----------------

    def _build_graph(self) -> CompiledStateGraph:
        graph = StateGraph(_GovernedTurnState)
        graph.add_node("preflight", self._preflight_node)
        graph.add_node("admission", self._admission_node)
        graph.add_node("confirmation", self._confirmation_node)
        graph.add_node("surface_inquiry", self._surface_inquiry_node)
        graph.add_node("conversational", self._conversational_node)
        graph.add_node("owner_path", self._owner_path_node)

        graph.add_edge(START, "preflight")
        graph.add_conditional_edges(
            "preflight",
            self._route_after_preflight,
            {"confirmation": "confirmation", "admission": "admission"},
        )
        graph.add_conditional_edges(
            "admission",
            self._route_after_admission,
            {
                "surface_inquiry": "surface_inquiry",
                "conversational": "conversational",
                "owner_path": "owner_path",
            },
        )
        graph.add_edge("confirmation", END)
        graph.add_edge("surface_inquiry", END)
        graph.add_edge("conversational", END)
        graph.add_edge("owner_path", END)
        return graph.compile()

    # ---------------- routing (deterministic, not model-owned) -----

    @staticmethod
    def _route_after_preflight(state: _GovernedTurnState) -> str:
        return (
            "confirmation"
            if state.get("confirmation") is not None
            else "admission"
        )

    @staticmethod
    def _route_after_admission(state: _GovernedTurnState) -> str:
        admission_class = state.get("admission_class")
        if admission_class == "surface_inquiry":
            return "surface_inquiry"
        if admission_class is not None:
            return "conversational"
        return "owner_path"

    @staticmethod
    def _traced(
        state: _GovernedTurnState, name: str
    ) -> dict[str, list[str]]:
        return {"trace": list(state.get("trace") or []) + [name]}

    # ---------------- nodes: ordering only — gates live in _gates --

    def _preflight_node(
        self, state: _GovernedTurnState
    ) -> dict[str, Any]:
        # Same terminal guards as Engine A's attempt entry: exhausted
        # budget/cancel raise the typed exceptions the shared runner
        # maps to PROCESSING_TIMEOUT.
        state["deadline"].check("turn_start")
        _emit_activity(
            phase=ActivityPhase.CONTEXTUALIZING,
            correlation=state["correlation"],
        )
        return self._traced(state, "preflight")

    def _admission_node(
        self, state: _GovernedTurnState
    ) -> dict[str, Any]:
        admission_class, owner_required = (
            self._gates._admit_conversational_turn(
                state["input_text"],
                workspace_context=state.get("workspace_context"),
                prior_turns=state.get("prior_turns") or (),
                correlation=state["correlation"],
                deadline=state["deadline"],
            )
        )
        return {
            **self._traced(state, "admission"),
            "admission_class": admission_class,
            "admission_owner_required": owner_required,
        }

    def _confirmation_node(
        self, state: _GovernedTurnState
    ) -> dict[str, Any]:
        attempt = self._gates._attempt_confirmation(
            state["confirmation"],
            actor_user_id=state.get("actor_user_id"),
            correlation=state["correlation"],
            prepare_only=state["prepare_only"],
            deadline=state["deadline"],
        )
        return {**self._traced(state, "confirmation"), "attempt": attempt}

    def _surface_inquiry_node(
        self, state: _GovernedTurnState
    ) -> dict[str, Any]:
        groups, failures = self._gates._groups(
            state["correlation"], state["deadline"]
        )
        attempt = self._gates._surface_inquiry_attempt(
            groups, failures, state["correlation"]
        )
        return {
            **self._traced(state, "surface_inquiry"),
            "attempt": attempt,
        }

    def _conversational_node(
        self, state: _GovernedTurnState
    ) -> dict[str, Any]:
        _logger.info(
            "orchestration engine=langgraph stage=interaction_admission "
            "decision=conversational class=%s correlation_id=%s",
            state.get("admission_class"),
            state["correlation"],
        )
        attempt = GovernedCapabilityAttempt(
            status=GovernedCapabilityStatus.NOT_APPLICABLE,
            correlation_id=state["correlation"],
            admission_outcome=EARLY_CONVERSATIONAL_ADMISSION,
        )
        return {
            **self._traced(state, "conversational"),
            "attempt": attempt,
        }

    def _owner_path_node(
        self, state: _GovernedTurnState
    ) -> dict[str, Any]:
        unbound_outcome = (
            OWNER_PATH_UNBOUND
            if state.get("admission_owner_required")
            else None
        )
        attempt = self._gates._governed_owner_path(
            state["input_text"],
            correlation=state["correlation"],
            actor_user_id=state.get("actor_user_id"),
            session_id=state.get("session_id"),
            workspace_context=state.get("workspace_context"),
            prior_turns=state.get("prior_turns") or (),
            prepare_only=state["prepare_only"],
            unbound_outcome=unbound_outcome,
            deadline=state["deadline"],
        )
        return {**self._traced(state, "owner_path"), "attempt": attempt}

    # ---------------- contract entrypoint ----------------

    def attempt(
        self,
        input_text: str,
        *,
        correlation_id: str | None = None,
        actor_user_id: str | None = None,
        session_id: str | None = None,
        confirmation: Mapping[str, Any] | None = None,
        workspace_context: WorkspaceContext | None = None,
        prior_turns: tuple[ConversationContextTurn, ...] = (),
        max_execution_stage: str | None = None,
        turn_deadline: TurnDeadline | None = None,
        activity_sink: ActivityEventSink | None = None,
        cancel_check: Callable[[], bool] | None = None,
    ) -> GovernedCapabilityAttempt:
        def attempt_once(
            correlation: str, deadline: TurnDeadline
        ) -> GovernedCapabilityAttempt:
            state: _GovernedTurnState = {
                "input_text": input_text,
                "correlation": correlation,
                "actor_user_id": actor_user_id,
                "session_id": session_id,
                "confirmation": confirmation,
                "workspace_context": workspace_context,
                "prior_turns": prior_turns,
                "prepare_only": max_execution_stage == "prepare",
                "deadline": deadline,
                "trace": [],
            }
            final = self._compiled_graph.invoke(state)
            self.last_node_trace = list(final.get("trace") or [])
            return final["attempt"]

        # Shared governed runner — identical budget anchoring,
        # request-scoped context binding, bounded resume and terminal
        # mapping as Engine A; only the single-attempt callable differs.
        return self._gates._run_governed_attempts(
            attempt_once,
            correlation_id=correlation_id,
            confirmation=confirmation,
            activity_sink=activity_sink,
            cancel_check=cancel_check,
            turn_deadline=turn_deadline,
        )
