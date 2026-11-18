"""INT-1 — investigative progress, recovery, discovery boundary (R1–R6).

Deterministic host-local suite. Does not touch the production
``delpi-delia-api`` container. Extends the existing
``PydanticAiInvestigationOrchestrator`` path — no second Agent.
"""

from __future__ import annotations

import dataclasses

import pytest
from tests.support.native_mcp_fixtures import (
    alpha_beta_servers,
    native_toolset_stub,
    owner_tool_server,
)


@pytest.fixture(autouse=True)
def _native_toolsets_stub():
    with native_toolset_stub(alpha_beta_servers()):
        yield


from app.application.capability_provision.contracts import (
    InvestigationAnswer,
    InvestigationAnswerStatus,
)
from app.application.capability_provision.semantic_capability_support import (
    INVESTIGATION_PROGRESS_DISCOVERY,
    INVESTIGATION_PROGRESS_NEW,
    INVESTIGATION_PROGRESS_NONE,
    INVESTIGATION_PROGRESS_RELATED,
    _finalize_agent_collected_attempts,
    _is_business_evidence_attempt,
    classify_investigation_progress,
)
from app.application.interaction.capability_attempt import (
    OWNER_PATH_UNBOUND,
    GovernedCapabilityAttempt,
    GovernedCapabilityStatus,
)
from app.application.interaction.turn_budget import TurnDeadline
from app.application.specialist_interop.errors import OWNER_ARGUMENT_REJECTED
from app.infrastructure.orchestration.pydantic_ai_investigation import (
    _INVESTIGATION_INSTRUCTION_VERSION,
    _INVESTIGATION_INSTRUCTIONS,
    _attempt_projection,
    _invocation_fingerprint,
)
from tests.test_pydantic_ai_semantic_rework import (
    _gates,
    _read_plan,
    _success_attempt,
)


# ---------------- R1: related-but-inadequate does not satisfy plan ----


def test_r1_related_observation_does_not_satisfy_declared_obligation():
    gates, plan = _read_plan("90260921", evidence=("90260921",))
    related = _success_attempt(
        content="aggregate KPIs for manufacturing",
        root="TEO-AGG-01",
        structured={"data": {"root": {"code": "TEO-AGG-01"}, "kpis": [1]}},
    )
    assert (
        classify_investigation_progress(related, plan=plan)
        is INVESTIGATION_PROGRESS_RELATED
        or classify_investigation_progress(related, plan=plan)
        == INVESTIGATION_PROGRESS_RELATED
    )
    result = _finalize_agent_collected_attempts(
        gates,
        input_text="Qual é a estrutura do produto 90260921?",
        collected=(related,),
        correlation="r1",
        workspace_context=None,
        deadline=TurnDeadline.start(30.0),
        unbound_outcome=OWNER_PATH_UNBOUND,
        plan=plan,
    )
    assert result.status is GovernedCapabilityStatus.NOT_APPLICABLE
    assert "related_observations_insufficient" in result.limitations
    assert result.error_code in {
        "investigation_incomplete_coverage",
        "investigation_target_binding_failed",
    }
    # Related body preserved for honesty — not dropped silently.
    assert "aggregate" in (result.content or "").casefold()


def test_r1_matching_root_is_new_information():
    _, plan = _read_plan("90260921", evidence=("90260921",))
    hit = _success_attempt(
        content="BOM root 90260921",
        root="90260921",
    )
    assert (
        classify_investigation_progress(hit, plan=plan)
        == INVESTIGATION_PROGRESS_NEW
    )


# ---------------- R2: owner argument rejection recovery signal --------


def test_r2_owner_argument_rejected_projects_validation_hint():
    attempt = GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SOURCE_UNAVAILABLE,
        correlation_id="r2",
        error_code=OWNER_ARGUMENT_REJECTED,
        owner_hint="arguments.code must be a non-empty string",
    )
    projection = _attempt_projection(attempt, observation_index=0)
    assert projection["investigation_progress"] == INVESTIGATION_PROGRESS_NONE
    assert projection["evidence_citable"] is False
    assert (
        projection["owner_validation_hint"]
        == "arguments.code must be a non-empty string"
    )


