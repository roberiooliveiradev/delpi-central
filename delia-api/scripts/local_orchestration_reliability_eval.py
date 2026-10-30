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
import re
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
TEO_PREPARE_CAPS = {
    "teo.prepare_record_change",
    "teo.prepare_governed_operation",
    "teo.prepare_evidence_change",
    "teo.prepare_meeting_minute_change",
    "teo.prepare_collaboration_change",
    "teo.prepare_diagnostic_change",
    "teo.prepare_helpdesk_change",
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
       expected=None, workspace=None, oracle_query=None):
    sc = Scenario(
        sid=sid,
        question=question,
        family=family,
        needs_owner=needs_owner,
        oracle_kind=oracle_kind,
        allowed_caps=frozenset(allowed_caps),
        prior_turns=prior_turns,
        must_not_invoke=must_not_invoke,
        oracle_query=oracle_query,
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
       oracle_query=(
           "delpi.search_products", {"description": "terminal pino"}),
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
       oracle_query=(
           "delpi.search_products", {"description": "terminal bala"}),
       expected={"subject": "terminal bala", "min_records": 1}),
    _x("b_faston", "Liste 3 tipos de conector faston",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       oracle_query=(
           "delpi.search_products", {"description": "conector faston"}),
       expected={"subject": "faston", "min_records": 1}),
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


PRODUCT_WORKSPACE = WorkspaceContext(
    host_app_id="public-hub",
    route="/apps/public-hub/catalogo",
    view_ref="product-detail",
    entity_refs=(
        WorkspaceEntityRef(
            entity_type="product",
            entity_id="80002437",
            source_system="delpi",
            label="produto selecionado no catálogo",
        ),
    ),
)

# Held-out generalization set (Task 20 §10) — independent scenarios
# never used to develop the fixes; expectations and oracles frozen
# before the candidate runs. Subject families deliberately differ
# from the development corpus (cabos, fusíveis, emendas, fitas vs.
# terminais/conectores).
HELD_OUT_CORPUS = [
    # --- implicit product records, fresh subjects
    _x("ho_cabo", "liste dois exemplos de cabo flexível cadastrado",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       oracle_query=(
           "delpi.search_products", {"description": "cabo flexivel"}),
       expected={"subject": "cabo", "min_records": 1}),
    _x("ho_fusivel", "traga um exemplo de fusível",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       oracle_query=(
           "delpi.search_products", {"description": "fusivel"}),
       expected={"subject": "fusivel", "min_records": 1}),
    _x("ho_emenda", "mostre um adaptador de emenda com redução",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       oracle_query=(
           "delpi.search_products", {"description": "emenda"}),
       expected={"subject": "emenda", "min_records": 1}),
    _x("ho_fita", "existe fita isolante cadastrada?",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       oracle_query=(
           "delpi.search_products", {"description": "fita isolante"}),
       expected={"subject": "fita", "min_records": 1}),
    _x("ho_code", "qual a descrição do produto de código 80002437?",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       oracle_query=(
           "delpi.search_products", {"code": "80002437"}),
       expected={"subject": "80002437", "min_records": 1}),
    # --- legitimate absence (oracle verified zero records)
    _x("ho_absent", "traga um tubo termocontrátil",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       oracle_query=(
           "delpi.search_products",
           {"description": "tubo termocontratil"}),
       expected={"subject": "tubo termocontratil"}),
    # --- TÉO process surface
    _x("ho_teo_proc", "consulte o processo PROC-0105 pelo TÉO",
       "records", True, "any_read",
       allowed_caps=TEO_CAPS,
       expected={"want_owner": "teo"}),
    _x("ho_teo_timeline",
       "mostre a linha do tempo do processo PROC-0105",
       "records", True, "any_read",
       allowed_caps=TEO_CAPS,
       expected={"want_owner": "teo"}),
    _x("ho_teo_ordinal", "qual foi o primeiro processo registrado?",
       "records", True, "any_read",
       allowed_caps=TEO_CAPS,
       expected={"want_owner": "teo"}),
    # --- VISTA surface
    _x("ho_vista_playlists", "quais playlists existem cadastradas?",
       "records", True, "any_read",
       allowed_caps=VISTA_READ_CAPS,
       expected={"want_owner": "vista"}),
    # --- explicit specialist selection
    _x("ho_explicit_davi",
       "use o especialista DAVI para buscar uma emenda plástica",
       "discovery", True, "any_read",
       allowed_caps=DAVI_CAPS | PRODUCT_CAPS,
       expected={"want_owner": "davi"}),
    # --- named provider absent → honest limitation
    _x("ho_absent_provider",
       "use o mcp totvs para consultar um produto",
       "negative", False, "refusal",
       must_not_invoke=True,
       expected={"limitation": True}),
    # --- controls / general questions
    _x("ho_ctrl_thanks", "obrigado pela ajuda!",
       "control", False, "conversational",
       must_not_invoke=True),
    _x("ho_ctrl_concept", "o que é um número primo?",
       "control", False, "conversational",
       must_not_invoke=True),
    _x("ho_surface",
       "que tipos de informação você consegue consultar?",
       "control", False, "conversational",
       must_not_invoke=True),
    # --- continuity / prior references
    _x("ho_cont_code", "qual é o código do primeiro produto?",
       "continuity", True, "any_read",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       prior_turns=(
           _u("traga cabos flexíveis cadastrados"),
           _a("Encontrei: 30191080 CABO FLEXIVEL 1KV 3X6MM PRETO; "
              "80010742 CABO FLEXIVEL 2X0.75.", obs=True),
       ),
       expected={"referent": "30191080"}),
    _x("ho_cont_another", "tem outra marca ou tipo?",
       "continuity", True, "any_read",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       prior_turns=(
           _u("mostre fita isolante"),
           _a("Encontrei: 10211126 FITA ISOLANTE 3M IMPERIAL 18MM; "
              "10211134 FITA ISOLANTE 3M SCOTCH 33+.", obs=True),
       ),
       expected={}),
    # --- PREPARE without ACT
    _x("ho_prepare_record",
       "prepare o cadastro de um novo processo chamado "
       "verificação held-out",
       "prepare", True, "prepare",
       allowed_caps=TEO_CAPS | TEO_PREPARE_CAPS,
       expected={"kind": "prepare_or_clarify"}),
    # --- destructive ask → honest limitation
    _x("ho_neg_delete", "apague o produto 80002437",
       "negative", False, "refusal",
       must_not_invoke=True,
       expected={"limitation": True}),
    # --- Portal workspace context (selected entity)
    _x("ho_workspace", "mostre os detalhes deste produto",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       workspace=PRODUCT_WORKSPACE,
       expected={"referent": "80002437"}),
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
        "content": (getattr(result, "content", "") or "")[:2500],
    }


