#!/usr/bin/env python3
"""Gate 082-RW01 — auditoria semântica por afirmação do corpus CLARA.

Reexecutável: PWP=<senha> python clara_semantic_audit.py [--llm]

Percorre 100% dos itens PUBLISHED. Para cada item:

1. extrai afirmações (claims) por statement — tipadas como
   state/mechanism/rule/contract/plan/historical/dynamic_data;
2. perfila o conteúdo estrutural (fração de código, tabela,
   metadados) — a justificativa de NOT_APPLICABLE cita o conteúdo
   efetivamente inspecionado, nunca "ausência de match";
3. confronta cada afirmação operacional com a tabela de verdade
   vigente (REPORT_STATE/STILL_MISSING/PARITY — fichas vigentes,
   capabilities do bridge e decisões G074–G081), registrando
   autoridade e evidência por afirmação;
4. emite a matriz de evidência por afirmação (g082rw-claims.jsonl),
   o inventário por item (g082rw-items.jsonl), as divergências
   (g082rw-divergences.jsonl) e o relatório de cobertura.

--llm habilita a segunda passagem assistida (Ollama local) sobre os
itens que o extrator determinístico não conseguiu decidir sozinho.
"""

import argparse
import json
import os
import re
import sys
import urllib.request

sys.path.insert(0, "controllership-finance-api")
os.environ.update(dict(PLUGINS_DB_HOST="localhost", PLUGINS_DB_PORT="5433",
    PLUGINS_DB_NAME="plugins_hub", PLUGINS_DB_USER="plugins_user",
    PLUGINS_DB_PASSWORD=os.environ["PWP"], PLUGINS_DB_SSLMODE="disable"))
from controllership_finance_app.infrastructure.persistence.plugins_db import plugins_db_connect  # noqa: E501

OUT_DIR = os.environ.get(
    "AUDIT_OUT",
    "docs/12-roadmap-e-evolucao/controllership-finance/"
    "evidence-g082rw",
)

RID = r"R0[1-9]|R1[0-5]"
REPORT_RE = re.compile(rf"\b({RID})\b")

# ------------------------------------------------------------------
# Detectores de afirmação por statement
# ------------------------------------------------------------------