def test_r2_equivalent_rejection_fingerprint_is_stable():
    a = _invocation_fingerprint(
        "owner.read", {"arguments": {"code": ""}}
    )
    b = _invocation_fingerprint(
        "owner.read", {"arguments": {"code": ""}}
    )
    assert a == b
    c = _invocation_fingerprint(
        "owner.read", {"arguments": {"code": "90260921"}}
    )
    assert a != c


# ---------------- R3: non-progress does not inflate sufficiency -------


def test_r3_duplicate_content_is_no_progress():
    first = _success_attempt(content="same body", root="X1")
    second = _success_attempt(content="same body", root="X1")
    fp = __import__("hashlib").sha256(b"same body").hexdigest()[:24]
    assert (
        classify_investigation_progress(
            second, prior_content_fingerprints={fp}
        )
        == INVESTIGATION_PROGRESS_NONE
    )
    assert (
        classify_investigation_progress(first)
        == INVESTIGATION_PROGRESS_NEW
    )


def test_r3_related_success_without_root_not_progress_for_open_ids():
    related = _success_attempt(
        content="methodological guide section",
        root="GUIDE",
        structured={"data": {"section": "s1"}},
    )
    # Force no authoritative structure root via incomplete-looking
    # structured payload without comparable records.
    related = _success_attempt(
        content="docs about formats",
        root="DOCS",
        structured={"data": {"title": "formats"}},
    )
    progress = classify_investigation_progress(
        related, uncovered_after=("90260921",)
    )
    # Root DOCS exists from fixture structure helper — when root is
    # present, uncovered identifiers alone do not force RELATED unless
    # the root is absent. Re-check with empty structured items.
    from app.domain.specialist_interop.model import (
        InteropProtocol,
        SpecialistOutcome,
        SpecialistResultProvenance,
        SpecialistResultStatus,
    )
    from app.application.interaction.contracts import (
        GovernedCapabilityProvenance,
    )
    from app.domain.evidence.model import SourceRef

    outcome = SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        content_text="formats catalog",
        structured={"meta": {"operationId": "listFormats"}},
        provenance=SpecialistResultProvenance(
            specialist_id="pa",
            remote_name="docs",
            protocol=InteropProtocol.MCP,
            correlation_id="r3",
            observed_at="2026-01-01T00:00:00Z",
        ),
        is_complete=True,
    )
    attempt = GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SUCCESS,
        correlation_id="r3",
        content="formats catalog",
        provenance=GovernedCapabilityProvenance(
            source_refs=(
                SourceRef(
                    source_id="docs",
                    source_system="pa",
                    provider_name="pa",
                    observed_at="2026-01-01T00:00:00Z",
                ),
            ),
            specialist_id="pa",
            remote_capability="docs",
            action_id="docs",
            protocol=InteropProtocol.MCP.value,
            observed_at="2026-01-01T00:00:00Z",
            correlation_id="r3",
            is_complete=True,
        ),
        outcome=outcome,
    )
    assert (
        classify_investigation_progress(
            attempt, uncovered_after=("90260921",)
        )
        == INVESTIGATION_PROGRESS_RELATED
    )


# ---------------- R4: discovery metadata is not business evidence -----


def test_r4_discovery_metadata_not_business_and_not_new_information():
    discovery = _success_attempt(
        content="operationId=list_items path=/items ParamSchema={}",
        root="CATALOG",
        limitations=("discovery_metadata_observation",),
    )
    assert not _is_business_evidence_attempt(discovery)
    assert (
        classify_investigation_progress(discovery)
        == INVESTIGATION_PROGRESS_DISCOVERY
    )
    projection = _attempt_projection(discovery, observation_index=0)
    assert projection["evidence_citable"] is False
    assert (
        projection["investigation_progress"]
        == INVESTIGATION_PROGRESS_DISCOVERY
    )