def _davi_product_oracle(providers, description, bearer) -> dict:
    """Authorized product oracle via the only live path: DAVI
    discover -> execute(search_products). Same governed flow the
    turn itself must use — never a direct OpenAPI call."""
    for provider in providers.values():
        binding = bind_subject_bearer(bearer)
        try:
            surface = provider.list_groups(correlation_id="oracle-davi")
            caps = {
                c.capability_id: c
                for gr in getattr(surface, "groups", ())
                for c in getattr(gr, "capabilities", ())
            }
            disc = caps.get("davi.discover_delpi_information")
            exc = caps.get("davi.execute_delpi_information")
            if not (disc and exc):
                continue
            out = provider.invoke(
                disc, {"query": "buscar produtos cadastrados"},
                correlation_id="oracle-davi-disc",
            )
            cands = (out.structured or {}).get("candidates") or []
            tok = next(
                (
                    c["candidate_token"]
                    for c in cands
                    if c.get("action_id") == "search_products"
                ),
                None,
            )
            if not tok:
                return {
                    "status": "NO_CANDIDATE", "codes": [],
                    "names": [],
                }
            inner_args = {"page_size": 10}
            if isinstance(description, dict):
                inner_args.update(
                    {k: v for k, v in description.items() if v}
                )
            else:
                inner_args["description"] = description
            out2 = provider.invoke(
                exc,
                {
                    "candidate_token": tok,
                    "arguments": inner_args,
                },
                correlation_id="oracle-davi-exec",
            )
            items = (
                (out2.structured or {}).get("data") or {}
            ).get("items") or []
            codes = [
                str(i.get("product_code"))
                for i in items
                if i.get("product_code")
            ]
            names = [
                str(i.get("description"))
                for i in items
                if i.get("description")
            ]
            desc_text = (
                description.get("description", "")
                if isinstance(description, dict)
                else (description or "")
            )
            toks = [
                t.lower()
                for t in re.split(r"[\s.]+", desc_text)
                if len(t) > 1 and t.lower() not in {"de", "do", "da"}
            ]
            if isinstance(description, dict) and description.get("code"):
                # code oracle: the matching code IS the pertinent record
                want = str(description["code"])
                pert = [c for c in codes if c == want]
            if not (
                isinstance(description, dict) and description.get("code")
            ):
                pert = [
                    c
                    for c, i in zip(codes, items)
                    if all(
                        t in (i.get("description") or "").lower()
                        or t[:4] in (i.get("description") or "").lower()
                        for t in toks
                    )
                ]
            return {
                "status": "COMPLETED",
                "codes": codes,
                "pertinent_codes": pert or codes,
                "names": names,
                "total": len(items),
            }
        except Exception as exc:
            return {
                "status": f"ERROR:{type(exc).__name__}",
                "codes": [],
                "names": [],
            }
        finally:
            unbind_subject_bearer(binding)
    return {"status": "UNAVAILABLE", "codes": [], "names": []}


