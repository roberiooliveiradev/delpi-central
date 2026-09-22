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
| 4 | tools/list / ChatGPT discovery | **20** tools (10 READ including `get_methodology_guide` + 1 ANALYSIS + 8 PREPARE + 1 commit_proposal); unbound ACT = 0 | code 20; live rediscovery **TEST_NOT_RUN** (published app) |
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
| Tools discovery 32/32 (2026-09-17) | **HISTORICAL PASS** |
| Tools discovery 20/20 including `get_methodology_guide`, `prepare_record_change`, `commit_proposal` | revalidar no app publicado |
| GPT Actions surface | **GOVERNED_PREPARE_COMMIT_V2** — 18 importable; 20/21 = HISTORICAL |
| READ live (`get_my_context` / `get_catalog` / `search_records`) | **PASS** (revalidate after catalog guidance deploy) |
| PREPARE via ChatGPT | **PROVEN** if observed; else **TEST_NOT_RUN** |
| COMMIT via ChatGPT | **TEST_NOT_RUN** |
| Wrong-user proposal | **TEST_NOT_RUN** |
| Agent Studio live | PENDING |
| Proposal store horizontal scale | TO_REVIEW if scale-out (single replica ACCEPT_WITH_RESIDUAL) |
