"""Doc 235 — Pydantic AI native-first consolidation RED/GREEN.

Proves optional goal declaration, typed invoke args, clarification,
agent-requested composition, heterogeneous obligations, and absence of
mandatory compare-only routing for simple READs.
"""

from __future__ import annotations

import pytest
from tests.support.native_mcp_fixtures import (
    alpha_beta_servers,
    native_toolset_stub,
)


@pytest.fixture(autouse=True)
def _native_toolsets_stub():
    """Owner MCP surfaces in-process — native toolsets real, SDK wire
    substituted; ``process_tool_call`` governance unchanged."""
    with native_toolset_stub(alpha_beta_servers()):
        yield


from app.application.capability_provision.semantic_capability_support import (
    OBLIGATION_SATISFIED,
    OBLIGATION_UNSATISFIED,
    _attempt_satisfies_obligation,
    _evaluate_material_obligations,
    _finalize_agent_collected_attempts,
)
from app.application.interaction.capability_attempt import (
    OWNER_PATH_UNBOUND,
    GovernedCapabilityAttempt,
    GovernedCapabilityStatus,
)
from app.application.interaction.turn_budget import TurnDeadline
from app.domain.evidence.model import SourceRef
from app.infrastructure.orchestration.pydantic_ai_investigation import (
    PydanticAiInvestigationOrchestrator,
)
from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import FunctionModel
from tests.test_pydantic_ai_semantic_rework import (
    _gates,
    _success_attempt,
)


def _final_answer(answer: str = "", status: str = "insufficient",
                  refs: list | None = None) -> ModelResponse:
    """Native typed output — the Agent now ends every run with a
    ``final_result`` call carrying the strict InvestigationAnswer
    shape instead of free text."""
    return ModelResponse(
        parts=[
            ToolCallPart(
                "final_result",
                {
                    "schema_version": "1",
                    "status": status,
                    "answer": answer,
                    "evidence_refs": refs or [],
                    "unmet_obligations": [],
                    "limitations": [],
                },
            )
        ]
    )


def test_simple_read_without_declare_goal_succeeds():
    gates = _gates()
    only = _success_attempt(content="estrutura MAT-1", root="MAT-1")
    result = _finalize_agent_collected_attempts(
        gates,
        input_text="estrutura MAT-1",
        collected=(only,),
        correlation="c1",
        workspace_context=None,
        deadline=TurnDeadline.start(30.0),
        unbound_outcome=None,
        plan=None,
    )
    assert result.status is GovernedCapabilityStatus.SUCCESS
    assert result.verified_composition is None


def test_clarification_short_circuits_finalize():
    gates = _gates()
    only = _success_attempt(content="partial", root="X")
    result = _finalize_agent_collected_attempts(
        gates,
        input_text="compare something",
        collected=(only,),
        correlation="c1",
        workspace_context=None,
        deadline=TurnDeadline.start(30.0),
        unbound_outcome=OWNER_PATH_UNBOUND,
        plan=None,
        clarification_question="Qual o segundo código do produto?",
    )
    assert result.status is GovernedCapabilityStatus.CLARIFICATION_REQUIRED
    assert "segundo código" in (result.content or "")


def test_agent_requested_composition_returned_by_finalize():
    gates = _gates()
    from app.application.interaction.contracts import VerifiedCompositeEvidence

    composed = GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SUCCESS,
        correlation_id="c1",
        content="composed",
        verified_composition=VerifiedCompositeEvidence(
            source_roots=("A", "B"),
            source_lineage=(
                (
                    SourceRef(
                        source_id="A",
                        source_system="pa",
                        provider_name="pa",
                        observed_at="2026-01-01T00:00:00Z",
                    ),
                ),
                (
                    SourceRef(
                        source_id="B",
                        source_system="pa",
                        provider_name="pa",
                        observed_at="2026-01-01T00:00:00Z",
                    ),
                ),
            ),
            observed_at="2026-01-01T00:00:00Z",
            correlation_id="c1",
            verdict="differences_found",
        ),
    )
    result = _finalize_agent_collected_attempts(
        gates,
        input_text="compare",
        collected=(),
        correlation="c1",
        workspace_context=None,
        deadline=TurnDeadline.start(30.0),
        unbound_outcome=None,
        composed_attempt=composed,
    )
    assert result is composed
    assert result.verified_composition is not None