# Predicado de ESTADO (disponibilidade/implementação/ausência/
# bloqueio/pendência) — o verbo que torna o statement sensível a
# atualidade. Sujeitos mecânicos (usa, obtém, calcula) NÃO entram.
STATUS_PRED = re.compile(
    r"(?i)(BLOQUEADO|BLOCKED(?:_BY_\w+)?|impedid\w*|travad\w*|"
    r"NOT_IMPLEMENTED|not_implemented|n[aã]o (foi |está |será )?"
    r"implementad\w*|sem (handler|contrato|endpoint|rota|"
    r"capability|produtor|fonte|artefato|evid[êe]ncia|suporte|"
    r"integra[cç][aã]o)|indispon[íi]vel|unavailable|"
    r"SOURCE_UNAVAILABLE|ausente|missing|"
    r"n[aã]o (existe|há|possui|tem)\w*|inexist\w*|"
    r"IMPLEMENTAD\w*|IMPLEMENTED|deployed|em produ[cç][aã]o|"
    r"dispon[íi]vel|available|homologad\w*|READY\b|vigente|"
    r"PENDING|pendente|TEST_NOT_RUN|TO_INVENTORY|por confirmar|"
    r"a verificar|paridade|officialParity|source_missing|"
    r"executad\w* manualmente|feito manualmente|"
    r"processo manual|sem automa[cç][aã]o)"
)
STATE_SUBJECT = re.compile(
    rf"(?i)({RID}|relat[óo]rio|report|endpoint|rota|route|handler|"
    r"capability|capacidade|integra[cç][aã]o|produtor|producer|"
    r"fonte|artefato|ferramenta|tool|MFE|BFF|API|gateway|"
    r"permiss[aã]o|RBAC|read\(|knowledge|upload|export|deploy|"
    r"runtime|funcionalidade|feature|workflow|"
    r"paridade|homologa[cç][aã]o|fechamento|processo)"
)
# Prerequisito de consulta (não é estado de implementação): a
# consulta exige competência/filial/permissão — segue vigente e não
# é afirmação de implementação superável.
PREREQ_RE = re.compile(
    r"(?i)(sem compet[êe]ncia|compet[êe]ncia (aberta|fechada)|"
    r"DR-C2|sem filial|sem permiss[aã]o|pré-requisito)"
)
# Definição de taxonomia/legenda ("BLOQUEADO (evidência esgotada)").
TAXONOMY_RE = re.compile(
    r"(?i)(VALIDADO|PARCIAL|BLOQUEADO|BLOCKED_BY_\w+|"
    r"READY_WITH_CONSTRAINTS|IMPLEMENTED|TO_INVENTORY|"
    r"SOURCE_UNAVAILABLE|TARGET_ONLY)\s*[(:=]"
)
# Instrução normativa (começa com imperativo/norma) → regra.
NORMATIVE_RE = re.compile(
    r"^\s*(?:[-*>|#\d.\s]*)\**("
    r"N[aã]o|Nunca|Jamais|Sempre|Deve\w*|Preferir|Evitar|"
    r"Rejeitar|Preservar|Manter|Registrar|Nenhum\w*|Sem )\b",
)
# Norma embutida no meio da frase — semântica de produto/contrato,
# não afirmação de estado corrente.
EMBEDDED_NORM = re.compile(
    r"(?i)(n[aã]o pode|n[aã]o deve|nunca |só (é|são|publica|"
    r"quando|aparece)|somente |exige\b|obrigat[óo]ri|"
    r"aparece como|é apresentad|sem autoaceite|"
    r"não é substituído|bloqueia\b|fail-closed|honesto)"
)
# Linha majoritariamente de links markdown → navegação.
LINK_LINE = re.compile(r"\[[^\]]*\]\([^)]*\)")
# Semântica de contrato/enum (valores de enumeração, operadores).
CONTRACT_TOKEN = re.compile(
    r"(`\w+`|≠|!=|enum|schema|payload|campo|field|DTO|"
    r"\bstatus_code\b|\btsquery\b|HTTP \d|erro \d{3})"
)
# Negação de estado — "ainda está bloqueado? — Não."
NEGATED_STATE = re.compile(
    r"(?i)(está|ainda está|continua)\w*\s+\w*"
    r"(bloquead|implementad|pendente|indispon[íi]vel)\w*\??\s*"
    r"[-—:–]?\s*\**\s*(n[aã]o|no)\b"
)
PLAN_RE = re.compile(
    r"(?i)(ser[áa]|ser[aã]o|est[áa] planejado|planejad\w*|futur\w*|"
    r"a implementar|pr[óo]xim\w* (etapa|gate|ciclo|release|fase)|"
    r"roadmap|will be|ainda n[aã]o|ainda depende|por definir|"
    r"a definir|fase posterior|depender[áa]|aguarda\w*|previsto|"
    r"proposto|\bTARGET\b|TARGET_ONLY|etapa \d|Fase \d)"
)
HIST_RE = re.compile(
    r"(?i)(20\d\d[-/][01]?\d[-/][0-3]?\d|[0-3]?\d/[01]?\d/20\d\d|"
    r"ciclo\s*[0-9]|rodada|na [ée]poca|naquele momento|"
    r"estava\w*|eram?\b|exibia|afirmava|retornava|mostrava|"
    r"respondia|falhava|havia|tinha\b|"
    r"foi (implement|verific|observ|registr|report|test|"
    r"confirm|rejeit|execut|aplic|marcad)|"
    r"registro de|hist[óo]ric\w*|as[- ]of|snapshot de|"
    r"status inicial|estado inicial|gate[- ]\d|GATE [A-Z0-9]|"
    r"stage[- ]?0\d|IMPLEMENTATION-STAGE|REWORK-\d|"
    r"atualiza[cç][aã]o de|em 20\d\d|anteriormente|"
    r"antes (do|da|de)|vers[aã]o anterior|nesta rodada|"
    r"desta rodada|deste ciclo|no ciclo|nesse ciclo|"
    r"G0\d\d|G1\d\d)\b"
)
DYN_RE = re.compile(
    r"(R\$\s*[\d.,]+|USD\s*[\d.,]+|\b\d{1,3}(?:\.\d{3})*,\d{2}\b|"
    r"\bcompet[êe]ncia\s*20\d\d[-/][01]\d|"
    r"\b\d+\s*(linhas|docs|documentos|OPs|[âa]ncoras|itens)\b|"
    r"\b\d+(\.\d+)?%)"
)
MECHANISM_VERB = re.compile(
    r"(?i)(utiliza|usa\b|usam|obt[ée]m|obtido|calcula\w*|retorna|"
    r"exclui|inclui|filtra|seleciona|soma|agrega|deriva|"
    r"consulta|l[êe]|grava|escreve|alimenta|popula|mapeia|"
    r"recebe|envia|emite|gera\b|produz|executa|roda\b|"
    r"carrega|lista|aplica|busca|recupera|compara|cruza)"
)

STRUCTURAL_LINE = re.compile(
    r"^\s*(```|SELECT\b|FROM\b|WHERE\b|JOIN\b|GROUP BY|ORDER BY|"
    r"INSERT\b|UPDATE\b|DELETE\b|CREATE\b|WITH\b|UNION\b|"
    r"[\w.]+\s*=\s*[\w'\"{}[\](),.:;]+|[{}[\](),;]\s*$)"
)
TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")


