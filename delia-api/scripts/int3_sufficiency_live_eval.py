"""INT-3 SUFFICIENCY SPECIALIST live eval — real Qwen + real MCP.

Runs ONE bounded READ scenario through the real composed turn handler
with ``DELIA_TWO_AGENT_EXPERIMENT=1`` and
``DELIA_THREE_AGENT_EXPERIMENT=1`` (both resolved from Settings —
fail-closed at boot in production or without the two-Agent flag).

Proof points: real model calls per Agent stage, the INT-3 typed
``SufficiencyAssessmentProposal`` the model emitted, the Application
acceptor verdict on it, owner evidence collected, and the final
grounded outcome. INCONCLUSIVE/NON_GROUNDED is a valid honest result;
nothing is faked. Never prints tokens, secrets, or auth headers.
"""

from __future__ import annotations

import dataclasses
import importlib.util as _ilu
import json
import os
import sys
import time
from pathlib import Path as _Path

sys.path.insert(0, os.environ.get("DELIA_APP_ROOT", "/app"))


def _env(name: str) -> str:
    return (os.environ.get(name) or "").strip()


# Reuse the native-MCP eval driver verbatim (compose/run/meter/auth).
_driver_path = _Path(__file__).resolve().parent / (
    "native_mcptoolset_direct_eval.py"
)
_driver_spec = _ilu.spec_from_file_location(
    "native_mcp_eval_driver", _driver_path
)
if _driver_spec is None or _driver_spec.loader is None:
    raise RuntimeError("cannot load native_mcptoolset_direct_eval")
_driver = _ilu.module_from_spec(_driver_spec)
sys.modules[_driver_spec.name] = _driver
_driver_spec.loader.exec_module(_driver)


_SUFF_CAPTURE: dict = {"proposals": [], "acceptances": []}


def _install_sufficiency_capture() -> None:
    """Wrap the Application acceptor — eval introspection only; the
    wrapped call is untouched. Records every model proposal and the
    deterministic verdict, so the report shows propose-vs-decide."""
    from app.application.capability_provision import (
        semantic_capability_support as _scs,
    )

    original = _scs._accept_sufficiency_assessment

    def _wrapped(*, proposal, **kwargs):
        acceptance = original(proposal=proposal, **kwargs)
        _SUFF_CAPTURE["proposals"].append(
            dataclasses.asdict(proposal)
            if dataclasses.is_dataclass(proposal)
            else str(proposal)[:2000]
        )
        _SUFF_CAPTURE["acceptances"].append(
            dataclasses.asdict(acceptance)
            if dataclasses.is_dataclass(acceptance)
            else {"accepted": getattr(acceptance, "accepted", None)}
        )
        return acceptance

    # The orchestrator imported the symbol by name — patch BOTH the
    # module attribute and the orchestrator's bound reference.
    _scs._accept_sufficiency_assessment = _wrapped
    try:
        from app.infrastructure.orchestration import (
            pydantic_ai_investigation as _inv,
        )

        if getattr(_inv, "_accept_sufficiency_assessment", None) is (
            original
        ):
            _inv._accept_sufficiency_assessment = _wrapped
    except Exception:
        pass


def main() -> int:
    for required in (
        "DEV_PORTAL_USERNAME",
        "DEV_PORTAL_PASSWORD",
        "KEYCLOAK_URL",
    ):
        if not _env(required):
            print(f"missing env {required}")
            return 2
    _driver._install_finalize_capture()
    _driver._install_usage_meter()
    _install_sufficiency_capture()
    cost_before = _driver._openrouter_usage(_env("DELIA_LLM_API_KEY"))
    from app.infrastructure.config.settings import Settings

    settings = Settings()
    flags = {
        "two_agent_experiment": bool(
            getattr(settings, "two_agent_experiment", False)
        ),
        "three_agent_experiment": bool(
            getattr(settings, "three_agent_experiment", False)
        ),
        "environment": settings.environment,
    }
    if not flags["three_agent_experiment"]:
        print("REFUSED: DELIA_THREE_AGENT_EXPERIMENT not active")
        return 3
    handler, mcp = _driver._compose()
    scenarios = json.loads(
        _env("DELIA_EVAL_SCENARIOS_JSON") or "[]"
    ) or [
        {
            "id": "INT3_read_processes",
            "question": (
                "Quais processos estão cadastrados no Transformômetro?"
            ),
            "prior": [],
        }
    ]
    out = {
        "model": settings.llm_model,
        "runtime_profile": settings.runtime_profile,
        "config_fingerprint": settings.runtime_config_fingerprint,
        "experiment_flags": flags,
        "instruction_version": "sufficiency_instructions.delpi.json",
        "scenarios": {},
    }
    started_all = time.monotonic()
    for spec in scenarios:
        sid, question = spec["id"], spec["question"]
        before_proposals = len(_SUFF_CAPTURE["proposals"])
        try:
            res = _driver._run(
                handler,
                mcp,
                question,
                _driver._subject_token(),
                prior_turns=_driver._prior_turns(spec.get("prior")),
            )
        except Exception as exc:
            res = {"error": type(exc).__name__}
        _driver._write_artifact(sid, question, res)
        out["scenarios"][sid] = {
            k: (v[:160] if k == "content" else v)
            for k, v in res.items()
            if k
            in (
                "content",
                "grounding",
                "error",
                "elapsed_s",
                "mcp_invoke_targets",
                "epistemic_class",
                "limitations",
                "declared_answer",
                "llm_runs",
            )
        }
        out["scenarios"][sid]["int3_proposals"] = _SUFF_CAPTURE[
            "proposals"
        ][before_proposals:]
        out["scenarios"][sid]["int3_acceptances"] = _SUFF_CAPTURE[
            "acceptances"
        ][before_proposals:]
        print(
            f"== {sid}: "
            f"{json.dumps(out['scenarios'][sid], ensure_ascii=False)}"
        )
    cost_after = _driver._openrouter_usage(_env("DELIA_LLM_API_KEY"))
    out["external_usage"] = {
        "model_calls": len(_driver._LLM_USAGE),
        "input_tokens": sum(
            (u["usage"] or {}).get("input_tokens", 0)
            for u in _driver._LLM_USAGE
        ),
        "output_tokens": sum(
            (u["usage"] or {}).get("output_tokens", 0)
            for u in _driver._LLM_USAGE
        ),
        "total_tokens": sum(
            (u["usage"] or {}).get("input_tokens", 0)
            + (u["usage"] or {}).get("output_tokens", 0)
            for u in _driver._LLM_USAGE
        ),
        "latency_ms_total": sum(
            u["elapsed_ms"] for u in _driver._LLM_USAGE
        ),
        "wall_s_total": round(time.monotonic() - started_all, 1),
        "openrouter_cost_usd": (
            round(cost_after - cost_before, 6)
            if cost_before is not None and cost_after is not None
            else None
        ),
    }
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
