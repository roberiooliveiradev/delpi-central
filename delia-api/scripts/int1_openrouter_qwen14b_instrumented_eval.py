#!/usr/bin/env python3
"""INT-1 instrumented P3/G1 eval — OpenRouter qwen/qwen3-14b (openrouter_qwen).

Reuses the real composed investigation path and native MCPToolset.
Persists decision traces on the host via int1_secure_decision_trace.

Security:
  - Requires DELIA_EVAL_EGRESS_AUTHORIZED=1
  - Requires DELIA_LLM_BASE_URL host == openrouter.ai (no localhost proxy)
  - Refuses production identity (DELIA_ENV must be development)
  - Never logs tokens/secrets

Does not alter Agent selection/progress/finalize logic — capture only.
"""

from __future__ import annotations

import dataclasses
import json
import os
import sys
import time
import uuid
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import urlsplit

_APP_ROOT = os.environ.get(
    "DELIA_APP_ROOT", str(Path(__file__).resolve().parents[1])
)
sys.path.insert(0, _APP_ROOT)

import importlib.util


def _load_script(module_name: str, filename: str):
    path = Path(_APP_ROOT) / "scripts" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


_trace = _load_script(
    "int1_secure_decision_trace", "int1_secure_decision_trace.py"
)
_native = _load_script(
    "native_mcptoolset_direct_eval", "native_mcptoolset_direct_eval.py"
)

from app.infrastructure.config.settings import Settings  # noqa: E402

append_event = _trace.append_event
check_security_gate = _trace.check_security_gate
ensure_trace_dir = _trace.ensure_trace_dir
sanitize_mapping = _trace.sanitize_mapping
_CAPTURE = _native._CAPTURE
_LLM_USAGE = _native._LLM_USAGE
_compose = _native._compose
_CountingMcpAdapter = _native._CountingMcpAdapter
_install_finalize_capture = _native._install_finalize_capture
_install_usage_meter = _native._install_usage_meter
_prior_turns = _native._prior_turns
_run = _native._run
_subject_token = _native._subject_token



TARGET_MODEL = "qwen/qwen3-14b"
TARGET_PROFILE = "openrouter_qwen"
TARGET_HOST = "openrouter.ai"

# Exact scenarios from the prior real-eval harness (G1 independent reword).
SCENARIOS = [
    {
        "id": "P3_visualization_formats",
        "question": "Quais formatos de visualização de dados estão disponíveis?",
        "prior": (),
    },
    {
        "id": "G1_semantic_reword_structure",
        "question": "Mostre a árvore de componentes e relações do item 90260921.",
        "prior": (),
    },
    {
        "id": "P1_product_structure_control",
        "question": "Qual é a estrutura do produto 90260921?",
        "prior": (),
    },
]


def _refuse_insecure() -> None:
    gate = check_security_gate()
    host = urlsplit(Settings().llm_base_url or "").hostname or ""
    if Settings().environment == "production":
        raise SystemExit("refused: DELIA_ENV=production not allowed for this eval")
    if host.lower() != TARGET_HOST:
        raise SystemExit(
            f"refused: LLM host must be {TARGET_HOST!r}, got {host!r} "
            "(localhost proxy is forbidden)"
        )
    if gate.get("SECURE_EVAL_GATE") not in {
        "READY_FOR_ISOLATED_EVAL",
        "PENDING_ISOLATION_EVIDENCE",
    }:
        # READY preferred; PENDING only if blockers empty but gate name lags —
        # still refuse when blockers present.
        if gate.get("BLOCKERS"):
            raise SystemExit(
                "refused: security gate blocked: "
                + "; ".join(gate["BLOCKERS"])
            )
    settings = Settings()
    if settings.llm_egress_blocked_reason:
        raise SystemExit(f"refused: {settings.llm_egress_blocked_reason}")
    if settings.llm_model != TARGET_MODEL:
        raise SystemExit(
            f"refused: model {settings.llm_model!r} != {TARGET_MODEL!r}"
        )
    if settings.runtime_profile != TARGET_PROFILE:
        raise SystemExit(
            f"refused: profile {settings.runtime_profile!r} != {TARGET_PROFILE!r}"
        )


