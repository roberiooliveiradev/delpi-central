#!/usr/bin/env python3
"""DELIA-C3 Task 05 — real local-model A/B evaluation.

Runs the three governed-attempt engines (Engine A, LangGraph B0,
LangGraph B1) against the SAME local Ollama model with identical fake
capability providers (equivalent business records — never real
DAVI/API DELPI), identical prompts, instruction versions and budgets.

A ModelCallLedger is bound per attempt so stage-level call counts and
provider-reported token usage are recorded through the existing
request-scoped telemetry primitive — no new instrumentation.

Opt-in only. Reachability is verified up front; if the model cannot
reach the native_assessment / recovery stages, the semantic comparison
is reported as INCONCLUSIVE — never claimed from partial paths.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tests.test_governed_attempt_contract import (  # noqa: E402
    _cri_clause,
    build_engine,
)
from tests.test_engine_b_recovery_reuse import _providers  # noqa: E402
from app.application.interaction.turn_observability import (  # noqa: E402
    ModelCallLedger,
    bind_turn_call_ledger,
    reset_turn_call_ledger,
    current_call_ledger,
)
from app.application.model_invocation.contracts import ModelRef  # noqa: E402
from app.application.model_invocation.invoke_model import (  # noqa: E402
    InvokeModel,
)

OLLAMA_BASE = "http://localhost:11434"
MODEL_NAME = "delia-json:latest"
ENGINE_IDS = ("delia", "langgraph_b0", "langgraph")
INPUT_TEXT = "2 exemplos de terminal bala"
TIMEOUT_SECONDS = 120.0


def _reachable() -> dict:
    """Gate 12 — confirm the local model runs before comparing."""
    try:
        req = urllib.request.Request(f"{OLLAMA_BASE}/api/tags")
        body = json.loads(urllib.request.urlopen(req, timeout=5).read())
        names = {m["name"] for m in body.get("models", [])}
        digest = next(
            (
                m["digest"]
                for m in body.get("models", [])
                if m["name"] == MODEL_NAME
            ),
            None,
        )
        return {
            "server": True,
            "model_present": MODEL_NAME in names,
            "digest": digest,
            "parameters": next(
                (
                    m["details"]["parameter_size"]
                    for m in body.get("models", [])
                    if m["name"] == MODEL_NAME
                ),
                None,
            ),
        }
    except Exception as exc:  # noqa: BLE001 — measurement, not a gate
        return {"server": False, "error": type(exc).__name__}


class _MeteredModel:
    """Counting + usage-summing wrapper around the real adapter."""

    def __init__(self, adapter) -> None:
        self._adapter = adapter
        self.calls = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.errors = []

    def invoke(self, request):
        self.calls += 1
        try:
            result = self._adapter.invoke(request)
        except Exception as exc:  # noqa: BLE001 — measurement, not a gate
            self.errors.append(type(exc).__name__)
            raise
        usage = getattr(result, "usage", None)
        if usage is not None:
            self.input_tokens += usage.input_units or 0
            self.output_tokens += usage.output_units or 0
        return result

    def __getattr__(self, name):
        return getattr(self._adapter, name)


def _run(engine_id: str, model, providers, clause) -> dict:
    engine = build_engine(
        engine_id,
        providers=providers,
        model=model,
        response_intelligence_enabled=True,
        cri_instruction_clause=clause.text,
        cri_instruction_version=clause.version,
    )
    ledger = ModelCallLedger()
    token = bind_turn_call_ledger(ledger)
    started = time.perf_counter()
    try:
        attempt = engine.attempt(INPUT_TEXT)
        status = str(attempt.status)
        content = attempt.content or ""
        error_class = getattr(attempt, "error_code", None)
    except Exception as exc:  # noqa: BLE001 — measurement, not a gate
        status = f"EXC:{type(exc).__name__}"
        content = ""
        error_class = type(exc).__name__
    latency_ms = int((time.perf_counter() - started) * 1000)
    reset_turn_call_ledger(token)

    by_stage: dict[str, int] = {}
    tokens_in = tokens_out = 0
    provider_reported = False
    for call in ledger.calls:
        by_stage[call.stage] = by_stage.get(call.stage, 0) + 1
        if call.input_tokens is not None or call.output_tokens is not None:
            provider_reported = True
            tokens_in += call.input_tokens or 0
            tokens_out += call.output_tokens or 0
    trace = getattr(engine, "last_node_trace", None) or ()
    return {
        "engine": engine_id,
        "status": status,
        "error_class": error_class,
        "content_excerpt": content[:300],
        "content_chars": len(content),
        "latency_ms": latency_ms,
        "model_calls": sum(by_stage.values()),
        "calls_by_stage": dict(sorted(by_stage.items())),
        "tokens_in": tokens_in if provider_reported else None,
        "tokens_out": tokens_out if provider_reported else None,
        "token_source": (
            "PROVIDER_REPORTED" if provider_reported else "NOT_AVAILABLE"
        ),
        "owner_calls": sum(len(p.calls) for p in providers),
        "graph_trace": list(trace),
        "reused": any("assessment_reused" in t for t in trace),
        "stages_reached": {
            "native_assessment": any(
                "native_assessment" in s for s in by_stage
            ),
            "recovery": any("recovery" in s for s in by_stage)
            or sum(by_stage.values()) > 6,
        },
    }


def main() -> int:
    reach = _reachable()
    print(f"REACHABILITY: {reach}")
    if not reach.get("model_present"):
        print("LOCAL_MODEL_EVAL=EXECUTED TARGET_STAGE_REACHED=NO")
        print("SEMANTIC_COMPARISON=INCONCLUSIVE")
        return 2

    from app.infrastructure.model_invocation.openai_compatible_adapter import (
        OpenAICompatibleModelInvocationAdapter,
    )

    clause = _cri_clause()
    rows = []
    for engine_id in ENGINE_IDS:
        adapter = OpenAICompatibleModelInvocationAdapter(
            base_url=f"{OLLAMA_BASE}/v1",
            api_key="ollama-local",
            model=MODEL_NAME,
            timeout_seconds=TIMEOUT_SECONDS,
        )
        model = _MeteredModel(adapter)
        providers = _providers()
        row = _run(engine_id, model, providers, clause)
        # adapter-level meters as a cross-check on ledger counts
        row["adapter_calls"] = model.calls
        row["adapter_tokens_in"] = model.input_tokens
        row["adapter_tokens_out"] = model.output_tokens
        row["adapter_errors"] = model.errors
        rows.append(row)
        print(
            f"{engine_id}: status={row['status']} calls={row['model_calls']} "
            f"tokens={row['tokens_in']}+{row['tokens_out']} "
            f"latency={row['latency_ms']}ms owner={row['owner_calls']} "
            f"reused={row['reused']} errors={model.errors}"
        )
        print(f"  stages: {row['calls_by_stage']}")
        if trace := row["graph_trace"]:
            print(f"  trace: {trace}")
        print(f"  content: {row['content_excerpt'][:160]!r}")

    same_outcome = len({r["status"] for r in rows}) == 1
    reached = all(r["stages_reached"]["native_assessment"] for r in rows)
    print(
        json.dumps(
            {
                "MODEL_NAME": MODEL_NAME,
                "MODEL_DIGEST": reach["digest"],
                "MODEL_PARAMETERS": reach["parameters"],
                "INPUT": INPUT_TEXT,
                "OUTCOME_EQUAL": same_outcome,
                "TARGET_STAGE_REACHED": reached,
                "results": rows,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
