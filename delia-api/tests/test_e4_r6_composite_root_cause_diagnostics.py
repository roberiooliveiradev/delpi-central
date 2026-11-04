"""E4-R6 diagnostic RED — composite collection / cardinality gate.

TASK: DELIA-C3-E4-R6-COMPOSITE-ROOT-CAUSE-INVESTIGATION-01
MODE: characterization of proven rejection predicates. No production
behaviour change in this file's companion product code.

Reproduces the homologation pattern (doc 228 §15):
two COMPLETED distinct-root owner READs can still fail fan-in when
``len(tracker.objectives) != 2``, with ``reasons=[]`` because the
cardinality gate does not emit a ``comparison_*`` limitation.
"""

from __future__ import annotations

from app.application.capability_provision.orchestration import (
    OperationalCapabilityOrchestrator,
)
from app.application.capability_provision.subobjective_tracker import (
    SubObjective,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityAttempt,
    GovernedCapabilityStatus,
)
from app.application.interaction.contracts import (
    GovernedCapabilityProvenance,
)
from app.application.interaction.turn_budget import TurnDeadline
from app.domain.evidence.model import SourceRef
from app.domain.specialist_interop.model import (
    InteropProtocol,
    SpecialistOutcome,
    SpecialistResultProvenance,
    SpecialistResultStatus,
)
from tests.test_multievidence_composition import _TREE_A, _TREE_B


def _outcome(root_structured, *, specialist="davi", remote="read_tree"):
    return SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        provenance=SpecialistResultProvenance(
            specialist_id=specialist,
            remote_name=remote,
            protocol=InteropProtocol.MCP,
            correlation_id="diag",
            observed_at="2026-11-04T12:00:00+00:00",
        ),
        content_text="tree",
        structured=root_structured,
        is_complete=True,
    )


def _success(root_structured, *, source_id: str) -> GovernedCapabilityAttempt:
    outcome = _outcome(root_structured)
    return GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SUCCESS,
        correlation_id="diag",
        outcome=outcome,
        provenance=GovernedCapabilityProvenance(
            source_refs=(
                SourceRef(
                    source_id=source_id,
                    source_system="api-delpi",
                    provider_name="davi",
                    observed_at=outcome.provenance.observed_at,
                ),
            ),
            specialist_id="davi",
            remote_capability="read_tree",
            action_id="read_tree",
            protocol="MCP",
            observed_at=outcome.provenance.observed_at,
            correlation_id="diag",
            is_complete=True,
            provider_id="mcp",
            capability_group_id="mcp:davi",
        ),
        content=f"estrutura {source_id}",
        limitations=(),
    )


def _clarify() -> GovernedCapabilityAttempt:
    """SUCCESS with content enters ``completed`` and then emits
    ``comparison_source_missing_or_incomplete``. The empty-reasons
    homologation pattern needs a non-completed third instead."""
    return GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SUCCESS,
        correlation_id="diag",
        content="Preciso de mais informações para continuar.",
        limitations=("missing_inputs",),
    )


def _unavailable() -> GovernedCapabilityAttempt:
    return GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SOURCE_UNAVAILABLE,
        correlation_id="diag",
        error_code="delpi_source_unverified",
        limitations=(),
    )


def _sub(oid: str, goal: str) -> SubObjective:
    return SubObjective(subobjective_id=oid, goal=goal, dependencies=())


def _orch() -> OperationalCapabilityOrchestrator:
    return object.__new__(OperationalCapabilityOrchestrator)


