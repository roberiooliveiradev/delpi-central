"""DELIA-C3-CRI-PRODUCTION-ACTIVATION-AND-NATURAL-RESPONSE-VERIFICATION-01.

Bounded CRI ON/OFF evaluation on the REAL governed chain:

    user question -> Ollama (local only) -> governed orchestration ->
    delegated credential exchange (RFC 8693) -> real dev MCP READ ->
    baseline render (CRI OFF) vs grounded CRI composition (CRI ON).

Part D is deterministic: a TÉO-shaped records fixture (the production
incident shape — PROC-0080 with codigo_processo / nome_processo /
gestor_responsavel UUID / status_processo / raw ISO created_at) is fed
through the baseline ``_render_synthesis`` and through the real CRI E3
seam (``presented_record`` + ``compose_cri_response`` on a live
orchestrator instance with the governed vocabulary resource). No model
is needed for this half — the render divergence is code-level.

Part L is live: the literal incident question runs end-to-end against
the dev MCPs with the real Ollama model, once per response mode, until
a real READ lands (bounded retries — small CPU-only models are
non-deterministic under contention).

Environment contract: same dev stack as the R4 eval (R4_* credential
envs + DELIA_* Ollama/MCP envs). No token, password or payload is ever
printed; output is sanitized JSON.
"""

from __future__ import annotations

import importlib.util
import json
import logging
import os
import re
import sys
import time
from types import SimpleNamespace

sys.path.insert(0, "/app")

_R4_PATH = "/app/scripts/r4_authenticated_resume_eval.py"
_spec = importlib.util.spec_from_file_location("r4_eval", _R4_PATH)
r4 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(r4)

from app.application.capability_provision.conversational_response import (
    _render_synthesis,
)
from app.application.capability_provision.orchestration import (
    OperationalCapabilityOrchestrator,
)
from app.application.capability_provision.outcome_assessment import (
    AnswerRequirements,
    EvidenceFacts,
    assess_outcome,
)
from app.infrastructure.config.cri_instruction_resource import (
    load_cri_presentation_vocabulary,
)

QUESTION = "qual o ultimo processo cadastrado?"

# Fixture replicating the production incident payload shape (doc:
# production-observations-2026-10-22-cri-contextual-owner-routing.md) —
# scalar fields only, newest-first by created_at, never real data.
_FIXTURE_RECORDS = (
    {
        "id": "d6e4d8f2-1111-4a00-9a00-000000000080",
        "codigo_processo": "PROC-0080",
        "nome_processo": (
            "Monitoramento e Analise dos Indicadores de Estoque"
        ),
        "gestor_responsavel": "9a1b2c3d-4444-4e5f-8a9b-0c1d2e3f4a5b",
        "status_processo": "ativo",
        "created_at": "2026-10-15T15:43:45.344799-03:00",
    },
    {
        "id": "d6e4d8f2-1111-4a00-9a00-000000000079",
        "codigo_processo": "PROC-0079",
        "nome_processo": "Revisao dos Parametros de Producao",
        "gestor_responsavel": "9a1b2c3d-4444-4e5f-8a9b-0c1d2e3f4a5b",
        "status_processo": "ativo",
        "created_at": "2026-10-10T09:12:00.000000-03:00",
    },
    {
        "id": "d6e4d8f2-1111-4a00-9a00-000000000078",
        "codigo_processo": "PROC-0078",
        "nome_processo": "Calibracao da Escala de Avaliacao",
        "gestor_responsavel": "9a1b2c3d-4444-4e5f-8a9b-0c1d2e3f4a5b",
        "status_processo": "concluido",
        "created_at": "2026-10-02T11:05:30.000000-03:00",
    },
)

_UUID_RE = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)
_RAW_ISO_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
_SNAKE_LABEL_RE = re.compile(r"\b[a-z]+_[a-z_]+\s*:")


def _content_checks(content: str) -> dict:
    """Mechanical-render signals that must be absent in a natural
    conversational answer."""
    return {
        "exposes_uuid": bool(_UUID_RE.search(content or "")),
        "exposes_raw_iso": bool(_RAW_ISO_RE.search(content or "")),
        "exposes_snake_field_labels": bool(
            _SNAKE_LABEL_RE.search(content or "")
        ),
        "has_ptbr_date": bool(
            re.search(r"\d{2}/\d{2}/\d{4}", content or "")
        ),
        "mentions_code": "PROC-0080" in (content or ""),
    }


class _DecisionLogTap(logging.Handler):
    """Captures response-mode / CRI decision log lines (bounded)."""

    def __init__(self) -> None:
        super().__init__()
        self.lines: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        msg = record.getMessage()
        if (
            "response_mode" in msg
            or "delia_response_intelligence" in msg
            or "cri_response" in msg
            or "cri_instruction_resource" in msg
            or "cri_presentation_resource" in msg
            or "outcome_assessment" in msg
        ):
            self.lines.append(msg[:240])


def _cri_orchestrator() -> OperationalCapabilityOrchestrator:
    vocabulary = load_cri_presentation_vocabulary(
        "/app/config/cri_presentation.delpi.json"
    )
    return OperationalCapabilityOrchestrator(
        providers=(),
        invoke_model=None,
        model_ref=None,
        response_intelligence_enabled=True,
        cri_instruction_clause="eval",
        cri_instruction_version="eval",
        cri_presentation_vocabulary=vocabulary.sections,
    )