def _install_catalog_and_progress_capture(
    *,
    evaluation_id: str,
    scenario_holder: dict,
) -> None:
    """Eval-only wrappers — return values unchanged."""
    from app.infrastructure.orchestration import pydantic_ai_investigation as pai

    original_proj = pai._attempt_projection
    seq = {"n": 0}

    def _proj_wrapped(attempt, **kwargs):
        projection = original_proj(attempt, **kwargs)
        seq["n"] += 1
        scenario_id = scenario_holder.get("id")
        correlation = scenario_holder.get("correlation")
        caps = getattr(attempt, "capability_id", None)
        append_event(
            evaluation_id,
            "tool_observation",
            {
                "call_sequence_number": seq["n"],
                "capability_id": str(caps or "") or None,
                "status": (
                    attempt.status.value
                    if getattr(attempt, "status", None) is not None
                    else None
                ),
                "investigation_progress_class": projection.get(
                    "investigation_progress"
                ),
                "evidence_citable": projection.get("evidence_citable"),
                "coverage_note": projection.get("coverage_note"),
                "authoritative_root_code": projection.get(
                    "authoritative_root_code"
                ),
                "provenance_specialist": projection.get(
                    "provenance_specialist"
                ),
                "provenance_capability": projection.get(
                    "provenance_capability"
                ),
                "action_id": projection.get("action_id"),
                "limitations": projection.get("limitations"),
                "uncovered_user_identifiers": projection.get(
                    "uncovered_user_identifiers"
                ),
                "pagination": projection.get("pagination"),
                "continuation_note": projection.get("continuation_note"),
                "owner_result_content_head": (attempt.content or "")[:400]
                or None,
            },
            scenario_id=scenario_id,
            correlation_id=correlation,
        )
        return projection

    pai._attempt_projection = _proj_wrapped  # type: ignore[assignment]

    # Capture model-visible catalog when the orchestrator prefetches it.
    original_init_tools = None
    Orchestrator = pai.PydanticAiInvestigationOrchestrator
    # Hook _project via gates after compose — installed in run_scenario.


def _catalog_snapshot(live_catalog: list) -> dict:
    tools = []
    specialists: set[str] = set()
    for entry in live_catalog:
        if not isinstance(entry, Mapping):
            continue
        cap = str(entry.get("capability_id") or "")
        remote = str(entry.get("remote_name") or "")
        specialist = str(
            entry.get("specialist_id")
            or entry.get("provider_id")
            or entry.get("group_id")
            or ""
        )
        if specialist:
            specialists.add(specialist)
        tools.append(
            {
                "capability_id": cap,
                "remote_name": remote,
                "specialist": specialist,
                "operation_class": entry.get("operation_class"),
                "description": (entry.get("description") or "")[:500],
                "input_schema": sanitize_mapping(entry.get("input_schema") or {}),
            }
        )
    return {
        "eligible_specialists": sorted(specialists),
        "eligible_capabilities": [t["capability_id"] for t in tools],
        "model_visible_tool_names": [t["capability_id"] for t in tools],
        "tools": tools,
        "tool_count": len(tools),
    }


def _install_catalog_capture(
    *,
    evaluation_id: str,
    scenario_holder: dict,
    catalog_box: dict,
) -> None:
    from app.application.capability_provision import (
        governed_capability_orchestrator as gco,
    )

    original = gco.OperationalCapabilityOrchestrator._project_semantic_tool_catalog

    def _wrapped(self, *args, **kwargs):
        live = original(self, *args, **kwargs)
        snap = _catalog_snapshot(list(live or ()))
        catalog_box["snapshot"] = snap
        append_event(
            evaluation_id,
            "model_visible_toolset",
            snap,
            scenario_id=scenario_holder.get("id"),
            correlation_id=scenario_holder.get("correlation"),
        )
        return live

    gco.OperationalCapabilityOrchestrator._project_semantic_tool_catalog = (
        _wrapped
    )


def run_scenario(
    *,
    handler,
    mcp: _CountingMcpAdapter,
    evaluation_id: str,
    scenario: dict,
    token: str,
) -> dict:
    scenario_holder = {
        "id": scenario["id"],
        "correlation": f"{evaluation_id}-{scenario['id']}",
    }
    before_records = len(mcp.invoke_records)
    before_usage = len(_LLM_USAGE)
    _CAPTURE["declared_answer"] = None
    _CAPTURE["collected"] = None

    append_event(
        evaluation_id,
        "scenario_start",
        {"question": scenario["question"], "prior": list(scenario["prior"])},
        scenario_id=scenario["id"],
        correlation_id=scenario_holder["correlation"],
    )

    # Re-bind progress capture sequence per scenario via fresh install is heavy;
    # sequence numbers continue across scenarios (acceptable) — reset by
    # reinstalling projection wrap once in main.

    result = _run(
        handler,
        mcp,
        scenario["question"],
        token,
        prior_turns=_prior_turns(scenario["prior"]),
    )

    # MCP wire records (specialist:remote + arg shapes/values + snippets).
    # Native adapter stores type shapes; optional sanitized values if present.
    records = mcp.invoke_records[before_records:]
    for index, record in enumerate(records, start=1):
        raw_args = record.get("args")
        append_event(
            evaluation_id,
            "mcp_invoke",
            {
                "call_sequence_number": index,
                "target": record.get("target"),
                "elapsed_s": record.get("elapsed_s"),
                "argument_keys": list(raw_args.keys())
                if isinstance(raw_args, Mapping)
                else None,
                "argument_types": raw_args,
                "argument_values_sanitized": sanitize_mapping(
                    record.get("args_values") or {}
                )
                if record.get("args_values") is not None
                else None,
                "result_snippet_head": str(record.get("result_snippet") or "")[
                    :500
                ],
                "error": record.get("error"),
            },
            scenario_id=scenario["id"],
            correlation_id=scenario_holder["correlation"],
        )

    usage_slice = _LLM_USAGE[before_usage:]
    append_event(
        evaluation_id,
        "finalization",
        {
            "declared_answer": _CAPTURE.get("declared_answer"),
            "collected_attempts": _CAPTURE.get("collected"),
            "grounding": result.get("grounding"),
            "epistemic_class": result.get("epistemic_class"),
            "limitations": result.get("limitations"),
            "content_head": (result.get("content") or "")[:400],
            "mcp_invoke_targets": result.get("mcp_invoke_targets"),
            "llm_runs": {
                "count": len(usage_slice),
                "input_tokens": sum(
                    (u["usage"] or {}).get("input_tokens", 0)
                    for u in usage_slice
                ),
                "output_tokens": sum(
                    (u["usage"] or {}).get("output_tokens", 0)
                    for u in usage_slice
                ),
                "elapsed_ms": sum(u["elapsed_ms"] for u in usage_slice),
            },
            "error": result.get("error"),
            "elapsed_s": result.get("elapsed_s"),
        },
        scenario_id=scenario["id"],
        correlation_id=scenario_holder["correlation"],
    )
    return result


