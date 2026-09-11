# E9.S13 — Live L1–L4 leve (compound + multi_turn) pós plano-02

**Status:** `ATENDIDO` (2026-09-11)  
**Onda:** H (plano 09)  
**Runners:** `scripts/smoke_c4_conversation_live.py`, `scripts/smoke_c5_mp_stock_followup_live.py`  
**Evidência JSON:** [`e9-s13-c4-conversation-live.json`](./e9-s13-c4-conversation-live.json) · [`e9-s13-c5-mp-followup-live.json`](./e9-s13-c5-mp-followup-live.json)

## Ambiente

- Keycloak/API healthy; AI API volume-mounted (`/app`)
- Smokes: agent dinâmico + token renovado por turno; timeout 600s; sem retry POST `/messages` após timeout
- Pós cutover plano-02 (taskPlanner ON)

## Correção C4 (follow-up sem `/structure`)

Causa: fan-out multi-scope passava a utterance composta (estrutura+estoque) ao OpenAPI-first, que colapsava em `/stock`.

Fix canônico:

1. `ChatProductMultiScopePlanningService._select_scope_action` — mensagem **scoped** por escopo (`scopedSelectMessage`)
2. `ChatFollowUpIntentService.follow_up_type` — ≥2 scopes → não colapsar tipo (guard de reentrada)
3. `ChatRouteContextService` — ≥2 scopes → sem `segment_from_message` único

## Resultados

| Smoke | Veredito | Nota |
|-------|----------|------|
| C4 PA seed+followup | **PASS L1–L4** | Followup paths: `/stock` + `/structure` (+ stock) |
| C5 MP seed+followup | **PASS L1–L4** | Multi-turn estoque (evidência prévia) |

## Gates E9.S6

| Gate | Antes | Depois |
|------|-------|--------|
| `multi_turn` | PASS_OFFLINE_AND_LIVE | **PASS_OFFLINE_AND_LIVE** (C5) |
| `compound` | PASS_OFFLINE | **PASS_OFFLINE_AND_LIVE** (C4) |
| `deleteAuthorized` | false | **false** (dims live ainda faltam) |

## Aceite

```text
MULTI_TURN_LIVE_L1L4 = PASS (C5)
COMPOUND_LIVE_L1L4 = PASS (C4 structure+stock)
TOKEN_REFRESH_PER_TURN = PASS
DELETE_AUTHORIZED = false
```

## Próximo

1. Live `unknown_api` / `safety` / `required_args` / `metamorphic` / `candidate_task_success`.
2. Só então reconsiderar `deleteAuthorized`.
