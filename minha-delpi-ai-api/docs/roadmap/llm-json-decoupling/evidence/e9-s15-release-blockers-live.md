# E9.S15 — Live release blockers (recommendations + parity)

**Status:** `ATENDIDO` (2026-09-11)  
**Onda:** H (plano 09)  
**Harness:** `scripts/smoke_e9_s15_release_blockers_live.py`  
**JSON:** `docs/roadmap/llm-json-decoupling/evidence/e9-s15-release-blockers-live.json`

## Objetivo

Promover as duas células que ainda bloqueavam `globalReleasePass` em E9.S8:

| Célula | Antes | Depois |
|--------|-------|--------|
| `recommendations_grounded` | `PASS_OFFLINE` | `PASS_OFFLINE_AND_LIVE` |
| `send_stream_simulate_parity` | `PASS_OFFLINE` | `PASS_OFFLINE_AND_LIVE` |

## Veredito live

```text
recommendations_grounded = PASS
send_stream_simulate_parity = PASS
OVERALL = PASS
```

## Asserções

### recommendations_grounded (SEND estoque)

- `dataCommentary.recommendations` com ≥1 hit em `recommendationQueries.stock` (label/query do content JSON).
- `presentationFollowUpSuggestions` com label+query acionáveis.
- `interactivity.suggestions.sourceKey` ∈ allowlist de catálogos conhecidos.
- Negativo: sem markers de write/delete nos chips; sem `actionId` rogue.

### send_stream_simulate_parity

| Superfície | Aceite |
|------------|--------|
| SEND | path `/products/{code}/stock` + display schema-driven + recs |
| STREAM | SSE `done` + plans/tables + path stock + sem path leak |
| SIMULATE | sandbox tools + plans/tables + path stock |

## Dataset

- Produto: `10080022` (override `SMOKE_PRODUCT_CODE`)
- Corpus hash imutável E9: inalterado
- Offline harnesses E6.S2 / E9.S10 permanecem válidos

## Próximo

Revalidar E9.S8 → `globalReleasePass=true` → fechar E9.S9 aceite final.
