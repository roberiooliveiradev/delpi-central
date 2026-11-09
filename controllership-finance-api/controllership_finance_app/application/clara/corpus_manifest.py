"""Manifest de fontes autorizadas do corpus CLARA (PROC-0072).

Cada entrada foi declarada explicitamente — o pipeline nunca varre o
repositório. A classificação de evidência reflete a proveniência real:

- OWNER_REPORTED_VIA_PO — observação/relato documentado (vídeo
  guiado, inventários e reconciliações escritos por responsáveis);
- APPROVED_RULE — decisão de produto aprovada (gates/GOs/decisões PO);
- TARGET — desenho/contrato desejado, não evidência de runtime;
- CURRENT_IMPLEMENTATION — evidência de execução do HEAD (doc 100);
- TO_INVENTORY — levantamento ainda não confirmado como oficial.
"""

from __future__ import annotations

from controllership_finance_app.application.clara.corpus_ingestion import (
    SourceSpec,
)

_D = "docs/12-roadmap-e-evolucao/controllership-finance"

ALL_RIDS = tuple(f"R{n:02d}" for n in range(1, 16))


def _s(
    source_id: str,
    filename: str,
    source_type: str,
    name: str,
    classification: str,
    topic: str,
    *,
    business_step: str | None = None,
    report_ids: tuple[str, ...] = (),
    authority: str = "OWNER",
    scope: str = "PORTAL_ACCESS",
) -> SourceSpec:
    return SourceSpec(
        source_id=source_id,
        path=f"{_D}/{filename}",
        source_type=source_type,
        name=name,
        origin_authority=authority,
        evidence_classification=classification,
        topic=topic,
        business_step=business_step,
        related_report_ids=report_ids,
        access_scope=scope,
    )


