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

ENGINE_IDS = ("delia", "langgraph")


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


SCENARIOS = {
    "S1_read": _scenario_read,
    "S2_two_records": _scenario_two_records,
    "S3_recovery": _scenario_recovery,
    "S7_owner_unavailable": _scenario_owner_unavailable,
    "S8_unauthorized_capability": _scenario_unauthorized,
    "S10_prepare_act_cold": _scenario_prepare_act,
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
                    "latency_ms": round(latency_ms, 2),
                }
            )
    header = (
        f"{'engine':<10} {'scenario':<26} {'status':<22} "
        f"{'conform':<8} {'model_calls':<12} {'owner_calls':<12} "
        f"{'latency_ms':<10}"
    )
    print(header)
    print("-" * len(header))
    for row in rows:
        print(
            f"{row['engine']:<10} {row['scenario']:<26} "
            f"{row['status']:<22} {str(row['conformant']):<8} "
            f"{row['fake_model_calls']:<12} {row['owner_calls']:<12} "
            f"{row['latency_ms']:<10}"
        )
    print()
    print(
        "NOTE: fake_model_calls = FAKE_MODEL_CALLS (scripted harness, "
        "no provider tokens). Latency is local-fake wall time — "
        "comparative only, not production cost."
    )
    divergent = [
        (a, b)
        for a in rows
        for b in rows
        if a["scenario"] == b["scenario"]
        and a["engine"] == "delia"
        and b["engine"] == "langgraph"
        and (a["status"] != b["status"] or a["conformant"] != b["conformant"])
    ]
    print(
        f"OUTCOME_DIVERGENCES={len(divergent)} "
        "(status/conformance deltas between engines)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