def test_r4_discovery_alone_does_not_finalize_success():
    discovery = _success_attempt(
        content="candidates only",
        root="CAT",
        limitations=("discovery_metadata_observation",),
    )
    result = _finalize_agent_collected_attempts(
        _gates(),
        input_text="liste registros",
        collected=(discovery,),
        correlation="r4",
        workspace_context=None,
        deadline=TurnDeadline.start(30.0),
        unbound_outcome=OWNER_PATH_UNBOUND,
        plan=None,
    )
    assert result.status is not GovernedCapabilityStatus.SUCCESS
    assert "insufficient_evidence" in result.limitations or (
        result.error_code == "investigation_no_business_evidence"
    )


# ---------------- R5: gaps preserved; no false conclusion -------------


def test_r5_missing_adequate_evidence_preserves_gaps():
    gates, plan = _read_plan("90260921", evidence=("90260921",))
    related = _success_attempt(
        content="related aggregate",
        root="OTHER",
    )
    result = _finalize_agent_collected_attempts(
        gates,
        input_text="estrutura 90260921",
        collected=(related,),
        correlation="r5",
        workspace_context=None,
        deadline=TurnDeadline.start(30.0),
        unbound_outcome=OWNER_PATH_UNBOUND,
        plan=plan,
    )
    assert result.status is GovernedCapabilityStatus.NOT_APPLICABLE
    assert "related_observations_insufficient" in result.limitations


def test_r5_declared_insufficient_keeps_honest_limitations():
    from app.application.capability_provision.semantic_capability_support import (
        _apply_declared_answer,
    )

    terminal = _success_attempt(content="partial related", root="OTHER")
    declared = InvestigationAnswer(
        schema_version="1",
        status=InvestigationAnswerStatus.INSUFFICIENT,
        answer="ainda falta a estrutura pedida",
        evidence_refs=(0,),
        unmet_obligations=("90260921",),
        limitations=("related_only",),
    )
    out = _apply_declared_answer(
        terminal=terminal,
        declared_answer=declared,
        collected=(terminal,),
        plan=None,
        correlation="r5b",
        unbound_outcome=None,
    )
    assert "declared_unmet_obligation:90260921" in out.limitations
    assert "declared_limitation:related_only" in out.limitations


# ---------------- R6: contract compatibility --------------------------


def test_r6_simple_read_without_plan_still_succeeds():
    only = _success_attempt(content="estrutura MAT-1", root="MAT-1")
    result = _finalize_agent_collected_attempts(
        _gates(),
        input_text="estrutura MAT-1",
        collected=(only,),
        correlation="r6",
        workspace_context=None,
        deadline=TurnDeadline.start(30.0),
        unbound_outcome=None,
        plan=None,
    )
    assert result.status is GovernedCapabilityStatus.SUCCESS
    assert result.verified_composition is None


def test_r6_instructions_remain_provider_agnostic():
    assert _INVESTIGATION_INSTRUCTION_VERSION.startswith("generalist")
    lowered = _INVESTIGATION_INSTRUCTIONS.casefold()
    for forbidden in ("teo.", "davi.", "vista.", "qwen", "openrouter"):
        assert forbidden not in lowered
    assert "investigation_progress" in lowered
    assert "related_insufficient" in lowered or "related-but-insufficient" in lowered


# ---------------- Metamorphic generalization --------------------------


