# Scope reconciliation

TASK_ID: DELIA-C3-T2-ENTITY-SUFFICIENCY-HTTP-MULTITURN-AND-VERIFIER-ACCEPTANCE-01
BASE_SHA: e38940c0c6b7ab26d25467b45500f9cc0b4193ad
GENERATED_AT_UTC: 2026-11-16T11:22:54Z

## In scope

- Entity congruence under presentation aggregation (`semantic_capability_support.py`)
- Directed sufficiency + HTTP multiturn boundary tests
- Live HTTP two-turn E2E via `POST /interaction/turns` + validated `context`
- Live G2 (`INT2_G2_aggregation_active_scope`) two-agent OpenRouter
- Env unblock: restore `V024__prc_record_flags.sql` to applied checksum (DAVI owner)
- Evidence package + independent verifier with full RQ/AC text

## Out of scope / preserved

- Concurrent api-delpi / DAVI / engineering WIP (not staged)
- PRODUCTION_DEPLOY / TWO_AGENT_PROMOTION / PHASE_ADVANCEMENT / Agents 3–4

## Residuals (non-critical)

- M3/M6/M7/M8/M9 live: PENDING where no authorized negative identity or not re-run live (contract fixtures cover M1/M2/M4/M5/M10)
- Turn-1 of HTTP live used fallback clarification after a transient provider error; turn-2 still recovered objective via canonical context and grounded on DAVI