AUTHORIZED_SOURCES: list[SourceSpec] = [
    # -- Processo AS-IS e evidências do vídeo --------------------------
    _s("doc-02", "02-proc-0072-as-is-e-baseline.md", "DOCUMENT",
       "PROC-0072 AS-IS e baseline", "OWNER_REPORTED_VIA_PO",
       "processo-as-is"),
    _s("doc-54", "54-video-19-33-cross-report-business-rules.md",
       "VIDEO_OBSERVATION", "Regras de negócio cruzadas do vídeo",
       "OWNER_REPORTED_VIA_PO", "video-regras-negocio",
       report_ids=ALL_RIDS),
    _s("doc-55", "55-proc0072-matriz-conferencias-estoques-custos-asis.md",
       "MATRIX", "Matriz de conferências de estoques e custos (AS-IS)",
       "OWNER_REPORTED_VIA_PO", "conferencias-estoques-custos",
       business_step="P3"),
    _s("doc-56", "56-proc0072-observacoes-guiadas-fechamento-custos.md",
       "VIDEO_OBSERVATION", "Observações guiadas do vídeo de fechamento",
       "OWNER_REPORTED_VIA_PO", "video-observacoes-guiadas"),
    _s("doc-57",
       "57-proc0072-matriz-mestra-revalidacao-video-e-roadmap-inventarios.md",
       "MATRIX", "Matriz-mestra de revalidação do vídeo",
       "OWNER_REPORTED_VIA_PO", "video-matriz-rastreabilidade"),
    # -- Inventários ciclo 1 (planilhas/relatórios R01–R15) ------------
    _s("doc-59", "59-ciclo1-checklist-abas-e-entregaveis-sanitizado.md",
       "MATRIX", "Checklist mensal — abas e entregáveis",
       "OWNER_REPORTED_VIA_PO", "checklist-mensal",
       business_step="P2"),
    _s("doc-60", "60-ciclo1-rotinas-contabeis-fiscais-totvs.md",
       "INVENTORY", "Rotinas contábeis/fiscais TOTVS observadas",
       "OWNER_REPORTED_VIA_PO", "rotinas-totvs"),
    _s("doc-61", "61-ciclo1-cpv-kardex-matriz-inventario.md",
       "REPORT_SAMPLE", "CPV/Kardex — matriz de inventário",
       "TO_INVENTORY", "relatorio-cpv-kardex", report_ids=("R06",)),
    _s("doc-62", "62-ciclo1-matr320-resumo-entradas-saidas.md",
       "REPORT_SAMPLE", "MATR320 — resumo de entradas e saídas",
       "TO_INVENTORY", "relatorio-matr320", report_ids=("R05",)),
    _s("doc-63", "63-ciclo1-p7-resumo-estoque-em-processo.md",
       "REPORT_SAMPLE", "P7 — resumo de estoque em processo",
       "TO_INVENTORY", "estoque-em-processo", report_ids=("R03",)),
    _s("doc-66", "66-ciclo1-invent-movimentos-inventario.md",
       "REPORT_SAMPLE", "Movimentos de inventário",
       "TO_INVENTORY", "movimentos-inventario",
       report_ids=("R07",)),
    _s("doc-64", "64-ciclo1-material-em-processo-inventario.md",
       "REPORT_SAMPLE", "Material em processo — inventário",
       "TO_INVENTORY", "estoque-em-processo"),
    _s("doc-65", "65-ciclo1-faturamento-mod-inventario.md",
       "REPORT_SAMPLE", "Faturamento MOD — inventário",
       "TO_INVENTORY", "faturamento-mod"),
    _s("doc-67", "67-ciclo1-nf-a-desconsiderar-sd2.md",
       "REPORT_SAMPLE", "Notas fiscais a desconsiderar (SD2)",
       "TO_INVENTORY", "nf-desconsiderar"),
    _s("doc-68", "68-ciclo1-resumo-estoque-variante-reduzida.md",
       "REPORT_SAMPLE", "Resumo de estoque variante reduzida",
       "TO_INVENTORY", "resumo-estoque"),
    _s("doc-69", "69-ciclo1-contas-a-pagar-posicao-titulos.md",
       "REPORT_SAMPLE", "Contas a pagar — posição de títulos",
       "TO_INVENTORY", "contas-a-pagar", report_ids=("R01",)),
    _s("doc-70", "70-ciclo1-contas-a-receber-posicao-titulos.md",
       "REPORT_SAMPLE", "Contas a receber — posição de títulos",
       "TO_INVENTORY", "contas-a-receber", report_ids=("R02",)),
    _s("doc-71", "71-ciclo1-pagos-por-data.md", "REPORT_SAMPLE",
       "Pagos por data", "TO_INVENTORY", "pagos-por-data"),
    _s("doc-72", "72-ciclo1-pagos-por-natureza.md", "REPORT_SAMPLE",
       "Pagos por natureza", "TO_INVENTORY", "pagos-por-natureza"),
    _s("doc-73", "73-ciclo1-pagos-0926-relacao-baixas.md",
       "REPORT_SAMPLE", "Relação de baixas pagas",
       "TO_INVENTORY", "baixas-pagas"),
    _s("doc-74", "74-ciclo1-recebidos-por-data.md", "REPORT_SAMPLE",
       "Recebidos por data", "TO_INVENTORY", "recebidos-por-data"),
    _s("doc-75", "75-ciclo1-recebidos-relacao-baixas.md",
       "REPORT_SAMPLE", "Relação de baixas recebidas",
       "TO_INVENTORY", "baixas-recebidas"),
    _s("doc-76", "76-ciclo1-fechamento-documental.md", "MATRIX",
       "Fechamento documental — matriz", "OWNER_REPORTED_VIA_PO",
       "fechamento-documental"),
    _s("doc-77", "77-ciclo1-reconciliacao-cc-matriz-analise.md",
       "MATRIX", "Reconciliação centro de custo — análise",
       "OWNER_REPORTED_VIA_PO", "reconciliacao-cc",
       business_step="P3"),
    _s("doc-78", "78-ciclo1-crosswalk-narracao-artefatos.md",
       "MATRIX", "Crosswalk narração do vídeo ↔ artefatos",
       "OWNER_REPORTED_VIA_PO", "video-crosswalk"),
    _s("doc-79", "79-ciclo1-aceite-formal-po.md", "DOCUMENT",
       "Aceite formal PO ciclo 1", "APPROVED_RULE",
       "aceites-decisoes"),
    _s("doc-80", "80-ciclo2-registro-vivo-investigacao-devin.md",
       "INVENTORY", "Registro vivo da investigação (ciclo 2)",
       "TO_INVENTORY", "investigacao"),
    _s("doc-81", "81-decisao-e6-historico-monetario-mod-opcao-c.md",
       "DOCUMENT", "Decisão E6 — histórico monetário MOD",
       "APPROVED_RULE", "aceites-decisoes"),
    _s("doc-82", "82-ciclo2-handoff-pacote-evidencias-owners.md",
       "INVENTORY", "Handoff — pacote de evidências owners",
       "TO_INVENTORY", "evidencias-owners"),
    _s("doc-83", "83-ciclo2-crosswalk-evidencias-r01-r15.md",
       "MATRIX", "Crosswalk evidências R01–R15",
       "OWNER_REPORTED_VIA_PO", "relatorios-r01-r15",
       report_ids=ALL_RIDS),
    _s("doc-84", "84-ciclo2-paridade-monetaria-relatorios-oficiais.md",
       "MATRIX", "Paridade monetária com relatórios oficiais",
       "OWNER_REPORTED_VIA_PO", "paridade-monetaria",
       business_step="P3", report_ids=ALL_RIDS),
    _s("doc-85", "85-ciclo2-catalogo-regras-negocio-r01-r15.md",
       "MATRIX", "Catálogo de regras de negócio R01–R15",
       "OWNER_REPORTED_VIA_PO", "relatorios-r01-r15",
       report_ids=ALL_RIDS),
    _s("doc-86", "86-ciclo2-relatorio-final-consolidado-e-handoff.md",
       "DOCUMENT", "Relatório consolidado ciclo 2",
       "OWNER_REPORTED_VIA_PO", "consolidacao-evidencias"),
    _s("doc-88", "88-ciclo3-r01-inventario-contratos-e-pacote-decisoes.md",
       "INVENTORY", "R01 — inventário de contratos",
       "TO_INVENTORY", "relatorio-r01", report_ids=("R01",)),
    _s("doc-89", "89-ciclo3-decisoes-aprovadas-e-gate-documental-r02.md",
       "DOCUMENT", "Decisões aprovadas e gate documental",
       "APPROVED_RULE", "aceites-decisoes", report_ids=("R02",)),
    _s("doc-90",
       "90-ciclo3-crosswalk-end-to-end-proc0072-teo-rq-ac-portal.md",
       "MATRIX", "Crosswalk E2E PROC-0072 ↔ TÉO ↔ RQ/AC",
       "OWNER_REPORTED_VIA_PO", "rastreabilidade-processo"),
    # -- Regras, decisões e arquitetura (TARGET / aprovadas) -----------
    _s("doc-04", "04-regras-de-negocio-consolidadas.md", "DOCUMENT",
       "Regras de negócio consolidadas", "APPROVED_RULE",
       "regras-negocio"),
    _s("doc-08", "08-p1-cockpit-da-competencia.md", "DOCUMENT",
       "P1 — cockpit da competência", "TARGET", "p1-cockpit",
       business_step="P1"),
    _s("doc-09", "09-p2-checklist-e-documentos.md", "DOCUMENT",
       "P2 — checklist e documentos", "TARGET", "p2-checklist",
       business_step="P2"),
    _s("doc-10", "10-p3-estoque-cutoff-e-conciliacao.md", "DOCUMENT",
       "P3 — estoque, cutoff e conciliação", "TARGET",
       "p3-estoque-cutoff", business_step="P3"),
    _s("doc-11", "11-p4-classificacoes-e-pendencias.md", "DOCUMENT",
       "P4 — classificações e pendências", "TARGET",
       "p4-pendencias", business_step="P4"),
    _s("doc-12", "12-p5-pacote-finalizacao-e-envio.md", "DOCUMENT",
       "P5 — pacote, finalização e envio", "TARGET", "p5-pacotes",
       business_step="P5"),
    _s("doc-13", "13-p6-administracao-e-configuracao.md", "DOCUMENT",
       "P6 — administração e configuração", "TARGET", "p6-admin",
       business_step="P6"),
    _s("doc-14", "14-seguranca-rbac-auditoria-e-ia.md", "CONTRACT",
       "Segurança, RBAC, auditoria e IA", "APPROVED_RULE",
       "seguranca-rbac"),
    _s("doc-15", "15-requisitos-criterios-de-aceite-e-testes.md",
       "DOCUMENT", "Requisitos e critérios de aceite",
       "APPROVED_RULE", "requisitos-aceite"),
    _s("doc-23", "23-ledger-rq-ac-testes.md", "MATRIX",
       "Ledger RQ/AC e testes", "APPROVED_RULE",
       "rastreabilidade-processo"),
    _s("doc-37", "37-p5-submissao-e-revisao-no-portal.md", "DOCUMENT",
       "P5 — submissão e revisão no Portal", "APPROVED_RULE",
       "p5-pacotes", business_step="P5"),
    _s("doc-93",
       "93-roadmap-executivo-central-fechamento-end-to-end-checkpoints.md",
       "DOCUMENT", "Roadmap executivo e checkpoints",
       "APPROVED_RULE", "roadmap-checkpoints"),
    _s("doc-94", "94-clara-especialista-mcp-controladoria-financas.md",
       "CONTRACT", "CLARA — arquitetura e contrato MCP",
       "APPROVED_RULE", "clara-mcp"),
    _s("doc-100",
       "100-ciclo3-p6-min-p2-read-runtime-evidencia-de-execucao.md",
       "TEST_EVIDENCE", "Evidência de execução do runtime",
       "CURRENT_IMPLEMENTATION", "implementacao-runtime", scope="INTERNAL_ONLY"),
    _s("doc-104",
       "104-plano-mestre-execucao-e2e-fechamento-aceite-deploy.md",
       "DOCUMENT", "Plano mestre E2E e gates", "APPROVED_RULE",
       "plano-mestre-gates"),
    _s("doc-105",
       "105-go-conclusao-integral-pendencias-implementacao-antes-refinamento.md",
       "DOCUMENT", "GO de conclusão integral", "APPROVED_RULE",
       "aceites-decisoes"),
    # -- Plano canônico, decisões UX e evidência autenticada -----------
    _s("doc-111",
       "111-clara-chatgpt-smoke-autenticado-retomada-central-2026-10-26.md",
       "TEST_EVIDENCE", "Smoke autenticado CLARA/ChatGPT",
       "CURRENT_IMPLEMENTATION", "implementacao-runtime", scope="INTERNAL_ONLY"),
    _s("doc-112",
       "112-design-visual-fechamento-mensal-wireframes.md",
       "DOCUMENT", "Design do fechamento mensal, decisões e inventário",
       "APPROVED_RULE", "fluxo-fechamento-decisoes"),
    _s("doc-113",
       "113-plano-canonico-fluxo-fechamento-controladoria-dre-vigencia-documental.md",
       "DOCUMENT", "Plano canônico do fluxo de fechamento (PO GO)",
       "APPROVED_RULE", "fluxo-fechamento-decisoes"),
    _s("doc-00", "README.md",
       "DOCUMENT", "Navegação e estado do produto",
       "CURRENT_IMPLEMENTATION", "implementacao-runtime", scope="INTERNAL_ONLY"),
    # -- Contratos de relatórios e base canônica (CLARA-PARITY-014) ---
    _s("doc-49", "49-r03-p7-operational-stock-query-contract-target.md",
       "CONTRACT", "R03/P7 — contrato TARGET de consulta operacional",
       "TARGET", "relatorio-p7", report_ids=("R03",)),
    _s("doc-91",
       "91-ciclo3-contabilidade-acesso-documentos-historicos-gate.md",
       "DOCUMENT", "Gate — acesso da contabilidade a documentos",
       "APPROVED_RULE", "documentos-dre"),
    _s("doc-115",
       "115-dre-access-019-documentos-recebidos-gate-91-implementacao.md",
       "DOCUMENT", "DRE-ACCESS-019 — documentos recebidos (execução)",
       "CURRENT_IMPLEMENTATION", "documentos-dre"),
    _s("doc-116",
       "116-ciclo-inteligencia-fechamento-analyses-001-005.md",
       "INVENTORY", "Ciclo de inteligência do fechamento (analyses)",
       "TO_INVENTORY", "inteligencia-fechamento"),
    _s("doc-117",
       "117-analysis-001-inventario-processo-real-joyce.md",
       "INVENTORY", "Inventário do processo real de fechamento (AS-IS)",
       "TO_INVENTORY", "processo-as-is"),
    _s("doc-118",
       "118-base-canonica-processo-fechamento-mensal-proc0072.md",
       "DOCUMENT", "Base canônica do processo PROC-0072",
       "APPROVED_RULE", "processo-fechamento"),
    _s("doc-119",
       "119-contratos-p7-implementacao-readiness.md",
       "CONTRACT", "Contratos definitivos P7 — readiness",
       "APPROVED_RULE", "relatorio-p7", report_ids=("R03",)),
    _s("doc-120",
       "120-plano-integracao-relatorios-r06-r15-clara-2026-10-29.md",
       "DOCUMENT", "Plano de integração R06–R15 e CLARA",
       "TARGET", "roadmap-evolucao",
       report_ids=("R04", "R06", "R07", "R09", "R10", "R11", "R12",
                   "R13", "R14", "R15")),
    _s("doc-121",
       "121-clara-paridade-portal-matriz-cp-2026-10-29.md",
       "MATRIX", "Matriz de paridade CLARA × Portal",
       "CURRENT_IMPLEMENTATION", "paridade-portal-clara",
       report_ids=ALL_RIDS),
    _s("doc-122",
       "122-gate-contratual-r06-r07-matr910-2026-10-29.md",
       "CONTRACT", "Gate contratual R06/R07 (MATR910) — contratos TARGET",
       "TARGET", "relatorio-cpv-kardex", report_ids=("R06", "R07")),
    _s("doc-123",
       "119-clara-mcp-semantico-plano-mestre-execucao-deploy.md",
       "DOCUMENT", "Plano mestre CLARA MCP semântico (seis tools)",
       "CURRENT_IMPLEMENTATION", "paridade-portal-clara"),
    _s("doc-124",
       "CLARA-MCP-SEMANTIC-001-capability-matrix.md",
       "MATRIX", "Matriz de migração CLARA MCP semântico",
       "CURRENT_IMPLEMENTATION", "paridade-portal-clara"),
    _s("doc-125",
       "123-clara-mcp-semantico-001-execution-report.md",
       "DOCUMENT", "Execução CLARA MCP semântico — relatório",
       "CURRENT_IMPLEMENTATION", "paridade-portal-clara"),
    _s("doc-126",
       "124-clara-write-execution-risk-policy.md",
       "DOCUMENT", "CLARA — política de execução de escrita por risco",
       "CURRENT_IMPLEMENTATION", "paridade-portal-clara"),
    _s("doc-127",
       "125-clara-mcp-semantico-002-execution-report.md",
       "DOCUMENT", "Execução CLARA SEMANTIC-002 — relatório",
       "CURRENT_IMPLEMENTATION", "paridade-portal-clara"),
    _s("doc-156",
       "156-glossario-responsabilidades-destinatarios-proc0072-2026-11-09.md",
       "DOCUMENT",
       "Glossário de responsabilidades e destinatários PROC-0072 (PO 2026-11-09)",
       "APPROVED_RULE", "processo-fechamento",
       authority="PO"),
    # -- Fichas técnicas R01–R15 (stage-04, D-06 do doc 126) -----------
    _s("ficha-index", "fichas/README.md",
       "MATRIX", "Fichas R01–R15 — índice e matriz de inventário",
       "APPROVED_RULE", "relatorios-r01-r15", report_ids=ALL_RIDS),
    _s("ficha-processo", "fichas/processo-fechamento-ficha.md",
       "DOCUMENT", "PROC-0072 — ficha do processo de fechamento",
       "APPROVED_RULE", "processo-fechamento"),
    _s("ficha-r01", "fichas/R01-ficha.md",
       "DOCUMENT", "Ficha R01 — Baixas a pagar",
       "APPROVED_RULE", "relatorios-r01-r15", report_ids=("R01",)),
    _s("ficha-r02", "fichas/R02-ficha.md",
       "DOCUMENT", "Ficha R02 — Baixas a receber",
       "APPROVED_RULE", "relatorios-r01-r15", report_ids=("R02",)),
    _s("ficha-r03", "fichas/R03-ficha.md",
       "DOCUMENT", "Ficha R03 — P7 / Registro de Inventário",
       "APPROVED_RULE", "relatorios-r01-r15", report_ids=("R03",)),
    _s("ficha-r04", "fichas/R04-ficha.md",
       "DOCUMENT", "Ficha R04 — Consumo por OP (visão operacional)",
       "TO_INVENTORY", "relatorios-r01-r15", report_ids=("R04",)),
    _s("ficha-r05", "fichas/R05-ficha.md",
       "DOCUMENT", "Ficha R05 — Entradas e Saídas (MATR320)",
       "APPROVED_RULE", "relatorios-r01-r15", report_ids=("R05",)),
    _s("ficha-r06", "fichas/R06-ficha.md",
       "DOCUMENT", "Ficha R06 — Kardex / CPV (MATR910)",
       "APPROVED_RULE", "relatorios-r01-r15", report_ids=("R06",)),
    _s("ficha-r07", "fichas/R07-ficha.md",
       "DOCUMENT", "Ficha R07 — Inventários",
       "APPROVED_RULE", "relatorios-r01-r15", report_ids=("R07",)),
    _s("ficha-r08", "fichas/R08-ficha.md",
       "DOCUMENT", "Ficha R08 — Material em Processo (MATR989)",
       "APPROVED_RULE", "relatorios-r01-r15", report_ids=("R08",)),
    _s("ficha-r09", "fichas/R09-ficha.md",
       "DOCUMENT", "Ficha R09 — Faturamento × MOD (DLP204)",
       "TARGET", "relatorios-r01-r15", report_ids=("R09",)),
    _s("ficha-r10", "fichas/R10-ficha.md",
       "DOCUMENT", "Ficha R10 — Despesas por Centro de Custo",
       "APPROVED_RULE", "relatorios-r01-r15", report_ids=("R10",)),
    _s("ficha-r11", "fichas/R11-ficha.md",
       "DOCUMENT", "Ficha R11 — NF a Desconsiderar",
       "APPROVED_RULE", "relatorios-r01-r15", report_ids=("R11",)),
    _s("ficha-r12", "fichas/R12-ficha.md",
       "DOCUMENT", "Ficha R12 — Fechamento de custo / Refaz Saldos",
       "TARGET", "relatorios-r01-r15", report_ids=("R12",)),
    _s("ficha-r13", "fichas/R13-ficha.md",
       "DOCUMENT", "Ficha R13 — Extratos e aplicações (externa)",
       "TO_INVENTORY", "relatorios-r01-r15", report_ids=("R13",)),
    _s("ficha-r14", "fichas/R14-ficha.md",
       "DOCUMENT", "Ficha R14 — Importação / câmbio (evidência documental externa)",
       "TO_INVENTORY", "relatorios-r01-r15", report_ids=("R14",)),
    _s("ficha-r15", "fichas/R15-ficha.md",
       "DOCUMENT", "Ficha R15 — Cutoff / virada / SB9",
       "TARGET", "relatorios-r01-r15", report_ids=("R15",)),
]