def main() -> int:
    ensure_trace_dir()
    _refuse_insecure()
    settings = Settings()
    evaluation_id = f"or-qwen14b-{uuid.uuid4().hex[:12]}"
    gate = check_security_gate()

    append_event(
        evaluation_id,
        "evaluation_meta",
        {
            "task_id": (
                "DELIA-C3-T2-INT1-LOCAL-QWEN14B-SETUP-AND-INSTRUMENTED-"
                "ROOT-CAUSE-EVAL-01"
            ),
            "model_id": settings.llm_model,
            "model_profile": settings.runtime_profile,
            "model_config_fingerprint": settings.runtime_config_fingerprint,
            "llm_base_host": urlsplit(settings.llm_base_url or "").hostname,
            "environment": settings.environment,
            "secure_eval_gate": gate.get("SECURE_EVAL_GATE"),
            "pydantic_ai": __import__("pydantic_ai").__version__,
            "scenarios": [s["id"] for s in SCENARIOS],
        },
        scenario_id="session",
        correlation_id=evaluation_id,
    )

    scenario_holder: dict = {"id": None, "correlation": evaluation_id}
    catalog_box: dict = {}
    _install_finalize_capture()
    _install_usage_meter()
    _install_catalog_and_progress_capture(
        evaluation_id=evaluation_id, scenario_holder=scenario_holder
    )
    _install_catalog_capture(
        evaluation_id=evaluation_id,
        scenario_holder=scenario_holder,
        catalog_box=catalog_box,
    )

    handler, mcp = _compose()
    # Eval-only: also retain sanitized argument values (native adapter
    # keeps type shapes only). Does not alter call semantics.
    _orig_call = mcp.call_remote_tool

    def _call_with_values(specialist, remote_name, *a, **kw):
        call_args = a[0] if a else kw.get("arguments")
        result = _orig_call(specialist, remote_name, *a, **kw)
        if mcp.invoke_records:
            last = mcp.invoke_records[-1]
            if isinstance(call_args, Mapping) and "args_values" not in last:
                last["args_values"] = sanitize_mapping(dict(call_args))
        return result

    mcp.call_remote_tool = _call_with_values  # type: ignore[method-assign]

    token = _subject_token()
    if not token:
        raise SystemExit("refused: subject token empty")

    summary = {
        "evaluation_id": evaluation_id,
        "model": settings.llm_model,
        "runtime_profile": settings.runtime_profile,
        "config_fingerprint": settings.runtime_config_fingerprint,
        "secure_eval_gate": gate.get("SECURE_EVAL_GATE"),
        "scenarios": {},
    }

    for spec in SCENARIOS:
        scenario_holder["id"] = spec["id"]
        scenario_holder["correlation"] = f"{evaluation_id}-{spec['id']}"
        print(f"== starting {spec['id']}", flush=True)
        res = run_scenario(
            handler=handler,
            mcp=mcp,
            evaluation_id=evaluation_id,
            scenario=spec,
            token=token,
        )
        summary["scenarios"][spec["id"]] = {
            "elapsed_s": res.get("elapsed_s"),
            "error": res.get("error"),
            "grounding": res.get("grounding"),
            "mcp_invoke_targets": res.get("mcp_invoke_targets"),
            "declared_answer": res.get("declared_answer"),
            "limitations": res.get("limitations"),
            "content_head": (res.get("content") or "")[:160],
            "llm_runs": res.get("llm_runs"),
        }
        print(
            f"== {spec['id']}: "
            f"{json.dumps(summary['scenarios'][spec['id']], ensure_ascii=False)}",
            flush=True,
        )

    summary["external_usage"] = {
        "model_calls": len(_LLM_USAGE),
        "input_tokens": sum(
            (u["usage"] or {}).get("input_tokens", 0) for u in _LLM_USAGE
        ),
        "output_tokens": sum(
            (u["usage"] or {}).get("output_tokens", 0) for u in _LLM_USAGE
        ),
        "latency_ms_total": sum(u["elapsed_ms"] for u in _LLM_USAGE),
    }
    summary["trace_dir"] = str(
        ensure_trace_dir() / evaluation_id
    )
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
