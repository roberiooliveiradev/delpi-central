"""NATIVE-MCPTOOLSET-DIRECT-ORCHESTRATION-01 — real owner eval.

Runs the REAL composed handler (real pydantic_ai investigation runtime,
real native ``MCPToolset`` discovery via the SDK client, real delegated
credential exchange, real governed ``call_remote_tool`` wire) against
the authorized specialists DAVI/TÉO/VISTA.

Scenarios:
  A DAVI single READ       — real product description
  B TÉO contextual consult — transformation initiatives
  C VISTA playlists        — operational panels
  D multi-specialist       — one question needing DAVI + VISTA data
  E generalization         — reworded variants + absent-record negative

Proof points per scenario: MCP invoke targets (governed wire calls —
process_tool_call interception precedes every one), grounding status,
content head, errors. INCONCLUSIVE is a valid outcome; nothing is
faked. Never prints tokens, secrets, or auth headers.

Env: DEV_PORTAL_USERNAME / DEV_PORTAL_PASSWORD + KEYCLOAK_URL inside
the delia-api container (or exported locally).
"""

from __future__ import annotations

import dataclasses
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from collections.abc import Mapping

sys.path.insert(0, os.environ.get("DELIA_APP_ROOT", "/app"))

from app.application.interaction.contracts import InteractiveTurnRequest
from app.application.model_invocation.contracts import (
    ConversationContextTurn,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.application.platform_access import PlatformAccessContext
from app.application.specialist_interop.specialist_interop import (
    SpecialistInterop,
)
from app.composition.root_composer import (
    _compose_turn_handler,
    _wire_delegated_credential_provider,
)
from app.domain.evidence.model import ModelRef
from app.domain.interaction.model import TurnKind
from app.infrastructure.auth.subject_bearer import (
    bind_subject_bearer,
    unbind_subject_bearer,
)
from app.infrastructure.config.settings import Settings
from app.infrastructure.interoperability.config import (
    specialist_connections_from_settings,
)
from app.infrastructure.interoperability.mcp.adapter import (
    McpSpecialistAdapter,
)
from app.infrastructure.model_invocation.pydantic_ai_adapter import (
    PydanticAiModelInvocationAdapter,
)


def _env(name: str) -> str:
    return (os.environ.get(name) or "").strip()


# Re-export eval subject-auth helpers (thin module; offline-testable).
import importlib.util as _ilu
from pathlib import Path as _Path

_auth_path = _Path(__file__).resolve().parent / "int1_eval_subject_auth.py"
_auth_spec = _ilu.spec_from_file_location("int1_eval_subject_auth", _auth_path)
if _auth_spec is None or _auth_spec.loader is None:
    raise RuntimeError("cannot load int1_eval_subject_auth")
_auth_mod = _ilu.module_from_spec(_auth_spec)
import sys as _sys

_sys.modules[_auth_spec.name] = _auth_mod
_auth_spec.loader.exec_module(_auth_mod)
SubjectAccessSession = _auth_mod.SubjectAccessSession
acquire_subject_access_session = _auth_mod.acquire_subject_access_session
subject_session_is_fresh = _auth_mod.subject_session_is_fresh
subject_session_public_meta = _auth_mod.subject_session_public_meta


def _subject_token() -> str:
    return acquire_subject_access_session().access_token


class _CountingMcpAdapter:
    def __init__(self, adapter) -> None:
        self._adapter = adapter
        self.list_calls = 0
        self.invoke_calls = 0
        self.invoke_targets: list[str] = []
        self.invoke_records: list[dict] = []

    def __getattr__(self, name):
        return getattr(self._adapter, name)

    def list_remote_tools(self, *args, **kwargs):
        self.list_calls += 1
        return self._adapter.list_remote_tools(*args, **kwargs)

    def call_remote_tool(self, specialist, remote_name, *a, **kw):
        self.invoke_calls += 1
        target = f"{getattr(specialist, 'value', specialist)}:{remote_name}"
        self.invoke_targets.append(target)
        started = time.monotonic()
        try:
            result = self._adapter.call_remote_tool(
                specialist, remote_name, *a, **kw
            )
        except Exception as exc:
            self.invoke_records.append(
                {
                    "target": target,
                    "elapsed_s": round(time.monotonic() - started, 2),
                    "error": type(exc).__name__,
                }
            )
            raise
        call_args = (
            a[0] if a else kw.get("arguments")
        )
        self.invoke_records.append(
            {
                "target": target,
                "elapsed_s": round(time.monotonic() - started, 2),
                "args": {
                    str(k): {
                        "type": type(v).__name__,
                        "json_kind": (
                            "object"
                            if isinstance(v, Mapping)
                            else "array"
                            if isinstance(v, (list, tuple))
                            else "string"
                            if isinstance(v, str)
                            else "boolean"
                            if isinstance(v, bool)
                            else "number"
                            if isinstance(v, (int, float))
                            else "null"
                            if v is None
                            else type(v).__name__
                        ),
                    }
                    for k, v in call_args.items()
                }
                if isinstance(call_args, Mapping)
                else {"type": type(call_args).__name__},
                "result_snippet": str(result)[:2500],
            }
        )
        return result


def _context() -> PlatformAccessContext:
    return PlatformAccessContext(
        user_id="native-mcp-eval",
        name="Native MCP Eval",
        email="native-mcp-eval@example.com",
        effective_permissions=("delia.access",),
        is_superadmin=False,
    )


def _compose():
    settings = Settings()
    if settings.llm_egress_blocked_reason:
        raise SystemExit(
            f"refused: {settings.llm_egress_blocked_reason}"
        )
    connections = specialist_connections_from_settings(settings)
    mcp = _CountingMcpAdapter(
        McpSpecialistAdapter(
            connections,
            credential_provider=_wire_delegated_credential_provider(
                settings, connections
            ),
        )
    )
    interop = SpecialistInterop(mcp)
    adapter = PydanticAiModelInvocationAdapter(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        timeout_seconds=settings.llm_timeout_seconds,
        default_max_output_units=settings.llm_max_output_tokens,
    )
    handler = _compose_turn_handler(
        InvokeModel(adapter),
        ModelRef(
            model_id=settings.llm_model,
            version="configured",
            owner_ref="DELPI",
            provider_ref="openai_compatible",
        ),
        interop,
        settings,
        connections,
    )
    return handler, mcp


# Eval-only instrumentation slots (patched in main(), never in the
# runtime composition): the Agent declared output and the governed
# collected observations, so each scenario report shows the real
# boundary chain — question → tools → owner data → declared output →
# final answer.
_CAPTURE: dict = {"declared_answer": None, "collected": None}
_LLM_USAGE: list[dict] = []


def _install_finalize_capture() -> None:
    """Wrap the deterministic finalization gate to observe what the
    model DECLARED (InvestigationAnswer) vs what was collected — eval
    introspection only; the wrapped call is untouched."""
    from app.application.capability_provision import (
        governed_capability_orchestrator as _gco,
    )

    original = _gco.OperationalCapabilityOrchestrator.__dict__[
        "_finalize_semantic_investigation"
    ]

    def _wrapped(
        self,
        *,
        input_text,
        collected,
        correlation,
        workspace_context,
        deadline,
        unbound_outcome,
        plan=None,
        clarification_question=None,
        composed_attempt=None,
        declared_answer=None,
    ):
        if declared_answer is not None:
            if hasattr(declared_answer, "model_dump"):
                _CAPTURE["declared_answer"] = declared_answer.model_dump()
            elif dataclasses.is_dataclass(declared_answer):
                _CAPTURE["declared_answer"] = dataclasses.asdict(
                    declared_answer
                )
            else:
                _CAPTURE["declared_answer"] = str(declared_answer)[:2000]
        _CAPTURE["collected"] = [
            {
                "status": str(getattr(item, "status", "")),
                "capability_id": str(
                    getattr(item, "capability_id", "") or ""
                ),
                "error_code": getattr(item, "error_code", None),
                "limitations": [
                    str(limitation)
                    for limitation in (
                        getattr(item, "limitations", None) or ()
                    )
                ][:8],
                # Bounded validation feedback (INVALID_ARGUMENTS:
                # field names/types only) — enough to audit rejected
                # arguments without logging argument values.
                "content_head": str(getattr(item, "content", "") or "")[
                    :300
                ]
                if getattr(item, "error_code", None)
                else None,
            }
            for item in collected
        ]
        return original(
            self,
            input_text=input_text,
            collected=collected,
            correlation=correlation,
            workspace_context=workspace_context,
            deadline=deadline,
            unbound_outcome=unbound_outcome,
            plan=plan,
            clarification_question=clarification_question,
            composed_attempt=composed_attempt,
            declared_answer=declared_answer,
        )

    _gco.OperationalCapabilityOrchestrator._finalize_semantic_investigation = (
        _wrapped
    )


def _install_usage_meter() -> None:
    """Count every real model run (tokens + latency) via the native
    ``Agent.run_sync`` seam — adapter stage calls and the investigation
    agent alike. Provider-side counters are preferred over estimates."""
    import pydantic_ai

    original = pydantic_ai.Agent.run_sync

    def _metered(self, *args, **kwargs):
        started = time.monotonic()
        result = original(self, *args, **kwargs)
        usage = None
        try:
            data = result.usage()
            usage = {
                "input_tokens": int(data.input_tokens or 0),
                "output_tokens": int(data.output_tokens or 0),
                "requests": int(getattr(data, "requests", 0) or 0),
            }
        except Exception:
            usage = None
        _LLM_USAGE.append(
            {
                "elapsed_ms": int((time.monotonic() - started) * 1000),
                "usage": usage,
            }
        )
        return result

    pydantic_ai.Agent.run_sync = _metered


def _openrouter_usage(api_key: str) -> float | None:
    """Real provider-reported lifetime usage (OpenRouter /auth/key).

    Returns None when unavailable — never an estimate."""
    if not api_key or "openrouter" not in _env("DELIA_LLM_BASE_URL"):
        return None
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/auth/key",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        usage = (data.get("data") or {}).get("usage")
        return float(usage) if usage is not None else None
    except Exception:
        return None


def _run(
    handler,
    mcp,
    question: str,
    bearer: str,
    *,
    prior_turns: tuple[ConversationContextTurn, ...] = (),
) -> dict:
    started = time.monotonic()
    binding = bind_subject_bearer(bearer)
    error = None
    result = None
    before = mcp.invoke_calls
    before_records = len(mcp.invoke_records)
    before_usage = len(_LLM_USAGE)
    _CAPTURE["declared_answer"] = None
    _CAPTURE["collected"] = None
    try:
        result = handler.execute(
            InteractiveTurnRequest(
                access_context=_context(),
                input_text=question,
                prior_turns=prior_turns,
            )
        )
    except Exception as exc:
        error = getattr(exc, "code", type(exc).__name__)
    finally:
        unbind_subject_bearer(binding)
    usage_slice = _LLM_USAGE[before_usage:]
    return {
        "elapsed_s": round(time.monotonic() - started, 1),
        "error": error,
        "grounding": str(getattr(result, "grounding_status", "")),
        "mcp_invoke_targets": [
            t.split(":")[-2].split("'")[1] + ":" + t.split(":")[-1]
            if "'" in t else t
            for t in mcp.invoke_targets[before:]
        ],
        "mcp_invoke_records": mcp.invoke_records[before_records:],
        "declared_answer": _CAPTURE["declared_answer"],
        "collected_attempts": _CAPTURE["collected"],
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
        "content": getattr(result, "content", "") or "",
        "epistemic_class": str(getattr(result, "epistemic_class", "")),
        "provenance": _safe_provenance(result),
        "limitations": [
            str(x)
            for x in (getattr(result, "limitations", None) or ())
        ],
    }


def _safe_provenance(result) -> dict | None:
    prov = getattr(result, "provenance", None)
    if prov is None:
        return None
    sources = getattr(prov, "sources", None) or []
    return {
        "sources": [
            {
                "source_id": str(getattr(s, "source_id", "")),
                "source_system": str(getattr(s, "source_system", "")),
                "action_id": str(getattr(s, "action_id", "")),
            }
            for s in sources
        ]
    }


def _write_artifact(scenario_id: str, question: str, res: dict) -> None:
    """Persist the full answer + evidence in a local protected dir.

    Never logs tokens/credentials; content is local-only business
    evidence for the executor's semantic review — not committed."""
    out_dir = os.environ.get(
        "DELIA_EVAL_ARTIFACT_DIR", "/tmp/delia_eval_artifacts"
    )
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{scenario_id}.json")
    payload = {
        "scenario": scenario_id,
        "question": question,
        "result": res,
    }
    with open(path, "w") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)