# Gate 085 — corpus operacional enxuto, conforme decisão do PO.
# Documentos de projeto, timelines, testes e inventários permanecem
# armazenados para auditoria, mas não entram na recuperação da CLARA.
# As fichas são a superfície operacional candidata; seus rótulos
# TARGET/TO_INVENTORY continuam explícitos, sem fingir runtime provado.
OPERATIONAL_SOURCE_IDS = frozenset(
    {"ficha-index", "ficha-processo"}
    | {f"ficha-r{n:02d}" for n in range(1, 16)}
)


def _operational_scope_only(spec: SourceSpec) -> SourceSpec:
    if spec.source_id in OPERATIONAL_SOURCE_IDS:
        return spec
    return SourceSpec(
        source_id=spec.source_id,
        path=spec.path,
        source_type=spec.source_type,
        name=spec.name,
        origin_authority=spec.origin_authority,
        evidence_classification=spec.evidence_classification,
        topic=spec.topic,
        business_step=spec.business_step,
        related_report_ids=spec.related_report_ids,
        access_scope="INTERNAL_ONLY",
        description=spec.description,
    )


AUTHORIZED_SOURCES = [_operational_scope_only(spec) for spec in AUTHORIZED_SOURCES]
assert len(OPERATIONAL_SOURCE_IDS) == 17
assert {s.source_id for s in AUTHORIZED_SOURCES if s.access_scope == "PORTAL_ACCESS"} == OPERATIONAL_SOURCE_IDS


