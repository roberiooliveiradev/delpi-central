"""E4-R6 RC-A homologation — semantic-safety probes (synthetic).

TASK: DELIA-C3-E4-R6-RCA-GOVERNED-HOMOLOGATION-AND-SEMANTIC-SAFETY-01

These cases exercise whether eligibility-time reclassification via
``_subgoal_is_composition_auxiliary`` can discard a material
obligation and emit verified composition / SUCCESS.

No product fix in this file — FAIL here is a security finding for
coordination rework, not a silent soft-pass.
"""

from __future__ import annotations

import pytest

from app.application.capability_provision.orchestration import (
    OperationalCapabilityOrchestrator,
)
from app.application.capability_provision.subobjective_tracker import (
    SubObjective,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityStatus,
)
from app.application.interaction.turn_budget import TurnDeadline
from tests.test_e4_r6_composite_root_cause_diagnostics import (
    _success,
    _unavailable,
)
from tests.test_e4_r6_rca_composition_eligibility import _run, _sub
from tests.test_multievidence_composition import _TREE_A, _TREE_B


def test_c01_true_auxiliary_analyze_allows_two_source_compose():
    orch = object.__new__(OperationalCapabilityOrchestrator)
    orch._acquisition_subobjectives = lambda objectives, **kw: objectives
    classes = {
        "acquire tree alpha": "read",
        "acquire tree beta": "read",
        "identify common items": "analyze",
        "summarize differences": "compare",
    }
    orch._understand_goal = (
        lambda text, *a, **k: orch._TurnGoal(
            goal_class=classes[text], declared=True
        )
    )
    attempt = _run(
        orch,
        (
            _sub("so_1", "acquire tree alpha"),
            _sub("so_2", "acquire tree beta"),
            _sub("so_3", "identify common items"),
            _sub("so_4", "summarize differences"),
        ),
        {
            "acquire tree alpha": _success(_TREE_A, source_id="90260147"),
            "acquire tree beta": _success(_TREE_B, source_id="90260148"),
            "identify common items": _unavailable(),
            "summarize differences": _unavailable(),
        },
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert attempt.verified_composition is not None


def test_c02_true_material_third_blocks():
    orch = object.__new__(OperationalCapabilityOrchestrator)
    orch._acquisition_subobjectives = lambda objectives, **kw: objectives
    classes = {
        "acquire tree alpha": "read",
        "acquire tree beta": "read",
        "acquire required specification gamma": "read",
    }
    orch._understand_goal = (
        lambda text, *a, **k: orch._TurnGoal(
            goal_class=classes[text], declared=True
        )
    )
    attempt = _run(
        orch,
        (
            _sub("so_1", "acquire tree alpha"),
            _sub("so_2", "acquire tree beta"),
            _sub("so_3", "acquire required specification gamma"),
        ),
        {
            "acquire tree alpha": _success(_TREE_A, source_id="90260147"),
            "acquire tree beta": _success(_TREE_B, source_id="90260148"),
            "acquire required specification gamma": _unavailable(),
        },
    )
    assert attempt.status is GovernedCapabilityStatus.SOURCE_UNAVAILABLE
    assert "comparison_material_obligation_incomplete" in attempt.limitations
    assert attempt.verified_composition is None


@pytest.mark.xfail(
    strict=True,
    reason=(
        "RC-A semantic-safety finding (doc228 §18): eligibility-time "
        "analyze reclass discards tracked material obligations → "
        "FALSE VerifiedCompositeEvidence. Rework required; do not "
        "remove this xfail without fixing orchestration."
    ),
)
def test_c03_material_reclassified_analyze_must_not_ground():
    """C03 SECURITY: eligibility reclass read→analyze must not drop
    a tracked material obligation and emit verified composition.

    If this assertion fails (SUCCESS / verified_composition set), the
    RC-A auxiliary classifier is unsafe under divergent LLM labels.
    """
    orch = object.__new__(OperationalCapabilityOrchestrator)
    orch._acquisition_subobjectives = lambda objectives, **kw: objectives
    calls: list[str] = []

    def _understand(text, correlation, workspace_context, prior_turns, deadline):
        calls.append(f"{correlation}:{text}")
        # Eligibility correlators use suffix -elig-cls / -{oid}.
        if "elig" in correlation or correlation.endswith("-so_3"):
            # Divergent later classification — unsafe if trusted.
            return orch._TurnGoal(goal_class="analyze", declared=True)
        return orch._TurnGoal(goal_class="read", declared=True)

    orch._understand_goal = _understand
    attempt = _run(
        orch,
        (
            _sub("so_1", "acquire tree alpha"),
            _sub("so_2", "acquire tree beta"),
            _sub("so_3", "acquire required specification gamma"),
        ),
        {
            "acquire tree alpha": _success(_TREE_A, source_id="90260147"),
            "acquire tree beta": _success(_TREE_B, source_id="90260148"),
            "acquire required specification gamma": _unavailable(),
        },
    )
    assert attempt.verified_composition is None, (
        "FALSE_GROUNDED: material obligation discarded after "
        f"reclassify-to-analyze; calls={calls}"
    )
    assert attempt.status is GovernedCapabilityStatus.SOURCE_UNAVAILABLE
    assert "comparison_material_obligation_incomplete" in attempt.limitations


def test_c04_classifier_exception_fail_closed():
    orch = object.__new__(OperationalCapabilityOrchestrator)
    orch._acquisition_subobjectives = lambda objectives, **kw: objectives

    def _boom(*a, **k):
        raise RuntimeError("model down")

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
    assert attempt.verified_composition is None


@pytest.mark.xfail(
    strict=True,
    reason=(
        "RC-A semantic-safety finding (doc228 §18): goal_class=analyze "
        "alone discards external-spec material dependency. Rework "
        "required; do not remove this xfail without fixing orchestration."
    ),
)
def test_c05_analyze_phrasing_with_external_spec_dependency_blocks():
    """Analytical phrasing that still names an external required source
    must not be discarded solely because goal_class=analyze."""
    orch = object.__new__(OperationalCapabilityOrchestrator)
    orch._acquisition_subobjectives = lambda objectives, **kw: objectives
    # Dangerous: classifier labels the whole ask as analyze.
    orch._understand_goal = (
        lambda text, *a, **k: orch._TurnGoal(
            goal_class="analyze", declared=True
        )
    )
    attempt = _run(
        orch,
        (
            _sub("so_1", "acquire tree alpha"),
            _sub("so_2", "acquire tree beta"),
            _sub(
                "so_3",
                "compare using the latest approved engineering specification",
            ),
        ),
        {
            "acquire tree alpha": _success(_TREE_A, source_id="90260147"),
            "acquire tree beta": _success(_TREE_B, source_id="90260148"),
            "compare using the latest approved engineering specification": (
                _unavailable()
            ),
        },
    )
    # Safe expectation: do not ground without the specification source.
    assert attempt.verified_composition is None, (
        "FALSE_GROUNDED: analyze-class discarded external-spec obligation"
    )
    assert attempt.status is GovernedCapabilityStatus.SOURCE_UNAVAILABLE