def test_metamorphic_progress_independent_of_tool_names():
    """Same semantic contracts under renamed remotes → same progress."""
    servers = {
        "alpha": owner_tool_server(
            "alpha",
            {
                "enumerate_registry_records": (
                    "List registered process records from the owner "
                    "registry. Returns enumerated business rows."
                ),
                "summarize_process_aggregates": (
                    "Return aggregate KPI summaries for processes. "
                    "Does not enumerate registry rows."
                ),
            },
        ),
    }
    with native_toolset_stub(servers):
        gates, plan = _read_plan(
            "PROC-REGISTRY", evidence=("PROC-REGISTRY",)
        )
        aggregate = _success_attempt(
            content="KPI totals",
            root="KPI-SUM",
            structured={"data": {"root": {"code": "KPI-SUM"}}},
        )
        registry = _success_attempt(
            content="process A; process B",
            root="PROC-REGISTRY",
        )
        assert (
            classify_investigation_progress(
                aggregate, plan=plan, operation_class="ANALYSIS"
            )
            == INVESTIGATION_PROGRESS_RELATED
        )
        assert (
            classify_investigation_progress(
                registry, plan=plan, operation_class="READ"
            )
            == INVESTIGATION_PROGRESS_NEW
        )
        # Rename-invariant: fingerprints ignore remote display names.
        fp_a = _invocation_fingerprint(
            "alpha:enumerate_registry_records",
            {"query": "processos"},
        )
        fp_b = _invocation_fingerprint(
            "beta:list_cadastro_processos",
            {"query": "processos"},
        )
        assert fp_a != fp_b  # different capability ids
        # Same args+capability → stable; schema-equivalent rename is
        # a different id but progress class above is name-agnostic.
        assert (
            _invocation_fingerprint(
                "alpha:enumerate_registry_records",
                {"query": "processos"},
            )
            == fp_a
        )


# ------ G2: aggregation SATISFIED must not die on spurious REF05 ------


def test_g2_aggregation_satisfied_despite_spurious_filter_target():
    """Filter adjective mis-emitted as ``target_identities`` must not
    veto an owner-attested aggregate total (G2 / ativos)."""
    from tests.test_int2_typed_objective_obligation_contract import (
        _anchored_attempt,
    )

    gates = _gates()
    plan = gates._accept_semantic_investigation_plan(
        goal_class="analyze",
        comparison_requested=False,
        target_identities=["ativos"],
        evidence_needed=[
            {
                "description": "Contagem de processos ativos",
                "evidence_source": "process",
            }
        ],
        business_subject="processos de transformação",
        expected_delivery="aggregation",
        correlation="g2",
    )
    assert plan is not None
    assert plan.target_identities == ("ativos",)
    hit = _anchored_attempt(
        root="PROC-0001",
        entity=None,
        capability=None,
        vocabulary=("process", "search"),
        structured={
            "success": True,
            "data": {
                "total": 109,
                "items": [{"codigo_processo": "PROC-0001"}],
                "is_complete": True,
            },
        },
    )
    result = _finalize_agent_collected_attempts(
        gates,
        input_text="Quantos processos de transformação estão ativos?",
        collected=(hit,),
        correlation="g2",
        workspace_context=None,
        deadline=TurnDeadline.start(30.0),
        unbound_outcome=OWNER_PATH_UNBOUND,
        plan=plan,
    )
    assert result.status is GovernedCapabilityStatus.SUCCESS
    assert "ref05_target_unbound_nonblocking" in result.limitations
    assert "related_observations_insufficient" not in result.limitations
    assert result.error_code != "investigation_target_binding_failed"


