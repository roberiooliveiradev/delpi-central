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
                                          +--> evidence_session
                                                    |
                                                owner_path -> END

H5 sequencing strategy (doc 196): ``evidence_session`` is the
graph-level decision point that records ``assessment_reuse`` in
typed state when ``recovery_reuse_enabled`` is set (B1); the
``owner_path`` node then binds the OPT-IN ambient
``_NATIVE_ASSESSMENT_LEDGER`` for that attempt — LangGraph executes
nodes in copied contexts, so the binding must live in the calling
node's context. With the flag off (B0 — the Task-03 framework
baseline) no ledger is bound and the runtime is byte-identical to
Engine A. The shared deterministic monotonic-reuse check inside the
governed recovery stage decides per call whether a prior
``foreign_evidence_required`` decision on the same target+goal is
still valid — reuse skips the redundant model call, never the
foreign consult, never a mandatory gate; every other premise
combination re-runs the assessment. Reuse/reassess events are
surfaced on the node trace for A/B attribution.
"""

from __future__ import annotations

import logging
import operator
from typing import Annotated, Any, Callable, Mapping, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Send

from app.application.capability_provision.governed_stage_gates import (
    SupportsGovernedStageGates,
)
from app.application.capability_provision.subobjective_tracker import (
    MAX_ATTEMPTS_PER_SUBOBJECTIVE,
    SUBOBJECTIVE_BLOCKED,
    SUBOBJECTIVE_COMPLETED,
    SUBOBJECTIVE_FAILED,
    SUBOBJECTIVE_PARTIAL,
    SubObjective,
    subobjective_outcome_transition,
)
from app.application.capability_provision.orchestration import (
    _emit_activity,
    _NATIVE_ASSESSMENT_LEDGER,
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
    assessment_reuse: bool
    attempt: GovernedCapabilityAttempt
    # S4 (doc 214): governed fan-out state. ``subobjectives`` carries the
    # validated decomposition proposal; ``sub_results`` accumulates one
    # bounded record per executed branch (operator.add reducer — order
    # of completion never changes the merged set); ``subobjective`` is
    # the per-branch Send payload.
    subobjectives: tuple[SubObjective, ...]
    sub_results: Annotated[list[dict], operator.add]
    subobjective: SubObjective
    sub_finished: bool
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

    def __init__(
        self,
        gates: SupportsGovernedStageGates,
        *,
        recovery_reuse_enabled: bool = True,
        subobjective_fanout_enabled: bool = False,
    ) -> None:
        # Shared governed primitives — the SAME gates Engine A runs;
        # the engine calls its stage-phase methods, never attempt()
        # or _attempt() flow entrypoints on any engine.
        self._gates = gates
        # H5 sequencing knob (B1 vs B0): binds the opt-in assessment
        # ledger per attempt in ``evidence_session``. Sequencing
        # policy only — no governed primitive changes behavior based
        # on this flag; the ledger merely exposes decisions the
        # shared monotonic check may safely reuse.
        self._recovery_reuse_enabled = recovery_reuse_enabled
        # S4 scheduling knob (default off — byte-identical to the
        # baseline graph): when enabled, the plan node may decompose a
        # compound objective into Send fan-out waves; when disabled no
        # model call is issued and the turn reaches owner_path exactly
        # as before (the governed path itself may still investigate
        # sequentially — sequencing parity, never a behavior fork).
        self._subobjective_fanout_enabled = subobjective_fanout_enabled
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
        graph.add_node("evidence_session", self._evidence_session_node)
        graph.add_node("subobjective_plan", self._subobjective_plan_node)
        graph.add_node("subobjective_branch", self._subobjective_branch_node)
        graph.add_node(
            "subobjective_synthesis", self._subobjective_synthesis_node
        )
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
                "owner_path": "evidence_session",
            },
        )
        graph.add_edge("evidence_session", "subobjective_plan")
        graph.add_conditional_edges(
            "subobjective_plan",
            self._route_subobjective_wave,
        )
        graph.add_edge("subobjective_branch", "subobjective_synthesis")
        graph.add_conditional_edges(
            "subobjective_synthesis",
            self._route_subobjective_wave,
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

    def _evidence_session_node(
        self, state: _GovernedTurnState
    ) -> dict[str, Any]:
        # H5 strategy seam: the graph-level DECISION to allow
        # assessment reuse for this attempt, recorded in typed state.
        # The ambient ledger itself must be bound inside owner_path's
        # own context — LangGraph executes each node in a copied
        # context, so a ContextVar set here would not propagate. B0
        # (flag off) records ``assessment_reuse=False`` and the
        # runtime is byte-identical to Engine A.
        return {
            **self._traced(state, "evidence_session"),
            "assessment_reuse": self._recovery_reuse_enabled,
        }

    def _owner_path_node(
        self, state: _GovernedTurnState
    ) -> dict[str, Any]:
        unbound_outcome = (
            OWNER_PATH_UNBOUND
            if state.get("admission_owner_required")
            else None
        )
        # Opt-in ambient carrier for THIS attempt only — bound with a
        # set/reset pair so cancellation, exceptions or non-copying
        # runtimes can never leak the binding outside this node. A
        # fresh dict per invocation; no decisions leak across
        # attempts or turns. The governed recovery stage
        # exposes/reuses decisions through the shared monotonic check.
        ledger_token = None
        if state.get("assessment_reuse"):
            ledger_token = _NATIVE_ASSESSMENT_LEDGER.set(
                {"records": {}, "events": []}
            )
        try:
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
            traced = self._traced(state, "owner_path")
            ledger = _NATIVE_ASSESSMENT_LEDGER.get()
            if ledger is not None:
                traced["trace"] = traced["trace"] + [
                    f"assessment_{event}"
                    for event, _group_key, _cap_id in ledger["events"]
                ]
            return {**traced, "attempt": attempt}
        finally:
            if ledger_token is not None:
                _NATIVE_ASSESSMENT_LEDGER.reset(ledger_token)

    # ---------------- S4: governed subobjective fan-out ------------
    #
    # Ordering semantics only — every gate (selection, argument
    # validation, invoke, judgment, budgets, provenance) still runs
    # inside the SAME governed owner path; the graph owns the schedule:
    # independent subobjectives fan out as Send branches per wave,
    # dependents wait for COMPLETED/PARTIAL dependencies, and the
    # shared TurnDeadline bounds the whole investigation (concurrency
    # never multiplies the global budget). Branches are isolated —
    # each returns one bounded record merged by the operator.add
    # reducer, so fan-in is independent of completion order.

    @staticmethod
    def _subobjective_states(state: _GovernedTurnState) -> dict[str, str]:
        """Latest terminal/non-terminal state per subobjective id."""
        states: dict[str, str] = {}
        for record in state.get("sub_results") or ():
            states[record["subobjective_id"]] = record["state"]
        return states

    @staticmethod
    def _subobjective_attempt_counts(
        state: _GovernedTurnState,
    ) -> dict[str, int]:
        counts: dict[str, int] = {}
        for record in state.get("sub_results") or ():
            oid = record["subobjective_id"]
            counts[oid] = counts.get(oid, 0) + 1
        return counts

    def _route_subobjective_wave(
        self, state: _GovernedTurnState
    ) -> Any:
        """Dependency-aware wave scheduler — deterministic, never
        model-owned. Called after ``subobjective_plan`` (first wave)
        and after ``subobjective_synthesis`` (next wave or END)."""
        if state.get("sub_finished"):
            return END
        objectives = state.get("subobjectives") or ()
        if not objectives:
            return "owner_path"
        deadline = state.get("deadline")
        if deadline is not None and deadline.remaining_seconds() <= 0:
            # Budget exhausted — synthesis closes every pending
            # subobjective with an honest gap, then END.
            return "subobjective_synthesis"
        states = self._subobjective_states(state)
        counts = self._subobjective_attempt_counts(state)
        satisfied = {
            oid
            for oid, s in states.items()
            if s in (SUBOBJECTIVE_COMPLETED, SUBOBJECTIVE_PARTIAL)
        }
        sends: list[Send] = []
        for obj in objectives:
            oid = obj.subobjective_id
            current = states.get(oid)
            if current in (
                SUBOBJECTIVE_COMPLETED,
                SUBOBJECTIVE_PARTIAL,
                SUBOBJECTIVE_BLOCKED,
            ):
                continue
            if current == SUBOBJECTIVE_FAILED and counts.get(oid, 0) >= (
                MAX_ATTEMPTS_PER_SUBOBJECTIVE
            ):
                continue  # retry budget spent — synthesis blocks it
            if all(dep in satisfied for dep in obj.dependencies):
                sends.append(
                    Send(
                        "subobjective_branch",
                        {**state, "subobjective": obj},
                    )
                )
        if sends:
            return sends
        return "subobjective_synthesis"

    def _subobjective_plan_node(
        self, state: _GovernedTurnState
    ) -> dict[str, Any]:
        if not self._subobjective_fanout_enabled:
            return {
                **self._traced(state, "subobjective_plan"),
                "subobjectives": (),
            }
        objectives = self._gates._decompose_objective(
            state["input_text"],
            correlation=state["correlation"],
            workspace_context=state.get("workspace_context"),
            deadline=state["deadline"],
        )
        return {
            **self._traced(state, "subobjective_plan"),
            "subobjectives": tuple(objectives or ()),
        }

    def _subobjective_branch_node(
        self, state: _GovernedTurnState
    ) -> dict[str, Any]:
        sub: SubObjective = state["subobjective"]
        correlation = f'{state["correlation"]}-{sub.subobjective_id}'
        attempt = self._gates._governed_owner_path(
            sub.goal,
            correlation=correlation,
            actor_user_id=state.get("actor_user_id"),
            session_id=state.get("session_id"),
            workspace_context=state.get("workspace_context"),
            prior_turns=(),
            prepare_only=state["prepare_only"],
            unbound_outcome=None,
            deadline=state["deadline"],
            depth=1,
        )
        outcome = attempt.outcome
        prov = getattr(outcome, "provenance", None) if outcome else None
        provenance_ref = (
            f"{getattr(prov, 'specialist_id', '')}."
            f"{getattr(prov, 'remote_name', '')}"
            if prov is not None
            else None
        )
        action, refs, gaps, recoverable = subobjective_outcome_transition(
            attempt.status.value,
            has_content=bool(attempt.content),
            provenance_ref=provenance_ref,
            correlation_id=correlation,
        )
        if action == "complete":
            sub_state = SUBOBJECTIVE_COMPLETED
        elif action == "partial":
            sub_state = SUBOBJECTIVE_PARTIAL
        else:
            sub_state = (
                SUBOBJECTIVE_FAILED
                if recoverable
                else SUBOBJECTIVE_BLOCKED
            )
        record = {
            "subobjective_id": sub.subobjective_id,
            "goal": sub.goal,
            "state": sub_state,
            "attempt_status": attempt.status.value,
            "content": attempt.content,
            "limitations": list(attempt.limitations),
            "evidence_refs": list(refs),
            "gaps": list(gaps),
        }
        return {"sub_results": [record]}

    def _subobjective_synthesis_node(
        self, state: _GovernedTurnState
    ) -> dict[str, Any]:
        objectives = state.get("subobjectives") or ()
        results = list(state.get("sub_results") or ())
        states = self._subobjective_states(state)
        counts = self._subobjective_attempt_counts(state)
        satisfied = {
            oid
            for oid, s in states.items()
            if s in (SUBOBJECTIVE_COMPLETED, SUBOBJECTIVE_PARTIAL)
        }
        deadline = state.get("deadline")
        deadline_gone = (
            deadline is not None and deadline.remaining_seconds() <= 0
        )
        # Anything still non-terminal and unschedulable (deadline gone,
        # blocked dependency, or retry budget spent) is an honest gap —
        # BLOCKED, never silently dropped.
        pending_gaps: dict[str, str] = {}
        finished = True
        for obj in objectives:
            oid = obj.subobjective_id
            if states.get(oid) in (
                SUBOBJECTIVE_COMPLETED,
                SUBOBJECTIVE_PARTIAL,
                SUBOBJECTIVE_BLOCKED,
            ):
                continue
            if deadline_gone:
                pending_gaps[oid] = "investigation budget exhausted"
                continue
            if states.get(oid) == SUBOBJECTIVE_FAILED and counts.get(
                oid, 0
            ) >= MAX_ATTEMPTS_PER_SUBOBJECTIVE:
                pending_gaps[oid] = "subobjective attempt cap reached"
                continue
            if not all(dep in satisfied for dep in obj.dependencies):
                pending_gaps[oid] = "dependency unresolved"
                continue
            finished = False
        contents: list[str] = []
        limitations: list[str] = []
        saw_source_unavailable = False
        saw_authz_denied = False
        order = {obj.subobjective_id: i for i, obj in enumerate(objectives)}
        for record in sorted(
            results, key=lambda r: order.get(r["subobjective_id"], 99)
        ):
            oid = record["subobjective_id"]
            if record["attempt_status"] == "SOURCE_UNAVAILABLE":
                saw_source_unavailable = True
            if record["attempt_status"] == "AUTHZ_DENIED":
                saw_authz_denied = True
            if record["state"] in (
                SUBOBJECTIVE_COMPLETED,
                SUBOBJECTIVE_PARTIAL,
            ) and record.get("content"):
                contents.append(record["content"])
            for lim in record.get("limitations") or ():
                limitations.append(f"{oid}: {lim}")
            for gap in record.get("gaps") or ():
                limitations.append(
                    f"{oid} {record['state']}: {gap}"
                )
        for oid, gap in pending_gaps.items():
            limitations.append(f"{oid} {SUBOBJECTIVE_BLOCKED}: {gap}")
        if contents:
            status = GovernedCapabilityStatus.SUCCESS
            content = "\n\n".join(contents)
        elif saw_source_unavailable:
            status = GovernedCapabilityStatus.SOURCE_UNAVAILABLE
            content = None
        elif saw_authz_denied:
            status = GovernedCapabilityStatus.AUTHZ_DENIED
            content = None
        else:
            status = GovernedCapabilityStatus.NOT_APPLICABLE
            content = None
        _logger.info(
            "orchestration engine=langgraph "
            "stage=subobjective_synthesis decision=done status=%s "
            "finished=%s correlation_id=%s",
            status.value,
            finished or bool(pending_gaps),
            state["correlation"],
        )
        out: dict[str, Any] = {
            **self._traced(state, "subobjective_synthesis")
        }
        if finished or pending_gaps:
            out["sub_finished"] = True
            out["attempt"] = GovernedCapabilityAttempt(
                status=status,
                correlation_id=state["correlation"],
                content=content,
                limitations=tuple(limitations[:24]),
            )
        return out

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
