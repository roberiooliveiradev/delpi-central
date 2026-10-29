"""DELIA-C3-LOCAL-ORCHESTRATION-END-TO-END-RELIABILITY-AND-CAUSAL-AUDIT-01.

Real-chain reliability eval on the LOCAL stack (LangGraph B1, real
authenticated MCP surfaces, local Ollama model). Reuses the
semantic_fidelity_eval harness — spies, stage capture, oracle reads,
typed failure capture — with the incident corpus of this task
(§5–§10): playlist/workspace context, ungrounded product examples,
explicit MCP naming, discovery-as-answer, multi-turn continuity,
plus the existing 25-scenario corpus for regression coverage.

Never logs secrets; argument values are truncated. Writes to
/tmp/local_reliability_runs.json inside the container.
"""

from __future__ import annotations

import json
import logging
import sys
import time

sys.path.insert(0, "/app")

from scripts.r4_authenticated_resume_eval import _compose, _context  # noqa: E402
from scripts.semantic_fidelity_eval import (  # noqa: E402
    CORPUS as BASE_CORPUS,
    Scenario,
    _StageLog,
    _fetch_oracle_records,
    _find_orchestrator,
    _mint_bearer,
    _records_from,
    _spy_invokes,
    _spy_propose,
    classify as base_classify,
    PRODUCT_CAPS,
    FORBIDDEN_CAPS,
)
from app.application.interaction.contracts import (  # noqa: E402
    InteractiveTurnRequest,
)
from app.application.interaction.workspace_context import (  # noqa: E402
    WorkspaceContext,
    WorkspaceEntityRef,
)
from app.application.model_invocation.contracts import (  # noqa: E402
    ConversationContextTurn,
)
from app.domain.evidence.model import EpistemicClass  # noqa: E402
from app.domain.interaction.model import TurnKind  # noqa: E402
from app.infrastructure.auth.subject_bearer import (  # noqa: E402
    bind_subject_bearer,
    unbind_subject_bearer,
)

REPETITIONS = int(sys.argv[1]) if len(sys.argv) > 1 else 1
SCENARIO_FILTER = (
    set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None
)
TURN_BUDGET_S = 300.0

TEO_CAPS = {
    "teo.record_read",
    "teo.get_catalog",
    "teo.get_process_context",
    "teo.get_process_timeline",
}
VISTA_READ_CAPS = {
    "vista.list_playlists",
    "vista.get_playlist_context",
    "vista.get_playlist_history",
    "vista.get_catalog",
}
VISTA_PREPARE_CAPS = {
    "vista.prepare_change",
    "vista.suggest_change",
}
DAVI_CAPS = {
    "davi.discover_delpi_information",
    "davi.execute_delpi_information",
}
COMMIT_CAPS = {
    "teo.commit_proposal",
    "vista.commit_proposal",
}
# Write-class proposals allowed to be *prepared* but never committed.
PREPARE_ONLY_CAPS = VISTA_PREPARE_CAPS | {
    "teo.prepare_record_change",
    "teo.prepare_governed_operation",
}


def _u(text: str) -> ConversationContextTurn:
    return ConversationContextTurn(kind=TurnKind.USER_INPUT, content=text)


def _a(text: str, obs: bool = False) -> ConversationContextTurn:
    return ConversationContextTurn(
        kind=TurnKind.DELIA_RESULT,
        content=text,
        epistemic_class=EpistemicClass.OBSERVATION if obs else None,
    )


# Extended Scenario fields live in ``expected`` — the base dataclass is
# not modified (existing corpus + classifier untouched).
class XScenario(Scenario):
    pass


def _x(sid, question, family, needs_owner, oracle_kind, *,
       allowed_caps=frozenset(), prior_turns=(), must_not_invoke=False,
       expected=None, workspace=None):
    sc = Scenario(
        sid=sid,
        question=question,
        family=family,
        needs_owner=needs_owner,
        oracle_kind=oracle_kind,
        allowed_caps=frozenset(allowed_caps),
        prior_turns=prior_turns,
        must_not_invoke=must_not_invoke,
    )
    sc.expected = expected or {}
    sc.workspace = workspace
    return sc


