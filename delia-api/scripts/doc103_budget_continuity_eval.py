"""DELIA-C3-LLM-60S-3RETRIES-300S — real Ollama GPU battery (doc 103).

Runs the real composed handler (real OpenAI-compatible adapter pointed
at the local Ollama /v1 endpoint, real MCP/OpenAPI surface wiring,
doc-103 budgets: 60s per call, max-3 governed call retries, 300s
monotonic interaction cap) against the eval scenarios:

  G — general conversational surface (greeting, conceptual, ambiguous,
      no-source, clarification)
  D — DELPI operational probes from the task brief
  V — semantic variations (paraphrase / implicit context / specialist
      switch / topic return)
  M — multi-turn continuity (bounded prior_turns, untrusted)
  C — bounded concurrency (2 parallel turns)

Per scenario it records: elapsed, phases, CONTINUING count, per-call
{purpose, ms, finish, in/out units, error class}, terminal status,
grounding and content head. Aggregates call-count distributions,
latency p50/p95 (n reported), per-purpose latency, error taxonomy and
token usage.

Requires DELIA_LLM_* pointing at the local Ollama endpoint; the harness
refuses external endpoints before any socket is opened
(settings.llm_egress_blocked_reason) — EXTERNAL_LLM_TEST_CALLS=0 and
PAID_FALLBACK=DISABLED by construction.
"""

from __future__ import annotations

import json
import os
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, "/app")
sys.path.insert(0, "/app/scripts")

from ollama_local_llm_eval import _compose, _context, _run

from app.application.interaction.contracts import InteractiveTurnRequest
from app.application.model_invocation.contracts import (
    ConversationContextTurn,
)
from app.domain.evidence.model import EpistemicClass
from app.domain.interaction.model import TurnKind
from app.infrastructure.config.settings import Settings


def _prior(*pairs: tuple[str, str]) -> tuple[ConversationContextTurn, ...]:
    return tuple(
        ConversationContextTurn(
            kind=TurnKind[kind],
            content=content,
            epistemic_class=(
                EpistemicClass.OBSERVATION
                if kind == "DELIA_RESULT"
                else None
            ),
        )
        for kind, content in pairs
    )


SCENARIOS: list[tuple[str, str, tuple[ConversationContextTurn, ...]]] = [
    # G — general conversational surface
    ("G1_greeting", "oi, tudo bem?", ()),
    ("G2_conceptual", "o que é um diagrama SIPOC?", ()),
    ("G3_ambiguous", "me ajuda com isso", ()),
    ("G4_no_source", "qual a previsão do tempo para amanhã?", ()),
    ("G5_clarify", "quero ver o processo", ()),
    # D — DELPI operational probes (task brief)
    ("D1_formats", "Quais formatos de dados estão disponíveis?", ()),
    ("D2_sipoc", "O que é SIPOC?", ()),
    ("D3_specialists", "Quais especialistas estão disponíveis?", ()),
    (
        "D4_tools",
        "Quais ferramentas podem consultar os processos?",
        (),
    ),
    ("D5_last_process", "Qual é o último processo cadastrado?", ()),
    (
        "D6_first_process",
        "Qual é o primeiro processo cadastrado no Transformômetro?",
        (),
    ),
    (
        "D7_material",
        "Qual é a descrição do material 10080043?",
        (),
    ),
    ("D8_terminal_bala", "Dê dois exemplos de terminal bala.", ()),
    ("D9_use_davi", "Agora use o DAVI.", ()),
    (
        "D10_davi_can_query",
        "O MCP DAVI consegue consultar isso?",
        _prior(
            ("USER_INPUT", "Dê dois exemplos de terminal bala."),
            (
                "DELIA_RESULT",
                "Terminal bala exemplo 1 e exemplo 2.",
            ),
        ),
    ),
    (
        "D11_try_again",
        "Tente novamente.",
        _prior(
            ("USER_INPUT", "Qual é o último processo cadastrado?"),
            ("DELIA_RESULT", "Não consegui concluir a consulta."),
        ),
    ),
    # V — semantic variations of the same intents (never keyword-routed)
    ("V1_syn_last", "me mostra o processo mais recente por favor", ()),
    (
        "V2_rephrase_terminal",
        "cite duas ocorrências de terminal bala no catálogo",
        (),
    ),
    ("V3_implicit_ctx", "e no Transformômetro?", ()),
    (
        "V4_specialist_switch",
        "agora consulte o especialista DAVI em vez disso",
        _prior(
            ("USER_INPUT", "Qual é o último processo cadastrado?"),
            ("DELIA_RESULT", "O último processo cadastrado é P-042."),
        ),
    ),
    ("V5_long_question", (
        "Estou revisando nossa documentação de processos e preciso "
        "saber, se possível, qual foi o processo mais recentemente "
        "cadastrado na plataforma para comparar com o nosso registro"
    ), ()),
    ("V6_incomplete", "o material 10080043", ()),
    (
        "V7_similar_vocab",
        "quais processos usam o formato SIPOC?",
        (),
    ),
    # M — multi-turn continuity
    (
        "M1_followup",
        "e qual a descrição dele?",
        _prior(
            ("USER_INPUT", "Qual é a descrição do material 10080043?"),
            (
                "DELIA_RESULT",
                "O material 10080043 é um componente de fixação.",
            ),
        ),
    ),
]