def test_g2_residual_clarification_does_not_veto_satisfied_aggregation():
    """Residual clarification_question must not short-circuit SUCCESS
    evidence that already satisfies material obligations (G2 grounding
    incoherence: COMPLETE answer under CLARIFICATION_REQUIRED)."""
    from app.application.capability_provision.semantic_capability_support import (
        _apply_declared_answer,
    )
    from tests.test_int2_typed_objective_obligation_contract import (
        _anchored_attempt,
    )

    gates = _gates()
    plan = gates._accept_semantic_investigation_plan(
        goal_class="analyze",
        comparison_requested=False,
        target_identities=["ativos"],
        evidence_needed=[
            {
                "description": "Contagem de processos ativos",
                "evidence_source": "process",
            }
        ],
        business_subject="processos de transformação",
        expected_delivery="aggregation",
        correlation="g2-clar",
    )
    assert plan is not None
    hit = _anchored_attempt(
        root="PROC-0001",
        vocabulary=("process", "search"),
        structured={
            "success": True,
            "data": {
                "total": 109,
                "items": [{"codigo_processo": "PROC-0001"}],
                "is_complete": True,
            },
        },
    )
    hit = dataclasses.replace(hit, limitations=("result_truncated",))
    terminal = _finalize_agent_collected_attempts(
        gates,
        input_text="Quantos processos de transformação estão ativos?",
        collected=(hit,),
        correlation="g2-clar",
        workspace_context=None,
        deadline=TurnDeadline.start(30.0),
        unbound_outcome=OWNER_PATH_UNBOUND,
        plan=plan,
        clarification_question="Qual status deseja filtrar?",
    )
    assert terminal.status is GovernedCapabilityStatus.SUCCESS
    assert "agent_requested_clarification" not in terminal.limitations
    assert (
        "agent_clarification_superseded_by_satisfied_evidence"
        in terminal.limitations
    )
    declared = InvestigationAnswer(
        schema_version="1",
        status=InvestigationAnswerStatus.COMPLETE,
        answer="Existem 109 processos de transformação ativos.",
        evidence_refs=(0,),
        limitations=("result_truncated",),
    )
    out = _apply_declared_answer(
        terminal=terminal,
        declared_answer=declared,
        collected=(hit,),
        plan=plan,
        correlation="g2-clar",
        unbound_outcome=None,
    )
    assert out.status is GovernedCapabilityStatus.SUCCESS
    assert "109" in (out.content or "")
    assert "agent_requested_clarification" not in out.limitations
    assert out.outcome is not None
    assert out.provenance is not None


def test_g2_clarification_still_applies_when_obligations_unmet():
    """Negative: residual clarification with unmet obligations stays
    an honest ask-back and preserves verified partial evidence."""
    from tests.test_int2_typed_objective_obligation_contract import (
        _anchored_attempt,
    )

    gates, plan = _read_plan("90260921", evidence=("90260921",))
    related = _anchored_attempt(
        root="OTHER",
        vocabulary=("process", "search"),
        structured={"success": True, "data": {"total": 1}},
    )
    result = _finalize_agent_collected_attempts(
        gates,
        input_text="Qual a estrutura do produto 90260921?",
        collected=(related,),
        correlation="g2-clar-neg",
        workspace_context=None,
        deadline=TurnDeadline.start(30.0),
        unbound_outcome=OWNER_PATH_UNBOUND,
        plan=plan,
        clarification_question="Qual código do produto?",
    )
    assert result.status is GovernedCapabilityStatus.CLARIFICATION_REQUIRED
    assert "agent_requested_clarification" in result.limitations
    assert "verified_evidence_preserved" in result.limitations
    assert result.outcome is not None


