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

Each item and the envelope carry:

```text
authorizationScope: "provider_approval_only"
```

**R1-RW05:** this S2S projection proves **provider approval only**. It does
**not** prove user/org ExternalConnection, Core business permission, or
Domain AuthZ. DÉLIA must revalidate eligibility at invoke (R1-RW01) and
preserve subject/Policy/Decision/Domain gates.

`registered != approved != enabled != authenticated != authorized`.

### Endpoint policy (R1-RW03 / full remediation)

**Domain** (`endpoint_policy.evaluate_mcp_endpoint_ref`): pure structure +
IP classification; no `os`/`socket`.

**Infrastructure** (`endpoint_network`): loads
`CORE_MCP_TRUSTED_ENDPOINT_HOSTS`, resolves DNS, feeds resolved IPs into
the domain evaluator at registration time.

Trusted in-cluster hosts are an **explicit allowlist** (env + defaults).
External hosts require HTTPS. Cadastro validation ≠ connection-time
controls — DÉLIA re-checks egress on `_connect`.

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
