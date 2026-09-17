# TÉO / Transformômetro — OpenAI Plugin + MCP

> Documentation does not prove runtime. Live OAuth/Plugin evidence must be revalidated after deploy + Keycloak apply.

## Specialist identity

| Field | Value |
|---|---|
| Short name | **TÉO** |
| Full name | TÉO — Especialista em Transformação Digital |
| Mission | Transformação / eficiência / otimização de processos no Transformômetro |

Branding ≠ authorization.

## Technical identities

| Surface | Technical id |
|---|---|
| Plugin / MCP server name | `transformometro` |
| Keycloak client | `mcp-transformometro` |
| MCP resource | `https://minhadelpi.com.br/apps/transformometro-api/mcp` |
| Manifest | `integrations/openai-plugin/mcp.json` |

## Architecture

```text
Workspace Agent / ChatGPT Plugin (TÉO)
  → OAuth Authorization Code + PKCE
  → Keycloak end-user identity (mcp-transformometro)
  → MCP Streamable HTTP /apps/transformometro-api/mcp
  → interface/mcp adapter
  → existing gpt_actions / application services (FULL CRUD)
  → canonical AuthZ (capability ≤ user)
  → Postgres transformometro
```

## Surface policy

```text
TEO_MCP_SURFACE = FULL_CRUD_GOVERNED
READ + PREPARE + ACT = REQUIRED
DAVI_READ_ONLY_COPY = FORBIDDEN
```

MCP tools may be 1 GPT operationId → N semantic tools (PREPARE/ACT split).
Parity gate: every GPT Actions operationId covered; MISSING=0. See
`docs/integrations/teo-mcp-capability-parity.md` and `tm_app/interface/mcp/constants.py`.

Write governance (MCP):

- Material writes: `prepare_*` → opaque `proposal_handle` → matching `act_*` (handle only)
- `prepare_improvement_package` binds the exact package; `act_commit_improvement_package` executes that proposal
- Incomplete packages: `ready=false` / `act_allowed=false` → NO WRITE
- Honor `confirm_delete`, `confirm_vigencia_change`, `confirm_resend` (proposal does not replace validators)
- ACT success (`isError=false`) requires authoritative read-back / verified postcondition
- MCP tool metadata / OAuth scopes ≠ RBAC

## Bridge

| Surface | Client | Lifecycle |
|---|---|---|
| GPT Actions | `chatgpt-transformometro` | LEGACY_TRANSITIONAL_BRIDGE |
| MCP Plugin/Agent | `mcp-transformometro` | TARGET |

Do not expand GPT Actions as the durable target. Deprecate only after live MCP CRUD parity + smoke.

## Auth model

- Transport requires OAuth before tools/list
- JWT `aud` must include `delpi-central` **and** exact MCP resource URL
- JWT `scope` must include `openid profile email mcp:tools`
- Service tokens forbidden on `/mcp`

## Ops

1. Deploy `transformometro-api` with `mcp` dependency.
2. Apply Keycloak per [keycloak-mcp-client-runbook.md](./keycloak-mcp-client-runbook.md).
3. Register Plugin URL = MCP resource.
4. Smoke READ + AuthZ negative + one governed ACT.

## Code ownership

| Piece | Path |
|---|---|
| OAuth contract | `tm_app/interface/mcp/oauth_contract.py` |
| FastMCP server | `tm_app/interface/mcp/server.py` |
| Tool bridge | `tm_app/interface/mcp/tool_bridge.py` |
| Auth middleware | `tm_app/middleware/auth_middleware.py` |
| Mount | `tm_app/main.py` → `/mcp` |