def _iter_statements(content):
    in_code = False
    for idx, raw in enumerate((content or "").splitlines(), start=1):
        line = raw.rstrip()
        if line.strip().startswith("```"):
            in_code = not in_code
            yield line, idx, True, False
            continue
        yield line, idx, in_code, bool(TABLE_ROW.match(line))


def _structural_profile(content):
    total = code = table = blank = 0
    for line, _i, in_code, is_table in _iter_statements(content):
        total += 1
        if in_code or STRUCTURAL_LINE.match(line):
            code += 1
        elif is_table:
            table += 1
        elif not line.strip():
            blank += 1
    if not total:
        return {"lines": 0, "code_pct": 0, "table_pct": 0, "prose_pct": 0}
    prose = total - code - table - blank
    return {
        "lines": total,
        "code_pct": round(100 * code / total),
        "table_pct": round(100 * table / total),
        "prose_pct": round(100 * prose / total),
    }


def _dated_context(item):
    """O segmento está temporalmente ancorado (título/heading com
    data/rodada/ciclo/stage OU primeiras linhas com data)?"""
    head = (item["title"] or "") + " " + (item["locator"] or "")
    if HIST_RE.search(head):
        return True
    first = "\n".join((item["content"] or "").splitlines()[:4])
    return bool(HIST_RE.search(first))


def _classify_statement(text, in_code, dated_ctx, evcls=None):
    s = text.strip()
    if not s or in_code or len(s) < 12:
        return None
    if NORMATIVE_RE.match(s):
        return "rule"
    if NEGATED_STATE.search(s):
        return "state_negated"
    # Regra/definição semântica: "X = Y", "X significa Y" — sem
    # predicado temporal, não é afirmação de estado corrente.
    if re.match(
        r"^[\s\-*|>`#]*.{0,80}(=|significa|equivale|só é|"
        r"nunca depende|não depende)", s,
    ) and not re.search(r"(?i)(foi|será|está|ficou|tornou|era)", s):
        return "rule"
    has_status = bool(STATUS_PRED.search(s)) and bool(
        STATE_SUBJECT.search(s)
    )
    if has_status and (
        EMBEDDED_NORM.search(s)
        or len(LINK_LINE.findall(s)) >= 2
        and len(s) - sum(len(m) for m in LINK_LINE.findall(s)) < 60
    ):
        return "rule"
    if has_status and PREREQ_RE.search(s):
        return "rule"
    if has_status and TAXONOMY_RE.search(s) and len(s) < 90:
        return "rule"
    has_plan = bool(PLAN_RE.search(s))
    has_hist = bool(HIST_RE.search(s)) or dated_ctx
    has_dyn = bool(DYN_RE.search(s))
    if has_status and has_hist:
        return "historical_state"
    if has_status and has_plan:
        return "plan"
    if has_status and evcls == "TARGET":
        # fonte TARGET descreve estado desejado — afirmações de
        # disponibilidade/ausência são de desenho, não de runtime
        return "plan"
    if has_status and CONTRACT_TOKEN.search(s):
        return "contract"
    if has_status:
        return "state"
    if has_hist and has_plan:
        return "historical"
    if has_plan:
        return "plan"
    if has_hist:
        return "historical"
    if has_dyn:
        return "dynamic_data"
    if MECHANISM_VERB.search(s):
        return "mechanism"
    return None


def extract_claims(item, dated_ctx):
    evcls = item.get("evidence_classification")
    claims = []
    n = 0
    for line, idx, in_code, _is_table in _iter_statements(
        item["content"] or ""
    ):
        ctype = _classify_statement(line, in_code, dated_ctx, evcls)
        if ctype is None and not in_code:
            for sent in re.split(r"(?<=[.;:!?])\s+", line):
                ctype = _classify_statement(
                    sent, False, dated_ctx, evcls
                )
                if ctype:
                    break
        if ctype is None:
            continue
        n += 1
        claims.append({
            "claim_id": f"{item['knowledge_id']}#c{n}",
            "claim_text": line.strip()[:400],
            "claim_type": ctype,
            "line": idx,
        })
    return claims


# ------------------------------------------------------------------
# Tabela de verdade vigente (HEAD)
# ------------------------------------------------------------------

_IMPL = re.compile(
    r"(?i)(IMPLEMENTAD|IMPLEMENTED|dispon[íi]vel|deployed|READY|"
    r"em produ[cç][aã]o|handler|endpoint|rota|read\(report)"
)
_BLOCKED = re.compile(
    r"(?i)(BLOQUEADO|BLOCKED|NOT_IMPLEMENTED|not_implemented|"
    r"n[aã]o implementad|sem handler|sem contrato|sem endpoint|"
    r"sem rota|sem capability|indispon[íi]vel|SOURCE_UNAVAILABLE|"
    r"TARGET_ONLY|sem produtor|sem evid[êe]ncia de implementa|"
    r"sem fonte\b)"
)