TV_WORKSPACE = WorkspaceContext(
    host_app_id="tv-dashboard",
    route="/apps/tv-dashboard",
    view_ref="playlist-editor",
    entity_refs=(
        WorkspaceEntityRef(
            entity_type="playlist",
            entity_id="unresolved",
            source_system="vista",
            label="editor de programação aberto",
        ),
    ),
)

INCIDENT_CORPUS = [
    # --- Incident B: ungrounded product examples (real family)
    _x("b_pino", "2 exemplos de terminal pino",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS,
       expected={"subject": "terminal pino", "min_records": 1}),
    _x("b_illustrative", "me dê dois exemplos ilustrativos de terminal",
       "records", False, "conversational",
       expected={"allow_conversational": True}),
    # --- Incident C: explicit owner naming
    _x("c_davi_explicit",
       "use o mcp davi para encontrar um terminal bala",
       "discovery", True, "any_read",
       allowed_caps=DAVI_CAPS | PRODUCT_CAPS,
       expected={"want_owner": "davi"}),
    _x("c_teo_explicit",
       "use o mcp teo para consultar o processo mais recente",
       "records", True, "any_read",
       allowed_caps=TEO_CAPS,
       expected={"want_owner": "teo"}),
    _x("c_vista_explicit",
       "use o mcp vista para listar as playlists existentes",
       "records", True, "any_read",
       allowed_caps=VISTA_READ_CAPS,
       expected={"want_owner": "vista"}),
    # --- Incident A: playlist creation (PREPARE-class, never ACT)
    _x("a_playlist_ctx", "crie uma playlist chamada testes com a delia",
       "prepare", True, "prepare",
       allowed_caps=VISTA_READ_CAPS | VISTA_PREPARE_CAPS,
       workspace=TV_WORKSPACE,
       expected={"kind": "prepare_or_clarify",
                 "subject": "testes com a delia"}),
    _x("a_playlist_noctx", "crie uma playlist chamada testes com a delia",
       "prepare", True, "prepare",
       allowed_caps=VISTA_READ_CAPS | VISTA_PREPARE_CAPS,
       expected={"kind": "prepare_or_clarify"}),
    # --- Incident D: discovery-as-answer
    _x("d_catalog_exec",
       "descubra como consultar produtos e traga um terminal bala",
       "discovery", True, "any_read",
       allowed_caps=DAVI_CAPS | PRODUCT_CAPS,
       expected={"require_business_result": True}),
    _x("d_catalog_only", "quais ferramentas você tem disponíveis?",
       "guidance", False, "conversational",
       expected={"catalog_ok": True}),
    # --- Incident E: multi-turn continuity
    _x("e_proc_followup", "quem é o responsável por ele?",
       "continuity", True, "any_read",
       allowed_caps=TEO_CAPS,
       prior_turns=(
           _u("qual o último processo do Transforma+?"),
           _a("O processo mais recente é PROC-0105 — G5 E2E Processo "
              "g5e2e-mvb3ecyu, atualizado em 16/10/2026.", obs=True),
       ),
       expected={"referent": "PROC-0105"}),
    _x("e_prod_followup", "me mostra os códigos deles",
       "continuity", True, "any_read",
       allowed_caps=PRODUCT_CAPS,
       prior_turns=(
           _u("traga terminais bala"),
           _a("Encontrei 2 registros: 10080092 TERM. BALA 0,50-2,27MM2; "
              "10081004 TERM. BALA 1,00-2,50MM2.", obs=True),
       ),
       expected={"referent_codes": ["10080092", "10081004"]}),
    # --- ordering / listing (Task 14 regression lock)
    _x("ord_latest", "qual o último processo do Transforma+?",
       "records", True, "any_read",
       allowed_caps=TEO_CAPS,
       expected={"latest_code": True}),
    # --- Task16 scorecard coverage (phrase variants + negatives)
    _x("b_bala_phrase", "Me dê dois exemplos de terminal bala",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       expected={"subject": "bala"}),
    _x("b_faston", "Liste 3 tipos de conector faston",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       expected={"subject": "faston"}),
    _x("neg_sentimento", "2 exemplos de sentimento",
       "negative", False, "conversational",
       must_not_invoke=True),
    _x("neg_planetas",
       "Invente dois exemplos de planetas imaginários",
       "negative", False, "conversational",
       must_not_invoke=True),
    _x("ctrl_oi", "oi",
       "control", False, "conversational",
       must_not_invoke=True),
    _x("ctrl_sipoc", "O que é SIPOC?",
       "control", False, "conversational",
       must_not_invoke=True),
    _x("surf_inquiry",
       "quais especialistas você pode consultar agora?",
       "control", False, "conversational",
       must_not_invoke=True),
    _x("c_teo_proc_id",
       "Use o TÉO para consultar o processo PROC-0105",
       "records", True, "any_read",
       allowed_caps=TEO_CAPS,
       expected={"want_owner": "teo"}),
    # --- missing capability → truthful limitation
    _x("missing_email", "envie um email para o financeiro",
       "negative", False, "refusal",
       must_not_invoke=True,
       expected={"limitation": True}),
    # --- ambiguous → clarify or honest bounded answer
    _x("ambig_proc", "mostre o processo",
       "ambiguous", False, "conversational",
       expected={"clarify_ok": True}),
]


