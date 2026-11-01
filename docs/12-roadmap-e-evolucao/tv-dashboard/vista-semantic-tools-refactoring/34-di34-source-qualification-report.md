# 34 — VISTA/TV DI-3.4 SOURCE QUALIFICATION & BINDING RESOLUTION REPORT

**Data:** 2026-10-31 · **Commit:** `6bf2a6f00e` · **Deploy:** `srv-api`
imagem `sha256:d51f1f2edb0f`

## Root cause — `ROOT_CAUSE_PROVEN`

1. `bindingPlan` DI-3.3 era global e não qualificava por contrato —
   rotas `document_export` (PDF/exportações) e não-GET entravam como
   candidatas de bloco de dados.
2. Nenhuma distinção por componente — mesma lista global para KPI,
   gráfico e tabela, apesar de `allowedDisplayModes`/`metaShape`
   existirem no catálogo canônico.
3. `status=ready` + "execução direta" contradizia
   `NEEDS_SOURCE_SELECTION` — layout pronto confundido com dados
   prontos.

## Correção — `REUSE_DECISION = EXTEND` (owner: `suggest_change` +
`TvDataRouteSuggestService` existente; catálogo já qualificava)

- `bindingPlan.blocks[]`: por bloco de dados — `blockType`,
  `requiredModes` (kpi_view→kpi; chart_view→line_chart/bar_chart
  conforme `chartType`; table_view→table), `state` por bloco,
  `candidates` qualificadas.
- Qualificação: exclui `metaShape=document_export` e não-GET;
  cruza `allowedDisplayModes` por bloco — `disqualifiedSources`
  contabilizado.
- `dataReadiness="pending_source_selection"` + `reason` honesta
  ("Layout pronto; seleção de fonte de dados pendente") quando
  state ≠ RESOLVED — "execução direta" não contradiz binding
  pendente.

## Testes

**2418/2418 PASS** — `test_design_intelligence_di34.py` 5 casos
(plano por bloco, document_export excluído, modes por componente,
readiness honesto, modos corretos em vendas); di33 ajustado ao
contrato por bloco.

## CHATGPT MCP REVALIDATION CONTRACT

```
analyze(analysis="intent_materialization",
  subject_refs={"playlistId":"<id>","slideId":"<id>"},
  parameters={"message":"crie um painel para acompanhar
    produtividade e problemas da fábrica","dry_run":true})
```
→ `ready` + `ops` + `bindingPlan.blocks[]` (por bloco:
`requiredModes`, `state`, `candidates` slim com
`allowedDisplayModes`/`metaShape`) + `dataReadiness=
pending_source_selection` + `disqualifiedSources` — sem
persistência. Verificar: exports/PDF ausentes; ambiguidade OEE
(realizado/meta/visão geral) preservada por bloco.

## Veredito

**`DI34_ACCEPTANCE = PASS`** — fontes qualificadas por contrato
por componente, estado de binding honesto por bloco, e readiness
que distingue layout de dados. Seis verbos e owners preservados.