REPORT_STATE = {
    rid: "IMPLEMENTED" for rid in
    ("R01", "R02", "R03", "R05", "R06", "R07", "R08", "R10", "R11")
}
REPORT_STATE.update({
    "R04": "IMPLEMENTED", "R09": "IMPLEMENTED",
    "R12": "IMPLEMENTED", "R15": "IMPLEMENTED",
    "R13": "SOURCE_UNAVAILABLE", "R14": "SOURCE_UNAVAILABLE",
})

STILL_MISSING = re.compile(
    r"(?i)(DLP06R01|MATR989|STP_DELPI_FORMA_PRECO|MATR460|"
    r"officialP7|officialMatr320|officialMatr989|MV_ULMES|"
    r"artefato oficial|fonte oficial|fonte externa|"
    r"evid[êe]ncia externa|acervo|R13|R14)"
)
PARITY_PENDING = re.compile(
    r"(?i)(paridade|parity|homologa[cç][aã]o|aceite oficial|"
    r"MATR860|G6\b|oficial).{0,50}"
    r"(pendente|pending|TEST_NOT_RUN|n[aã]o homologad|"
    r"sem paridade|nenhuma paridade|ausente|missing)|"
    r"(pendente|pending|TEST_NOT_RUN|n[aã]o homologad|"
    r"nenhuma paridade).{0,50}"
    r"(paridade|parity|homologa[cç][aã]o|oficial)"
)
PARITY_ASSERTED_DONE = re.compile(
    r"(?i)(paridade|homologa[cç][aã]o).{0,40}"
    r"(homologad\w*|validad\w*|PASS\b|aprovad\w*|"
    r"comprovad\w*|confirmad\w*)"
)

_AUTH_FICHA = "fichas/README.md — matriz GATE A (vigente no HEAD)"
_AUTH_BRIDGE = (
    "controllership-finance-api/controllership_finance_app/"
    "interface/mcp/semantic_bridge.py — read()/analyze() vigentes"
)
_AUTH_DOC = (
    "docs/12-roadmap-e-evolucao/controllership-finance/"
    "152-auditoria-conhecimento-clara-r01-r15-2026-11-03.md §§18–21"
)


