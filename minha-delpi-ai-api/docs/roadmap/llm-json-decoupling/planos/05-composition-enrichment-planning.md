# Plano 05 — Composition/enrichment -> planejamento orientado por goals e budget

**Prioridade:** P1  
**Status execução:** Onda E · consumers `routeId`/composition no inventário §2 · após/com 04  
**Evidência:** [`../evidence/onda-a-inventory.md`](../evidence/onda-a-inventory.md) · [`../evidence/execution-ledger.md`](../evidence/execution-ledger.md)  
**Objetivo perceptível:** consultas compostas e enriquecimentos devem ser escolhidos pelo objetivo real do usuário, pelos dados já disponíveis e pelas actions autorizadas, não por listas fixas de `routeIds` e mapas `scope -> route`.

## CURRENT

Fontes prioritárias:

- `entity_capability_catalog.json`;
- `department_meta_composition.json`;
- `product_enrichment_composition.json`;
- consumers de `scopeToRouteId`, `composeRouteIds`, `primaryRouteId`, `artifactToEnrichKey`, `enrichInsightScopes` e limites associados.

Padrão residual:

```text
profile/entity/scope conhecido
-> routeId predefinido
-> fan-out predefinido
-> composição
```

## TARGET

```text
current goals
+ facts/results já obtidos
+ allowed Action Catalog
+ remaining tool/latency/token budget
-> planner/critic estruturado
-> optional additional goals/actions
-> validation/policy
-> bounded execution
```

## Requisitos

| ID | Requisito |
|---|---|
| R05-01 | Separar limite/budget legítimo de roteamento hardcoded. |
| R05-02 | Remover `scope -> routeId` como requisito de composição. |
| R05-03 | Evitar tool calls redundantes quando resultado atual já cobre o goal. |
| R05-04 | Permitir enrichment útil para API externa sem mapa local. |
| R05-05 | Preservar fan-out máximo, safety e partial failure. |

## Etapas

### E5.S1 — Inventário de decisões de composição

**Fazer:** mapear onde entity/profile/artifact dispara tool adicional e como o sistema decide primary vs enrich.

**Classificar:** `DETERMINISTIC_POLICY` para caps/budget; `SEMANTIC_ROUTING_HEURISTIC` para route maps; `BUSINESS_RULE` quando houver regra real de domínio.

### E5.S2 — Baseline de composição

Cobrir product 360, structure + stock, factory status, departmental meta + KPI, multi-domain request e resultado já suficiente.

Medir tool count, task success, redundancy, latency e partial-failure behavior.

### E5.S3 — Goal coverage contract

**Fazer:** formalizar quando um goal está `fulfilled`, `partial`, `blocked`, `needs_more_data`; usar facts/result metadata, não path literal.

**Teste:** empty payload, partial pagination, sibling schema, unknown API.

### E5.S4 — Planner-driven enrichment

**Fazer:** permitir que planner/critic proponha action adicional somente entre allowed candidates, justificando qual goal não coberto resolve.

**Não fazer:** auto-fan-out só porque entity pertence a uma lista.

**Teste:** extra action necessária vs desnecessária; max budget; same action duplicate suppression.

### E5.S5 — Department composition cutover

**Fazer:** substituir `primaryRouteId/composeRouteIds` por goals semânticos + retrieval. Taxonomia de departamento pode permanecer como contexto de negócio quando canônica.

**Teste:** financial/commercial/quality/production + provider/path rename.

### E5.S6 — Entity enrichment cutover

**Fazer:** retirar `scopeToRouteId` e maps equivalentes quando goal coverage + retrieval cobrirem o caso; manter limites de fan-out e modos fast/normal/thinker.

**Teste:** product and unknown entity/API; max routes; mixed goals.

### E5.S7 — Cleanup

**Fazer:** remover maps mortos, atualizar docs/help quando user-facing e manter somente policies de budget legítimas.

## Invariantes

- Tool budget continua determinístico.
- Planner não amplia permissions.
- Reads independentes podem paralelizar; writes/dependencies preservam ordem.
- Falha de enrichment não apaga resposta válida já obtida.
- Enrichment deve aumentar cobertura do objetivo, não apenas “deixar a resposta mais rica”.

## Aceite

```text
GOAL_COVERAGE = PASS
NO_FIXED_ROUTE_MAP_REQUIRED = PASS
REDUNDANT_TOOL_RATE = sem regressão
UNKNOWN_API_ENRICHMENT = PASS quando semanticamente aplicável
BUDGET_ENFORCEMENT = PASS
PARTIAL_FAILURE = PASS
```
