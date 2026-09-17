# TÉO MCP — Plugin / Agent Studio smoke checklist

> Live ChatGPT Plugin/Agent smoke is **PENDING_OPS** (requires Keycloak `mcp-transformometro` applied + deploy).  
> Code-level evidence is in `tests/test_teo_mcp_contract.py` and `tests/test_teo_mcp_write_governance.py`.

## Preconditions

1. `transformometro-api` deployed with `mcp` dependency and `/mcp` mount.
2. Keycloak client `mcp-transformometro` applied per [keycloak-mcp-client-runbook.md](./keycloak-mcp-client-runbook.md).
3. Token Evaluate proves `aud` includes `delpi-central` + MCP resource URL and `scope` includes `mcp:tools`.

## Smoke steps (live)

| # | Step | Expected |
|---|---|---|
| 1 | GET `.../apps/transformometro-api/.well-known/oauth-protected-resource` | 200, resource URL exact |
| 2 | POST MCP without Bearer | 401 + WWW-Authenticate |
| 3 | ChatGPT Plugin connect OAuth `mcp-transformometro` | Sign-in succeeds |
| 4 | tools/list | 20 tools (FULL CRUD) |
| 5 | `get_catalog` | 200 with registration_guide |
| 6 | User without `transformometro.view` | AuthZ deny on catalog/analyze |
| 7 | `validate_improvement_package` incomplete | ready=false, no write |
| 8 | Governed ACT only after confirmation | domain confirm_* honored |

## Structural smoke (CI / local)

```bash
cd transformometro-api
PYTHONPATH=.:../shared pytest tests/test_teo_mcp_contract.py tests/test_teo_mcp_write_governance.py -q
```

## Status

| Item | Status |
|---|---|
| Code MCP adapter | IMPLEMENTED |
| Contract tests | PASS (local) |
| Keycloak production apply | PENDING_OPS |
| ChatGPT Plugin live connect | PENDING_OPS |
| Agent Studio live | PENDING_OPS |