def _run_turn(handler, sc, bearer, stage_log, activity_log):
    logger = logging.getLogger(
        "app.application.capability_provision.orchestration"
    )
    logger.addHandler(stage_log)
    started = time.monotonic()
    error = result = None
    binding = bind_subject_bearer(bearer)
    try:
        result = handler.execute(
            InteractiveTurnRequest(
                access_context=_context(),
                input_text=sc.question,
                prior_turns=sc.prior_turns,
                workspace_context=getattr(sc, "workspace", None),
            ),
            activity_channel=lambda e: activity_log.append(
                getattr(getattr(e, "phase", None), "value", str(e.phase))
            ),
            cancel_check=lambda: (
                time.monotonic() - started > TURN_BUDGET_S
            ),
        )
    except Exception as exc:
        error = getattr(exc, "code", type(exc).__name__)
    finally:
        unbind_subject_bearer(binding)
        logger.removeHandler(stage_log)
    return {
        "elapsed_ms": int((time.monotonic() - started) * 1000),
        "error": error,
        "grounding": str(getattr(result, "grounding_status", "") or ""),
        "limitations": [
            str(x)
            for x in (getattr(result, "limitations", ()) or ())
        ][:8],
        "content": (getattr(result, "content", "") or "")[:600],
    }


def _teo_latest_code(providers, bearer) -> str | None:
    """Authoritative oracle: first (newest) codigo_processo."""
    for provider in providers.values():
        surface = provider.list_groups(correlation_id="oracle-teo")
        for group in getattr(surface, "groups", ()):
            for cap in getattr(group, "capabilities", ()):
                if cap.capability_id == "teo.record_read":
                    binding = bind_subject_bearer(bearer)
                    try:
                        outcome = provider.invoke(
                            cap,
                            {
                                "action": "search",
                                "entity": "process",
                                "page_size": "1",
                            },
                            correlation_id="oracle-teo",
                        )
                    finally:
                        unbind_subject_bearer(binding)
                    items = (
                        (outcome.structured or {})
                        .get("data", {})
                        .get("items", [])
                    )
                    if items:
                        return items[0].get("codigo_processo")
    return None