# Gate 080 (PO/decisão produto — issue #130): seleção DETERMINÍSTICA
# de fontes vigentes. Segmentos datados que afirmam um estado hoje
# superado NÃO podem ser expostos à CLARA:
#
#   action="drop" — o segmento inteiro é um registro datado superado;
#                 sai da ingestão (o item antigo vira SUPERSEDED pelo
#                 sweep por locator; GitHub/banco preservam o histórico).
#
#   action="fix"  — o segmento mistura afirmações vigentes e superadas;
#                 `fix_lines` reescreve apenas as linhas superadas e o
#                 conteúdo corrigido volta pelo mesmo citation_locator
#                 (versão antiga SUPERSEDED, trilha de auditoria íntegra).
#
# Critério: somente afirmações comprovadamente falsas hoje (R04/R09/
# R12/R15 implementados); estados ainda verdadeiros (ex.: R13/R14
# BLOQUEADO) NÃO são alterados nem removidos.
STALE_SEGMENT_FIXES: tuple[dict, ...] = (
    # ---------------- segmentos inteiramente superados ----------------
    dict(source_id="doc-83",
         title_contains="R04 — Consumo por OP — **BLOQUEADO",
         action="drop",
         reason="R04 implementado (consumption-audit) — ficha vigente"),
    dict(source_id="doc-85",
         title_contains="§4 — R04 · Consumo por OP — `BLOQUEADO`",
         action="drop",
         reason="R04 implementado (consumption-audit) — ficha vigente"),
    dict(source_id="doc-121",
         title_contains="Adendo — stage-04 (31/10/2026): conhecimento governado",
         action="drop",
         reason="matriz de capabilities datada — R04/R09/R12/R15 sem contrato superado"),
    dict(source_id="doc-23",
         title_contains="G054–G057 — R04/R06/R07 (2026-11-02) — status inicial",
         action="drop",
         reason="registro datado — produtores R04/R06/R07 implementados"),
    dict(source_id="doc-23",
         title_contains="R04-G059 — owner/contrato confirmados (2026-11-02)",
         action="drop",
         reason="registro datado — contrato BFF R04 implementado"),
    dict(source_id="doc-23",
         title_contains="IMPLEMENTATION-STAGE-04 — conhecimento especializado",
         action="drop",
         reason="registro datado — R04/R13/R14 bloqueados e R09/R12/R15 TARGET_ONLY superados"),

    # ---------------- segmentos mistos: só linhas superadas ----------------
    dict(source_id="doc-80",
         title_contains="27.C — Status por item",
         action="fix",
         fix_lines=[(
             "R04/R13/R14 BLOQUEADO (R04 sem artefato de consumo-OP; "
             "R13 externalidade confirmada por checklist; R14 sem evidência).",
             "R13/R14 BLOQUEADO (R13 externalidade confirmada por checklist; "
             "R14 sem evidência); R04 implementado como visão operacional "
             "(consumption-audit) — paridade MATR860 pendente.",
         )],
         reason="afirmação mista: R04 superado, R13/R14 vigentes"),
    dict(source_id="doc-80",
         title_contains="48.1 — Validação da matriz",
         action="fix",
         fix_lines=[(
             "- R04/R13/R14: bloqueados por owner — sem artefato/fonte",
             "- R13/R14: bloqueados por owner — sem fonte; R04 implementado "
             "(consumption-audit — paridade MATR860 pendente); busca residual",
         )],
         reason="afirmação mista: R04 superado, R13/R14 vigentes"),
    dict(source_id="doc-83",
         title_contains="§7 — Resultado por item",
         action="fix",
         fix_lines=[(
             "| R04 Consumo por OP | BLOQUEADO | — | — |",
             "| R04 Consumo por OP | IMPLEMENTADO (visão operacional — "
             "consumption-audit; paridade MATR860 pendente) | — | — |",
         )],
         reason="linha R04 superada em matriz com estados vigentes"),
    dict(source_id="doc-86",
         title_contains="8. Readiness — classificação do próximo ciclo",
         action="fix",
         fix_lines=[
             ("| R04 | `BLOCKED_BY_OWNER` | sem artefato/critério oficial |",
              "| R04 | `IMPLEMENTED` (visão operacional — consumption-audit) | "
              "paridade MATR860 pendente |"),
             ("11/15 itens `READY_WITH_CONSTRAINTS` (R01, R02, R05–R12 e R15) "
              "e 4/15 `BLOCKED_BY_OWNER` (R03, R04, R13 e R14)",
              "12/15 itens `READY_WITH_CONSTRAINTS` (R01, R02, R04–R12 e R15) "
              "e 3/15 `BLOCKED_BY_OWNER` (R03, R13 e R14)"),
         ],
         reason="linha/contagem R04 superadas em matriz vigente"),
    dict(source_id="doc-86",
         title_contains="Matriz canônica R01–R15",
         action="fix",
         fix_lines=[(
             "| R04 | Consumo por OP | `MATR860` (candidato) | sem artefato "
             "oficial | G1–G4 PENDING · G5 TEST_NOT_RUN | artefato/critério → "
             "Controladoria |",
             "| R04 | Consumo por OP | `consumption-audit` + `MATR860` "
             "(candidato) | implementado; sem artefato oficial MATR860 | "
             "paridade `PENDING` | paridade → Controladoria |",
         )],
         reason="linha R04 superada em matriz vigente"),
    dict(source_id="doc-113",
         title_contains="§29.22",
         action="fix",
         fix_lines=[(
             "R04, R13, R14 bloqueados por produtor/owner/fonte específica.",
             "R13, R14 bloqueados por fonte específica; R04 implementado "
             "posteriormente a este plano (consumption-audit — paridade "
             "MATR860 pendente).",
         )],
         reason="afirmação mista: R04 superado, R13/R14 vigentes"),
    dict(source_id="doc-118",
         title_contains="3. Matriz mestra de evidências",
         action="fix",
         fix_lines=[(
             "| EV-23 | `MATR860` é candidato a consumo por OP; nenhum "
             "artefato na pasta | doc 83 R04 | `TO_INVENTORY`/`BLOQUEADO` | "
             "GAP-01 |",
             "| EV-23 | `MATR860` é candidato a consumo por OP; consumo "
             "implementado via consumption-audit (artefato oficial MATR860 "
             "não localizado) | doc 83 R04, ficha R04 | `PROVEN` implementação "
             "/ paridade `PENDING` | GAP-01 parcial |",
         )],
         reason="linha EV-23 superada em matriz de evidências vigente"),
    dict(source_id="doc-118",
         title_contains="6. Catálogo canônico de relatórios e transformações",
         action="fix",
         fix_lines=[(
             "| R04 | Consumo por OP | `MATR860` candidato | — | — | ? | "
             "`BLOQUEADO` (sem artefato) | nenhum → GAP-01 |",
             "| R04 | Consumo por OP | `consumption-audit` (api-delpi — "
             "SD4/SD3/SC2/SB1) | competência, filial, OP | nenhuma | "
             "Controladoria | implementado; paridade MATR860 `PENDING` | "
             "`/closing/competences/{period}/production-order-consumption` |",
         )],
         reason="linha R04 superada em catálogo vigente"),
    # Gate 083 — eliminação de resíduos superados em contexto datado.
    # Cada fix_lines anota a afirmação superada com a verdade vigente;
    # o texto original permanece em SUPERSEDED para auditoria.
    dict(source_id="doc-00",
         title_contains="Ciclo 2 — Correção de classificação",
         action="fix",
         fix_lines=[(
             "Bloqueados por owner: R03 (fonte MATR460 — E2), "
             "R04/R13/R14 (sem artefato/fonte)",
             "Bloqueados por owner na época: R03 (fonte MATR460 — "
             "E2), R04/R13/R14 (sem artefato/fonte) — R03/R04 "
             "implementadas posteriormente",
         ),(
             "`BLOCKED_BY_OWNER` para R03/R04/R13/R14",
             "`BLOCKED_BY_OWNER` para R03/R04/R13/R14 na época — "
             "hoje implementadas (R13/R14 seguem sem fonte)",
         )],
         reason="índice datado repete bloqueios já resolvidos (G083)"),
    dict(source_id="doc-00",
         title_contains="G2 aprovado",
         action="fix",
         fix_lines=[(
             "T03/T05/R04+, seeds e fontes G1 pendentes",
             "T03/T05/G1 pendentes na época — R04 implementado "
             "posteriormente (consumption-audit)",
         )],
         reason="registro de aceite datado afirmava R04 pendente — "
                "anotado com estado vigente (G083)"),
    dict(source_id="doc-100",
         title_contains="4. Pauta G1 consolidada",
         action="fix",
         fix_lines=[(
             "`PENDING_CONTRACT` (R04, R06, R07, R09, R12, R15)",
             "`PENDING_CONTRACT` (R04, R06, R07, R09, R12, R15) "
             "— registro datado; hoje contratos vigentes",
         )],
         reason="lista datada de contratos pendentes — superada (G083)"),
    dict(source_id="doc-100",
         title_contains="5. Matriz de homologação G2",
         action="fix",
         fix_lines=[(
             "catálogos P6; R04/R06/R07/R09/R12/R15 `PENDING_CONTRACT`",
             "catálogos P6; R04/R06/R07/R09/R12/R15 `PENDING_CONTRACT` "
             "*(datado — contratos vigentes)*",
         )],
         reason="linha de matriz datada com PENDING_CONTRACT (G083)"),
    dict(source_id="doc-100",
         title_contains="Estado",
         action="fix",
         fix_lines=[(
             "52 fontes / 1.283 itens / retrieval com citação — "
             "**PASS real**",
             "corpus da época: 52 fontes e 1.283 itens (vigente: "
             "88 fontes / 2.208 itens) / retrieval com citação — "
             "**PASS real**",
         )],
         reason="métrica datada de corpus (G083)"),
    dict(source_id="doc-100",
         title_contains="Estado honesto",
         action="fix",
         fix_lines=[(
             "owners/contratos das fontes `PENDING_CONTRACT`",
             "owners/contratos das fontes `PENDING_CONTRACT` "
             "*(datado — pauta G1 segue para fontes oficiais "
             "ausentes)*",
         )],
         reason="pauta datada sobre fontes PENDING_CONTRACT (G083)"),
    dict(source_id="doc-100",
         title_contains="Evidência de execução",
         action="fix",
         fix_lines=[(
             "13 passed — 18 tools, schemas sem flag de consentimento",
             "13 passed — 18 tools na época (hoje seis tools "
             "semânticas + read/analyze), schemas sem flag de "
             "consentimento",
         )],
         reason="contagem datada de tools MCP (G083)"),
    dict(source_id="doc-100",
         title_contains="Implementado",
         action="fix",
         fix_lines=[(
             "**52 fontes autorizadas**",
             "**52 fontes autorizadas** *(na época; hoje 88)*",
         ),(
             "52 fontes → 1.283 itens",
             "52 fontes → 1.283 itens *(na época; hoje 88 → "
             "2.207)*",
         ),(
             "R07, R09, R12, R15 `PENDING_CONTRACT`",
             "R07, R09, R12, R15 `PENDING_CONTRACT` *(datado — "
             "contratos vigentes)*",
         )],
         reason="métricas e estados datados de corpus/contratos (G083)"),
    dict(source_id="doc-100",
         title_contains="F3 — R01",
         action="fix",
         fix_lines=[(
             "`PENDING_CONTRACT` (R04/R06/R07/R09/R12/R15)",
             "`PENDING_CONTRACT` (R04/R06/R07/R09/R12/R15) "
             "*(datado — contratos vigentes)*",
         )],
         reason="status datado de relatórios (G083)"),
    dict(source_id="doc-100",
         title_contains="Pauta G1 consolidada (decisões",
         action="fix",
         fix_lines=[(
             "Owners/contratos das fontes `PENDING_CONTRACT` "
             "(R04, R06, R07,",
             "Owners/contratos das fontes `PENDING_CONTRACT` "
             "*(datado — pauta de fontes oficiais segue vigente)* "
             "(R04, R06, R07,",
         )],
         reason="item de pauta datado (G083)"),
    dict(source_id="doc-111",
         title_contains="2. Matriz de evidência",
         action="fix",
         fix_lines=[(
             "18 tools CLARA expostas ao assistente",
             "tools CLARA expostas ao assistente — contagem "
             "datada: 18 (vigente: seis tools semânticas + "
             "read/analyze)",
         )],
         reason="contagem datada de tools (G083)"),
    dict(source_id="doc-117",
         title_contains="10. Matriz de análises",
         action="fix",
         fix_lines=[(
             "R04 (PENDING_CONTRACT)",
             "R04 (PENDING_CONTRACT — datado; implementado)",
         ),(
             "R06 (PENDING_CONTRACT)",
             "R06 (PENDING_CONTRACT — datado; implementado)",
         ),(
             "R07 (PENDING_CONTRACT)",
             "R07 (PENDING_CONTRACT — datado; implementado)",
         )],
         reason="estados datados de relatórios na matriz (G083)"),
    dict(source_id="doc-117",
         title_contains="14. Comparação",
         action="fix",
         fix_lines=[(
             "R04/R06/R07/R09/R12/R15 PENDING_CONTRACT; "
             "R13/R14 EXTERNAL_SOURCE",
             "R04/R06/R07/R09/R12/R15 PENDING_CONTRACT *(datado — "
             "contratos vigentes)*; R13/R14 EXTERNAL_SOURCE",
         )],
         reason="linha de matriz datada (G083)"),
    dict(source_id="doc-119",
         title_contains="REWORK-008",
         action="fix",
         fix_lines=[(
             "**Estado de R05/R08 (CP5):** sem produtor em api-delpi",
             "**Estado de R05/R08 (CP5), na época:** sem produtor "
             "em api-delpi — hoje com produtores vigentes",
         )],
         reason="rótulo de estado datado (G083)"),
    dict(source_id="doc-121",
         title_contains="5. Relatórios operacionais",
         action="fix",
         fix_lines=[(
             "| R04, R09, R12, R15 | consumo OP, Fat×MOD, wizard, "
             "cutoff | — | PENDING_CONTRACT | — | — | PLANNED",
             "| R04, R09, R12, R15 | consumo OP, Fat×MOD, wizard, "
             "cutoff | — | PENDING_CONTRACT *(datado — "
             "implementadas)* | — | — | PLANNED",
         )],
         reason="linha de plano datada com estados superados (G083)"),
    dict(source_id="doc-121",
         title_contains="Adendo",
         action="fix",
         fix_lines=[(
             "R11, CPV; demais respondem "
             "`report_not_implemented`/`unknown_report`.",
             "R11, CPV; demais relatórios respondiam "
             "`report_not_implemented`/`unknown_report` na época "
             "— hoje todas as capabilities vigentes respondem.",
         ),(
             "linha 137 superada parcialmente — **R12/R15** deixam "
             "`PENDING_CONTRACT`",
             "linha 137 superada parcialmente — **R12/R15** deixam "
             "`PENDING_CONTRACT` (atualização G083: R04/R09/R12/R15 "
             "todas implementadas)",
         )],
         reason="nota de superação parcial — complementada (G083)"),
    dict(source_id="doc-122",
         title_contains="1. Preflight",
         action="fix",
         fix_lines=[(
             "`REPORT_CATALOG` (`reports_routes.py:90-107`) tem "
             "R06/R07 `PENDING_CONTRACT`",
             "`REPORT_CATALOG` (`reports_routes.py:90-107`) tinha "
             "R06/R07 `PENDING_CONTRACT` na época — hoje contratos "
             "vigentes",
         )],
         reason="baseline datado de catálogo (G083)"),
    dict(source_id="doc-86",
         title_contains="8. Readiness",
         action="fix",
         fix_lines=[(
             "sem contrato TARGET",
             "sem contrato TARGET na época — hoje "
             "read(report.cost_closing_state) vigente",
         ),(
             "R03 | `BLOCKED_BY_OWNER` | fonte MATR460/params/"
             "emissão resumida (E2)",
             "R03 | `BLOCKED_BY_OWNER` na época — implementada via "
             "read(report.stock_inventory); fonte oficial MATR460 "
             "(E2) segue pendente | (E2)",
         )],
         reason="classificação de readiness datada (G083)"),
    dict(source_id="doc-86",
         title_contains="9. Priorização",
         action="fix",
         fix_lines=[(
             "**Bloqueados** R03/R13/R14",
             "**Bloqueados** R03/R13/R14 *(R03 implementada desde "
             "então; R13/R14 seguem bloqueados)*",
         ),(
             "**Bloqueados** R03/R04/R13/R14",
             "**Bloqueados** *(lista datada)*: R03/R04/R13/R14 "
             "— hoje apenas R13/R14 permanecem bloqueados",
         )],
         reason="priorização datada listando R03 bloqueado (G083)"),
    dict(source_id="doc-88",
         title_contains="11. Estado e encaminhamento",
         action="fix",
         fix_lines=[(
             "Runtime permanece bloqueado",
             "Runtime permanecia bloqueado na época — read-only "
             "autorizado posteriormente",
         )],
         reason="condição de gate datada (G083)"),
    dict(source_id="doc-90",
         title_contains="9. Registro de lacunas",
         action="fix",
         fix_lines=[(
             "R04/R13/R14 externos sem fonte",
             "R04/R13/R14 externos sem fonte *(datado — R04 "
             "implementado via consumption-audit; artefato oficial "
             "MATR860 pendente)*",
         )],
         reason="registro de lacuna datado (G083)"),
    dict(source_id="doc-100",
         title_contains="D2 — Pendências de integração",
         action="fix",
         fix_lines=[(
             "| R01–R15 sem contrato | PROVEN (`PENDING_CONTRACT`, "
             "sem falso oficial) |",
             "| R01–R15 sem contrato — registro datado "
             "(`PENDING_CONTRACT` na época) | estado atual: "
             "contratos vigentes — read(report.*) + rotas BFF |",
         )],
         reason="afirmação datada de ausência de contrato — hoje "
                "superada; reescrita com marcação temporal (G082-RW02)"),
    dict(source_id="doc-118",
         title_contains="8. Matriz AS-IS",
         action="fix",
         fix_lines=[(
             "| CLARA | conhecimento tribal | MCP 18 tools "
             "publicadas (READ autenticado no ChatGPT, corpus 52 "
             "fontes/1.298 itens — doc 111); "
             "`clara_consent_routes` + batch |",
             "| CLARA | conhecimento tribal | MCP seis tools "
             "semânticas + read/analyze (vigente); registro datado: "
             "18 tools / corpus 52 fontes em out/2026 — doc 111 |",
         )],
         reason="contagem datada da superfície MCP/corpus — "
                "superada; reescrita com valor vigente + nota "
                "datada (G082-RW02)"),
    dict(source_id="doc-124",
         title_contains="4. Lacunas declaradas",
         action="fix",
         fix_lines=[(
             "Reports `R04, R06, R07, R09–R15`: sem handler BFF — "
             "`NOT_IMPLEMENTED`\n  honesto via `not_implemented` "
             "(doc 120/122 = TARGET).",
             "Reports `R13, R14`: sem handler BFF — `NOT_IMPLEMENTED` honesto "
             "via `not_implemented` (fontes externas — doc 120/122 = TARGET). "
             "R04/R06/R07/R09–R12/R15 implementados com handlers vigentes.",
         )],
         reason="lista de handlers superada — R04/R09/R12/R15 implementados"),
    dict(source_id="doc-85",
         title_contains="BR-CMP-005",
         action="fix",
         fix_lines=[(
             "Relatórios sem contrato\nimplementado (R04/R09/R12/R15) → "
             "`report_not_implemented`; R13/R14 são\nevidência externa sem "
             "medida numérica.",
             "R13/R14 são evidência externa sem\nmedida numérica e sem "
             "contrato implementado → `report_not_implemented`;\n"
             "R04/R09/R12/R15 possuem contrato implementado.",
         )],
         reason="mapeamento report_not_implemented superado na regra"),
    dict(source_id="doc-120",
         title_contains="Adendo — Estado de integracao produtivo",
         action="fix",
         fix_lines=[(
             "Pacotes R04 (GAP-01), R09 (E6-D1..D6/E9), R13/R14 (D-5) "
             "permanecem `DECISION_REQUIRED`/`BLOCKED_BY_EVIDENCE`.",
             "R13/R14 (D-5) permanecem `BLOCKED_BY_EVIDENCE`; R04 e R09 "
             "implementados desde então (visão operacional; paridades "
             "pendentes).",
         )],
         reason="afirmação mista: R04/R09 superados, R13/R14 vigentes"),

    # Gate 085: R09 operational corpus excludes superseded timelines.
    dict(source_id="ficha-r09", title_contains="Histórico de implementação",
         action="drop", reason="timeline is not operational knowledge"),
    dict(source_id="ficha-r09", title_contains="Atualização — Gate 040",
         action="drop", reason="obsolete deployment snapshot"),
    dict(source_id="ficha-r09", title_contains="Atualização — Gate 041",
         action="drop", reason="obsolete implementation snapshot"),
    dict(source_id="ficha-r09", title_contains="Atualização — Gate 042",
         action="drop", reason="obsolete calculation snapshot"),
    dict(source_id="ficha-r09", title_contains="Registro anterior",
         action="drop", reason="superseded ficha version preserved in GitHub"),
    # ---------------- Gate 081 — auditoria integral (22214 itens) ----------------
    dict(source_id="doc-121",
         title_contains="Adendo — stage-03 (31/10/2026): comparação transversal",
         action="drop",
         reason="registro datado — 'demais respondem report_not_implemented' superado"),
    dict(source_id="doc-23",
         title_contains="G060 — Correção de classificação (2026-11-02)",
         action="drop",
         reason="registro datado — R06 implementado"),
    dict(source_id="doc-23",
         title_contains="IMPLEMENTATION-STAGE-03 — comparação transversal",
         action="drop",
         reason="registro datado — 'R09/R12/R15 seguem sem contrato' superado"),
    dict(source_id="doc-23",
         title_contains="REWORK-008 — Integração P7",
         action="drop",
         reason="registro datado — afirmações de produtor superadas"),
    dict(source_id="doc-85",
         title_contains="Adendo — Publicacao produtiva",
         action="drop",
         reason="registro datado — 'R04 sem contrato' superado"),
    dict(source_id="doc-88",
         title_contains="C3-D01 — Escopo mínimo da primeira entrega",
         action="drop",
         reason="registro datado — 'R05–R11 sem contrato' superado"),
    dict(source_id="doc-88",
         title_contains="C3-D06 — Dependências incompletas",
         action="drop",
         reason="registro datado — 'R04 BLOCKED' superado"),
    dict(source_id="doc-86",
         title_contains="9. Priorização recomendada",
         action="fix",
         fix_lines=[(
             "Bloqueados** R03/R04/R13/R14",
             "Bloqueados** R03/R13/R14 (R04 implementado posteriormente — "
             "visão operacional; paridade MATR860 pendente)",
         )],
         reason="lista de bloqueados superada para R04"),
)