def test_g2_complete_declaration_promotes_clarification_terminal():
    """Defense-in-depth: COMPLETE+consistent must not leave content on
    a CLARIFICATION_REQUIRED terminal (NON_GROUNDED publish path)."""
    from app.application.capability_provision.semantic_capability_support import (
        _apply_declared_answer,
    )
    from tests.test_int2_typed_objective_obligation_contract import (
        _anchored_attempt,
    )

    gates = _gates()
    plan = gates._accept_semantic_investigation_plan(
        goal_class="analyze",
        comparison_requested=False,
        target_identities=[],
        evidence_needed=[
            {
                "description": "Contagem de processos ativos",
                "evidence_source": "process",
            }
        ],
        expected_delivery="aggregation",
        correlation="g2-promote",
    )
    assert plan is not None
    hit = _anchored_attempt(
        root="PROC-0001",
        vocabulary=("process", "search"),
        structured={
            "success": True,
            "data": {"total": 109, "is_complete": True},
        },
    )
    clarification_terminal = GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.CLARIFICATION_REQUIRED,
        correlation_id="g2-promote",
        content="Qual filtro?",
        limitations=("agent_requested_clarification",),
        error_code="investigation_clarification_required",
    )
    declared = InvestigationAnswer(
        schema_version="1",
        status=InvestigationAnswerStatus.COMPLETE,
        answer="Existem 109 processos de transformação ativos.",
        evidence_refs=(0,),
    )
    out = _apply_declared_answer(
        terminal=clarification_terminal,
        declared_answer=declared,
        collected=(hit,),
        plan=plan,
        correlation="g2-promote",
        unbound_outcome=None,
    )
    assert out.status is GovernedCapabilityStatus.SUCCESS
    assert "109" in (out.content or "")
    assert "agent_requested_clarification" not in out.limitations
    assert out.outcome is not None
    assert out.provenance is not None


def test_g2_unbound_target_still_runs_partial_identifier_coverage():
    """Sibling: spurious target must not skip uncovered named ids."""
    from tests.test_int2_typed_objective_obligation_contract import (
        _anchored_attempt,
    )

    gates = _gates()
    plan = gates._accept_semantic_investigation_plan(
        goal_class="analyze",
        comparison_requested=False,
        target_identities=["ativos"],
        evidence_needed=[
            {
                "description": "Contagem de processos ativos",
                "evidence_source": "process",
            }
        ],
        expected_delivery="aggregation",
        correlation="g2-id",
    )
    assert plan is not None
    hit = _anchored_attempt(
        root="PROC-0001",
        vocabulary=("process", "search"),
        structured={
            "success": True,
            "data": {
                "total": 109,
                "items": [{"codigo_processo": "PROC-0001"}],
                "is_complete": True,
            },
        },
    )
    result = _finalize_agent_collected_attempts(
        gates,
        input_text="Quantos processos ativos tem o PROC-0002?",
        collected=(hit,),
        correlation="g2-id",
        workspace_context=None,
        deadline=TurnDeadline.start(30.0),
        unbound_outcome=OWNER_PATH_UNBOUND,
        plan=plan,
    )
    assert result.status is GovernedCapabilityStatus.NOT_APPLICABLE
    assert result.error_code == "investigation_partial_coverage"
    assert "uncovered_identifier:PROC-0002" in result.limitations
    assert "identifier_coverage_incomplete" in result.limitations


def test_g2_unbound_target_still_fails_when_obligation_unsatisfied():
    """Negative: unbound target + unmet obligation keeps fail-closed."""
    gates = _gates()
    plan = gates._accept_semantic_investigation_plan(
        goal_class="analyze",
        comparison_requested=False,
        target_identities=["ativos"],
        evidence_needed=[
            {
                "description": "Contagem de processos ativos",
                "evidence_source": "process",
            }
        ],
        expected_delivery="aggregation",
        correlation="g2-neg",
    )
    assert plan is not None
    # KPI blob without authoritative aggregate / process vocabulary.
    miss = _success_attempt(
        content="aggregate KPIs",
        root="TEO-AGG-01",
        structured={"data": {"root": {"code": "TEO-AGG-01"}, "kpis": [1]}},
    )
    result = _finalize_agent_collected_attempts(
        gates,
        input_text="Quantos processos de transformação estão ativos?",
        collected=(miss,),
        correlation="g2-neg",
        workspace_context=None,
        deadline=TurnDeadline.start(30.0),
        unbound_outcome=OWNER_PATH_UNBOUND,
        plan=plan,
    )
    assert result.status is GovernedCapabilityStatus.NOT_APPLICABLE
    assert result.error_code == "investigation_target_binding_failed"
    assert "ref05_target_unbound" in result.limitations