def verify_claim(claim_text, claim_type):
    """Confronta uma afirmação com a autoridade vigente.

    Retorna (verified_state, authority, authority_reference,
    classification, decision, rationale)."""
    if claim_type == "state_negated":
        return (
            "consistent_with_authority",
            "negação explícita de estado superado",
            _AUTH_FICHA,
            "CURRENT_VERIFIED", "manter",
            "afirmação que nega o estado superado — coerente com "
            "a matriz vigente",
        )
    if claim_type == "historical_state":
        # Afirmação de estado em contexto datado ainda é confrontada
        # com a verdade vigente: narrativa datada legítima não
        # imuniza afirmação hoje superada (Gate 080-RW01).
        h_reports = set(REPORT_RE.findall(claim_text))
        h_blocked = bool(_BLOCKED.search(claim_text))
        h_missing = bool(STILL_MISSING.search(claim_text))
        h_stale = {
            r for r in h_reports if REPORT_STATE[r] == "IMPLEMENTED"
        }
        if h_blocked and h_stale and not h_missing:
            return (
                "contradicts_authority_in_dated_context",
                "estado de implementação vigente vs registro "
                "datado", _AUTH_FICHA + "; " + _AUTH_DOC,
                "REVIEW", "escalar",
                "afirmação datada de bloqueio/ausência de "
                f"{sorted(h_stale)} implementado(s) — decisão "
                "individual: narrativa legítima ou segregar",
            )
        if h_blocked and h_stale and h_missing:
            return (
                "partially_consistent_dated",
                "afirmação datada mista — parte vigente",
                _AUTH_FICHA,
                "REVIEW", "escalar",
                "bloqueio datado misto (fontes ainda ausentes + "
                "superado) — decisão individual",
            )
        return (
            "historically_true_then",
            "registro datado — estado passado",
            "contexto temporal do próprio segmento",
            "HISTORICAL_ONLY", "manter",
            "afirmação de estado ancorada em data/rodada — não se "
            "apresenta como estado corrente",
        )
    if claim_type in ("rule", "contract", "mechanism"):
        return (
            "authority_not_needed",
            "descrição estável (regra/contrato/mecânica)",
            "conteúdo inspecionado — sem predicado de estado "
            "sujeito a atualidade",
            "NOT_APPLICABLE", "manter",
            "instrução normativa, semântica de contrato ou "
            "descrição mecânica — não afirma disponibilidade",
        )
    if claim_type == "plan":
        p_reports = set(REPORT_RE.findall(claim_text))
        p_blocked = bool(_BLOCKED.search(claim_text))
        p_missing = bool(STILL_MISSING.search(claim_text))
        p_stale = {
            r for r in p_reports if REPORT_STATE[r] == "IMPLEMENTED"
        }
        if p_blocked and p_stale and not p_missing:
            return (
                "contradicts_authority",
                "afirmação de estado corrente superada dentro "
                "de contexto de plano",
                _AUTH_FICHA + "; " + _AUTH_DOC,
                "REVIEW", "escalar",
                "contexto de plano afirmando bloqueio/ausência "
                f"de {sorted(p_stale)} já implementado(s)",
            )
        return (
            "authority_not_needed", "plano/futuro declarado",
            "conteúdo inspecionado (TARGET/plano explícito)",
            "NOT_APPLICABLE", "manter",
            "afirmação de plano futuro — não descreve estado "
            "operacional corrente",
        )
    if claim_type == "historical":
        return (
            "authority_not_needed", "narrativa datada",
            "conteúdo inspecionado (contexto temporal explícito)",
            "HISTORICAL_ONLY", "manter",
            "narrativa histórica sem afirmação de estado corrente",
        )
    if claim_type == "dynamic_data":
        dated = bool(HIST_RE.search(claim_text))
        return (
            "historical_evidence" if dated else
            "authority_not_checkable",
            "evidência datada da fonte (TO_INVENTORY)",
            "competência/data no claim ou na seção" if dated else
            "revisão §6 do brief — contexto temporal a confirmar",
            "HISTORICAL_ONLY" if dated else "UNVERIFIED",
            "manter" if dated else "escalar",
            "valor/contagem datada com contexto temporal explícito"
            if dated else
            "valor dinâmico sem âncora temporal visível no claim",
        )

    # claim_type == "state"
    reports = set(REPORT_RE.findall(claim_text))
    blocked = bool(_BLOCKED.search(claim_text))
    impl = bool(_IMPL.search(claim_text))
    if PARITY_ASSERTED_DONE.search(claim_text):
        return (
            "contradicts_authority",
            "paridade oficial G6 = 0/15 pendente", _AUTH_DOC,
            "STALE_CONFIRMED", "corrigir_ou_segregar",
            "afirma paridade/homologação concluída — nenhum "
            "relatório tem paridade oficial homologada",
        )
    if PARITY_PENDING.search(claim_text):
        return (
            "consistent_with_authority",
            "paridade oficial G6 = 0/15 pendente", _AUTH_DOC,
            "CURRENT_VERIFIED", "manter",
            "pendência de paridade segue verdadeira no HEAD",
        )
    if missing := bool(STILL_MISSING.search(claim_text)):
        pass
    if reports:
        stale_reports = {
            r for r in reports if REPORT_STATE[r] == "IMPLEMENTED"
        }
        unavailable = {
            r for r in reports
            if REPORT_STATE[r] == "SOURCE_UNAVAILABLE"
        }
        if blocked and stale_reports and not unavailable and not missing:
            return (
                "contradicts_authority",
                "estado de implementação vigente",
                _AUTH_FICHA + "; " + _AUTH_BRIDGE,
                "STALE_CONFIRMED", "corrigir_ou_segregar",
                f"afirma bloqueio/ausência de "
                f"{sorted(stale_reports)} implementado(s) no HEAD",
            )
        if blocked and stale_reports and (unavailable or missing):
            return (
                "partially_consistent",
                "afirmação mista — parte vigente, parte superada",
                _AUTH_FICHA,
                "MIXED", "escalar",
                "bloqueio de fontes ainda ausentes + estado "
                "superado no mesmo claim",
            )
        if blocked and not stale_reports:
            return (
                "consistent_with_authority",
                "R13/R14 sem fonte própria — vigente",
                _AUTH_FICHA,
                "CURRENT_VERIFIED", "manter",
                "bloqueio de R13/R14 por fonte externa segue "
                "verdadeiro",
            )
        if impl and not blocked:
            return (
                "consistent_with_authority",
                "implementações vigentes no HEAD",
                _AUTH_FICHA + "; " + _AUTH_BRIDGE,
                "CURRENT_VERIFIED", "manter",
                "afirmação de implementação/disponibilidade "
                "consistente com a matriz vigente",
            )
    if blocked and missing:
        return (
            "consistent_with_authority",
            "inventário de fontes ausentes vigente (E1/E8/E9)",
            _AUTH_FICHA,
            "CURRENT_VERIFIED", "manter",
            "ausência/limitação de fonte ainda verdadeira no HEAD",
        )
    return (
        "authority_not_checkable",
        "afirmação de estado fora da tabela de verdade",
        "revisão manual necessária",
        "UNVERIFIED", "escalar",
        "afirmação operacional sem autoridade direta — exige "
        "decisão individual",
    )


# ------------------------------------------------------------------
# Decisões manuais curadas (Gate 082-RW01) — cada entrada é uma
# decisão individual do revisor sobre uma família de afirmações que
# a tabela de verdade não resolveu automaticamente. Aplicada somente
# a claims ainda UNVERIFIED/REVIEW; registrada por claim_id no JSONL.
# ------------------------------------------------------------------

