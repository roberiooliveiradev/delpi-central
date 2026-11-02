# 37 — VISTA/TV DI-3.6.1 BUSINESS DOMAIN ANCHORING EXECUTION REPORT

**Data:** 2026-10-31 · **Commit:** `27d3832652` · **Deploy:** `srv-api`
imagem `sha256:95b133526176`

## Root cause — `ROOT_CAUSE_PROVEN`

As queries por propósito introduzidas no DI-3.6 (sufixos "série",
"indicador", "lista", "detalhes", "problemas") **dominavam o ranking
lexical sobre a intenção de negócio** — qualquer rota cross-domain
que casasse termos de apresentação era promovida:

- `get_openapi_diff` → KPI de produção.
- `get_commercial_rol_series`/`get_transformometro_*` → gráfico de
  produção.
- Auditorias 5S → tabela de "problemas da fábrica".

## Correção — `EXTEND` (owner: `suggest_change`/bindingPlan +
`TvDataRouteSuggestService` existente; sem novo mecanismo semântico)

**Business domain anchoring**: a mensagem original (sem sufixo)
produz as top candidates → `anchor_categories` (score ≥ 50% do topo)
+ `anchor_ids` (≥ 35%). Por bloco, só permanecem candidatos cuja
`category` pertence aos domínios âncora **ou** que já eram relevantes
na query bruta — cross-domain só com justificativa real do pedido.

## Antes/depois — "produtividade e problemas da fábrica"

| Bloco | Antes | Depois |
|---|---|---|
| `kpi_view` | `get_openapi_diff` no topo | `production_factory_shifts`, `OEE`, `inspecoes`, `machine_load` |
| `chart_view` | `commercial_rol`, `transformometro_savings` | `production_appointments_series`, `unproductive_hours`, `eficiencia_fabril_efficiency_series`, `production_oee_series` |
| `table_view` | dominado por 5S genéricos | `retrabalhos_detalhes` + 5S (âncora inspeções → fronteira legítima) |

Comercial: todas as séries/indicadores mantidos em `commercial`.
5S explícito preservado quando o pedido é de auditoria.

## Testes

**2436/2436 PASS** — `test_design_intelligence_di361.py` 6 casos
(openapi_diff excluído, séries cross-domain fora, OEE presente,
vendas comercial, avatar fora, estados tipados).

## CHATGPT MCP REVALIDATION CONTRACT

```
analyze(analysis="intent_materialization",
  subject_refs={"playlistId":"<id>","slideId":"<id>"},
  parameters={"message":"crie um painel para acompanhar
    produtividade e problemas da fábrica","dry_run":true})
```
→ `bindingPlan.blocks[]` — apenas fontes do domínio produção
(ou justificadamente ancoradas); `dataReadiness` honesto;
sem persistência.

## Veredito

**`DI361_ACCEPTANCE = PASS`** — sufixos de propósito não promovem
mais cross-domain; âncora semântica pela mensagem de negócio;
ambiguidades legítimas preservadas.