QUESTIONS = {
    "A_davi_product": "Qual é a descrição do produto 50220013?",
    "B_teo_transform": (
        "Quais informações estão disponíveis sobre as iniciativas "
        "de transformação digital?"
    ),
    "C_vista_playlists": (
        "Quais playlists estão disponíveis nos painéis operacionais?"
    ),
    "D_multi_mcp": (
        "Qual é a descrição do produto 50220013 e quais playlists "
        "estão disponíveis nos painéis operacionais?"
    ),
    "E1_reword_davi": "me diz o que é o item 50220013",
    "E2_reword_vista": "liste para mim as playlists dos dashboards",
    "E3_absent_record": "Qual é a descrição do produto 00000000?",
    "H1_data_formats": "Quais formatos de dados estão disponíveis?",
    "H2_sipoc_concept": "O que é SIPOC?",
    "H3_product_structure": "Mostre a estrutura do produto 90260921.",
    "H4_other_product": "Qual é a descrição do produto 99999999?",
}


def _scenarios() -> list[dict]:
    """Scenario list — default battery above, or an explicit
    ``DELIA_EVAL_SCENARIOS_JSON`` list of
    ``[{"id": ..., "question": ..., "prior": [[role, content], ...]}]``
    where role is "user"|"assistant". Prior turns are untrusted
    context (TurnKind.USER_INPUT / DELIA_RESULT), never authority."""
    raw = _env("DELIA_EVAL_SCENARIOS_JSON")
    if not raw:
        return [
            {"id": sid, "question": q, "prior": []}
            for sid, q in QUESTIONS.items()
        ]
    data = json.loads(raw)
    if not isinstance(data, list):
        raise SystemExit("DELIA_EVAL_SCENARIOS_JSON must be a JSON list")
    out = []
    for item in data:
        out.append(
            {
                "id": str(item["id"]),
                "question": str(item["question"]),
                "prior": list(item.get("prior") or []),
            }
        )
    return out