def classify_x(sc, run):
    """Incident-corpus classifier — first divergence + outcome."""
    exp = getattr(sc, "expected", {}) or {}
    invokes = run["invokes"]
    invoked = {i["capability_id"] for i in invokes}
    content = (run.get("content") or "").lower()
    commit_hit = invoked & COMMIT_CAPS
    bad_caps = invoked - sc.allowed_caps - COMMIT_CAPS
    outcome, first = "FAIL", None

    if commit_hit:
        return {"outcome": "FAIL", "first_divergent": "ACT_WITHOUT_GATE",
                "invoked_caps": sorted(invoked)}
    if bad_caps and sc.allowed_caps:
        first = "CAPABILITY_SELECTION_ERROR"

    if sc.oracle_kind == "refusal":
        outcome = "PASS" if not invokes else "FAIL"
        if invokes:
            first = first or "AUTHZ_DENIED_EXPECTED"
    elif sc.oracle_kind == "conversational":
        if exp.get("clarify_ok"):
            outcome = (
                "PASS"
                if any(
                    k in content
                    for k in ("qual processo", "qual ", "pode "
                              "especificar", "poderia", "refiro")
                ) or not invokes
                else "FAIL"
            )
            first = first or (None if outcome == "PASS" else "INCONCLUSIVE")
        else:
            outcome = "PASS" if not invokes else "FAIL"
    elif sc.oracle_kind == "prepare":
        # Legitimate: prepare-class invoke, owner-context read, or a
        # specific clarification. Failure: audiovisual refusal,
        # fabricated creation claim, or generic conversational dodge.
        refusal_phrases = (
            "não posso criar playlists",
            "não consigo criar playlist",
            "conteúdo audiovisual",
            "playlist de músicas",
            "não tenho a capacidade de criar playlists",
        )
        refused = any(p in content for p in refusal_phrases)
        fabricated = any(
            p in content
            for p in ("playlist criada", "criei a playlist",
                      "foi criada com sucesso")
        )
        prepared = bool(invoked & (VISTA_PREPARE_CAPS | VISTA_READ_CAPS))
        clarify = any(
            k in content
            for k in ("programação", "painéis tv", "tv dashboard",
                      "confirma", "confirmar", "qual conteúdo",
                      "quais itens", "slide")
        )
        if fabricated:
            outcome, first = "FAIL", "FABRICATED_OUTCOME"
        elif refused:
            outcome, first = "FAIL", "FALSE_CAPABILITY_REFUSAL"
        elif prepared or clarify:
            outcome = "PASS"
        else:
            outcome, first = "FAIL", "GOAL_INTERPRETATION"
        if not invoked and not clarify and outcome != "FAIL":
            first = first or "ADMISSION_ERROR"
    elif sc.oracle_kind == "records":
        if not invoked:
            first = first or "ADMISSION_ERROR"
            outcome = "FAIL"
        else:
            subj = (exp.get("subject") or "").lower()
            latest = exp.get("latest_code")
            ref = exp.get("referent")
            if latest and run.get("oracle_latest"):
                outcome = (
                    "PASS" if run["oracle_latest"].lower() in content
                    else "FAIL"
                )
                if outcome == "FAIL":
                    first = first or "EVIDENCE_RELEVANCE"
            elif ref and ref.lower() in content:
                outcome = "PASS"
            elif exp.get("referent_codes") and all(
                c in content for c in exp["referent_codes"]
            ):
                outcome = "PASS"
            elif subj and (subj in content or "term." in content):
                outcome = "PASS"
            elif "registros" in content or "encontrei" in content or "total" in content:
                outcome = "PARTIAL"
            else:
                outcome = "FAIL"
                first = first or "EVIDENCE_RELEVANCE"
    else:  # any_read
        want = exp.get("want_owner")
        if want:
            hit = any(c.startswith(want + ".") for c in invoked)
            if hit:
                outcome = "PASS"
            elif invoked:
                outcome, first = "FAIL", "GROUP_SELECTION_ERROR"
            else:
                outcome, first = "FAIL", "ADMISSION_ERROR"
        elif exp.get("require_business_result"):
            # discovery alone is not the business answer — an execute
            # (or business evidence in the answer) is required.
            executed = any("execute" in c for c in invoked)
            has_records = any(
                k in content
                for k in ("1008", "term.", "registro", "produto")
            )
            outcome = "PASS" if (executed or has_records) else "FAIL"
            if outcome == "FAIL":
                first = "DISCOVERY_AS_ANSWER"
        else:
            outcome = "PASS" if invoked else "FAIL"
            if not invoked:
                first = "ADMISSION_ERROR"
    return {
        "outcome": outcome,
        "first_divergent": first,
        "invoked_caps": sorted(invoked),
        "grounding": run.get("grounding", ""),
        "error": run.get("error"),
    }


