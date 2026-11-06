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


CAIO_CAPS = {
    "caio.get_context", "caio.read", "caio.analyze",
    "caio.knowledge", "caio.commercial",
}
CLARA_CAPS = {
    "clara.get_context", "clara.read", "clara.analyze",
    "clara.knowledge", "clara.controllership-finance",
}
SURI_CAPS = {
    "suri.get_context", "suri.read", "suri.analyze",
    "suri.knowledge",
}
EVA_CAPS = {
    "eva.get_catalog", "eva.get_engineering_home",
    "eva.get_engineering_overview", "eva.search_nonconformities",
    "eva.get_nonconformity", "eva.get_nonconformity_history",
}

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


HELD_OUT_CORPUS_V2 = [
    # --- implicit product records, fresh subjects/formulations (8)
    _x("nh_conector", "me mostre dois conectores elétricos",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       oracle_query=[
           ("delpi.search_products",
            {"description": "conector", "page_size": 50}),
           ("delpi.search_products",
            {"description": "conector eletrico", "page_size": 50}),
       ],
       expected={"subject": "conector", "min_records": 2}),
    _x("nh_disjuntor", "existe algum disjuntor registrado?",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       oracle_query=[
           ("delpi.search_products",
            {"description": "disjuntor", "page_size": 50}),
           ("delpi.search_products",
            {"description": "disjuntores", "page_size": 50}),
       ],
       expected={"subject": "disjuntor", "min_records": 1}),
    _x("nh_ilhos", "liste três exemplos de ilhó",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       oracle_query=[
           ("delpi.search_products",
            {"description": "ilhos", "page_size": 50}),
           ("delpi.search_products",
            {"description": "ilho", "page_size": 50}),
       ],
       expected={"subject": "ilhos", "min_records": 3}),
    _x("nh_espaguete", "traga um espaguete termorretrátil",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       oracle_query=[
           ("delpi.search_products",
            {"description": "espaguete", "page_size": 50}),
           ("delpi.search_products",
            {"description": "espaguete termorretratil",
             "page_size": 50}),
       ],
       expected={"subject": "espaguete", "min_records": 1}),
    _x("nh_estanho", "mostre solda de estanho",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       oracle_query=[
           ("delpi.search_products",
            {"description": "estanho", "page_size": 50}),
           ("delpi.search_products",
            {"description": "solda estanho", "page_size": 50}),
       ],
       expected={"subject": "estanho", "min_records": 1}),
    _x("nh_conduite", "procure um conduite",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       oracle_query=[
           ("delpi.search_products",
            {"description": "conduite", "page_size": 50}),
           ("delpi.search_products",
            {"description": "conduites", "page_size": 50}),
       ],
       expected={"subject": "conduite", "min_records": 1}),
    _x("nh_tomada", "quero ver duas tomadas cadastradas",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       oracle_query=[
           ("delpi.search_products",
            {"description": "tomada", "page_size": 50}),
           ("delpi.search_products",
            {"description": "tomadas", "page_size": 50}),
       ],
       expected={"subject": "tomada", "min_records": 2}),
    _x("nh_code", "descreva o produto de código 80002437",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       oracle_query=(
           "delpi.search_products", {"code": "80002437"}),
       expected={"subject": "80002437", "min_records": 1}),
    # --- legitimate absence (oracle verified zero records)
    _x("nh_absent", "traga uma placa acrílica",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       oracle_query=(
           "delpi.search_products",
           {"description": "placa acrilica", "page_size": 50}),
       expected={"subject": "placa acrilica"}),
    # --- TÉO process surface (3)
    _x("nh_teo_ctx", "qual o contexto do processo PROC-0105?",
       "records", True, "any_read",
       allowed_caps=TEO_CAPS,
       expected={"want_owner": "teo"}),
    _x("nh_teo_hist",
       "mostre o histórico do processo PROC-0105",
       "records", True, "any_read",
       allowed_caps=TEO_CAPS,
       expected={"want_owner": "teo"}),
    _x("nh_teo_list", "liste os processos registrados",
       "records", True, "any_read",
       allowed_caps=TEO_CAPS,
       expected={"want_owner": "teo"}),
    # --- VISTA surface
    _x("nh_vista", "mostre as playlists disponíveis",
       "records", True, "any_read",
       allowed_caps=VISTA_READ_CAPS,
       expected={"want_owner": "vista"}),
    # --- explicit specialist selection
    _x("nh_explicit_davi",
       "peça ao DAVI para encontrar um sensor",
       "discovery", True, "any_read",
       allowed_caps=DAVI_CAPS | PRODUCT_CAPS,
       expected={"want_owner": "davi"}),
    # --- continuity / prior references
    _x("nh_cont", "e quais são os códigos deles?",
       "continuity", True, "any_read",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       prior_turns=(
           _u("me mostre conectores"),
           _a("Encontrei: 80014158 4 CONECTOR CIRCULAR M23; "
              "10090661 ACESSORIOS DO CONECTOR 10 VIAS AMPHENOL "
              "MS3100F 18-S1.", obs=True),
       ),
       expected={"referent_codes": ["80014158", "10090661"]}),
    # --- write ask on a read-only surface → honest limitation
    _x("nh_neg_update", "atualize o preço do produto 80002437",
       "negative", False, "refusal",
       must_not_invoke=True,
       expected={"limitation": True}),
    # --- missing capability → honest limitation
    _x("nh_neg_whatsapp", "mande um WhatsApp para o cliente",
       "negative", False, "refusal",
       must_not_invoke=True,
       expected={"limitation": True}),
    # --- controls / general questions
    _x("nh_ctrl_greet", "bom dia!",
       "control", False, "conversational",
       must_not_invoke=True),
    _x("nh_ctrl_math", "quanto é 12 vezes 8?",
       "control", False, "conversational",
       must_not_invoke=True),
    _x("nh_surface",
       "o que você consegue consultar pra mim?",
       "control", False, "conversational",
       must_not_invoke=True),
    # --- PREPARE without ACT
    _x("nh_prep",
       "prepare o cadastro de um novo processo chamado "
       "revisão semanal",
       "prepare", True, "prepare",
       allowed_caps=TEO_CAPS | TEO_PREPARE_CAPS,
       expected={"kind": "prepare_or_clarify"}),
]


