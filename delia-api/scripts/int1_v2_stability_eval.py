#!/usr/bin/env python3
"""INT-1 v2 stability / context-recovery real eval harness.

EXTENDS existing OpenRouter / decision-trace / MCP harnesses.
Baseline instructions frozen (generalist-semantic-v2). Used for
auth-lifetime and investigation-context remediation batteries.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
import uuid
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path

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
_or = _load_script(
    "int1_openrouter_qwen14b_instrumented_eval",
    "int1_openrouter_qwen14b_instrumented_eval.py",
)

from app.infrastructure.config.cri_instruction_resource import (  # noqa: E402
    default_investigation_instructions_path,
    load_investigation_instructions,
)
from app.infrastructure.config.settings import Settings  # noqa: E402
from app.infrastructure.orchestration.pydantic_ai_investigation import (  # noqa: E402
    load_selected_investigation_instructions,
)

append_event = _trace.append_event
check_security_gate = _trace.check_security_gate
ensure_trace_dir = _trace.ensure_trace_dir
sanitize_mapping = _trace.sanitize_mapping
_LLM_USAGE = _native._LLM_USAGE
_compose = _native._compose
_install_finalize_capture = _native._install_finalize_capture
_install_usage_meter = _native._install_usage_meter
acquire_subject_access_session = _native.acquire_subject_access_session
subject_session_is_fresh = _native.subject_session_is_fresh
subject_session_public_meta = _native.subject_session_public_meta
_install_catalog_and_progress_capture = (
    _or._install_catalog_and_progress_capture
)
_install_catalog_capture = _or._install_catalog_capture
run_scenario = _or.run_scenario
_refuse_insecure = _or._refuse_insecure

from app.domain.specialist_interop.model import SpecialistRef  # noqa: E402
from app.infrastructure.auth.subject_bearer import (  # noqa: E402
    bind_subject_bearer,
    unbind_subject_bearer,
)

_PREFLIGHT_REFS = (
    SpecialistRef(
        specialist_id="davi", display_name="DAVI", owner_ref="api-delpi"
    ),
    SpecialistRef(
        specialist_id="teo",
        display_name="TEO",
        owner_ref="transformometro-api",
    ),
    SpecialistRef(
        specialist_id="vista",
        display_name="VISTA",
        owner_ref="tv-dashboard-api",
    ),
)
AUTH_SKEW_SECONDS = 90.0

BASELINE = "generalist-semantic-v2"
EXPECTED_FP = "7dbc94c5035b0f19"
TARGET_MODEL = "qwen/qwen3-14b"
TARGET_PROFILE = "openrouter_qwen"
REPETITIONS = 3

# Exact questions from int1_instruction_ab_eval.py (frozen).
SCENARIOS = [
    {
        "id": "P1_product_structure",
        "family": "known",
        "question": "Qual é a estrutura do produto 90260921?",
    },
    {
        "id": "P2_transformation_processes",
        "family": "known",
        "question": "Quais processos de transformação estão cadastrados?",
    },
    {
        "id": "P3_visualization_formats",
        "family": "known",
        "question": "Quais formatos de visualização de dados estão disponíveis?",
    },
    {
        "id": "G1_semantic_reword_structure",
        "family": "known",
        "question": (
            "Mostre a árvore de componentes e relações do item 90260921."
        ),
    },
    {
        "id": "H1_product_description",
        "family": "holdout",
        "question": "Qual a descrição do produto 90260921?",
    },
    {
        "id": "H2_missing_product_structure",
        "family": "holdout",
        "question": "Qual é a estrutura do produto 00000000?",
    },
    {
        "id": "H3_vista_playlists",
        "family": "holdout",
        "question": "Quais playlists estão disponíveis?",
    },
    {
        "id": "H4_teo_dashboard_summary",
        "family": "holdout",
        "question": (
            "Mostre o resumo ao vivo dos indicadores do Transformômetro."
        ),
    },
]

# Interleaved schedule: all scenarios for rep 1, then rep 2, then rep 3.
SCHEDULE = [
    (spec, rep)
    for rep in range(1, REPETITIONS + 1)
    for spec in SCENARIOS
]


def _load_generalization_scenarios() -> list[dict]:
    """Novel holdout frozen before live remediation eval (1 rep each)."""
    path = (
        Path(_APP_ROOT) / "scripts" / "int1_context_recovery_generalization.json"
    )
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    scenarios = payload.get("scenarios") or []
    out: list[dict] = []
    for item in scenarios:
        if not isinstance(item, Mapping):
            continue
        sid = str(item.get("id") or "").strip()
        question = str(item.get("question") or "").strip()
        if not sid or not question:
            continue
        out.append(
            {
                "id": sid,
                "family": str(item.get("family") or "generalization"),
                "question": question,
                "tests": item.get("tests"),
            }
        )
    return out


GENERALIZATION_SCENARIOS = _load_generalization_scenarios()
GENERALIZATION_SCHEDULE = [(spec, 1) for spec in GENERALIZATION_SCENARIOS]
FULL_SCHEDULE = SCHEDULE + GENERALIZATION_SCHEDULE

MAX_CORE_RUNS = len(SCHEDULE)  # 24
MAX_SCENARIO_RUNS = len(FULL_SCHEDULE)  # 24 + generalization
MAX_WALL_SECONDS = 90 * 60  # 90 min soft wall
MAX_AUTHORIZED_COST = "UNAVAILABLE_PROVIDER_METER_NULL"
TASK_ID = (
    "DELIA-C3-T2-INT1-INVESTIGATION-CONTEXT-"
    "TOOL-SURFACE-AND-RECOVERY-REMEDIATION-01"
)


def _env_identity() -> dict:
    return {
        "evaluated_sha": (os.environ.get("DELIA_EVALUATED_SHA") or "").strip()
        or "INCONCLUSIVE",
        "runtime_image_digest": (
            os.environ.get("DELIA_RUNTIME_IMAGE_DIGEST") or ""
        ).strip()
        or "NOT_OBSERVED",
        "runtime_image_id": (
            os.environ.get("DELIA_RUNTIME_IMAGE_ID") or ""
        ).strip()
        or "NOT_OBSERVED",
        "runtime_container_id": (
            os.environ.get("DELIA_RUNTIME_CONTAINER_ID") or ""
        ).strip()
        or "NOT_OBSERVED",
        "host_git_sha_fallback": _host_git_sha(),
    }


def _host_git_sha() -> str:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=str(Path(_APP_ROOT).parent),
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )
    except Exception:  # noqa: BLE001
        return "NOT_OBSERVED"


def _toolset_fp(capabilities: list[str]) -> str:
    return hashlib.sha256("|".join(capabilities).encode()).hexdigest()[:16]


def _short_target(target: str | None) -> str | None:
    if not target:
        return None
    if "specialist_id='" in target:
        sid = target.split("specialist_id='")[1].split("'")[0]
        tool = target.rsplit("):", 1)[-1]
        return f"{sid}:{tool}"
    return target[:80]


def _load_rubric() -> dict:
    path = Path(_APP_ROOT) / "scripts" / "int1_v2_stability_rubric.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _preflight_mcp_catalog(mcp, token: str) -> dict:
    """Authorized catalog probe without LLM. Never logs the bearer."""
    binding = bind_subject_bearer(token)
    results: dict[str, dict] = {}
    try:
        for ref in _PREFLIGHT_REFS:
            started = time.time()
            try:
                tools = mcp.list_remote_tools(ref, timeout_seconds=12.0)
                results[ref.specialist_id] = {
                    "status": "OK",
                    "tool_count": len(tools or ()),
                    "elapsed_s": round(time.time() - started, 2),
                }
            except Exception as exc:  # noqa: BLE001 — preflight reports
                code = getattr(exc, "code", None) or type(exc).__name__
                results[ref.specialist_id] = {
                    "status": "FAIL",
                    "error_code": str(code),
                    "elapsed_s": round(time.time() - started, 2),
                }
    finally:
        unbind_subject_bearer(binding)
    ok = all(v.get("status") == "OK" and v.get("tool_count", 0) > 0 for v in results.values())
    return {
        "auth_valid": ok,
        "mcp_catalog_available": ok,
        "owners": results,
    }


def main() -> int:
    _refuse_insecure()
    identity = _env_identity()
    if identity["evaluated_sha"] in {"", "INCONCLUSIVE", "NOT_OBSERVED"}:
        print(
            json.dumps(
                {
                    "BLOCKED": "EVALUATED_SHA_INCONCLUSIVE",
                    "identity": identity,
                    "message": (
                        "Host must inject DELIA_EVALUATED_SHA before live calls"
                    ),
                },
                ensure_ascii=False,
                indent=2,
            ),
            flush=True,
        )
        return 6

    rubric = _load_rubric()
    assert rubric.get("frozen_before_eval") is True
    bundle = load_investigation_instructions(
        default_investigation_instructions_path()
    )
    selected = load_selected_investigation_instructions(
        instruction_version=BASELINE
    )
    assert selected.instruction_version == BASELINE
    assert selected.text_fingerprint == EXPECTED_FP
    os.environ["DELIA_INVESTIGATION_INSTRUCTION_VERSION"] = BASELINE

    settings = Settings()
    assert settings.llm_model == TARGET_MODEL
    assert settings.runtime_profile == TARGET_PROFILE
    gate = check_security_gate()
    if gate.get("SECURE_EVAL_GATE") != "READY_FOR_ISOLATED_EVAL":
        print(json.dumps(gate, ensure_ascii=False, indent=2), flush=True)
        return 5

    evaluation_id = f"ctx-rec-{uuid.uuid4().hex[:10]}"
    ensure_trace_dir()
    artifact = Path(
        os.environ.get("DELIA_EVAL_ARTIFACT_DIR")
        or (Path(_APP_ROOT) / ".battery" / "int1-context-recovery-rerun")
    )
    artifact.mkdir(parents=True, exist_ok=True)

    cost_ceiling = {
        "max_scenario_runs": MAX_SCENARIO_RUNS,
        "max_core_runs": MAX_CORE_RUNS,
        "max_generalization_runs": len(GENERALIZATION_SCHEDULE),
        "max_wall_seconds": MAX_WALL_SECONDS,
        "max_authorized_cost": MAX_AUTHORIZED_COST,
        "max_model_requests_note": (
            "profile request_limit=12 per turn; not a global budget"
        ),
        "max_tool_calls_note": "profile tool_calls_limit=8 per turn",
        "planned_runs": MAX_CORE_RUNS,
        "planned_generalization_runs": len(GENERALIZATION_SCHEDULE),
        "repetitions_per_scenario": REPETITIONS,
        "scenarios": len(SCENARIOS),
        "generalization_scenarios": len(GENERALIZATION_SCENARIOS),
    }
    print(json.dumps({"COST_CEILING": cost_ceiling}, ensure_ascii=False), flush=True)

    meta = {
        "task_id": TASK_ID,
        "evaluation_id": evaluation_id,
        "evaluation_timestamp": datetime.now(timezone.utc).isoformat(),
        "instruction_version": selected.instruction_version,
        "instruction_fingerprint": selected.text_fingerprint,
        "model_id": settings.llm_model,
        "model_profile": settings.runtime_profile,
        "model_config_fingerprint": settings.runtime_config_fingerprint,
        "pydantic_ai": __import__("pydantic_ai").__version__,
        "model_temperature": "UNAVAILABLE",
        "model_top_p": "UNAVAILABLE",
        "model_seed_if_supported": "UNAVAILABLE",
        "request_limit": 12,
        "tool_call_limit": 8,
        "timeout_settings": {
            "provider_call_timeout_seconds": 90.0,
            "model_stage_timeout_seconds": 120.0,
            "turn_budget_seconds": 300.0,
        },
        "secure_eval_gate": gate.get("SECURE_EVAL_GATE"),
        "credential_scope": gate.get("EVALUATION_CREDENTIAL_SCOPE"),
        "identity": identity,
        "cost_ceiling": cost_ceiling,
        "rubric_sha256": hashlib.sha256(
            json.dumps(rubric, sort_keys=True).encode()
        ).hexdigest()[:16],
        "schedule": [
            {"scenario_id": s["id"], "repetition_id": r} for s, r in SCHEDULE
        ],
        "generalization_schedule": [
            {"scenario_id": s["id"], "repetition_id": r}
            for s, r in GENERALIZATION_SCHEDULE
        ],
        "remediation": {
            "envelope_hint_preserves_owner_description": True,
            "pagination_projected_to_observations": True,
            "baseline_reference_doc": 298,
            "baseline_evaluation_id": "stab-v2-5b0e914eb9",
        },
    }
    append_event(
        evaluation_id,
        "evaluation_meta",
        meta,
        scenario_id="session",
        correlation_id=evaluation_id,
    )
    (artifact / "freeze-identity.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
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
    _LLM_USAGE.clear()
    handler, mcp = _compose()
    _orig = mcp.call_remote_tool

    def _call_with_values(specialist, remote_name, *a, **kw):
        call_args = a[0] if a else kw.get("arguments")
        result = _orig(specialist, remote_name, *a, **kw)
        if mcp.invoke_records:
            last = mcp.invoke_records[-1]
            if isinstance(call_args, Mapping) and "args_values" not in last:
                last["args_values"] = sanitize_mapping(dict(call_args))
        return result

    mcp.call_remote_tool = _call_with_values  # type: ignore[method-assign]

    runs: list[dict] = []
    wall_started = time.monotonic()
    executed = 0
    env_invalid = 0
    for spec, rep in FULL_SCHEDULE:
        if time.monotonic() - wall_started > MAX_WALL_SECONDS:
            print("BUDGET_STOP=wall", flush=True)
            break
        if executed >= MAX_SCENARIO_RUNS:
            print("BUDGET_STOP=scenario_runs", flush=True)
            break

        run_id = f"{spec['id']}__r{rep}__{uuid.uuid4().hex[:8]}"
        scenario_id = f"{spec['id']}__r{rep}"
        scenario_holder["id"] = scenario_id
        scenario_holder["correlation"] = f"{evaluation_id}-{run_id}"
        print(f"== {scenario_id}", flush=True)

        # Reacquire subject token per scenario — prior battery reused one
        # password-grant token across ~17 min and hit MCP auth failures
        # after ~6–7 min (subject expiry). Existing mint path only.
        session = acquire_subject_access_session()
        auth_meta = subject_session_public_meta(session)
        auth_meta["scenario_started_at_epoch"] = time.time()
        auth_meta["subject_session_fresh"] = subject_session_is_fresh(
            session, skew_seconds=AUTH_SKEW_SECONDS
        )
        preflight = _preflight_mcp_catalog(mcp, session.access_token)
        auth_meta["catalog_enumeration_started_at_epoch"] = time.time()
        auth_meta["catalog_auth_result"] = preflight
        append_event(
            evaluation_id,
            "auth_preflight",
            sanitize_mapping(auth_meta),
            scenario_id=scenario_id,
            correlation_id=scenario_holder["correlation"],
        )
        print(
            json.dumps(
                {
                    "AUTH_PREFLIGHT": {
                        "fresh": auth_meta["subject_session_fresh"],
                        "expires_in": auth_meta["auth_expires_in_seconds"],
                        "fp": auth_meta["auth_token_fingerprint"],
                        "catalog_ok": preflight.get("mcp_catalog_available"),
                        "owners": {
                            k: v.get("status")
                            for k, v in (preflight.get("owners") or {}).items()
                        },
                    }
                },
                ensure_ascii=False,
            ),
            flush=True,
        )

        if not preflight.get("mcp_catalog_available"):
            env_invalid += 1
            record = {
                "run_id": run_id,
                "scenario_id": spec["id"],
                "repetition_id": rep,
                "family": spec["family"],
                "question": spec["question"],
                "env_validity": "INVALID",
                "objective_satisfaction": "INCONCLUSIVE",
                "skip_llm": True,
                "auth_meta": auth_meta,
                "evaluated_sha": identity["evaluated_sha"],
                "runtime_image_digest": identity["runtime_image_digest"],
                "instruction_fingerprint": selected.text_fingerprint,
                "error": "ENV_PREFLIGHT_MCP_AUTH",
                "grounding": None,
                "first_mcp_target": None,
                "tool_calls": 0,
                "limitations": ["catalog_failure:mcp_authentication_failed"],
                "content_head": "",
                "llm_runs": {
                    "count": 0,
                    "input_tokens": None,
                    "output_tokens": None,
                    "elapsed_ms": 0,
                },
            }
            runs.append(record)
            executed += 1
            print(json.dumps(record, ensure_ascii=False)[:500], flush=True)
            continue

        before = len(mcp.invoke_records)
        before_u = len(_LLM_USAGE)
        started = time.monotonic()
        res = run_scenario(
            handler=handler,
            mcp=mcp,
            evaluation_id=evaluation_id,
            scenario={
                "id": scenario_id,
                "question": spec["question"],
                "prior": (),
            },
            token=session.access_token,
        )
        invokes = mcp.invoke_records[before:]
        usage = _LLM_USAGE[before_u:]
        caps = []
        snap = catalog_box.get("snapshot") or {}
        if snap:
            caps = list(snap.get("eligible_capabilities") or [])
        first = invokes[0].get("target") if invokes else None
        lim = list(res.get("limitations") or [])
        env_validity = "VALID"
        if any(
            "catalog_failure:mcp_authentication_failed" in str(x)
            for x in lim
        ) and len(invokes) == 0:
            env_validity = "INVALID"
            env_invalid += 1
        record = {
            "run_id": run_id,
            "scenario_id": spec["id"],
            "repetition_id": rep,
            "family": spec["family"],
            "question": spec["question"],
            "env_validity": env_validity,
            "auth_meta": auth_meta,
            "evaluated_sha": identity["evaluated_sha"],
            "runtime_image_digest": identity["runtime_image_digest"],
            "runtime_image_id": identity["runtime_image_id"],
            "model_id": settings.llm_model,
            "model_config_fingerprint": settings.runtime_config_fingerprint,
            "instruction_version": selected.instruction_version,
            "instruction_fingerprint": selected.text_fingerprint,
            "toolset_fingerprint": _toolset_fp(caps) if caps else None,
            "toolset_capabilities": caps,
            "elapsed_s": round(time.monotonic() - started, 1),
            "error": res.get("error"),
            "grounding": res.get("grounding"),
            "first_mcp_target": _short_target(first),
            "mcp_invoke_targets": res.get("mcp_invoke_targets"),
            "tool_call_order": [
                _short_target(i.get("target")) for i in invokes
            ],
            "tool_arguments_sanitized": [
                sanitize_mapping(i.get("args_values") or {}) for i in invokes
            ],
            "owner_errors": [i.get("error") for i in invokes],
            "tool_calls": len(invokes),
            "limitations": lim,
            "declared_answer": res.get("declared_answer"),
            "content_head": (res.get("content") or "")[:280],
            "llm_runs": {
                "count": len(usage),
                "input_tokens": sum(
                    (u["usage"] or {}).get("input_tokens", 0) for u in usage
                )
                or None,
                "output_tokens": sum(
                    (u["usage"] or {}).get("output_tokens", 0) for u in usage
                )
                or None,
                "elapsed_ms": sum(u["elapsed_ms"] for u in usage),
            },
            "scenario_finished_at_epoch": time.time(),
        }
        runs.append(record)
        executed += 1
        print(json.dumps(record, ensure_ascii=False)[:500], flush=True)

    core_runs = [r for r in runs if r.get("family") != "generalization"]
    gen_runs = [r for r in runs if r.get("family") == "generalization"]
    out = {
        "task_id": meta["task_id"],
        "evaluation_id": evaluation_id,
        "freeze": meta,
        "rubric_path": "scripts/int1_v2_stability_rubric.json",
        "auth_lifecycle": {
            "strategy": "reacquire_subject_token_per_scenario",
            "existing_mechanism": "acquire_subject_access_session/password_grant_gateway",
            "skew_seconds": AUTH_SKEW_SECONDS,
        },
        "executed_runs": executed,
        "planned_runs": MAX_CORE_RUNS,
        "planned_generalization_runs": len(GENERALIZATION_SCHEDULE),
        "invalid_runs": env_invalid,
        "valid_env_runs": executed - env_invalid,
        "core_executed_runs": len(core_runs),
        "generalization_executed_runs": len(gen_runs),
        "runs": runs,
        "core_runs": core_runs,
        "generalization_runs": gen_runs,
    }
    path = artifact / "stability-comparison.json"
    path.write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"executed_runs": executed}, ensure_ascii=False))
    print(f"STABILITY_COMPARISON_PATH={path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
