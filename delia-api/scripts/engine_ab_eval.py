#!/usr/bin/env python3
"""DELIA C3 — local A/B evaluation of the two governed-attempt
engines behind ``SupportsGovernedCapabilityAttempt``.

Engine A: ``OperationalCapabilityOrchestrator`` (production default).
Engine B: ``LangGraphCapabilityOrchestrator`` (experimental,
LOCAL_TEST_ONLY — never composed into the production root).

Both engines receive identical fakes (owner surfaces, scripted
proposal models, governed instructions) and are measured on the
same deterministic scenarios S1/S2/S3/S7/S8/S10 from the doc-192
matrix. All model calls are FAKE_MODEL_CALLS — no provider tokens
exist in this harness; semantics are asserted by the conformance
suite, not here.

Usage (inside the delia-api dev container / venv):

    python scripts/engine_ab_eval.py

Exit code 0 always — this is a measurement harness, not a gate.
Divergences are printed, not hidden.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.application.interaction.capability_attempt import (  # noqa: E402
    GovernedCapabilityStatus,
)
from app.application.specialist_interop.errors import (  # noqa: E402
    SPECIALIST_DISABLED,
    SpecialistInteropError,
)
from tests.test_governed_attempt_contract import (  # noqa: E402
    ARGUMENTS_INSTRUCTION_ID,
    GOAL_EVIDENCE_RELEVANCE_INSTRUCTION_ID,
    FakePort,
    FakeProposalModel,
    TEO_TOOLS,
    VISTA_TOOLS,
    build_engine,
    _items_provider,
    _select,
)
from tests.test_goal_evidence_relevance import (  # noqa: E402
    FakeProposalModel as RelevanceProposalModel,
    _cri_clause,
    _outcome,
    _select as _rel_select,
)
from app.application.capability_provision.orchestration import (  # noqa: E402
    NATIVE_ASSESSMENT_INSTRUCTION_ID,
)

ENGINE_IDS = ("delia", "langgraph_b0", "langgraph")


def _assessment_count(model):
    return len(
        [
            r
            for r in model.requests
            if r.task_purpose_id == NATIVE_ASSESSMENT_INSTRUCTION_ID
        ]
    )


def _scenario_read():
    """S1 — single authorized READ, grounded answer."""
    port = FakePort(tools_by_specialist={"teo": TEO_TOOLS})
    model = FakeProposalModel(
        _select("teo", "analyze", {"view": "summary"})
    )
    return {
        "input": "resumo",
        "expect": GovernedCapabilityStatus.SUCCESS,
        "kwargs": {
            "port": port,
            "specialist_ids": ("teo",),
            "model": model,
        },
        "meter": lambda: (len(model.requests), len(port.calls)),
    }


def _scenario_two_records():
    """S2 — two correct owner records surface verbatim."""
    provider = _items_provider(
        _outcome(
            "ok",
            structured={
                "data": {
                    "items": [
                        {"code": "10080092",
                         "description": "TERM. BALA 0,50-2,27MM2"},
                        {"code": "10081004",
                         "description": "TERM. BALA 1,00-2,50MM2"},
                    ]
                }
            },
        )
    )
    model = RelevanceProposalModel(
        _rel_select(
            "mcp:alpha", "search_items",
            args={"arguments": {"query": "terminal bala"}},
        )
    )
    return {
        "input": "Dois exemplos de terminal bala",
        "expect": GovernedCapabilityStatus.SUCCESS,
        "kwargs": {"providers": [provider], "model": model},
        "meter": lambda: (len(model.requests), len(provider.calls)),
    }


def _scenario_recovery():
    """S3 — irrelevant first result, one bounded recovery round."""
    clause = _cri_clause()
    irrelevant = _outcome(
        "ok", structured={"items": [{"name": "BALANCA 1"}]}
    )
    relevant = _outcome(
        "ok",
        structured={
            "items": [{"name": "TERMINAL ILHOS TUBULAR 16MM"}]
        },
    )
    provider = _items_provider([irrelevant, relevant])
    model = RelevanceProposalModel(
        [
            _rel_select(
                "mcp:alpha", "search_items",
                args={"arguments": {"query": "terminal"}},
                relevance=None,
            ),
            {
                GOAL_EVIDENCE_RELEVANCE_INSTRUCTION_ID: {
                    "correspondence": "irrelevant",
                    "mismatch_hint": "scales, not terminals",
                }
            },
            {
                ARGUMENTS_INSTRUCTION_ID: {
                    "arguments": {"query": "terminal ilhos"}
                }
            },
            {
                GOAL_EVIDENCE_RELEVANCE_INSTRUCTION_ID: {
                    "correspondence": "corresponds",
                }
            },
        ]
    )
    return {
        "input": "terminal tubular",
        "expect": GovernedCapabilityStatus.SUCCESS,
        "kwargs": {
            "providers": [provider],
            "model": model,
            "response_intelligence_enabled": True,
            "cri_instruction_clause": clause.text,
            "cri_instruction_version": clause.version,
        },
        "meter": lambda: (len(model.requests), len(provider.calls)),
    }


def _scenario_owner_unavailable():
    """S7 — owner disabled mid-turn: truthful SOURCE_UNAVAILABLE."""
    port = FakePort(
        tools_by_specialist={"teo": TEO_TOOLS},
        errors={
            ("teo", "analyze"): SpecialistInteropError(
                SPECIALIST_DISABLED, "off"
            )
        },
    )
    model = FakeProposalModel(_select("teo", "analyze"))
    return {
        "input": "resumo",
        "expect": GovernedCapabilityStatus.SOURCE_UNAVAILABLE,
        "kwargs": {
            "port": port,
            "specialist_ids": ("teo",),
            "model": model,
        },
        "meter": lambda: (len(model.requests), len(port.calls)),
    }


def _scenario_unauthorized():
    """S8 — model proposes an invented capability: fail closed."""
    port = FakePort(tools_by_specialist={"teo": TEO_TOOLS})
    model = FakeProposalModel(_select("teo", "ghost_tool"))
    return {
        "input": "resumo",
        "expect_not": GovernedCapabilityStatus.SUCCESS,
        "kwargs": {
            "port": port,
            "specialist_ids": ("teo",),
            "model": model,
        },
        "meter": lambda: (len(model.requests), len(port.calls)),
    }


def _scenario_prepare_act():
    """S10 — ACT selected cold with no pending proposal:
    WRITE_REJECTED, zero wire calls."""
    port = FakePort(tools_by_specialist={"vista": VISTA_TOOLS})
    model = FakeProposalModel(
        _select(
            "vista",
            "commit_proposal",
            goal_class="create_or_modify",
        )
    )
    return {
        "input": "confirme a alteração",
        "expect": GovernedCapabilityStatus.WRITE_REJECTED,
        "kwargs": {
            "port": port,
            "specialist_ids": ("vista",),
            "model": model,
        },
        "meter": lambda: (len(model.requests), len(port.calls)),
    }


def _scenario_assessment_reuse():
    """S11 — H5 target: two-group recovery where round-1 assessment
    was ``foreign_evidence_required`` and recovery re-selects the
    same target. B1 may reuse the established decision (1 call);
    A and B0 pay the redundant second assessment (2 calls)."""
    from tests.test_engine_b_recovery_reuse import (
        _providers,
        _reuse_proposal,
    )

    providers = _providers()
    model = RelevanceProposalModel(_reuse_proposal())
    clause = _cri_clause()
    return {
        "input": "2 exemplos de terminal bala",
        "expect": GovernedCapabilityStatus.SUCCESS,
        "kwargs": {
            "providers": providers,
            "model": model,
            "response_intelligence_enabled": True,
            "cri_instruction_clause": clause.text,
            "cri_instruction_version": clause.version,
        },
        "meter": lambda: (
            len(model.requests),
            sum(len(p.calls) for p in providers),
        ),
        "stage_meter": lambda: _assessment_count(model),
        "stage_name": "native_assessment",
    }


SCENARIOS = {
    "S1_read": _scenario_read,
    "S2_two_records": _scenario_two_records,
    "S3_recovery": _scenario_recovery,
    "S7_owner_unavailable": _scenario_owner_unavailable,
    "S8_unauthorized_capability": _scenario_unauthorized,
    "S10_prepare_act_cold": _scenario_prepare_act,
    "S11_recovery_reuse": _scenario_assessment_reuse,
}


def main() -> int:
    rows = []
    for scenario_id, factory in SCENARIOS.items():
        for engine_id in ENGINE_IDS:
            spec = factory()
            engine = build_engine(engine_id, **spec["kwargs"])
            started = time.perf_counter()
            try:
                attempt = engine.attempt(spec["input"])
                status = attempt.status
            except Exception as exc:  # measurement, not a gate
                status = f"EXC:{type(exc).__name__}"
            latency_ms = (time.perf_counter() - started) * 1000
            model_calls, owner_calls = spec["meter"]()
            stage_meter = spec.get("stage_meter")
            stage_calls = stage_meter() if stage_meter else None
            expect = spec.get("expect")
            if expect is not None:
                conformant = status == expect
            else:
                conformant = status != spec["expect_not"]
            rows.append(
                {
                    "engine": engine_id,
                    "scenario": scenario_id,
                    "status": str(status),
                    "conformant": conformant,
                    "fake_model_calls": model_calls,
                    "owner_calls": owner_calls,
                    "stage_name": spec.get("stage_name", "-"),
                    "stage_calls": stage_calls,
                    "latency_ms": round(latency_ms, 2),
                }
            )
    header = (
        f"{'engine':<13} {'scenario':<26} {'status':<22} "
        f"{'conform':<8} {'model_calls':<12} {'owner_calls':<12} "
        f"{'stage_calls':<12} {'latency_ms':<10}"
    )
    print(header)
    print("-" * len(header))
    for row in rows:
        stage = (
            f"{row['stage_name']}={row['stage_calls']}"
            if row["stage_calls"] is not None
            else "-"
        )
        print(
            f"{row['engine']:<13} {row['scenario']:<26} "
            f"{row['status']:<22} {str(row['conformant']):<8} "
            f"{row['fake_model_calls']:<12} {row['owner_calls']:<12} "
            f"{stage:<12} {row['latency_ms']:<10}"
        )
    print()
    print(
        "NOTE: fake_model_calls = FAKE_MODEL_CALLS (scripted harness, "
        "no provider tokens). Latency is local-fake wall time — "
        "comparative only, not production cost. Engines: delia=A, "
        "langgraph_b0=B0 framework baseline, langgraph=B1 strategy."
    )
    # Divergence gate (task 04 §15): ANY cross-engine status or
    # conformance delta on an identical scenario is an invalid
    # comparison — exit nonzero. Absence of a B1 improvement is NOT
    # an error; it is reported as a metric.
    divergent = []
    by_scenario: dict[str, list] = {}
    for row in rows:
        by_scenario.setdefault(row["scenario"], []).append(row)
    for scenario_id, group in by_scenario.items():
        baseline = group[0]
        for other in group[1:]:
            if (
                other["status"] != baseline["status"]
                or other["conformant"] != baseline["conformant"]
            ):
                divergent.append((scenario_id, baseline, other))
    nonconformant = [r for r in rows if not r["conformant"]]
    print(f"OUTCOME_DIVERGENCES={len(divergent)}")
    for scenario_id, a, b in divergent:
        print(
            f"  DIVERGENT {scenario_id}: {a['engine']}={a['status']} "
            f"vs {b['engine']}={b['status']}"
        )
    print(f"NONCONFORMANT_ROWS={len(nonconformant)}")
    # H5 metric: assessment calls avoided on the reuse scenario.
    s11 = by_scenario.get("S11_recovery_reuse", [])
    if s11:
        for row in s11:
            print(
                f"  S11 {row['engine']}: assessments="
                f"{row['stage_calls']} total_calls="
                f"{row['fake_model_calls']}"
            )
    if divergent or nonconformant:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
