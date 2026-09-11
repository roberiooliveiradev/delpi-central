# E2.S7 — Cleanup heurísticas (plano-02)

**Status:** `ATENDIDO` — JUSTIFIED_FAST_PATH (2026-09-10)  
**Onda:** C (plano 02)

## Decisão (TARGET do plano-02)

> Fast paths pequenos podem permanecer apenas para sinais inequívocos e mensuravelmente úteis.

DELETE total dos JSON major **não** é o alvo quando ainda são fallback/guard determinístico. Estado final = **JUSTIFIED_KEEP** aprovado.

## KEEP aprovado

| Superfície | Papel residual |
|------------|----------------|
| `intent_router.json` | cascade SQL/RAG/web/short-context (não coberto barato por TU) |
| `analysis_intent_vocabulary.json` | terms + email-from-data + guards |
| `product_query_intent.json` | fallback mapper-first product |
| `production_operational_intent.json` | fallback mapper-first production |
| `department_kpi_rules.json` | fallback mapper-first KPI |

## Gate

`turn_understanding_heuristics_json` → status **KEEP_APPROVED** (não DELETE).  
`deleteAuthorized` global permanece `false` para markers de outros planos até Onda H live PASS.

## Aceite

```text
NO_UNAUTHORIZED_DELETE = PASS
MAJOR_HEURISTICS_JUSTIFIED_FAST_PATH = PASS
PLANO_02_TARGET_FAST_PATHS = PASS
```