def _run_prepared(handler, measuring, text, prior):
    events: list[str] = []
    started = time.monotonic()
    try:
        result = handler.execute(
            InteractiveTurnRequest(
                access_context=_context(),
                input_text=text,
                prior_turns=prior,
            ),
            activity_channel=lambda e: events.append(
                getattr(e.phase, "value", str(e.phase))
            ),
        )
    except Exception as exc:
        return {
            "elapsed_s": round(time.monotonic() - started, 2),
            "terminal": "EXCEPTION",
            "error": str(exc)[:200],
            "model_calls": measuring.calls,
            "continuing_events": events.count("CONTINUING"),
            "phases": events,
        }
    return {
        "elapsed_s": round(time.monotonic() - started, 2),
        "epistemic_class": str(
            getattr(result, "epistemic_class", "")
        ),
        "grounding": str(getattr(result, "grounding_status", "")),
        "confirmation_required": bool(
            getattr(result, "confirmation_request", None)
        ),
        "model_calls": measuring.calls,
        "continuing_events": events.count("CONTINUING"),
        "phases": events,
        "content_head": (result.content or "")[:160],
    }


def _percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    idx = min(len(ordered) - 1, int(round(q * (len(ordered) - 1))))
    return round(ordered[idx], 2)


def _aggregate(runs: list[dict]) -> dict:
    calls: list[dict] = [
        call for run in runs for call in run["model_calls"]
    ]
    latencies = [c["ms"] / 1000.0 for c in calls if "ms" in c]
    per_purpose: dict[str, list[float]] = {}
    for c in calls:
        if "ms" in c:
            per_purpose.setdefault(str(c["purpose"]), []).append(
                c["ms"] / 1000.0
            )
    errors = [c.get("error") for c in calls if c.get("error")]
    in_units = [
        c["in_units"] for c in calls if c.get("in_units") is not None
    ]
    out_units = [
        c["out_units"] for c in calls if c.get("out_units") is not None
    ]
    elapsed = [r["elapsed_s"] for r in runs]
    return {
        "scenarios": len(runs),
        "total_real_calls": len(calls),
        "call_latency_s": {
            "n": len(latencies),
            "p50": _percentile(latencies, 0.50),
            "p95": _percentile(latencies, 0.95),
            "max": round(max(latencies), 2) if latencies else None,
        },
        "call_latency_by_purpose_s": {
            purpose: {
                "n": len(vals),
                "p50": _percentile(vals, 0.50),
                "max": round(max(vals), 2),
            }
            for purpose, vals in sorted(per_purpose.items())
        },
        "turn_elapsed_s": {
            "n": len(elapsed),
            "p50": _percentile(elapsed, 0.50),
            "p95": _percentile(elapsed, 0.95),
            "max": round(max(elapsed), 2) if elapsed else None,
        },
        "error_taxonomy": {e: errors.count(e) for e in set(errors)},
        "token_units": {
            "input_n": len(in_units),
            "input_total": sum(in_units),
            "output_n": len(out_units),
            "output_total": sum(out_units),
        },
        "continuing_events_total": sum(
            r["continuing_events"] for r in runs
        ),
        "outcomes": {
            o: [
                str(
                    r.get("grounding")
                    or r.get("terminal")
                    or r.get("epistemic_class")
                )
                for r in runs
            ].count(o)
            for o in set(
                str(
                    r.get("grounding")
                    or r.get("terminal")
                    or r.get("epistemic_class")
                )
                for r in runs
            )
        },
    }


def main() -> int:
    probe = Settings()
    if probe.llm_egress_blocked_reason:
        raise SystemExit(f"refused: {probe.llm_egress_blocked_reason}")
    report: dict = {
        "model": probe.llm_model,
        "base_url": probe.llm_base_url,
        "environment": probe.environment,
        "budgets": {
            "llm_timeout_seconds": probe.llm_timeout_seconds,
            "model_stage_timeout_seconds": (
                probe.model_stage_timeout_seconds
            ),
            "turn_budget_seconds": probe.turn_budget_seconds,
            "interaction_total_budget_seconds": (
                probe.interaction_total_budget_seconds
            ),
            "max_governed_attempts": probe.max_governed_attempts,
        },
        "scenarios": {},
    }
    runs: list[dict] = []
    started_all = time.monotonic()
    for label, text, prior in SCENARIOS:
        handler, measuring = _compose(cri=True)
        result = _run_prepared(handler, measuring, text, prior)
        result["question"] = text
        report["scenarios"][label] = result
        runs.append(result)
        print(
            f"[{label}] {result['elapsed_s']}s "
            f"calls={len(result['model_calls'])} "
            f"status={result.get('status', result.get('terminal'))}",
            file=sys.stderr,
            flush=True,
        )
    # C — bounded concurrency: two parallel turns on composed handlers.
    def _parallel(pair):
        handler, measuring = _compose(cri=True)
        return _run_prepared(handler, measuring, pair[1], pair[2])

    with ThreadPoolExecutor(max_workers=2) as pool:
        c_runs = list(
            pool.map(
                _parallel,
                [
                    ("C1a", "oi, tudo bem?", ()),
                    ("C1b", "O que é SIPOC?", ()),
                ],
            )
        )
    for label, result in zip(("C1a", "C1b"), c_runs):
        result["question"] = label
        report["scenarios"][label] = result
        runs.append(result)
    report["wall_clock_all_s"] = round(time.monotonic() - started_all, 1)
    report["aggregate"] = _aggregate(runs)
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