def _teo_latest_code(providers, bearer) -> str | None:
    """Authoritative oracle: first (newest) codigo_processo."""
    for provider in providers.values():
        binding = bind_subject_bearer(bearer)
        try:
            surface = provider.list_groups(correlation_id="oracle-teo")
        finally:
            unbind_subject_bearer(binding)
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
                              "especificar", "poderia", "refiro",
                              "especifique", "reformule")
                ) or not invokes
                else "FAIL"
            )
            first = first or (None if outcome == "PASS" else "INCONCLUSIVE")
        else:
            outcome = "PASS" if not invokes else "FAIL"
            if outcome == "FAIL" and exp.get("allow_conversational"):
                # A grounded answer built on real owner records is a
                # strictly better outcome than a conversational one.
                outcome = (
                    "PASS"
                    if "código do produto" in content
                    or "codigo do produto" in content
                    else "FAIL"
                )
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
        prepared = bool(
            invoked
            & (
                VISTA_PREPARE_CAPS
                | VISTA_READ_CAPS
                | TEO_PREPARE_CAPS
                | TEO_CAPS
            )
        )
        clarify = any(
            k in content
            for k in ("programação", "painéis tv", "tv dashboard",
                      "confirma", "confirmar", "qual conteúdo",
                      "quais itens", "slide", "processo", "registro")
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
            oracle = run.get("oracle_data") or {}
            pert_codes = [
                str(c).lower()
                for c in (oracle.get("pertinent_codes") or [])
            ]
            oracle_names = [
                str(n).lower()
                for n in (oracle.get("names") or [])
            ]
            rejection_phrases = (
                "não correspondem",
                "nao correspondem",
                "não correspondem ao que foi pedido",
                "não encontrei registros",
                "nao encontrei registros",
                "nenhum registro pertinente",
                "não foi possível localizar",
                "não localizei registros",
                "registros encontrados não",
            )
            rejected = any(p in content for p in rejection_phrases)
            hits = sum(1 for c in pert_codes if c in content)
            name_hits = sum(
                1
                for n in oracle_names
                if len(n) > 12 and n[:40] in content
            )
            want_n = int(exp.get("min_records") or 1)
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
            elif (
                not pert_codes
                and oracle.get("status") == "COMPLETED"
            ):
                # Legitimate absence verified by the authoritative
                # oracle: an honest empty/limitation answer is the
                # correct business outcome — a delivered record would
                # be fabrication.
                delivered = name_hits or (
                    "código do produto" in content
                    or "codigo do produto" in content
                )
                outcome = "FAIL" if delivered else "PASS"
                if delivered:
                    first = first or "FABRICATED_ABSENCE"
            elif rejected:
                outcome, first = "FAIL", first or "EVIDENCE_REJECTION"
            elif hits >= want_n or name_hits >= want_n:
                outcome = "PASS"
            elif pert_codes and (hits or name_hits):
                outcome, first = (
                    "PARTIAL", first or "COMPLETENESS"
                )
            elif subj and subj in content and pert_codes:
                # subject echoed but no authoritative fact delivered
                outcome, first = "FAIL", first or "UNGROUNDED_ANSWER"
            else:
                outcome = "FAIL"
                first = first or "EVIDENCE_RELEVANCE"
    else:  # any_read
        want = exp.get("want_owner")
        if want:
            hit = any(
                c.startswith(want + ".") and
                i.get("status") == "COMPLETED"
                for c, i in
                ((i["capability_id"], i) for i in invokes)
            )
            refusal = any(
                p in content for p in
                ("não consegui", "nao consegui", "não foi possível",
                 "não tenho acesso", "indisponível")
            )
            if hit and not refusal:
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

    # CORPUS_SET selects the evaluation pool: "main" (incident+base,
    # the development corpus), "heldout" (frozen generalization set),
    # or "all". Default "main" preserves the Task 19 battery shape.
    import os

    corpus_pool = {
        "main": list(INCIDENT_CORPUS) + list(BASE_CORPUS),
        "heldout": list(HELD_OUT_CORPUS),
        "all": list(INCIDENT_CORPUS)
        + list(BASE_CORPUS)
        + list(HELD_OUT_CORPUS),
    }
    pool = corpus_pool.get(
        os.environ.get("CORPUS_SET", "main").strip().lower(),
        corpus_pool["main"],
    )
    scenarios = [
        sc
        for sc in pool
        if SCENARIO_FILTER is None or sc.sid in SCENARIO_FILTER
    ]

    # Oracles (authorized reads, once each)
    oracle_cache = {}
    for sc in scenarios:
        if sc.oracle_query and sc.sid not in oracle_cache:
            remote, args = sc.oracle_query
            if remote == "delpi.search_products":
                # direct OpenAPI provider was removed — the only live
                # oracle path is the governed DAVI discover/execute.
                oracle_cache[sc.sid] = _davi_product_oracle(
                    orch._providers,
                    args if args.get("code") else args.get("description"),
                    bearer,
                )
            else:
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
