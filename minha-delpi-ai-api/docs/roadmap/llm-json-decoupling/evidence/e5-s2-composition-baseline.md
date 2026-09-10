# E5.S2 — Baseline de composição / enrichment

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** E (plano 05)  
**Harness:** `tests/unit/domain/services/test_e5_s2_composition_baseline.py` (10 passed)  
**Inventário:** [`e5-s1-composition-inventory.md`](./e5-s1-composition-inventory.md)

## Veredito

```text
COMPOSITION_BASELINE_FAMILIES = PASS
LIVE_MULTI_SCOPE = PASS
LIVE_GROUNDED_ENRICH = PASS
DEAD_PLAN_WIRING = PASS
BUDGET_CAPS = PASS
SUFFICIENT_NO_AUTO_FOLLOWUP = PASS
```

## Famílias congeladas

| Family | Mensagem | Tool count (esperado) | Authority atual |
|--------|----------|----------------------|-----------------|
| product_360_overview | me fale do produto 10080001 | **0** (DEAD `.plan`) | `looks_like` + `composeRouteIds` no JSON; orquestração não chama `.plan` |
| structure_plus_stock | estrutura e estoque do 10080001 | **2** LIVE | `plan_product_scope_fetches` |
| factory_status | status … na fabrica | **1** (single playbook) | predicate + readiness; multi-scope vazio |
| department_meta_kpi | painel indicadores engenharia | **0** (DEAD `.plan`) | `route_ids_for_department` compose ≥3 no content |
| multi_domain_request | estoque + meta engenharia | **1** (só produto) | sinais híbridos sem planner unificado |
| result_already_sufficient | estoque do 10080001 | **1** + sufficiency | sem overview; critic → `sufficient` |

## Live enrich (irmão)

| Sinal | Freeze |
|-------|--------|
| `enrich_insight_scopes('structure')` | `('stock', 'profile')` |
| grounded plan após estrutura | scopes `stock`+`profile`, `max_calls=4` |
| `maxExtraRoutesPerTurn` | `4` |
| mode caps fast/normal/thinker | 2 / 4 / 6 |

## Métricas (harness unitário)

| Métrica | Como medido | Freeze |
|---------|-------------|--------|
| tool_count | planned fetches / corpus | ver tabela |
| redundancy | sufficiency em estoque único | follow-ups = `[]` |
| partial-failure | fora do escopo S2 (runtime) | N/A — E5.S3+ |
| latency | fora do escopo S2 | N/A — evals Onda H |

## Drift observável (não corrigir no freeze)

- `visão 360` **não** dispara `looks_like_product_overview` (trigger = «visão do produto» / «me fale»…).
- Product/department `.plan` existem e passam em TU isolados, mas **não** estão wired em `app/` (exceto `anomaly_follow_up_plans` no critic path).
- Multi-domain não compõe departamento + produto numa única lista de tools.

## Próximo

**E5.S3** — Goal coverage contract (`fulfilled` / `partial` / `blocked` / `needs_more_data`).
