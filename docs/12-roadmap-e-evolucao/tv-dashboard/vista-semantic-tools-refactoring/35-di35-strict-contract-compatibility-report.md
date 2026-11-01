# 35 — VISTA/TV DI-3.5 STRICT DATA CONTRACT COMPATIBILITY REPORT

**Data:** 2026-10-31 · **Commit:** `bf659ef1a9` · **Deploy:** `srv-api`
imagem `sha256:da60f147b6d9`

## Root cause — `ROOT_CAUSE_PROVEN`

A interseção `{modo_especifico, auto} & {..., auto}` introduzida no
DI-3.4 classificava **qualquer rota `auto` como compatível com
qualquer bloco** — uma fonte `["kpi","auto"]`/`scalar` era elegível
para `line_chart` sem evidência de série temporal. Semântica
canônica de `auto`: o catálogo auto-seleciona o modo pelo shape do
retorno — **não** é "serve para qualquer componente".

## Correção — `EXTEND` (owner: `suggest_change`/bindingPlan)

- `requiredModes` agora só modos específicos.
- `_compatible()`: modo específico declarado **ou** `auto` +
  `metaShape` compatível — `kpi ← scalar/object/composite_analysis/
  product_snapshot`; `table ← list/paged_list/hierarchy/
  playbook_report/composite_analysis`; `line_chart`/`bar_chart` só
  modo declarado (scalar+auto nunca é série temporal).
- **Fallback por domínio**: bloco `NEEDS_CONTEXT` → busca em
  `TvDataRouteCatalogService.list_routes()` do mesmo domínio das
  top candidates rotas com o modo/shape exigido (bounded 8) —
  ranking lexical fraco não prova inexistência.
- Discovery limit 8→20 (bounded, read-only).

## Antes/depois — "produtividade da fábrica"

| Bloco | Antes (DI-3.4) | Depois |
|---|---|---|
| `kpi_view` | 6 candidatos | 6 (scalar-qualificadas) |
| `chart_view` line | **6 (as mesmas do kpi!)** | 6 séries reais — `production_appointments_series`, `eficiencia_fabril_efficiency_series`… |
| `table_view` | 6 (idem) | 5 (list/paged_list) |

Comercial: `chart_view` → 3 séries (`sales_conversion_rate_series`,
`billing_portfolio_series`, `commercial_rol_series`) — PDF ainda
excluído.

## Testes

**2424/2424 PASS** — `test_design_intelligence_di35.py` 6 casos
(scalar não elegível para linha, conjuntos distintos por
componente, séries declaradas, document_export excluído, estados
tipados); di34 atualizado ao novo contrato de `auto`.

## CHATGPT MCP REVALIDATION CONTRACT

```
analyze(analysis="intent_materialization",
  subject_refs={"playlistId":"<id>","slideId":"<id>"},
  parameters={"message":"crie um painel para acompanhar
    produtividade e problemas da fábrica","dry_run":true})
```
→ `bindingPlan.blocks[]` — `chart_view` (line) agora tem
**candidatos distintos** do `kpi_view` (séries declaradas), sem
scalar-only; `dataReadiness` + `reason` honestos; sem persistência.

## Veredito

**`DI35_ACCEPTANCE = PASS`** — `auto` não é mais evidência de
compatibilidade; cada bloco qualifica por contrato real de modo/
shape; fallback por domínio prova ausência vs ranking fraco.
