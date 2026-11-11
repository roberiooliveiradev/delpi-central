#!/usr/bin/env python3
"""INT-1 instruction ablation diagnostic — one group at a time vs v2.

Runs baseline + selected ablation variants on a frozen diagnostic matrix.
No Agent code changes. Instruction version selected via env only.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import uuid
from collections.abc import Mapping
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
ensure_trace_dir = _trace.ensure_trace_dir
_LLM_USAGE = _native._LLM_USAGE
_compose = _native._compose
_install_finalize_capture = _native._install_finalize_capture
_install_usage_meter = _native._install_usage_meter
_subject_token = _native._subject_token
_install_catalog_and_progress_capture = (
    _or._install_catalog_and_progress_capture
)
_install_catalog_capture = _or._install_catalog_capture
run_scenario = _or.run_scenario
_refuse_insecure = _or._refuse_insecure

BASELINE = "generalist-semantic-v2"
VARIANTS = [
    BASELINE,
    "generalist-semantic-ablation-obj-v1",
    "generalist-semantic-ablation-prog-v1",
    "generalist-semantic-ablation-disc-v1",
]

# Diagnostic matrix (frozen). H4 included for dashboard hypothesis.
DIAGNOSTIC = [
    {
        "id": "P1_product_structure",
        "question": "Qual é a estrutura do produto 90260921?",
    },
    {
        "id": "P2_transformation_processes",
        "question": "Quais processos de transformação estão cadastrados?",
    },
    {
        "id": "P3_visualization_formats",
        "question": "Quais formatos de visualização de dados estão disponíveis?",
    },
    {
        "id": "G1_semantic_reword_structure",
        "question": (
            "Mostre a árvore de componentes e relações do item 90260921."
        ),
    },
    {
        "id": "H4_teo_dashboard_summary",
        "question": (
            "Mostre o resumo ao vivo dos indicadores do Transformômetro."
        ),
    },
]

# Cost ceiling (documented before live calls).
MAX_ARMS = len(VARIANTS)
MAX_SCENARIOS_PER_ARM = len(DIAGNOSTIC)
MAX_REPETITIONS = 1
MAX_SCENARIO_RUNS = MAX_ARMS * MAX_SCENARIOS_PER_ARM * MAX_REPETITIONS
# Empirical prior: ~20–90s/scenario; soft wall ~45 min.
MAX_WALL_SECONDS = 45 * 60


def _git_sha() -> str:
    env = (os.environ.get("DELIA_EVALUATED_SHA") or "").strip()
    if env:
        return env
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


def _short_target(target: str | None) -> str | None:
    if not target:
        return None
    if "specialist_id='" in target:
        sid = target.split("specialist_id='")[1].split("'")[0]
        tool = target.rsplit("):", 1)[-1]
        return f"{sid}:{tool}"
    return target[:80]


def run_arm(instruction_version: str) -> dict:
    os.environ["DELIA_INVESTIGATION_INSTRUCTION_VERSION"] = (
        instruction_version
    )
    selected = load_selected_investigation_instructions(
        instruction_version=instruction_version
    )
    settings = Settings()
    evaluation_id = (
        f"abl-{instruction_version.split('ablation-')[-1][:12]}"
        f"-{uuid.uuid4().hex[:8]}"
    )
    ensure_trace_dir()
    append_event(
        evaluation_id,
        "evaluation_meta",
        {
            "task_id": (
                "DELIA-C3-T2-INT1-INSTRUCTION-ABLATION-AND-"
                "REGRESSION-FREE-EVOLUTION-01"
            ),
            "arm": instruction_version,
            "instruction_version": selected.instruction_version,
            "instruction_base_fingerprint": selected.text_fingerprint,
            "model_id": settings.llm_model,
            "model_profile": settings.runtime_profile,
            "model_config_fingerprint": settings.runtime_config_fingerprint,
            "evaluated_sha": _git_sha(),
            "pydantic_ai": __import__("pydantic_ai").__version__,
            "max_scenario_runs_budget": MAX_SCENARIO_RUNS,
            "scenarios": [s["id"] for s in DIAGNOSTIC],
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
    _LLM_USAGE.clear()
    handler, mcp = _compose()
    _orig = mcp.call_remote_tool

    def _call_with_values(specialist, remote_name, *a, **kw):
        call_args = a[0] if a else kw.get("arguments")
        result = _orig(specialist, remote_name, *a, **kw)
        if mcp.invoke_records:
            last = mcp.invoke_records[-1]
            if isinstance(call_args, Mapping) and "args_values" not in last:
                last["args_values"] = _trace.sanitize_mapping(
                    dict(call_args)
                )
        return result

    mcp.call_remote_tool = _call_with_values  # type: ignore[method-assign]
    token = _subject_token()
    if not token:
        raise SystemExit("refused: empty subject token")

    summary = {
        "evaluation_id": evaluation_id,
        "instruction_version": selected.instruction_version,
        "instruction_base_fingerprint": selected.text_fingerprint,
        "evaluated_sha": _git_sha(),
        "model": settings.llm_model,
        "config_fingerprint": settings.runtime_config_fingerprint,
        "scenarios": {},
    }
    for spec in DIAGNOSTIC:
        scenario_holder["id"] = spec["id"]
        scenario_holder["correlation"] = f"{evaluation_id}-{spec['id']}"
        print(f"== {instruction_version} :: {spec['id']}", flush=True)
        before = len(mcp.invoke_records)
        before_u = len(_LLM_USAGE)
        started = time.monotonic()
        res = run_scenario(
            handler=handler,
            mcp=mcp,
            evaluation_id=evaluation_id,
            scenario={**spec, "prior": ()},
            token=token,
        )
        invokes = mcp.invoke_records[before:]
        usage = _LLM_USAGE[before_u:]
        first = invokes[0].get("target") if invokes else None
        summary["scenarios"][spec["id"]] = {
            "question": spec["question"],
            "repetition_id": 1,
            "elapsed_s": round(time.monotonic() - started, 1),
            "grounding": res.get("grounding"),
            "error": res.get("error"),
            "first_mcp_target": _short_target(first),
            "mcp_invoke_targets": res.get("mcp_invoke_targets"),
            "tool_calls": len(invokes),
            "limitations": res.get("limitations"),
            "content_head": (res.get("content") or "")[:220],
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
        }
        print(
            json.dumps(summary["scenarios"][spec["id"]], ensure_ascii=False)[
                :450
            ],
            flush=True,
        )
    summary["trace_dir"] = str(ensure_trace_dir() / evaluation_id)
    return summary


def main() -> int:
    _refuse_insecure()
    wall_started = time.monotonic()
    print(
        json.dumps(
            {
                "COST_CEILING": {
                    "max_arms": MAX_ARMS,
                    "max_scenarios_per_arm": MAX_SCENARIOS_PER_ARM,
                    "max_repetitions": MAX_REPETITIONS,
                    "max_scenario_runs": MAX_SCENARIO_RUNS,
                    "max_wall_seconds": MAX_WALL_SECONDS,
                    "note": (
                        "tokens/cost unavailable from provider meter; "
                        "wall+scenario caps enforce stop"
                    ),
                }
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    bundle = load_investigation_instructions(
        default_investigation_instructions_path()
    )
    for v in VARIANTS:
        assert v in bundle.instructions, v
    arms = {}
    runs = 0
    for version in VARIANTS:
        if time.monotonic() - wall_started > MAX_WALL_SECONDS:
            print("BUDGET_STOP=wall", flush=True)
            break
        if runs + MAX_SCENARIOS_PER_ARM > MAX_SCENARIO_RUNS:
            print("BUDGET_STOP=scenario_runs", flush=True)
            break
        arms[version] = run_arm(version)
        runs += MAX_SCENARIOS_PER_ARM
    out = {
        "task_id": (
            "DELIA-C3-T2-INT1-INSTRUCTION-ABLATION-AND-"
            "REGRESSION-FREE-EVOLUTION-01"
        ),
        "baseline": BASELINE,
        "variants": VARIANTS,
        "fingerprints": {
            v: bundle.select(v).text_fingerprint for v in VARIANTS
        },
        "evaluated_sha": _git_sha(),
        "scenario_runs_executed": runs,
        "arms": arms,
    }
    artifact = Path(
        os.environ.get("DELIA_EVAL_ARTIFACT_DIR")
        or (Path(_APP_ROOT) / ".battery" / "int1-instruction-ablation")
    )
    artifact.mkdir(parents=True, exist_ok=True)
    path = artifact / "ablation-comparison.json"
    path.write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(out, ensure_ascii=False, indent=1))
    print(f"ABLATION_COMPARISON_PATH={path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