def test_heterogeneous_obligation_matches_authoritative_root_only():
    attempt = _success_attempt(
        content="inventory snapshot",
        root="OTHER",
        structured={
            "items": [{"code": "OTHER", "label": "x", "path": ["OTHER"]}]
        },
    )
    assert _attempt_satisfies_obligation(attempt, "OTHER")
    # Capability / remote name is not business evidence (doc 237 R-E2).
    coverage = _evaluate_material_obligations(
        obligations=("search_items",),
        business=(attempt,),
    )
    assert dict(coverage)["search_items"] == OBLIGATION_UNSATISFIED


def test_omitted_obligation_stays_unsatisfied():
    attempt = _success_attempt(content="only A", root="A1")
    coverage = _evaluate_material_obligations(
        obligations=("A1", "MISSING-SPEC"),
        business=(attempt,),
    )
    states = dict(coverage)
    assert states["A1"] == OBLIGATION_SATISFIED
    assert states["MISSING-SPEC"] == OBLIGATION_UNSATISFIED


def test_request_clarification_tool_wires_into_finalize():
    gates = _gates()
    seen: dict[str, object] = {}
    original = gates._finalize_semantic_investigation

    def _capture(**kwargs):
        seen.update(kwargs)
        return original(**kwargs)

    gates._finalize_semantic_investigation = _capture  # type: ignore[method-assign]

    def _fn(messages, _info):
        if not any(isinstance(m, ModelResponse) for m in messages):
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        "request_user_clarification",
                        {
                            "question": "Qual produto deseja consultar?",
                            "missing_aspects": ["product_code"],
                        },
                    )
                ]
            )
        return _final_answer("waiting")

    engine = PydanticAiInvestigationOrchestrator(
        gates, model=FunctionModel(_fn), tool_calls_limit=4
    )
    attempt = engine.attempt("me mostra a estrutura")
    assert attempt.status is GovernedCapabilityStatus.CLARIFICATION_REQUIRED
    assert seen.get("clarification_question")


def test_typed_invoke_arguments_dict_path():
    gates = _gates()
    catalog = gates._project_semantic_tool_catalog(
        correlation="c", deadline=TurnDeadline.start(30.0)
    )
    read = next(c for c in catalog if c["operation_class"] == "READ")
    calls: list[dict] = []

    def _fn(messages, _info):
        if not any(isinstance(m, ModelResponse) for m in messages):
            return ModelResponse(
                parts=[
                    ToolCallPart(read["capability_id"], {"query": "terminal"})
                ]
            )
        return _final_answer("done")

    # Spy invoke
    original = gates._governed_semantic_tool_invoke

    def _spy(**kwargs):
        calls.append(dict(kwargs.get("arguments") or {}))
        return original(**kwargs)

    gates._governed_semantic_tool_invoke = _spy  # type: ignore[method-assign]
    engine = PydanticAiInvestigationOrchestrator(
        gates, model=FunctionModel(_fn), tool_calls_limit=4
    )
    engine.attempt("liste terminais")
    assert calls and calls[0].get("query") == "terminal"


def test_compose_tool_optional_not_hardwired_for_two_reads():
    """Two independent READs without compose/plan must not auto-compare."""
    gates = _gates()
    a = _success_attempt(content="a", root="IND-A")
    b = _success_attempt(content="b", root="IND-B")
    result = _finalize_agent_collected_attempts(
        gates,
        input_text="two independent facts",
        collected=(a, b),
        correlation="c1",
        workspace_context=None,
        deadline=TurnDeadline.start(30.0),
        unbound_outcome=None,
        plan=None,
    )
    assert result.verified_composition is None
    assert "multiple_observations_without_compose" in result.limitations


def test_module_exposes_native_first_tools():
    from pathlib import Path

    src = (
        Path(__file__).resolve().parents[1]
        / "app/infrastructure/orchestration/pydantic_ai_investigation.py"
    ).read_text(encoding="utf-8")
    assert "request_user_clarification" in src
    assert "compose_verified_observations" in src
    assert "arguments: dict[str, Any] | None" in src
    assert "OPTIONAL" in src
    assert "run_governed_investigation" not in src
    assert "_COMPARE_INTENT" not in src