def _prior_turns(prior) -> tuple[ConversationContextTurn, ...]:
    turns = []
    for role, content in prior:
        kind = (
            TurnKind.USER_INPUT
            if str(role).lower() in ("user", "user_input")
            else TurnKind.DELIA_RESULT
        )
        turns.append(ConversationContextTurn(kind=kind, content=content))
    return tuple(turns)


def main() -> int:
    for required in (
        "DEV_PORTAL_USERNAME",
        "DEV_PORTAL_PASSWORD",
        "KEYCLOAK_URL",
    ):
        if not _env(required):
            print(f"missing env {required}")
            return 2
    _install_finalize_capture()
    _install_usage_meter()
    cost_before = _openrouter_usage(_env("DELIA_LLM_API_KEY"))
    settings = Settings()
    handler, mcp = _compose()
    out = {
        "model": settings.llm_model,
        "runtime_profile": settings.runtime_profile,
        "config_fingerprint": settings.runtime_config_fingerprint,
        "scenarios": {},
    }
    for spec in _scenarios():
        sid, question = spec["id"], spec["question"]
        try:
            res = _run(
                handler,
                mcp,
                question,
                _subject_token(),
                prior_turns=_prior_turns(spec["prior"]),
            )
        except Exception as exc:
            res = {"error": type(exc).__name__}
        _write_artifact(sid, question, res)
        out["scenarios"][sid] = {
            k: (v[:160] if k == "content" else v)
            for k, v in res.items()
            if k in ("content", "grounding", "error", "elapsed_s",
                     "mcp_invoke_targets", "epistemic_class",
                     "limitations", "declared_answer", "llm_runs")
        }
        print(
            f"== {sid}: "
            f"{json.dumps(out['scenarios'][sid], ensure_ascii=False)}"
        )
    cost_after = _openrouter_usage(_env("DELIA_LLM_API_KEY"))
    out["external_usage"] = {
        "model_calls": len(_LLM_USAGE),
        "input_tokens": sum(
            (u["usage"] or {}).get("input_tokens", 0)
            for u in _LLM_USAGE
        ),
        "output_tokens": sum(
            (u["usage"] or {}).get("output_tokens", 0)
            for u in _LLM_USAGE
        ),
        "total_tokens": sum(
            (u["usage"] or {}).get("input_tokens", 0)
            + (u["usage"] or {}).get("output_tokens", 0)
            for u in _LLM_USAGE
        ),
        "latency_ms_total": sum(u["elapsed_ms"] for u in _LLM_USAGE),
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
