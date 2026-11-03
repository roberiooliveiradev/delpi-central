# 36 — VISTA/TV DI-3.6 SEMANTIC METRIC MATCHING & BINDING COMPLETION REPORT

**Data:** 2026-10-31 · **Commit:** `08046d4189` · **Deploy:** `srv-api`
imagem `sha256:e6bd693f41e7`

## Root cause — `ROOT_CAUSE_PROVEN`

DI-3.5 qualificava por contrato (modo/shape) mas a query de
descoberta era **global e única** — a mesma mensagem servia KPI,
gráfico e tabela, sem refinamento por propósito. Resultado: rotas
semanticamente fracas (ex.: `get_customer_avatar` em vendas)
qualificavam por modo mas não por relevância à pergunta do
componente. Catalog sem response-schema impedia binding de campo
sem preview.

## Correção — `EXTEND` (owner: `suggest_change`/bindingPlan +
`TvDataRouteSuggestService` existente)

- **Query por propósito do bloco**: `kpi_view` → "indicador valor
  atual"; `chart_view(line)` → "série evolução período";
  `table_view` → "lista detalhes problemas" — o ranking lexical
  responde à pergunta real do componente.
- **Limiar de relevância**: score ≥ 50% do topo do bloco remove
  ruído cross-domain.
- **Cap 8** candidatos por bloco (bounded).
- **Binding spec canônico** em `RESOLVED`: `operationId` +
  `displayMode` + `missingParams` (params required non-optional
  explicitados — nunca inventados) — compatível com
  `build_preview_block_from_route`/`validate_route_params`
  (dataBinding: operationId+params+displayMode+label).

## Antes/depois — "produtividade da fábrica"

| Bloco | DI-3.5 | DI-3.6 |
|---|---|---|
| `kpi_view` | 6 (mesma lista global) | 7 relevantes (indicador) |
| `chart_view` | 6 séries | 8 séries propósito-alinhadas (`appointments_series`, `unproductive_hours`, `eficiencia_series`) |
| `table_view` | 5 | 8 (`retrabalhos_detalhes`, audit NC — problemas reais) |

Comercial: `chart_view` → 5 séries comerciais; `get_customer_avatar`
fora (limiar).

## Testes

**2430/2430 PASS** — `test_design_intelligence_di36.py` 6 casos
(séries preferidas em chart, listas em table, cap 8, avatar
excluído, estados tipados, binding spec em RESOLVED).

## Resíduos honestos

- `dataReadiness` segue `pending_source_selection` — ambiguidade
  real de métricas (OEE meta/realizado/consolidado) preservada.
- `RESOLVED` exige 1 candidato — raro por design; binding de campo
  (measure/dimension) precisa `data_block_preview`/DataModel —
  `missingParams` explicita o que falta.

## CHATGPT MCP REVALIDATION CONTRACT

```
analyze(analysis="intent_materialization",
  subject_refs={"playlistId":"<id>","slideId":"<id>"},
  parameters={"message":"crie um painel para acompanhar
    produtividade e problemas da fábrica","dry_run":true})
```
→ `bindingPlan.blocks[]` por propósito (chart→séries, table→listas
de problemas, kpi→indicadores) + `binding{operationId, displayMode,
missingParams}` quando RESOLVED + `dataReadiness` — sem persistência.

## Veredito

**`DI36_ACCEPTANCE = PASS`** — seleção semântica por propósito de
componente + binding spec canônico; E2E com dados reais segue
pendente do canal autorizado (homologação), registrado honestamente.
