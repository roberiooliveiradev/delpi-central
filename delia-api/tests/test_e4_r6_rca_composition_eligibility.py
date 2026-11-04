"""E4-R6 RC-A — evidence-obligation composition eligibility (RED→GREEN).

TASK: DELIA-C3-E4-R6-EVIDENCE-OBLIGATION-AND-COMPOSITION-ELIGIBILITY-FIX-01
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
from tests.test_e4_r6_composite_root_cause_diagnostics import (
    _clarify,
    _success,
    _unavailable,
)
from tests.test_multievidence_composition import _TREE_A, _TREE_B


def _sub(oid: str, goal: str) -> SubObjective:
    return SubObjective(subobjective_id=oid, goal=goal, dependencies=())


def _orch_with_classes(classes: dict[str, str]) -> OperationalCapabilityOrchestrator:
    orch = object.__new__(OperationalCapabilityOrchestrator)
    orch._acquisition_subobjectives = lambda objectives, **kw: objectives

    def _understand(text, correlation, workspace_context, prior_turns, deadline):
        goal_class = classes[text]
        return orch._TurnGoal(
            goal_class=goal_class,
            comparison_requested=goal_class == "compare",
            declared=True,
        )

    orch._understand_goal = _understand
    return orch


def _run(orch, objectives, by_goal, *, compose=True):
    orch._governed_owner_path = lambda sub_goal, **kw: by_goal[sub_goal]
    if compose:
        orch._compose_multi_evidence = lambda *a, **k: (
            "comparacao",
            (),
            "differences_found",
        )
    return orch._investigate_subobjectives(
        objectives,
        "compare structures alpha and beta",
        correlation="rca-fix",
        actor_user_id="u1",
        session_id="s1",
        workspace_context=None,
        prepare_only=True,
        deadline=TurnDeadline.start(30),
        depth=1,
        comparison=True,
        prior_turns=(),
    )


def test_t01_two_sources_plus_analytical_incomplete_composes():
    """Auxiliary analytical leftover must not block two good sources."""
    orch = _orch_with_classes(
        {
            "acquire tree alpha": "read",
            "acquire tree beta": "read",
            "list exclusive differences": "analyze",
        }
    )
    attempt = _run(
        orch,
        (
            _sub("so_1", "acquire tree alpha"),
            _sub("so_2", "acquire tree beta"),
            _sub("so_3", "list exclusive differences"),
        ),
        {
            "acquire tree alpha": _success(_TREE_A, source_id="90260147"),
            "acquire tree beta": _success(_TREE_B, source_id="90260148"),
            "list exclusive differences": _unavailable(),
        },
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert attempt.verified_composition is not None
    assert set(attempt.verified_composition.source_roots) == {
        "90260147",
        "90260148",
    }


def test_t02_third_material_pending_rejects_with_reason():
    orch = _orch_with_classes(
        {
            "acquire tree alpha": "read",
            "acquire tree beta": "read",
            "acquire required spec gamma": "read",
        }
    )
    attempt = _run(
        orch,
        (
            _sub("so_1", "acquire tree alpha"),
            _sub("so_2", "acquire tree beta"),
            _sub("so_3", "acquire required spec gamma"),
        ),
        {
            "acquire tree alpha": _success(_TREE_A, source_id="90260147"),
            "acquire tree beta": _success(_TREE_B, source_id="90260148"),
            "acquire required spec gamma": _unavailable(),
        },
    )
    assert attempt.status is GovernedCapabilityStatus.SOURCE_UNAVAILABLE
    assert attempt.verified_composition is None
    assert "comparison_material_obligation_incomplete" in attempt.limitations


def test_t03_duplicate_root_still_rejected():
    orch = _orch_with_classes({"read left": "read", "read right": "read"})
    same = _success(_TREE_A, source_id="90260147")
    attempt = _run(
        orch,
        (_sub("so_1", "read left"), _sub("so_2", "read right")),
        {"read left": same, "read right": same},
    )
    assert attempt.status is GovernedCapabilityStatus.SOURCE_UNAVAILABLE
    assert "comparison_duplicate_root" in attempt.limitations


def test_t05_clarify_without_provenance_on_material_rejects():
    orch = _orch_with_classes(
        {
            "acquire tree alpha": "read",
            "acquire tree beta": "read",
            "acquire tree gamma": "read",
        }
    )
    attempt = _run(
        orch,
        (
            _sub("so_1", "acquire tree alpha"),
            _sub("so_2", "acquire tree beta"),
            _sub("so_3", "acquire tree gamma"),
        ),
        {
            "acquire tree alpha": _success(_TREE_A, source_id="90260147"),
            "acquire tree beta": _success(_TREE_B, source_id="90260148"),
            "acquire tree gamma": _clarify(),
        },
    )
    assert attempt.status is GovernedCapabilityStatus.SOURCE_UNAVAILABLE
    assert "comparison_source_missing_or_incomplete" in attempt.limitations


def test_t07_analytical_clarify_does_not_poison_two_sources():
    """Analytical SUCCESS without provenance is not a material source miss."""
    orch = _orch_with_classes(
        {
            "acquire tree alpha": "read",
            "acquire tree beta": "read",
            "summarize differences": "analyze",
        }
    )
    attempt = _run(
        orch,
        (
            _sub("so_1", "acquire tree alpha"),
            _sub("so_2", "acquire tree beta"),
            _sub("so_3", "summarize differences"),
        ),
        {
            "acquire tree alpha": _success(_TREE_A, source_id="90260147"),
            "acquire tree beta": _success(_TREE_B, source_id="90260148"),
            "summarize differences": _clarify(),
        },
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert attempt.verified_composition is not None
    assert "comparison_source_missing_or_incomplete" not in attempt.limitations


def test_t08_unclassifiable_incomplete_stays_blocking():
    orch = object.__new__(OperationalCapabilityOrchestrator)
    orch._acquisition_subobjectives = lambda objectives, **kw: objectives

    def _boom(*a, **k):
        raise RuntimeError("classifier down")

    orch._understand_goal = _boom
    attempt = _run(
        orch,
        (
            _sub("so_1", "acquire tree alpha"),
            _sub("so_2", "acquire tree beta"),
            _sub("so_3", "opaque leftover"),
        ),
        {
            "acquire tree alpha": _success(_TREE_A, source_id="90260147"),
            "acquire tree beta": _success(_TREE_B, source_id="90260148"),
            "opaque leftover": _unavailable(),
        },
    )
    assert attempt.status is GovernedCapabilityStatus.SOURCE_UNAVAILABLE
    assert "comparison_material_obligation_incomplete" in attempt.limitations


def test_t09_exactly_two_material_reads_compose():
    orch = _orch_with_classes(
        {"acquire tree alpha": "read", "acquire tree beta": "read"}
    )
    attempt = _run(
        orch,
        (
            _sub("so_1", "acquire tree alpha"),
            _sub("so_2", "acquire tree beta"),
        ),
        {
            "acquire tree alpha": _success(_TREE_A, source_id="90260147"),
            "acquire tree beta": _success(_TREE_B, source_id="90260148"),
        },
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert attempt.verified_composition is not None


def test_t11_rejection_always_has_structured_comparison_reason():
    orch = _orch_with_classes(
        {
            "acquire tree alpha": "read",
            "acquire tree beta": "read",
            "acquire tree gamma": "read",
        }
    )
    attempt = _run(
        orch,
        (
            _sub("so_1", "acquire tree alpha"),
            _sub("so_2", "acquire tree beta"),
            _sub("so_3", "acquire tree gamma"),
        ),
        {
            "acquire tree alpha": _success(_TREE_A, source_id="90260147"),
            "acquire tree beta": _success(_TREE_B, source_id="90260148"),
            "acquire tree gamma": _unavailable(),
        },
    )
    reasons = [
        lim for lim in attempt.limitations if lim.startswith("comparison_")
    ]
    assert reasons
    assert "comparison_material_obligation_incomplete" in reasons
