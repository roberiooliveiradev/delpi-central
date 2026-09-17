# TÉO MCP — Plugin / Agent Studio smoke checklist

> Live ChatGPT Plugin evidence dated **2026-09-17** (produção via SSH + ChatGPT).
> Code-level evidence: `tests/test_teo_mcp_contract.py`, `tests/test_teo_mcp_write_governance.py`.
> Shared onboarding: [`docs/10-guias-operacionais/mcp-chatgpt-plugin-onboarding-runbook.md`](../../../docs/10-guias-operacionais/mcp-chatgpt-plugin-onboarding-runbook.md).

## Preconditions

1. `transformometro-api` deployed with `mcp` dependency and `/mcp` mount (same Python as uvicorn).
2. Keycloak client `mcp-transformometro` applied per [keycloak-mcp-client-runbook.md](./keycloak-mcp-client-runbook.md).
3. Token Evaluate proves:
   - `azp` = `mcp-transformometro`
   - `aud` includes `delpi-central` + `…/transformometro-api/mcp`
   - `aud` does **not** include `…/api-delpi/mcp`
   - `scope` includes `mcp:tools` (and `offline_access` if Plugin requested it)
4. **ENVIRONMENT PROVENANCE GATE:** production verdicts only from prod host/Keycloak — not local Docker.

## Smoke steps (live)

| # | Step | Expected | Status (2026-09-17) |
|---|---|---|---|
| 1 | GET `.../apps/transformometro-api/.well-known/oauth-protected-resource` | 200, resource URL exact | PASS |
| 2 | POST MCP without Bearer | 401 + WWW-Authenticate | PASS (prod) |
| 3 | ChatGPT Plugin connect OAuth `mcp-transformometro` | Sign-in succeeds (user-defined client) | PASS |
| 4 | tools/list / ChatGPT discovery | **32** tools (9 READ + 1 ANALYSIS + 11 PREPARE + 11 ACT); unbound ACT = 0 | PASS 32/32 |
| 5 | `get_my_context` | authenticated user context | PASS |
| 6 | `get_catalog` | registration_guide present | PASS |
| 7 | `search_records` (domain READ) | canonical data (ex.: process Transforma → PROC-0001) | PASS |
| 8 | User without `transformometro.view` | AuthZ deny | TEST_NOT_RUN |
| 9 | PREPARE segura (ex. improvement package incomplete / prepare_*) | proposal_handle; no write | **TEST_NOT_RUN** |
| 10 | ACT after explicit test auth | read-back verifies outcome | **TEST_NOT_RUN** |

## Structural smoke (CI / local)

```bash
cd transformometro-api
PYTHONPATH=.:../shared pytest tests/test_teo_mcp_contract.py tests/test_teo_mcp_write_governance.py -q
```

## Status

| Item | Status |
|---|---|
| Code MCP adapter | IMPLEMENTED |
| Contract / write-governance tests | PASS (local) |
| Keycloak production apply | **PROVEN** |
| ChatGPT Plugin create + OAuth | **PASS** |
| Tools discovery 32/32 | **PASS** |
| READ live (`get_my_context` / `get_catalog` / `search_records`) | **PASS** |
| PREPARE via ChatGPT | **TEST_NOT_RUN** |
| ACT / WRITE BUSINESS OUTCOME via ChatGPT | **TEST_NOT_RUN** |
| GPT Actions legacy bridge (20 ops) | **LEGACY_TRANSITIONAL_BRIDGE** — still up |
| Agent Studio live | PENDING |
| Proposal store horizontal scale | TARGET (single replica ACCEPTED_WITH_RESIDUAL) |