def test_rc_a_two_complete_reads_rejected_when_objectives_gt_two():
    """Characterization→fix: analytical leftover no longer blocks.

    Pre-fix: sources=2 + third incomplete → SOURCE_UNAVAILABLE with
    empty comparison_* reasons (objectives cardinality coupling).
    Post-fix (doc 228 §17): third classified analyze/compare is
    auxiliary → composition eligible with structured path.
    """
    orch = _orch()
    orch._acquisition_subobjectives = (
        lambda objectives, **kw: objectives
    )
    orch._understand_goal = (
        lambda text, correlation, workspace_context, prior_turns, deadline: (
            orch._TurnGoal(
                goal_class=(
                    "analyze"
                    if "diferen" in text.casefold()
                    else "read"
                ),
                declared=True,
            )
        )
    )

    by_goal = {
        "ler estrutura 90260147": _success(_TREE_A, source_id="90260147"),
        "ler estrutura 90260148": _success(_TREE_B, source_id="90260148"),
        "detalhar diferenças relevantes": _unavailable(),
    }

    orch._governed_owner_path = lambda sub_goal, **kw: by_goal[sub_goal]
    orch._compose_multi_evidence = lambda *a, **k: (
        "comparacao",
        (),
        "differences_found",
    )

    attempt = orch._investigate_subobjectives(
        (
            _sub("so_1", "ler estrutura 90260147"),
            _sub("so_2", "ler estrutura 90260148"),
            _sub("so_3", "detalhar diferenças relevantes"),
        ),
        "compare 90260147 e 90260148",
        correlation="diag-rca",
        actor_user_id="u1",
        session_id="s1",
        workspace_context=None,
        prepare_only=True,
        deadline=TurnDeadline.start(30),
        depth=1,
        comparison=True,
        prior_turns=(),
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert attempt.verified_composition is not None
    assert set(attempt.verified_composition.source_roots) == {
        "90260147",
        "90260148",
    }


def test_rc_a_third_success_without_provenance_emits_comparison_reason():
    """Sibling: SUCCESS clarify content enters completed then fails
    provenance → ``comparison_source_missing_or_incomplete``."""
    orch = _orch()
    orch._acquisition_subobjectives = (
        lambda objectives, **kw: objectives
    )
    by_goal = {
        "ler estrutura 90260147": _success(_TREE_A, source_id="90260147"),
        "ler estrutura 90260148": _success(_TREE_B, source_id="90260148"),
        "detalhar diferenças relevantes": _clarify(),
    }
    orch._governed_owner_path = lambda sub_goal, **kw: by_goal[sub_goal]
    attempt = orch._investigate_subobjectives(
        (
            _sub("so_1", "ler estrutura 90260147"),
            _sub("so_2", "ler estrutura 90260148"),
            _sub("so_3", "detalhar diferenças relevantes"),
        ),
        "compare 90260147 e 90260148",
        correlation="diag-rca-clarify",
        actor_user_id="u1",
        session_id="s1",
        workspace_context=None,
        prepare_only=True,
        deadline=TurnDeadline.start(30),
        depth=1,
        comparison=True,
        prior_turns=(),
    )
    assert attempt.status is GovernedCapabilityStatus.SOURCE_UNAVAILABLE
    assert "comparison_source_missing_or_incomplete" in attempt.limitations


def test_rc_a_control_exactly_two_objectives_composes():
    """Positive control: same two READs with objectives==2 compose."""
    orch = _orch()
    orch._acquisition_subobjectives = (
        lambda objectives, **kw: objectives
    )
    by_goal = {
        "ler estrutura 90260147": _success(_TREE_A, source_id="90260147"),
        "ler estrutura 90260148": _success(_TREE_B, source_id="90260148"),
    }
    orch._governed_owner_path = lambda sub_goal, **kw: by_goal[sub_goal]
    orch._compose_multi_evidence = lambda *a, **k: (
        "comparacao",
        (),
        "differences_found",
    )
    attempt = orch._investigate_subobjectives(
        (
            _sub("so_1", "ler estrutura 90260147"),
            _sub("so_2", "ler estrutura 90260148"),
        ),
        "compare 90260147 e 90260148",
        correlation="diag-rca-ok",
        actor_user_id="u1",
        session_id="s1",
        workspace_context=None,
        prepare_only=True,
        deadline=TurnDeadline.start(30),
        depth=1,
        comparison=True,
        prior_turns=(),
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert attempt.verified_composition is not None
    assert set(attempt.verified_composition.source_roots) == {
        "90260147",
        "90260148",
    }


def test_rc_a_control_duplicate_root_emits_comparison_reason():
    orch = _orch()
    orch._acquisition_subobjectives = (
        lambda objectives, **kw: objectives
    )
    same = _success(_TREE_A, source_id="90260147")
    by_goal = {
        "ler A": same,
        "ler A novamente": same,
    }
    orch._governed_owner_path = lambda sub_goal, **kw: by_goal[sub_goal]
    attempt = orch._investigate_subobjectives(
        (_sub("so_1", "ler A"), _sub("so_2", "ler A novamente")),
        "compare",
        correlation="diag-dup",
        actor_user_id="u1",
        session_id="s1",
        workspace_context=None,
        prepare_only=True,
        deadline=TurnDeadline.start(30),
        depth=1,
        comparison=True,
        prior_turns=(),
    )
    assert attempt.status is GovernedCapabilityStatus.SOURCE_UNAVAILABLE
    assert "comparison_duplicate_root" in attempt.limitations


def test_rc_c_candidate_bound_is_orchestrated_dead_end():
    """RC-C: execute requiring candidate_token is typed dead-end for
    direct selection — discovery must be preferred when listed."""
    from app.application.capability_provision.orchestration import (
        _capability_dead_end,
        _capability_requires_orchestrated_input,
        _is_candidate_bound,
    )
    from tests.test_goal_evidence_relevance import _cap

    execute = _cap(
        "davi",
        "mcp",
        "execute_delpi_information",
        schema={
            "type": "object",
            "required": ["candidate_token", "arguments"],
            "properties": {
                "candidate_token": {"type": "string"},
                "arguments": {"type": "object"},
            },
        },
    )
    discover = _cap(
        "davi",
        "mcp",
        "discover_delpi_information",
        schema={
            "type": "object",
            "required": ["query"],
            "properties": {"query": {"type": "string"}},
        },
    )
    assert _is_candidate_bound(execute)
    assert _capability_requires_orchestrated_input(execute)
    assert _capability_dead_end(execute, "estrutura do produto 90260147")
    assert not _capability_dead_end(
        discover, "estrutura do produto 90260147"
    )