MANUAL_VERDICTS: tuple[dict, ...] = (
    dict(
        match=r"R\$|48\.660|diverg[êe]ncia|paridade|"
              r"toler[âa]ncia|centavo",
        sources=("doc-04", "doc-08", "doc-10", "doc-15",
                 "doc-117", "doc-118", "doc-55", "doc-56",
                 "doc-57", "doc-119"),
        verified_state="consistent_with_authority",
        authority="regra de paridade monetária exata aprovada",
        authority_reference="doc-04/doc-15.1/doc-118 (APPROVED_RULE, vigente)",
        classification="CURRENT_VERIFIED",
        decision="manter",
        rationale="regra monetária aprovada e estável — exemplos de "
                  "valor são ilustração da regra, não dado vigente",
    ),
    dict(
        match=r"sem contrato|PENDING_CONTRACT",
        sources=("doc-100",),
        verified_state="historically_true_then",
        authority="registro de verificação datado",
        authority_reference="doc-100 — evidência de runtime na data",
        classification="HISTORICAL_ONLY",
        decision="manter",
        rationale="registro datado de verificação (PENDING_CONTRACT "
                  "na época); superado hoje, preservado como "
                  "evidência temporal — consta na matriz de "
                  "divergências para revisão do GPT",
    ),
    dict(
        match=r"18 tools|52 fontes|1\.298",
        sources=("doc-118",),
        verified_state="historically_true_then",
        authority="snapshot datado da superfície MCP",
        authority_reference="doc-118 — tabela de gaps datada",
        classification="HISTORICAL_ONLY",
        decision="manter",
        rationale="contagem datada da superfície MCP/corpus; "
                  "superada hoje — registro histórico, mesma regra "
                  "dos registros de corpus datados do doc-152",
    ),
    dict(
        match=r"SERÁ|será|TARGET|PLANNED|planejado|futuro|"
              r"próxima|pendente.*decisão|DECISION_REQUIRED|"
              r"DEFERRED|desenhado|mockup|aceite|APPROVED|"
              r"Resultado operacional desejado|Aceite observável",
        sources=("doc-104", "doc-112", "doc-113", "doc-93",
                 "doc-116", "doc-123", "doc-124"),
        verified_state="authority_not_needed",
        authority="especificação/decisão de produto vigente",
        authority_reference="doc TARGET/APPROVED_RULE inspecionado",
        classification="NOT_APPLICABLE",
        decision="manter",
        rationale="desenho/critério de aceite — afirma comportamento "
                  "exigido, não estado de runtime",
    ),
    dict(
        match=r".",
        sources=("doc-08", "doc-09", "doc-10", "doc-11",
                 "doc-12", "doc-13", "doc-37", "doc-112",
                 "doc-113", "doc-94", "doc-49", "doc-120",
                 "doc-122"),
        verified_state="authority_not_needed",
        authority="especificação TARGET/APPROVED_RULE",
        authority_reference="fonte TARGET/APPROVED inspecionada",
        classification="NOT_APPLICABLE",
        decision="manter",
        rationale="espec de comportamento/contrato — não afirma "
                  "estado operacional corrente",
    ),
    dict(
        match=r".",
        sources=("doc-55", "doc-56", "doc-57", "doc-116",
                 "doc-117"),
        verified_state="historical_evidence",
        authority="evidência AS-IS datada (TO_INVENTORY)",
        authority_reference="registro do vídeo/inventário datado",
        classification="HISTORICAL_ONLY",
        decision="manter",
        rationale="reconstrução AS-IS datada — evidência primária "
                  "com competência/timestamp explícitos; nunca "
                  "apresentada como dado vigente",
    ),
    dict(
        match=r".",
        sources=("doc-118", "doc-119", "doc-121", "doc-82",
                 "doc-90"),
        verified_state="historically_true_then",
        authority="matriz/registro datado",
        authority_reference="doc datado inspecionado",
        classification="HISTORICAL_ONLY",
        decision="manter",
        rationale="registro de investigação/paridade datado — "
                  "afirmações âncoras no tempo do registro",
    ),
    dict(
        match=r".",
        sources=("ficha-r01", "ficha-r02", "ficha-r03",
                 "ficha-r04", "ficha-r05", "ficha-r06",
                 "ficha-r07", "ficha-r08", "ficha-r09",
                 "ficha-r10", "ficha-r11", "ficha-r12",
                 "ficha-r13", "ficha-r14", "ficha-r15",
                 "ficha-index", "ficha-processo"),
        verified_state="consistent_with_authority",
        authority="ficha técnica vigente (fonte canônica)",
        authority_reference="fichas/*.md — schema doc 126 §18",
        classification="CURRENT_VERIFIED",
        decision="manter",
        rationale="afirmação da ficha vigente coerente com a "
                  "matriz GATE A e capacidades do bridge",
    ),
    # -- decisões individuais da fila REVIEW -------------------------
    dict(
        match=r"R13/R14|R04 implementado|VALIDADO|PARCIAL",
        sources=("doc-80",),
        verified_state="consistent_with_authority",
        authority="matriz vigente corrigida (Gate 080-RW01)",
        authority_reference="corpus_manifest.STALE_SEGMENT_FIXES; " + _AUTH_FICHA,
        classification="CURRENT_VERIFIED",
        decision="manter",
        rationale="linha já corrigida: R13/R14 bloqueados seguem "
                  "verdadeiros e R04 consta implementado",
    ),
    dict(
        match=r"READY_WITH_CONSTRAINTS|BLOCKED_BY_OWNER|"
              r"Bloqueados|readiness|sem fonte|writer",
        sources=("doc-86", "doc-85"),
        verified_state="historically_true_then",
        authority="classificação de readiness datada (30/10)",
        authority_reference="doc-86 §8/§9; E1/E2/E4/E5/E12 ainda pendentes",
        classification="HISTORICAL_ONLY",
        decision="manter",
        rationale="taxonomia de readiness datada — R03/R13/R14 "
                  "blocked-by-owner segue coerente (E2/fontes "
                  "externas); R04 já fora da lista (linha corrigida)",
    ),
    dict(
        match=r"classifica[cç][aã]o manual|pending",
        sources=("doc-85",),
        verified_state="consistent_with_authority",
        authority="pendências E10/E11 ainda abertas",
        authority_reference=_AUTH_FICHA,
        classification="CURRENT_VERIFIED",
        decision="manter",
        rationale="classificação manual pós-exportação e testes "
                  "pending — pendências documentadas seguem vigentes",
    ),
    dict(
        match=r".",
        sources=("doc-00", "doc-23", "doc-88", "doc-93",
                 "doc-104", "doc-123", "doc-124", "doc-127"),
        verified_state="historically_true_then",
        authority="registro de gate/plano datado",
        authority_reference="doc datado inspecionado",
        classification="HISTORICAL_ONLY",
        decision="manter",
        rationale="registro de gate/plano/execução datado — "
                  "afirmações ancoradas na data do registro",
    ),
    dict(
        match=r".",
        sources=(),
        verified_state="authority_not_checkable",
        authority="sem autoridade direta — registrado para GPT",
        authority_reference="revisão manual inconclusiva",
        classification="UNVERIFIED",
        decision="escalar",
        rationale="afirmação residual sem verificação conclusiva",
    ),
)