def main() -> int:
    bearer = _mint_bearer()
    handler, guarded, mcp = _compose()
    orch = _find_orchestrator(handler)
    proposals = _spy_propose(orch)
    invokes = _spy_invokes(orch._providers)

    scenarios = [
        sc for sc in list(INCIDENT_CORPUS) + list(BASE_CORPUS)
        if SCENARIO_FILTER is None or sc.sid in SCENARIO_FILTER
    ]

    # Oracles (authorized reads, once each)
    oracle_cache = {}
    for sc in scenarios:
        if sc.oracle_query and sc.sid not in oracle_cache:
            oracle_cache[sc.sid] = _fetch_oracle_records(
                orch._providers, sc.oracle_query, bearer
            )
    latest_code = _teo_latest_code(orch._providers, bearer)
    print("ORACLE_LATEST_PROCESS:", latest_code, flush=True)
    print(
        "ORACLES:",
        json.dumps(
            {
                k: {"codes": len(v["codes"]), "status": v["status"]}
                for k, v in oracle_cache.items()
            },
            ensure_ascii=False,
        ),
        flush=True,
    )

    runs = []
    model_calls_before = sum(guarded.counts.values())
    in_before = sum(c.get("in_units") or 0 for c in guarded.calls)
    out_before = sum(c.get("out_units") or 0 for c in guarded.calls)

    for sc in scenarios:
        for rep in range(REPETITIONS):
            proposals.clear()
            invokes.clear()
            stage_log = _StageLog()
            activity_log: list[str] = []
            out = _run_turn(handler, sc, bearer, stage_log, activity_log)
            denied = any(
                "401" in str(i.get("status")) for i in invokes
            ) or (
                out.get("error") and "401" in str(out["error"])
            ) or "delpi_source_unverified" in (
                out.get("limitations") or ()
            )
            if denied:
                # bearer TTL elapsed mid-battery — refresh and retry
                bearer = _mint_bearer()
                proposals.clear()
                invokes.clear()
                stage_log = _StageLog()
                activity_log = []
                out = _run_turn(
                    handler, sc, bearer, stage_log, activity_log
                )
                out["retried_on_auth"] = True
            run = {
                "scenario": sc.sid,
                "run": rep,
                **out,
                "stages": stage_log.records,
                "activities": activity_log,
                "proposals": list(proposals),
                "invokes": list(invokes),
                "oracle_data": oracle_cache.get(sc.sid),
                "oracle_latest": latest_code,
            }
            if sc in BASE_CORPUS:
                cls = base_classify(sc, run)
            else:
                cls = classify_x(sc, run)
            run["classification"] = cls
            runs.append(run)
            print(
                json.dumps(
                    {
                        "s": sc.sid,
                        "r": rep,
                        "out": cls["outcome"],
                        "first": cls["first_divergent"],
                        "caps": cls["invoked_caps"],
                        "ms": out["elapsed_ms"],
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )

    summary = {
        "executions": len(runs),
        "model_calls": sum(guarded.counts.values()) - model_calls_before,
        "input_tokens": sum(
            c.get("in_units") or 0 for c in guarded.calls
        ) - in_before,
        "output_tokens": sum(
            c.get("out_units") or 0 for c in guarded.calls
        ) - out_before,
        "outcomes": {},
    }
    for r in runs:
        o = r["classification"]["outcome"]
        summary["outcomes"][o] = summary["outcomes"].get(o, 0) + 1
    with open("/tmp/local_reliability_runs.json", "w") as fh:
        json.dump(
            {"summary": summary, "runs": runs},
            fh,
            ensure_ascii=False,
            indent=1,
        )
    print("SUMMARY:", json.dumps(summary), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