# Task 22 acceptance held-out — independent entities and formulations
# (parafuso/porca/arruela/rolamento/abracadeira/correia families never
# appeared in main/heldout/newheldout); frozen before the T22
# candidate runs. Oracles resolved through the governed DAVI route
# (multi-query union, same as V2).
HELD_OUT_CORPUS_V3 = [
    # --- implicit product records, fresh families (7)
    _x("t2_parafuso", "traga dois parafusos cadastrados",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       oracle_query=[
           ("delpi.search_products",
            {"description": "parafuso", "page_size": 50}),
       ],
       expected={"subject": "parafuso", "min_records": 1}),
    _x("t2_porca", "existe alguma porca sextavada no sistema?",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       oracle_query=[
           ("delpi.search_products",
            {"description": "porca", "page_size": 50}),
           ("delpi.search_products",
            {"description": "porca sextavada", "page_size": 50}),
       ],
       expected={"subject": "porca", "min_records": 1}),
    _x("t2_arruela", "mostre um exemplo de arruela",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       oracle_query=[
           ("delpi.search_products",
            {"description": "arruela", "page_size": 50}),
       ],
       expected={"subject": "arruela", "min_records": 1}),
    _x("t2_abracadeira", "liste duas abracadeiras",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       oracle_query=[
           ("delpi.search_products",
            {"description": "abracadeira", "page_size": 50}),
       ],
       expected={"subject": "abracadeira", "min_records": 1}),
    _x("t2_rolamento", "tem rolamento registrado?",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       oracle_query=[
           ("delpi.search_products",
            {"description": "rolamento", "page_size": 50}),
       ],
       expected={"subject": "rolamento"}),
    _x("t2_correia", "traga uma correia dentada",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       oracle_query=[
           ("delpi.search_products",
            {"description": "correia", "page_size": 50}),
           ("delpi.search_products",
            {"description": "correia dentada", "page_size": 50}),
       ],
       expected={"subject": "correia"}),
    _x("t2_tubo", "mostre um tubo cadastrado",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       oracle_query=[
           ("delpi.search_products",
            {"description": "tubo", "page_size": 50}),
       ],
       expected={"subject": "tubo"}),
    # --- code lookup on a known record (Task 20 ledger documented)
    _x("t2_code", "qual a descrição do produto 10080683?",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       oracle_query=[
           ("delpi.search_products", {"code": "10080683"}),
       ],
       expected={"subject": "10080683", "min_records": 1}),
    # --- legitimate absence candidate (oracle decides)
    _x("t2_absent", "traga um sensor de proximidade",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       oracle_query=[
           ("delpi.search_products",
            {"description": "sensor", "page_size": 50}),
           ("delpi.search_products",
            {"description": "sensor de proximidade", "page_size": 50}),
       ],
       expected={"subject": "sensor"}),
    # --- TÉO surface
    _x("t2_teo_resp", "quem é o responsável pelo processo PROC-0105?",
       "records", True, "any_read",
       allowed_caps=TEO_CAPS,
       expected={"want_owner": "teo"}),
    _x("t2_teo_status", "qual o status do processo PROC-0105?",
       "records", True, "any_read",
       allowed_caps=TEO_CAPS,
       expected={"want_owner": "teo"}),
    # --- VISTA surface
    _x("t2_vista_screens", "quais telas de TV estão cadastradas?",
       "records", True, "any_read",
       allowed_caps=VISTA_READ_CAPS,
       expected={"want_owner": "vista"}),
    # --- explicit specialist
    _x("t2_davi_explicit", "peça ao DAVI para buscar porcas",
       "discovery", True, "any_read",
       allowed_caps=DAVI_CAPS | PRODUCT_CAPS,
       expected={"want_owner": "davi"}),
    # --- continuity over prior observation
    _x("t2_cont", "e o segundo item, qual é o código?",
       "continuity", True, "any_read",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       prior_turns=(
           _u("traga porcas sextavadas"),
           _a("Encontrei: 10090012 PORCA SEXTAVADA M6 ZINCADA; "
              "10090020 PORCA SEXTAVADA M8 ZINCADA.", obs=True),
       ),
       expected={"referent": "10090020"}),
    # --- workspace-selected entity
    _x("t2_workspace", "qual a descrição deste item?",
       "records", True, "records",
       allowed_caps=PRODUCT_CAPS | DAVI_CAPS,
       workspace=PRODUCT_WORKSPACE,
       expected={"referent": "80002437"}),
    # --- PREPARE without ACT
    _x("t2_prep", "prepare um processo chamado auditoria task22",
       "prepare", True, "prepare",
       allowed_caps=TEO_CAPS | TEO_PREPARE_CAPS,
       expected={"kind": "prepare_or_clarify"}),
    # --- refusals / controls
    _x("t2_neg_delete", "delete o produto 10080683",
       "negative", False, "refusal",
       must_not_invoke=True,
       expected={"limitation": True}),
    _x("t2_neg_whatsapp", "envie um whatsapp para o cliente",
       "negative", False, "refusal",
       must_not_invoke=True,
       expected={"limitation": True}),
    _x("t2_ctrl_greet", "bom dia, tudo bem?",
       "control", False, "conversational",
       must_not_invoke=True),
    _x("t2_ctrl_concept", "o que é um banco de dados relacional?",
       "control", False, "conversational",
       must_not_invoke=True),
]