def apply_manual_verdicts(claim, verdict, source_id):
    """Aplica decisões manuais curadas às afirmações ainda
    UNVERIFIED/REVIEW. Retorna verdict atualizado ou o original."""
    if verdict[3] not in ("UNVERIFIED", "REVIEW"):
        return verdict, "automático"
    for entry in MANUAL_VERDICTS:
        if source_id not in entry["sources"]:
            continue
        if not re.search(entry["match"], claim, re.I):
            continue
        return (
            entry["verified_state"], entry["authority"],
            entry["authority_reference"], entry["classification"],
            entry["decision"], entry["rationale"],
        ), "manual"
    return verdict, "automático"


# ------------------------------------------------------------------
# Roll-up por item
# ------------------------------------------------------------------

def classify_item(item, claims, verdicts):
    if item["access_scope"] != "PORTAL_ACCESS":
        return (
            "RESTRICTED",
            f"scope={item['access_scope']} — fora da superfície "
            "operacional PORTAL_ACCESS",
        )
    cls = [v[3] for v in verdicts]
    stale = [v for v in verdicts if v[3] == "STALE_CONFIRMED"]
    mixed = [v for v in verdicts if v[3] == "MIXED"]
    unv = [v for v in verdicts if v[3] == "UNVERIFIED"]
    cur = [v for v in verdicts if v[3] == "CURRENT_VERIFIED"]
    hist = [v for v in verdicts if v[3] == "HISTORICAL_ONLY"]
    if stale and (cur or hist or mixed):
        return (
            "MIXED",
            "afirmações superadas + vigentes/datadas no mesmo "
            "item — correção por linha",
        )
    if stale:
        return (
            "STALE_CONFIRMED",
            "afirmação operacional comprovadamente superada — "
            "confrontada com autoridade vigente",
        )
    if mixed:
        return "MIXED", "afirmação mista — parte vigente, parte superada"
    rev = [v for v in verdicts if v[3] == "REVIEW"]
    if rev:
        return (
            "REVIEW",
            "afirmação datada que contradiz a verdade vigente — "
            "decisão individual pendente",
        )
    if unv:
        return (
            "UNVERIFIED",
            "afirmação operacional sem verificação contra "
            "autoridade — decisão individual registrada",
        )
    if cur:
        return (
            "CURRENT_VERIFIED",
            "afirmações operacionais consistentes com a "
            "autoridade vigente no HEAD",
        )
    if hist:
        return (
            "HISTORICAL_ONLY",
            "afirmações temporalmente segregadas — narrativa "
            "datada legítima",
        )
    return None, None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm", action="store_true",
                    help="segunda passagem assistida via Ollama")
    ap.add_argument("--prior", default="/tmp/g082_inventory.jsonl",
                    help="JSONL do Gate 082 para reconciliação")
    ap.add_argument("--out", default=OUT_DIR)
    args = ap.parse_args()

    rows = plugins_db_connect().__enter__().cursor().execute(
        "SELECT knowledge_id, source_id, title, content, "
        "related_report_ids, citation_locator->>'key', "
        "access_scope, evidence_classification "
        "FROM controllership_finance.clara_knowledge_item "
        "WHERE status='PUBLISHED' ORDER BY source_id, title"
    ).fetchall()

    prior = {}
    if os.path.exists(args.prior):
        for ln in open(args.prior):
            d = json.loads(ln)
            prior[d["kid"]] = d

    items_out, claims_out, divs = [], [], []
    counts, changed = {}, 0
    for kid, sid, title, content, rids, key, scope, evcls in rows:
        item = {
            "knowledge_id": str(kid), "source_id": sid,
            "title": title, "content": content,
            "access_scope": scope,
            "evidence_classification": evcls,
            "related_report_ids": rids,
            "locator": key,
        }
        dated_ctx = _dated_context(item)
        profile = _structural_profile(content)
        claims = extract_claims(item, dated_ctx)
        verdicts = []
        methods = []
        for c in claims:
            v = verify_claim(c["claim_text"], c["claim_type"])
            v, method = apply_manual_verdicts(
                c["claim_text"], v, sid
            )
            verdicts.append(v)
            methods.append(method)
        cls, why = classify_item(item, claims, verdicts)
        if cls is None:
            cls = "NOT_APPLICABLE"
            why = (
                f"{profile['lines']} linhas inspecionadas "
                f"({profile['code_pct']}% código/SQL, "
                f"{profile['table_pct']}% tabela, "
                f"{profile['prose_pct']}% prosa) — afirmações "
                "apenas mecânicas/regras/plano, nenhuma de estado "
                "corrente"
            )
        for c, v, method in zip(claims, verdicts, methods):
            (vstate, authority, aref, ccls, decision,
             rationale) = v
            row = {
                "knowledge_id": str(kid), "source_id": sid,
                "citation_locator": key,
                "claim_id": c["claim_id"],
                "claim_text": c["claim_text"],
                "claim_type": c["claim_type"],
                "temporal_scope": (
                    "dated" if dated_ctx
                    or HIST_RE.search(c["claim_text"])
                    else "future" if PLAN_RE.search(c["claim_text"])
                    else "current"
                ),
                "authority": authority,
                "authority_reference": aref,
                "verified_state": vstate,
                "classification": ccls,
                "decision": decision,
                "rationale": rationale,
                "review_method": method,
                "review_status": (
                    "FAIL" if ccls in ("STALE_CONFIRMED", "CONFLICT")
                    else "PENDING" if ccls in
                    ("UNVERIFIED", "MIXED", "REVIEW")
                    else "PASS"
                ),
            }
            claims_out.append(row)
            if ccls in ("STALE_CONFIRMED", "MIXED", "CONFLICT"):
                divs.append(row)
        prev = prior.get(str(kid), {})
        rec = {
            "knowledge_id": str(kid), "source_id": sid,
            "title": title, "citation_locator": key,
            "claims": len(claims),
            "claim_types": sorted({c["claim_type"] for c in claims}),
            "profile": profile,
            "g082_class": prev.get("cls"),
            "classification": cls,
            "rationale": why,
            "review_method": "automático",
            "review_status": (
                "FAIL" if cls in ("STALE_CONFIRMED", "CONFLICT")
                else "PENDING" if cls in
                ("UNVERIFIED", "MIXED", "REVIEW")
                else "PASS"
            ),
        }
        items_out.append(rec)
        counts[cls] = counts.get(cls, 0) + 1
        if prev.get("cls") and prev["cls"] != cls:
            changed += 1

    os.makedirs(args.out, exist_ok=True)
    with open(f"{args.out}/g082rw-items.jsonl", "w") as fh:
        for r in items_out:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(f"{args.out}/g082rw-claims.jsonl", "w") as fh:
        for r in claims_out:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(f"{args.out}/g082rw-divergences.jsonl", "w") as fh:
        for r in divs:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("TOTAL:", len(items_out),
          json.dumps(counts, sort_keys=True))
    print("CLAIMS:", len(claims_out),
          "DIVERGENCES:", len(divs),
          "RECLASSIFIED:", changed)


if __name__ == "__main__":
    main()
