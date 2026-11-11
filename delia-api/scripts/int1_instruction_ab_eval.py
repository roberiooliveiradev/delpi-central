#!/usr/bin/env python3
"""INT-1 instruction A/B real eval — baseline vs candidate (Qwen 14B).

Frozen dataset. Same model/profile/tool surface; only
``DELIA_INVESTIGATION_INSTRUCTION_VERSION`` differs between arms.
Does not alter Agent decision logic beyond the instruction resource.
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
_or = _load_script(
    "int1_openrouter_qwen14b_instrumented_eval",
    "int1_openrouter_qwen14b_instrumented_eval.py",
)

from app.infrastructure.config.cri_instruction_resource import (  # noqa: E402
    load_investigation_instructions,
    default_investigation_instructions_path,
)
from app.infrastructure.config.settings import Settings  # noqa: E402
from app.infrastructure.orchestration.pydantic_ai_investigation import (  # noqa: E402
    load_selected_investigation_instructions,
)

append_event = _trace.append_event
check_security_gate = _trace.check_security_gate
ensure_trace_dir = _trace.ensure_trace_dir
_CAPTURE = _native._CAPTURE
_LLM_USAGE = _native._LLM_USAGE
_compose = _native._compose
_install_finalize_capture = _native._install_finalize_capture
_install_usage_meter = _native._install_usage_meter
_prior_turns = _native._prior_turns
_run = _native._run
_subject_token = _native._subject_token
_install_catalog_and_progress_capture = (
    _or._install_catalog_and_progress_capture
)
_install_catalog_capture = _or._install_catalog_capture
run_scenario = _or.run_scenario
_refuse_insecure = _or._refuse_insecure

TARGET_MODEL = "qwen/qwen3-14b"
TARGET_PROFILE = "openrouter_qwen"
BASELINE_VERSION = "generalist-semantic-v2"
CANDIDATE_VERSION = "generalist-semantic-v3-objective-progress"

# Frozen before candidate evaluation. Holdouts were not used to author
# the candidate prose.
KNOWN = [
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
]
HOLDOUT = [
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
SCENARIOS = KNOWN + HOLDOUT


def _git_sha() -> str:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=_APP_ROOT,
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )
    except Exception:  # noqa: BLE001
        return "NOT_OBSERVED"


def _toolset_fp(capabilities: list[str]) -> str:
    return hashlib.sha256("|".join(capabilities).encode()).hexdigest()[:16]


def run_arm(instruction_version: str) -> dict:
    os.environ["DELIA_INVESTIGATION_INSTRUCTION_VERSION"] = (
        instruction_version
    )
    # Clear import-time caches are not used for selection — loader
    # reads env on each select.
    selected = load_selected_investigation_instructions(
        instruction_version=instruction_version
    )
    settings = Settings()
    evaluation_id = (
        f"ab-{instruction_version.replace('generalist-semantic-', '')}"
        f"-{uuid.uuid4().hex[:10]}"
    )
    ensure_trace_dir()
    gate = check_security_gate()
    append_event(
        evaluation_id,
        "evaluation_meta",
        {
            "task_id": (
                "DELIA-C3-T2-INT1-SPECIALIZED-INSTRUCTIONS-AND-"
                "REAL-GENERALIZATION-EVOLUTION-01"
            ),
            "arm": instruction_version,
            "instruction_version": selected.instruction_version,
            "instruction_base_fingerprint": selected.text_fingerprint,
            "model_id": settings.llm_model,
            "model_profile": settings.runtime_profile,
            "model_config_fingerprint": settings.runtime_config_fingerprint,
            "llm_base_host": urlsplit(settings.llm_base_url or "").hostname,
            "evaluated_sha": _git_sha(),
            "pydantic_ai": __import__("pydantic_ai").__version__,
            "secure_eval_gate": gate.get("SECURE_EVAL_GATE"),
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
    # Reset usage meter between arms when possible
    _LLM_USAGE.clear()

    handler, mcp = _compose()
    # Sanitized arg values capture (same as OpenRouter harness)
    _orig_call = mcp.call_remote_tool

    def _call_with_values(specialist, remote_name, *a, **kw):
        call_args = a[0] if a else kw.get("arguments")
        result = _orig_call(specialist, remote_name, *a, **kw)
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
        raise SystemExit("refused: subject token empty")

    arm_summary: dict = {
        "evaluation_id": evaluation_id,
        "instruction_version": selected.instruction_version,
        "instruction_base_fingerprint": selected.text_fingerprint,
        "model": settings.llm_model,
        "runtime_profile": settings.runtime_profile,
        "config_fingerprint": settings.runtime_config_fingerprint,
        "evaluated_sha": _git_sha(),
        "scenarios": {},
    }
    for spec in SCENARIOS:
        scenario_holder["id"] = spec["id"]
        scenario_holder["correlation"] = f"{evaluation_id}-{spec['id']}"
        print(f"== {instruction_version} :: {spec['id']}", flush=True)
        before_invokes = len(mcp.invoke_records)
        before_usage = len(_LLM_USAGE)
        started = time.monotonic()
        res = run_scenario(
            handler=handler,
            mcp=mcp,
            evaluation_id=evaluation_id,
            scenario={**spec, "prior": ()},
            token=token,
        )
        invokes = mcp.invoke_records[before_invokes:]
        usage = _LLM_USAGE[before_usage:]
        caps = []
        snap = catalog_box.get("snapshot") or {}
        if snap:
            caps = list(snap.get("eligible_capabilities") or [])
        first_target = None
        if invokes:
            first_target = invokes[0].get("target")
        arm_summary["scenarios"][spec["id"]] = {
            "family": spec["family"],
            "question": spec["question"],
            "elapsed_s": round(time.monotonic() - started, 1),
            "error": res.get("error"),
            "grounding": res.get("grounding"),
            "mcp_invoke_targets": res.get("mcp_invoke_targets"),
            "first_mcp_target": first_target,
            "tool_calls": len(invokes),
            "declared_answer": res.get("declared_answer"),
            "limitations": res.get("limitations"),
            "content_head": (res.get("content") or "")[:200],
            "toolset_fingerprint": _toolset_fp(caps) if caps else None,
            "toolset_capabilities": caps,
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
            json.dumps(
                arm_summary["scenarios"][spec["id"]],
                ensure_ascii=False,
            )[:500],
            flush=True,
        )
    arm_summary["trace_dir"] = str(ensure_trace_dir() / evaluation_id)
    return arm_summary


def main() -> int:
    _refuse_insecure()
    bundle = load_investigation_instructions(
        default_investigation_instructions_path()
    )
    assert BASELINE_VERSION in bundle.instructions
    assert CANDIDATE_VERSION in bundle.instructions
    arms = {}
    for version in (BASELINE_VERSION, CANDIDATE_VERSION):
        arms[version] = run_arm(version)
    comparison = {
        "task_id": (
            "DELIA-C3-T2-INT1-SPECIALIZED-INSTRUCTIONS-AND-"
            "REAL-GENERALIZATION-EVOLUTION-01"
        ),
        "baseline_version": BASELINE_VERSION,
        "candidate_version": CANDIDATE_VERSION,
        "baseline_fingerprint": bundle.select(
            BASELINE_VERSION
        ).text_fingerprint,
        "candidate_fingerprint": bundle.select(
            CANDIDATE_VERSION
        ).text_fingerprint,
        "arms": arms,
    }
    print(json.dumps(comparison, ensure_ascii=False, indent=1))
    artifact = Path(
        os.environ.get("DELIA_EVAL_ARTIFACT_DIR")
        or (Path(_APP_ROOT) / ".battery" / "int1-instruction-ab-eval")
    )
    artifact.mkdir(parents=True, exist_ok=True)
    out = artifact / "ab-comparison.json"
    out.write_text(
        json.dumps(comparison, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"AB_COMPARISON_PATH={out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
