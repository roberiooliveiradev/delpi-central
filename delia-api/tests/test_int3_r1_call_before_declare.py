"""INT-3 R1 — CALL_BEFORE_DECLARE deterministic reproduction.

Task DELIA-C3-T2-INT3-R1-CALL-BEFORE-DECLARE-BOUNDED-REMEDIATION-01.

Real-model evidence (evals ``or-qwen14b-205331140f0e`` arm A /
``or-qwen14b-b37c420b89c3`` arm B, qwen/qwen3-14b): every scenario that
executed a business READ ran the FIRST owner call while
``InvestigationDeps.investigation_plan is None`` — the observation was
projected with ``coverage_note`` "Typed objective undeclared", so typed
obligation coverage could not be evaluated mid-flight.

Frozen-corpus A/B result: instruction specialization alone (v2-6,
strict "declare FIRST" ordering) did NOT change the first-call order
in ANY scenario with calls — the divergence is structural, not
lexical: ``_governed_invoke`` executes the governed owner call before
any typed-plan precondition is checked. A governed pre-invocation
boundary (ModelRetry -> declare -> revalidate) is the Alternative-C
contract gate pending coordination decision.
"""

from __future__ import annotations

import inspect
import re

import pytest

from app.application.capability_provision.governed_capability_orchestrator import (
    OperationalCapabilityOrchestrator,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityAttempt,
    GovernedCapabilityProvenance,
    GovernedCapabilityStatus,
)
from app.domain.evidence.model import SourceRef
from app.domain.specialist_interop.model import (
    InteropProtocol,
    SpecialistOutcome,
    SpecialistResultProvenance,
    SpecialistResultStatus,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.infrastructure.orchestration import pydantic_ai_investigation as _inv
from tests.support.capability_fixtures import (
    FakeProposalModel,
    _providers,
    load_test_orchestration_instructions,
)


def _gates() -> OperationalCapabilityOrchestrator:
    return OperationalCapabilityOrchestrator(
        _providers(),
        orchestration_instructions=load_test_orchestration_instructions(),
        invoke_model=InvokeModel(FakeProposalModel(())),
    )


def _successful_owner_read() -> GovernedCapabilityAttempt:
    """Successful business READ exactly as a governed owner call lands
    in ``ctx.deps.collected`` — the trace-reproduced pre-declare call."""
    structured = {
        "capability": "search_processes",
        "action_id": "search_processes",
        "entity": "process",
        "shape": "paged_list",
        "data": {
            "items": [{"code": "P-001"}],
            "total": 1,
            "is_complete": True,
            "truncated": False,
        },
    }
    outcome = SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        content_text="records",
        structured=structured,
        provenance=SpecialistResultProvenance(
            specialist_id="teo",
            remote_name="read",
            protocol=InteropProtocol.MCP,
            correlation_id="r1",
            observed_at="2026-01-01T00:00:00Z",
        ),
        is_complete=True,
    )
    return GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SUCCESS,
        correlation_id="r1",
        content="records",
        limitations=(),
        provenance=GovernedCapabilityProvenance(
            source_refs=(
                SourceRef(
                    source_id="src",
                    source_system="teo",
                    provider_name="teo",
                    observed_at="2026-01-01T00:00:00Z",
                ),
            ),
            specialist_id="teo",
            remote_capability="read",
            action_id="read",
            protocol=InteropProtocol.MCP.value,
            observed_at="2026-01-01T00:00:00Z",
            correlation_id="r1",
            is_complete=True,
            operation_class="READ",
            invocation_vocabulary=("search_processes",),
            invocation_identity=(),
            invocation_scope=(),
        ),
        outcome=outcome,
    )


# -------------------------------------------------------------------
# R1 defect — owner READ executes while typed plan is absent
# -------------------------------------------------------------------


def test_dependent_owner_read_with_plan_none_yields_no_coverage():
    """RED (defect reproduced): a successful owner READ projected while
    ``investigation_plan is None`` can only surface the pending-goal
    signal — typed coverage evaluation is unavailable for a call that
    already executed. This is the exact projection the runtime emitted
    for every pre-declare call in both eval arms."""
    projection = _inv._attempt_projection(
        _successful_owner_read(),
        observation_index=0,
        plan=None,
        operation_class="READ",
        capability_id="teo.read",
    )
    assert projection["goal_declaration_pending"] is True
    note = (projection.get("coverage_note") or "").casefold()
    assert "typed objective undeclared" in note
    assert "coverage cannot be evaluated" in note


def test_same_read_with_accepted_plan_enables_midflight_coverage():
    """Control: the identical owner READ projected WITH an accepted
    typed plan carries evaluable coverage context — the only variable
    is plan presence, proving the defect is ordering, not capability."""
    plan = _gates()._accept_semantic_investigation_plan(
        goal_class="read",
        comparison_requested=False,
        target_identities=[],
        evidence_needed=[
            {
                "description": "listagem de processos",
                "evidence_source": "process",
                "operation": "read",
            }
        ],
        expected_delivery="enumeration",
        correlation="r1",
    )
    assert plan is not None
    projection = _inv._attempt_projection(
        _successful_owner_read(),
        observation_index=0,
        plan=plan,
        operation_class="READ",
        capability_id="teo.read",
    )
    assert "goal_declaration_pending" not in projection
    note = (projection.get("coverage_note") or "").casefold()
    assert "undeclared" not in note


@pytest.mark.xfail(
    strict=True,
    reason=(
        "INT3-R1 Alternative-C pending coordination decision: "
        "_governed_invoke must reject a dependent owner call with a "
        "bounded ModelRetry BEFORE _governed_semantic_tool_invoke "
        "executes while ctx.deps.investigation_plan is None. "
        "Instruction specialization (arm B, v2-6) did not fix the "
        "order in any corpus scenario — a governed pre-invocation "
        "boundary is the remaining proven-minimal correction."
    ),
)
def test_invariant_declare_before_dependent_read_gate_exists():
    """Desired invariant (currently absent): inside ``_governed_invoke``
    a missing typed plan must stop the dependent owner call at the
    invocation boundary — ModelRetry, never fabricated plan — so the
    model declares the goal and the SAME call is then revalidated and
    executed. Today the owner call executes first and the 'undeclared'
    note arrives only in the post-observation projection."""
    source = inspect.getsource(_inv)
    region = re.search(
        r"def _governed_invoke\(.*?\n(.*?)\n\s+def ",
        source,
        re.DOTALL,
    )
    assert region is not None
    body = region.group(1)
    invoke_pos = body.find("ctx.deps.gates._governed_semantic_tool_invoke")
    gate_pos = body.find("ctx.deps.investigation_plan is None")
    assert invoke_pos != -1
    # The gate exists only if a plan-missing check precedes the call.
    assert -1 != gate_pos < invoke_pos