def _deterministic() -> dict:
    orch = _cri_orchestrator()
    out: dict = {}

    # D1 — baseline render of the incident shape (the mechanical
    # response observed in production under decision=baseline): model
    # proposal selects every scalar field of the newest record, detail
    # presentation. This is the exact generator of the incident prose.
    scalar_fields = [
        key
        for key, value in _FIXTURE_RECORDS[0].items()
        if isinstance(value, str)
    ]
    baseline_content, baseline_reason = _render_synthesis(
        {
            "items": [
                {"record_index": 0, "fields": scalar_fields}
            ],
            "presentation": "detail",
        },
        _FIXTURE_RECORDS,
    )
    out["D1_baseline_detail_render"] = {
        "render_reason": baseline_reason,
        "content": baseline_content,
        "checks": _content_checks(baseline_content or ""),
    }

    # D2 — CRI E3 on the same records, ordering requirement as the
    # goal stage would type it for "o ultimo cadastrado" (newest_first;
    # no verifiable creation semantic -> neutral wording expected).
    req = AnswerRequirements(ordering="newest_first")
    facts = EvidenceFacts(
        records=_FIXTURE_RECORDS,
        has_business_evidence=True,
        is_complete=True,
        coverage_complete=True,
    )
    verdict = assess_outcome(facts, req)
    cri = orch._compose_cri_response(
        facts,
        verdict,
        SimpleNamespace(answer_requirements=req),
        "eval-d2",
        contract_text=None,
    )
    out["D2_cri_ordering_answered"] = {
        "verdict": verdict.decision,
        "verdict_reasons": list(verdict.reasons),
        "content": cri.content if cri is not None else None,
        "presented": cri.presented_records if cri is not None else 0,
        "checks": _content_checks(cri.content if cri else ""),
    }

    # D3 — same question but coverage unproven (paginated owner):
    # ordering alone can never claim the global "ultimo".
    facts_pg = EvidenceFacts(
        records=_FIXTURE_RECORDS,
        has_business_evidence=True,
        is_complete=True,
        coverage_complete=False,
        total_count=None,
    )
    verdict_pg = assess_outcome(facts_pg, req)
    cri_pg = orch._compose_cri_response(
        facts_pg,
        verdict_pg,
        SimpleNamespace(answer_requirements=req),
        "eval-d3",
        contract_text=None,
    )
    out["D3_cri_ordering_coverage_unproven"] = {
        "verdict": verdict_pg.decision,
        "verdict_reasons": list(verdict_pg.reasons),
        "content": cri_pg.content if cri_pg is not None else None,
        "checks": _content_checks(cri_pg.content if cri_pg else ""),
    }

    # D4 — no ordering requirement, single record: CRI single_found
    # path renders labeled leaves (fields present; labels are the
    # governed vocabulary's, never raw snake_case… verify).
    facts_one = EvidenceFacts(
        records=_FIXTURE_RECORDS[:1],
        has_business_evidence=True,
        is_complete=True,
        coverage_complete=True,
    )
    verdict_one = assess_outcome(facts_one, None)
    cri_one = orch._compose_cri_response(
        facts_one,
        verdict_one,
        SimpleNamespace(answer_requirements=None),
        "eval-d4",
        contract_text=None,
    )
    out["D4_cri_single_found"] = {
        "verdict": verdict_one.decision,
        "content": cri_one.content if cri_one is not None else None,
        "checks": _content_checks(cri_one.content if cri_one else ""),
    }
    return out


def _live(question: str, cri_enabled: bool, tries: int = 3) -> dict:
    if cri_enabled:
        os.environ["DELIA_RESPONSE_INTELLIGENCE_ENABLED"] = "true"
    else:
        os.environ.pop("DELIA_RESPONSE_INTELLIGENCE_ENABLED", None)
    tap = _DecisionLogTap()
    logging.getLogger().addHandler(tap)
    try:
        last = None
        for attempt in range(tries):
            handler, guarded, mcp = r4._compose()
            last = r4._run(
                handler, guarded, mcp, question, r4._subject_token()
            )
            # The full content is needed for naturalness review —
            # ``_run`` caps at 100 chars, so re-derive from the result
            # object is not available here; the run dict is extended
            # by a second capture below via sink… instead we re-run
            # ``handler.execute`` path through r4._run and accept the
            # head, and separately capture the full content by calling
            # execute once more on the same handler only when a READ
            # landed (bounded duplicate turn, same input).
            last["try_index"] = attempt
            if last["mcp_invoke_calls"] >= 1:
                result_holder = {}
                binding = r4.bind_subject_bearer(r4._subject_token())
                try:
                    res = handler.execute(
                        r4.InteractiveTurnRequest(
                            access_context=r4._context(),
                            input_text=question,
                        )
                    )
                    result_holder["content"] = getattr(
                        res, "content", ""
                    )
                    result_holder["grounding"] = str(
                        getattr(res, "grounding_status", "")
                    )
                except Exception as exc:
                    result_holder["error"] = getattr(
                        exc, "code", type(exc).__name__
                    )
                finally:
                    r4.unbind_subject_bearer(binding)
                last.update(result_holder)
                break
        last["decision_log"] = tap.lines[-8:]
        return last
    finally:
        logging.getLogger().removeHandler(tap)


def main() -> int:
    for required in ("R4_DEV_USERNAME", "R4_DEV_PASSWORD",
                     "R4_KC_TOKEN_URL"):
        if not r4._env(required):
            return r4._fail(f"missing env {required}")

    started = time.monotonic()
    out = {
        "model": r4._env("DELIA_LLM_MODEL"),
        "question": QUESTION,
        "deterministic": _deterministic(),
        "live": {},
    }
    out["live"]["OFF_baseline"] = _live(QUESTION, cri_enabled=False)
    out["live"]["ON_cri"] = _live(QUESTION, cri_enabled=True)
    out["elapsed_s"] = round(time.monotonic() - started, 1)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
