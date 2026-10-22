"""DELIA-C3-CONTEXTUAL-INTELLIGENCE-DAVI-MULTITURN-REMEDIATION-01.

Stage-level live probe on the REAL chain (authenticated MCP surface +
real Ollama model calls) — one model call per case so each semantic
decision is observable inside the CPU-bound latency envelope that
starves full 60s governed turns.

Cases exercise the two contracts changed by this task:

  * group selection now embeds the bounded untrusted
    prior_observation projection (was: zero context channel);
  * admission/group instructions now cover named-source routing
    directives and catalog-entity examples.

Every proposal is captured typed+sanitized through an eval-only spy
on ``_propose`` — no chain-of-thought, no raw payloads beyond the
validated fields. Deterministic revalidation stays authoritative.

Environment contract: identical to r4_authenticated_resume_eval.
"""

from __future__ import annotations

import json
import sys
import time

sys.path.insert(0, "/app")

from app.application.interaction.turn_budget import TurnDeadline
from app.application.capability_provision.orchestration import (
    _StageDeadlineExceeded,
)
from app.application.model_invocation.errors import (
    ModelInvocationError,
)
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
    _env,
    _subject_token,
)

PROBE_BUDGET_SECONDS = 120.0


def _turn(kind: TurnKind, content: str,
          epistemic: EpistemicClass | None = None) -> ConversationContextTurn:
    return ConversationContextTurn(
        kind=kind, content=content, epistemic_class=epistemic
    )


T1_PAIR = (
    _turn(TurnKind.USER_INPUT, "2 exemplos de terminal bala"),
    _turn(
        TurnKind.DELIA_RESULT,
        "Exemplos comuns do conceito incluem formatos genericos.",
        EpistemicClass.HYPOTHESIS,
    ),
)

OBS_PAIR = (
    _turn(TurnKind.USER_INPUT, "liste os processos cadastrados"),
    _turn(
        TurnKind.DELIA_RESULT,
        "Consulta a fonte transformometro-api retornou: "
        "PROC-0080 Monitoramento e Analise dos Indicadores de Estoque.",
        EpistemicClass.OBSERVATION,
    ),
)


def main() -> int:
    for required in ("R4_DEV_USERNAME", "R4_DEV_PASSWORD",
                     "R4_KC_TOKEN_URL"):
        _env(required)
    handler, guarded, mcp = _compose()
    orch = handler._capability_orchestration  # eval-only stage access
    if orch is None:
        raise SystemExit("no orchestrator composed")

    proposals: list[dict] = []
    real_propose = orch._propose

    def spy(*args, **kwargs):
        proposal = real_propose(*args, **kwargs)
        proposals.append(
            {
                "input_kind": kwargs.get("input_kind"),
                "proposal": (
                    dict(proposal) if isinstance(proposal, dict) else None
                ),
            }
        )
        return proposal

    orch._propose = spy  # type: ignore[method-assign]

    binding = bind_subject_bearer(_subject_token())
    out: dict[str, object] = {"cases": {}}
    try:
        deadline = TurnDeadline.start(PROBE_BUDGET_SECONDS)
        groups, failures = orch._groups("stage-probe", deadline)
        out["surface"] = {
            "groups": sorted(groups),
            "failures": failures,
            "capabilities": {
                key: [
                    cap.remote_name
                    for cap in group.capabilities
                ]
                for key, group in sorted(groups.items())
            },
        }
        cases = out["cases"]

        def admission(text, prior):
            before = len(proposals)
            try:
                verdict = orch._admit_conversational_turn(
                    text,
                    workspace_context=None,
                    prior_turns=prior,
                    correlation="stage-probe",
                    deadline=deadline,
                )
            except (_StageDeadlineExceeded, ModelInvocationError) as exc:
                return {"stage_error": getattr(exc, "reason",
                        getattr(exc, "code", type(exc).__name__))}
            return {
                "conversational": verdict,
                "proposal": proposals[before]["proposal"]
                if len(proposals) > before
                else None,
            }

        def group_sel(text, prior):
            before = len(proposals)
            try:
                status, key = orch._select_group(
                    text,
                    groups,
                    None,
                    prior,
                    correlation="stage-probe",
                    deadline=deadline,
                )
            except (_StageDeadlineExceeded, ModelInvocationError) as exc:
                return {"stage_error": getattr(exc, "reason",
                        getattr(exc, "code", type(exc).__name__))}
            return {
                "status": status,
                "group_key": key,
                "proposal": proposals[before]["proposal"]
                if len(proposals) > before
                else None,
            }

        cases["admit_terminal_bala"] = admission(
            "2 exemplos de terminal bala", ()
        )
        cases["admit_use_o_davi"] = admission("use o davi", T1_PAIR)
        cases["admit_thanks"] = admission("obrigado, era isso", OBS_PAIR)
        cases["group_o_mcp_davi"] = group_sel("o mcp davi", T1_PAIR)
        cases["group_use_o_davi"] = group_sel("use o davi", T1_PAIR)
        cases["group_outro_especialista"] = group_sel(
            "agora use outro especialista, se ele tiver uma fonte melhor",
            OBS_PAIR,
        )
        cases["group_terminal_bala"] = group_sel(
            "2 exemplos de terminal bala", ()
        )
    finally:
        unbind_subject_bearer(binding)

    out["elapsed_s"] = round(time.monotonic() - 0, 2)
    out["mcp_list_calls"] = mcp.list_calls
    out["mcp_invoke_calls"] = mcp.invoke_calls
    print(json.dumps(out, indent=2, default=str, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
