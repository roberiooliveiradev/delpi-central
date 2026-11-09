# Core — Governed MCP provider registry

Owner: `core-api`  
Consumers: admin Portal/Control Tower (future UI); DÉLIA via S2S eligibility  
Authorization: Documento 293 §2A.9 (`PO_IMPLEMENTATION_AUTHORIZATION=APPROVED`, DEV)

## Persistence

Table: `mcp_providers` (PostgreSQL `delpi_core`, public schema — not Keycloak, not DÉLIA).

Does **not** store tokens, client secrets, refresh tokens, or `tools/list` catalogs.

## Permissions

| Code | Use |
|---|---|
| `mcp_providers.view` | List/get admin records |
| `mcp_providers.manage` | Register, review, approve/reject, enable/disable, revoke |

## Admin HTTP

Prefix: `/admin/mcp-providers`

| Method | Path | operationId | Permission |
|---|---|---|---|
| GET | `/` | `list_mcp_providers` | view |
| GET | `/{providerRef}` | `get_mcp_provider` | view |
| POST | `/` | `register_mcp_provider` | manage |
| POST | `/{providerRef}/review` | `review_mcp_provider` | manage |
| POST | `/{providerRef}/approve` | `approve_mcp_provider` | manage |
| POST | `/{providerRef}/reject` | `reject_mcp_provider` | manage |
| POST | `/{providerRef}/enable` | `enable_mcp_provider` | manage |
| POST | `/{providerRef}/disable` | `disable_mcp_provider` | manage |
| POST | `/{providerRef}/revoke` | `revoke_mcp_provider` | manage |

Optimistic concurrency: optional `expectedVersion` query/body.

## S2S eligibility (DÉLIA)

```text
GET /integrations/mcp-providers/eligible
operationId: list_eligible_mcp_providers
Auth: CORE_API_INTEGRATIONS_SERVICE_TOKEN
```

Returns only `enabled=true` providers in `APPROVED|ACTIVE|DEGRADED`.

`registered != approved != enabled != authenticated != authorized`.

## DEV seed

```bash
cd core-api
# after alembic upgrade
python scripts/seed_mcp_providers_dev.py
```

Seeds seven specialists idempotently; enables only `davi`/`teo`/`vista` by default.

## DÉLIA consumer

```text
DELIA_MCP_PROVIDER_REGISTRY_MODE=core
CORE_API_URL=...
CORE_API_INTEGRATIONS_SERVICE_TOKEN=...
```

Fail closed when Core is unavailable — no fallback to env-enabled specialists.

## Out of scope (this contract)

- ExternalConnection physical table
- External OAuth secret store
- Production deploy / Keycloak production writes
- Snapshot / tools/list persistence
