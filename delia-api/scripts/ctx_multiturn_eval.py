"""DELIA-C3-CONTEXTUAL-INTELLIGENCE-DAVI-MULTITURN-REMEDIATION-01.

Multiturn contextual-intelligence reproduction on the REAL chain:

    prior-turn context (typed, untrusted) -> admission -> live surface
    -> semantic group/capability selection -> delegated credential ->
    real MCP invoke -> outcome -> honest terminal.

Reproduces the production incident sequence in dev with Ollama only:

    T1 "2 exemplos de terminal bala"
    T2 "use o davi"            (prior context = T1 pair)
    T3 "o mcp davi"            (prior context = T1+T2 pairs)

Plus generalization probes (no DAVI-specific rules):

    G1 "qual a descricao do material 10080043?"  real DELPI record read
    G2 "consulte os produtos disponiveis na empresa" catalog read
    G3 "o que voce encontrou?"                   anaphoric continuation

Every turn runs the real governed handler end-to-end; stage decisions
are captured from the typed model-call purposes and the MCP wire
counters — nothing is inferred from prose.

Environment contract: identical to r4_authenticated_resume_eval
(R4_DEV_*, R4_KC_*, DELIA_LLM_* Ollama-gated, DELIA_MCP_*).
"""

from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, "/app")

from app.application.interaction.contracts import InteractiveTurnRequest
from app.application.model_invocation.contracts import (
    ConversationContextTurn,
)
from app.domain.evidence.model import EpistemicClass
from app.domain.interaction.model import TurnKind
from app.infrastructure.auth.subject_bearer import (
    bind_subject_bearer,
    unbind_subject_bearer,
)

from scripts.r4_authenticated_resume_eval import (
    _compose,
    _context,
    _env,
    _subject_token,
)


def _prior(kind: TurnKind, content: str,
           epistemic: EpistemicClass | None = None) -> ConversationContextTurn:
    return ConversationContextTurn(
        kind=kind, content=content, epistemic_class=epistemic
    )


def _run_turn(handler, guarded, mcp, question: str, bearer: str,
              prior_turns=()) -> dict:
    events: list[str] = []
    started = time.monotonic()
    binding = bind_subject_bearer(bearer)
    error = None
    result = None
    call_base = len(guarded.calls)
    try:
        result = handler.execute(
            InteractiveTurnRequest(
                access_context=_context(),
                input_text=question,
                prior_turns=tuple(prior_turns),
            ),
            activity_channel=lambda e: events.append(
                getattr(e.phase, "value", str(e.phase))
            ),
        )
    except Exception as exc:
        error = getattr(exc, "code", type(exc).__name__)
    finally:
        unbind_subject_bearer(binding)
    stages = [c["purpose"] for c in guarded.calls[call_base:]]
    detail = [
        {
            "purpose": c["purpose"],
            "ms": c.get("ms"),
            "error": c.get("error"),
            "finish": c.get("finish"),
        }
        for c in guarded.calls[call_base:]
    ]
    return {
        "elapsed_s": round(time.monotonic() - started, 2),
        "error": error,
        "message_kind": getattr(result, "message_kind", None),
        "grounding": str(getattr(result, "grounding_status", "")),
        "phases": events,
        "stage_sequence": stages,
        "stage_detail": detail,
        "mcp_list_calls": mcp.list_calls,
        "mcp_invoke_calls": mcp.invoke_calls,
        "mcp_invoke_targets": list(mcp.invoke_targets),
        "content_head": (getattr(result, "content", "") or "")[:220],
        "result_content": (getattr(result, "content", "") or ""),
    }


def main() -> int:
    for required in ("R4_DEV_USERNAME", "R4_DEV_PASSWORD",
                     "R4_KC_TOKEN_URL"):
        if not _env(required):
            print(json.dumps({"fatal": f"missing env {required}"}))
            return 2

    handler, guarded, mcp = _compose()
    report: dict = {}

    def converged(question: str, prior_turns=(), limit: int = 3):
        """Retry the SAME logical turn until it leaves the timeout-
        dominated regime — stage completions, not luck, are what we
        measure. A fresh governed attempt each try (new checkpoint,
        fresh subject token)."""
        last = None
        for i in range(limit):
            last = _run_turn(handler, guarded, mcp, question,
                             _subject_token(), prior_turns=prior_turns)
            last["try_index"] = i
            if last["message_kind"] != "PROCESSING_TIMEOUT":
                break
        return last

    # --- Incident reproduction: one logical conversation, three turns.
    t1 = converged("2 exemplos de terminal bala")
    report["T1_terminal_bala"] = t1

    t1_result = t1["result_content"] or "sem resposta"
    priors_2 = (
        _prior(TurnKind.USER_INPUT, "2 exemplos de terminal bala"),
        _prior(TurnKind.DELIA_RESULT, t1_result,
               EpistemicClass.HYPOTHESIS),
    )
    t2 = converged("use o davi", priors_2)
    report["T2_use_o_davi"] = t2

    priors_3 = priors_2 + (
        _prior(TurnKind.USER_INPUT, "use o davi"),
        _prior(TurnKind.DELIA_RESULT,
               t2["result_content"] or "sem resposta",
               EpistemicClass.HYPOTHESIS),
    )
    t3 = converged("o mcp davi", priors_3)
    report["T3_o_mcp_davi"] = t3

    # --- Generalization probes (fresh bearer per turn, no shared state
    # beyond the typed prior context the client would legitimately send).
    g1 = converged("qual a descricao do material 10080043?")
    report["G1_material_description"] = g1

    g2 = converged("consulte os produtos disponiveis na empresa")
    report["G2_products_catalog"] = g2

    priors_g3 = (
        _prior(TurnKind.USER_INPUT,
               "consulte os produtos disponiveis na empresa"),
        _prior(TurnKind.DELIA_RESULT,
               g2["result_content"] or "sem resposta",
               EpistemicClass.OBSERVATION),
    )
    g3 = converged("o que voce encontrou?", priors_g3)
    report["G3_anaphoric_followup"] = g3

    report["totals"] = {
        "mcp_list_calls": mcp.list_calls,
        "mcp_invoke_calls": mcp.invoke_calls,
        "mcp_invoke_targets": list(mcp.invoke_targets),
    }
    out = {k: v for k, v in report.items()}
    for key, value in out.items():
        if isinstance(value, dict):
            value.pop("result_content", None)
    print(json.dumps(out, indent=2, default=str, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
