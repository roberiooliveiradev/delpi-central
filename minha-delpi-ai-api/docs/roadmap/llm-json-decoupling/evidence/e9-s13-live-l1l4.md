# E9.S13 — Live L1–L4 leve (compound + multi_turn) pós plano-02

**Status:** `ATENDIDO_PARCIAL` (2026-09-10)  
**Onda:** H (plano 09)  
**Runners:** `scripts/smoke_c4_conversation_live.py`, `scripts/smoke_c5_mp_stock_followup_live.py`  
**Evidência JSON:** [`e9-s13-c4-conversation-live.json`](./e9-s13-c4-conversation-live.json) · [`e9-s13-c5-mp-followup-live.json`](./e9-s13-c5-mp-followup-live.json)

## Ambiente

- Keycloak/API healthy
- Smokes: agent dinâmico + token renovado por turno (corrige 401 de turns longos)
- Pós cutover plano-02 (taskPlanner ON)

## Resultados

| Smoke | Veredito | Nota |
|-------|----------|------|
| C4 PA seed+followup | **FAIL_QUALITATIVO** | Seed PASS; followup sem `/structure`/`/analyser` (L1) |
| C5 MP seed+followup | **PASS L1–L4** | Multi-turn estoque; vendas ausentes mas L1 aceita `/stock` |

## Gates E9.S6

| Gate | Antes | Depois |
|------|-------|--------|
| `multi_turn` | PASS_OFFLINE | **PASS_OFFLINE_AND_LIVE** (C5) |
| `compound` | PASS_OFFLINE | **PASS_OFFLINE** (sem promoção — C4 L1 structure FAIL) |
| `deleteAuthorized` | false | **false** (inalterado) |

## Aceite parcial

```text
MULTI_TURN_LIVE_L1L4 = PASS (C5)
COMPOUND_LIVE_L1L4 = FAIL (C4 structure miss)
TOKEN_REFRESH_PER_TURN = PASS
DELETE_AUTHORIZED = false
```

## Próximo

1. Investigar C4 followup sem BOM/structure (ownership produto/routing).
2. Live `unknown_api` / `safety` / `required_args` / `metamorphic` / `candidate_task_success`.
3. Só então reconsiderar `deleteAuthorized`.