# Doc 211 corpus — 28 composite READ-only questions (verbatim).
DOC211_CORPUS = [
    _x("cmp_01", "CAIO, produza um diagnóstico completo da situação comercial da DELPI nos últimos 90 dias com dados oficiais do Portal Comercial. Examine ROL, faturamento e evolução temporal, metas, taxa de fechamento e tendências; concentração por carteira e cliente, clientes que reduziram compras e oportunidades; pedidos em aberto, atrasos, OTD e saldo a faturar; propostas, etapas do funil, oportunidades estagnadas e impacto potencial. Concilie definições, períodos e denominadores antes de comparar. Identifique as cinco prioridades por impacto e urgência; para cada uma inclua números e evidências, entidades autorizadas, impacto financeiro calculável, causa comprovada ou hipótese, ação recomendada, responsável sugerido apenas com fundamento e KPI. Termine com plano de ação textual de 30 dias, dependências e limitações. Não crie tarefas nem execute mudanças.",
       "composite", True, "any_read",
       allowed_caps=CAIO_CAPS,
       expected={"want_owner": "caio", "require_business_result": True}),
    _x("cmp_02", "CAIO, investigue os clientes e carteiras com maior queda de compras nos últimos 180 dias, comparando períodos equivalentes e sazonalidade disponível. Separe perda de frequência, redução de ticket, concentração de receita, clientes inativos e migração de mix; confronte pedidos, propostas e histórico de faturamento onde houver vínculo oficial. Produza ranking de até cinco riscos e até cinco oportunidades, com critérios transparentes, cliente/carteira apenas se autorizado, magnitude monetária e lacunas. Para cada item proponha abordagem comercial e indicador de acompanhamento para 30 dias, sem inferir motivos do cliente sem evidência nem disparar contato.",
       "composite", True, "any_read",
       allowed_caps=CAIO_CAPS,
       expected={"want_owner": "caio", "require_business_result": True}),
    _x("cmp_03", "CAIO, avalie as propostas e oportunidades abertas dos últimos 120 dias: quantidade, valor, estágios, envelhecimento, conversão histórica por etapa e oportunidades sem avanço. Compare o pipeline com metas e faturamento realizado, explicitando quais indicadores são oficialmente disponíveis e sem converter automaticamente valor bruto em receita provável. Projete cenários conservador/base/otimista somente se houver histórico e premissas defensáveis; mostre fórmulas, intervalos e incerteza. Identifique cinco intervenções prioritárias com justificativa, proprietário sugerido fundamentado e indicadores. Entregue recomendações, sem alterar propostas ou estágios.",
       "composite", True, "any_read",
       allowed_caps=CAIO_CAPS,
       expected={"want_owner": "caio", "require_business_result": True}),
    _x("cmp_04", "CAIO, consolide pedidos abertos, atrasados e previstos para entrega nos próximos 30 dias. Relacione OTD, saldo a faturar, prazo prometido, histórico de entrega e concentração por cliente/carteira conforme as fontes autorizadas. Diferencie atraso confirmado, risco previsto e impedimento cuja causa não esteja documentada; não atribua culpa à produção ou suprimentos sem evidência. Estime exposição financeira sem dupla contagem, liste prioridades com pedidos identificados quando autorizado, proponha mitigação e painel textual de acompanhamento semanal. Nenhuma alteração de pedido nem comunicação externa.",
       "composite", True, "any_read",
       allowed_caps=CAIO_CAPS,
       expected={"want_owner": "caio", "require_business_result": True}),
    _x("cmp_05", "CLARA, analise os últimos três fechamentos mensais disponíveis: receitas, custos, despesas, margem, desvios contra orçamento e pendências de fechamento conforme evidências oficiais acessíveis. Explique a base contábil e os períodos antes de cruzar valores; identifique inconsistências e tarefas com evidência ausente, distinguindo pendência documental de erro contábil. Ordene cinco riscos ou melhorias por materialidade e urgência, com valores, origem, causa comprovada versus hipótese, responsáveis documentados quando houver e ações de controle para 30 dias. Apenas relatório; não fechar tarefas nem lançar ajustes.",
       "composite", True, "any_read",
       allowed_caps=CLARA_CAPS,
       expected={"want_owner": "clara", "require_business_result": True}),
    _x("cmp_06", "CLARA, investigue os maiores desvios orçado versus realizado dos últimos 90 dias, por centro de custo ou rubrica quando disponível. Separe efeito preço, volume, classificação e competência apenas se os dados permitirem, incluindo ponte matemática reproduzível e reconciliação de totais. Mostre os cinco desvios mais relevantes e as fontes de cada valor; assinale insuficiência de evidências sem preencher lacunas por suposição. Recomende verificações e indicadores para os próximos 30 dias, sem lançamentos ou mudanças em orçamento.",
       "composite", True, "any_read",
       allowed_caps=CLARA_CAPS,
       expected={"want_owner": "clara", "require_business_result": True}),
    _x("cmp_07", "CLARA, avalie a prontidão do fechamento mensal mais recente e dos dois anteriores: tarefas concluídas, atrasadas, evidências anexadas, responsáveis formalmente designados, dependências e exceções. Cruze a evolução dos atrasos com os registros de controladoria disponíveis, distinguindo falha de processo de ausência de informação. Produza matriz de risco, cinco ações priorizadas com criticidade e evidência, e plano de conferência semanal. Não aprovar, concluir nem modificar tarefas.",
       "composite", True, "any_read",
       allowed_caps=CLARA_CAPS,
       expected={"want_owner": "clara", "require_business_result": True}),
    _x("cmp_08", "CLARA, usando somente números oficiais disponíveis, avalie exposição a variações de receitas e custos para os próximos 30–90 dias. Identifique tendência observada, sazonalidade conhecida e os fatores que não podem ser previstos. Se houver base suficiente, calcule três cenários de margem/resultado com premissas e sensibilidades explicitadas; caso contrário apresente apenas diagnóstico das lacunas. Termine com cinco prioridades de monitoramento, responsáveis somente se formalmente vinculados e métricas. Não tratar cenários como fatos nem executar qualquer ajuste financeiro.",
       "composite", True, "any_read",
       allowed_caps=CLARA_CAPS,
       expected={"want_owner": "clara", "require_business_result": True}),
    _x("cmp_09", "SURI, investigue a situação dos pedidos de compra em aberto dos últimos 90 dias e das entregas previstas nos próximos 30 dias. Identifique atrasos confirmados, lead times, itens críticos, concentrações por fornecedor, quantidades e valores quando disponíveis. Diferencie falta real de material, risco de abastecimento e indisponibilidade de informação. Priorize cinco casos com IDs autorizados, impacto operacional potencial verificável, evidências, causa ou hipótese, alternativa recomendada e KPI. Sem emitir, cancelar ou modificar pedidos.",
       "composite", True, "any_read",
       allowed_caps=SURI_CAPS,
       expected={"want_owner": "suri", "require_business_result": True}),
    _x("cmp_10", "SURI, compare desempenho de fornecedores em janelas equivalentes dos últimos 180 dias por prazo, quantidade, incidência de atraso e valor das compras, conforme a fonte oficial permitir. Evite rankings sem denominadores comparáveis ou julgamentos não documentados. Apresente padrões de recorrência, cinco riscos e cinco oportunidades de melhoria com evidências de pedidos, premissas e recomendações de acompanhamento em 30 dias. Não enviar cobrança, avaliação formal ou mensagem a fornecedores.",
       "composite", True, "any_read",
       allowed_caps=SURI_CAPS,
       expected={"want_owner": "suri", "require_business_result": True}),
    _x("cmp_11", "SURI, examine solicitações e pedidos de compra disponíveis que possam impactar as próximas seis semanas. Agrupe por item, prazo, status e dependência legítima; identifique duplicidades possíveis sem afirmar que são duplicatas sem identificadores e prova. Calcule saldo pendente e exposição de valor somente quando campos oficiais permitirem. Monte uma sequência sugerida de acompanhamento com cinco prioridades, indicadores, limites e dados faltantes. Não criar requisições nem aprovar compras.",
       "composite", True, "any_read",
       allowed_caps=SURI_CAPS,
       expected={"want_owner": "suri", "require_business_result": True}),
    _x("cmp_12", "SURI, avalie os tempos e estados de um ciclo de compra — solicitação, aprovação, pedido e recebimento — para o período recente, somente nas etapas publicadas pelas APIs autorizadas. Localize possíveis filas, exceções e retrabalhos com timestamps verificáveis; se uma etapa não estiver disponível, marque lacuna. Apresente cinco gargalos priorizados com evidências, cálculo do atraso, hipótese causal separada de fato e plano de melhoria de 30 dias. Nenhuma execução operacional.",
       "composite", True, "any_read",
       allowed_caps=SURI_CAPS,
       expected={"want_owner": "suri", "require_business_result": True}),
    _x("cmp_13", "EVA, analise as demandas e solicitações de Engenharia dos últimos 90 dias: volumes, status, tempo em aberto, envelhecimento, prioridades registradas, responsáveis autorizados e evidências de conclusão. Investigue dependências e gargalos observáveis sem inferir automaticamente que atrasos são falhas pessoais. Selecione cinco prioridades com IDs, impacto documentado, causa ou hipótese, ação recomendada e indicador semanal. Não alterar demandas ou encaminhar tarefas.",
       "composite", True, "any_read",
       allowed_caps=EVA_CAPS,
       expected={"want_owner": "eva", "require_business_result": True}),
    _x("cmp_14", "EVA, investigue LMPs e documentos de engenharia disponíveis, sua revisão, vinculações com solicitações e inconsistências formalmente registradas. Diferencie revisão vigente, obsoleta e desconhecida conforme contrato e evidências; não deduza conformidade técnica ou segurança física a partir de texto livre. Liste cinco riscos ou melhorias com referência documental, necessidade de validação humana e plano textual de revisão em 30 dias. Não publicar, aprovar ou editar arquivos.",
       "composite", True, "any_read",
       allowed_caps=EVA_CAPS,
       expected={"want_owner": "eva", "require_business_result": True}),
    _x("cmp_15", "EVA, investigue a evolução do fluxo de solicitações técnicas ao longo dos últimos 180 dias, calculando throughput, tempo por estágio e demandas paradas apenas quando timestamps e status oficiais permitirem. Segmente por tipo de demanda e prioridade quando cabível; evite estatísticas com amostra insuficiente. Identifique cinco restrições de fluxo, exponha evidências, hipóteses e recomendações, e proponha indicadores de acompanhamento sem redistribuir trabalho automaticamente.",
       "composite", True, "any_read",
       allowed_caps=EVA_CAPS,
       expected={"want_owner": "eva", "require_business_result": True}),
    _x("cmp_16", "EVA, avalie demandas técnicas com prazo próximo, atrasadas ou dependentes de documentos, desenhos ou LMPs. Identifique vínculos comprovados, bloqueios e incertezas; não invente relação com produção, compras ou clientes que não esteja publicada. Construa um mapa textual de até cinco cadeias críticas, explique a origem de cada vínculo e sugira mitigação e pontos de verificação nos próximos 30 dias. Não comandar máquinas, publicar desenhos ou executar ações.",
       "composite", True, "any_read",
       allowed_caps=EVA_CAPS,
       expected={"want_owner": "eva", "require_business_result": True}),
    _x("cmp_17", "TÉO, analise iniciativas e processos de transformação digital dos últimos 90 dias com dados oficiais do Transformômetro: andamento, metas, atrasos, benefícios registrados, dependências, riscos e evidências de progresso. Cruze categorias e status somente quando publicados e comparáveis. Identifique cinco prioridades por impacto e urgência, diferenciando benefício realizado, estimativa e hipótese; proponha ações e métricas de 30 dias. Não criar nem modificar iniciativas.",
       "composite", True, "any_read",
       allowed_caps=TEO_CAPS,
       expected={"want_owner": "teo", "require_business_result": True}),
    _x("cmp_18", "TÉO, identifique processos ou iniciativas disponíveis com lacunas de documentação, handoffs ou indicadores. Examine evidências de SIPOC ou modelos processuais apenas quando registrados; não invente etapas do processo. Selecione até cinco oportunidades de padronização, com owner conhecido, lacunas, riscos e propostas práticas de diagnóstico. Produza uma agenda textual de 30 dias e indicadores sem editar o Transformômetro.",
       "composite", True, "any_read",
       allowed_caps=TEO_CAPS,
       expected={"want_owner": "teo", "require_business_result": True}),
    _x("cmp_19", "TÉO, investigue iniciativas com atrasos repetidos ou mudanças de prazo nos últimos 180 dias. Compare histórico e dependências; se não houver histórico versionado, declare a impossibilidade de provar reincidência. Separe causa registrada de hipótese e estime impacto apenas quando houver base quantitativa. Apresente cinco prioridades, evidência por iniciativa, responsáveis formalmente associados e plano de acompanhamento não executável.",
       "composite", True, "any_read",
       allowed_caps=TEO_CAPS,
       expected={"want_owner": "teo", "require_business_result": True}),
    _x("cmp_20", "TÉO, avalie se as iniciativas recentes dispõem de baseline, indicador-alvo, data, resultado observado e evidência de benefício. Classifique como benefício comprovado, parcialmente observado, projetado ou não mensurável, sem tratar estimativas como resultado. Identifique cinco lacunas prioritárias de medição e proponha coleta/validação humana e indicadores para 30 dias. Nenhuma atualização de registros.",
       "composite", True, "any_read",
       allowed_caps=TEO_CAPS,
       expected={"want_owner": "teo", "require_business_result": True}),
    _x("cmp_21", "VISTA, apresente um inventário fundamentado dos painéis e indicadores disponíveis para análise operacional, incluindo definição, granularidade, período coberto, fonte e atualização quando publicados. Identifique cobertura ausente, dados desatualizados e métricas com definição ambígua, distinguindo o que o catálogo declara do que foi efetivamente lido. Priorize cinco riscos de interpretação e recomende um plano de validação de 30 dias. Não modificar painéis nem programações.",
       "composite", True, "any_read",
       allowed_caps=VISTA_READ_CAPS,
       expected={"want_owner": "vista", "require_business_result": True}),
    _x("cmp_22", "VISTA, selecione indicadores operacionais efetivamente acessíveis com série recente e examine tendências dos últimos 90 dias. Compare períodos equivalentes e evidencie valores observados; não chamar uma variação de anomalia estatística sem base suficiente. Identifique cinco pontos de atenção, cálculos reproduzíveis, possíveis causas somente como hipóteses e ações de investigação. Se só existir catálogo, explique por que não há série para análise.",
       "composite", True, "any_read",
       allowed_caps=VISTA_READ_CAPS,
       expected={"want_owner": "vista", "require_business_result": True}),
    _x("cmp_23", "VISTA, investigue se uma mesma métrica pode ser consultada em diferentes formatos ou painéis publicados. Compare definições, filtros, atualização, unidades, agregações e totalizadores, sem presumir que formatos de exibição diferentes são conjuntos de dados equivalentes. Identifique divergências comprovadas e limites do catálogo, priorizando cinco verificações e indicadores de reconciliação. Não criar ou alterar visualizações.",
       "composite", True, "any_read",
       allowed_caps=VISTA_READ_CAPS,
       expected={"want_owner": "vista", "require_business_result": True}),
    _x("cmp_24", "VISTA, avalie as métricas disponíveis para uma revisão gerencial mensal, identificando cobertura, atualidade, permissões, filtros possíveis e ausência de denominadores. Proponha um quadro textual de até cinco indicadores prioritários com definição, evidência, risco de uso incorreto, responsável pelo dado somente quando oficialmente identificado e validação recomendada em 30 dias. Não invente KPIs ou resultados ausentes.",
       "composite", True, "any_read",
       allowed_caps=VISTA_READ_CAPS,
       expected={"want_owner": "vista", "require_business_result": True}),
    _x("cmp_25", "DAVI, investigue no cadastro oficial materiais de conexão elétrica descritos como terminal pino, terminal bala, conector e variantes técnicas semelhantes. Descubra capacidades e fontes autorizadas; execute apenas consultas pertinentes e compare códigos, designações, medidas, materiais e variantes sem fundir itens distintos por semelhança textual. Entregue até dez exemplos reais com campos verificáveis, critérios de inclusão, ambiguidades e ausências. Não inventar cadastro nem editar materiais.",
       "composite", True, "any_read",
       allowed_caps=DAVI_CAPS,
       expected={"want_owner": "davi", "require_business_result": True}),
    _x("cmp_26", "DAVI, com base em um identificador empresarial autorizado fornecido pelo contexto de teste, investigue quais registros oficiais e relações podem ser consultados sobre essa entidade. Diferencie identificação direta, associação comprovada e mera coincidência textual; respeite a fronteira de cada Domain API. Produza linha de evidências com origem, timestamps quando disponíveis, relações encontradas e lacunas; se o identificador não estiver fornecido, não escolha arbitrariamente outro. Nenhuma alteração.",
       "composite", True, "any_read",
       allowed_caps=DAVI_CAPS,
       expected={"want_owner": "davi", "require_business_result": True}),
    _x("cmp_27", "DAVI, examine duas consultas oficiais relacionadas a um mesmo assunto empresarial conforme fixtures/oráculos previamente preparados, usando discovery e execução governada. Identifique se os resultados são realmente comparáveis em período, unidade, entidade e escopo; explique possíveis divergências e se podem ou não ser conciliadas. Gere tabela de fontes, evidências, conclusões sustentadas e pontos que exigem validação do owner. Não resolver inconsistências inventando uma versão da verdade.",
       "composite", True, "any_read",
       allowed_caps=DAVI_CAPS,
       expected={"want_owner": "davi", "require_business_result": True}),
    _x("cmp_28", "DAVI, receba uma solicitação empresarial ambígua com múltiplas entidades homônimas existentes nos dados de teste. Mostre como identifica o objetivo, descobre as superfícies autorizadas e decide quando precisa de esclarecimento, sem escolher um registro sem evidência suficiente. Quando a desambiguação for possível por contexto oficial, conclua a consulta com rastreabilidade; caso contrário apresente alternativas comprovadas e a informação faltante. Não executar writes.",
       "composite", True, "any_read",
       allowed_caps=DAVI_CAPS,
       expected={"want_owner": "davi", "require_business_result": True}),
]

def _run_turn(handler, sc, bearer, stage_log, activity_log):
    logger = logging.getLogger(
        "app.application.capability_provision.governed_capability_orchestrator"
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
        # Fabrication is judged on prose only — a governed PREPARE
        # card legitimately carries the requested description inside
        # its ops payload ("description: playlist criada..."), which
        # is payload data, not a completion claim.
        prose = re.split(
            r"\n\s*(?:target|ops|operationNames|payload|changes)"
            r"\s*:",
            content,
            maxsplit=1,
        )[0]
        fabricated = any(
            p in prose
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
                want_hit_err = any(
                    c.startswith(want + ".")
                    and i.get("status") != "COMPLETED"
                    for c, i in
                    ((i["capability_id"], i) for i in invokes)
                )
                if want_hit_err:
                    # the intended owner WAS selected and invoked —
                    # the divergence is the owner call result, never
                    # a selection mistake.
                    outcome, first = (
                        "FAIL",
                        "OWNER_ACCESS_OR_AVAILABILITY",
                    )
                else:
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
        "newheldout": list(HELD_OUT_CORPUS_V2),
        "t22heldout": list(HELD_OUT_CORPUS_V3),
        "doc211": list(DOC211_CORPUS),
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
            # oracle_query may be a single (remote, args) pair or a
            # list of pairs — a list collects each authorized oracle
            # read and unions the pertinent sets, covering the
            # legitimate phrasings a governed turn may emit (owner
            # search caps each query result page independently).
            queries = (
                sc.oracle_query
                if isinstance(sc.oracle_query, list)
                else [sc.oracle_query]
            )
            merged_oracle = None
            for remote, args in queries:
                if remote == "delpi.search_products":
                    # direct OpenAPI provider was removed — the only
                    # live oracle path is the governed DAVI
                    # discover/execute.
                    one = _davi_product_oracle(
                        orch._providers,
                        args if args.get("code")
                        else args.get("description"),
                        bearer,
                    )
                else:
                    one = _fetch_oracle_records(
                        orch._providers, (remote, args), bearer
                    )
                if merged_oracle is None:
                    merged_oracle = one
                    continue
                for key in ("codes", "pertinent_codes", "names"):
                    seen = set(merged_oracle.get(key) or [])
                    merged_oracle[key] = list(seen) + [
                        v
                        for v in (one.get(key) or [])
                        if v not in seen
                    ]
                if one.get("status") != "COMPLETED":
                    merged_oracle["status"] = one["status"]
            oracle_cache[sc.sid] = merged_oracle
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
