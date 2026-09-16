# DAVI / API DELPI — OpenAI Plugin + MCP

> **Documentation does not prove runtime.** Runtime/provider evidence is recorded separately and must be revalidated after material code, provider or configuration changes.

## Scope / authority

```text
This document owns the CURRENT API DELPI + OpenAI/MCP integration
contract/evidence.

It is not the global DAVI product architecture.

General DAVI product/architecture baseline:
docs/12-roadmap-e-evolucao/davi/README.md
```

API DELPI is the **first major information source / domain contract family** for DAVI Wave 1 — not DAVI architecture itself.

## Specialist identity (user-facing)

| Field | Value |
|---|---|
| Short name | **DAVI** |
| Full name | DAVI — Especialista em Dados e Informações DELPI |
| Mission | Consultar informações autorizadas da DELPI respeitando a identidade e as permissões do usuário |

DAVI is branding/orchestration identity — **not** an authorization authority.

## Technical identities (do not rename for branding)

| Surface | Technical id |
|---|---|
| Plugin `name` | `api-delpi` |
| MCP server name | `api-delpi` |
| Keycloak client | `mcp-api-delpi` |
| MCP resource | `https://minhadelpi.com.br/apps/api-delpi/mcp` |
| V1 business tool | `search_products` |

## Architecture status

| Item | Value |
|---|---|
| Classification | **CURRENT PROVEN V1 — API DELPI integration** (not universal DAVI TARGET) |
| Strategic target (platform) | OpenAI Plugin/App → remote MCP → semantic capability → existing use case |
| Workspace Agent consumer | DAVI Agent Studio draft/preview uses the same DAVI app/MCP with end-user authentication |
| Legacy | `/gpt-actions/v1` = `LEGACY_TRANSITIONAL`; do not expand by default; GPT Actions `operationId` catalog is **not** the DAVI semantic capability authority |
| V1 business tool | `search_products` (read-only Product Master) |
| MCP auth model | Transport requires OAuth |
| Resource audience | JWT `aud` must include exact MCP resource **and** `delpi-central` |
| Keycloak client | `mcp-api-delpi` — predefined/user-defined OAuth client |
| ChatGPT connection | **PROVEN** |
| Tool discovery | **PROVEN** — ChatGPT UI lists exactly `search_products` |
| Live business invocation | **PROVEN** — authenticated searches returned approved Product Master projection |
| MCP hardened contract | **PROVEN in runtime/provider** — bounded input schema + safe validation; typed output proven in runtime |
| Agent private preview | **PROVEN** for current operator |
| Negative business AuthZ | **PENDING** — second user without access still required |
| Rate limit | `MCP_RATE_POLICY = PENDING_OWNER_DECISION` |
| Layering | `DAVI_V1_EXTERNAL_CAPABILITY_LAYERING = RESOLVED` (Application no longer imports Composition Root; use case injected at Interface/Composition) |

## CURRENT PROVEN V1 — API DELPI integration

```text
Workspace Agent DAVI (optional consumer layer)
  ↓
ChatGPT / Codex / approved provider surface
  → OpenAI Plugin/App
  → OAuth Authorization Code + PKCE
  → Keycloak end-user identity
  → MCP Streamable HTTP /apps/api-delpi/mcp
  → interface/mcp adapter
  → application/external_capabilities
  → SearchProducts use case
  → canonical backend AuthZ
  → authoritative source
```

This chain is **CURRENT PROVEN V1** for the API DELPI information source. It is **not** the universal DAVI TARGET architecture (see `docs/12-roadmap-e-evolucao/davi/README.md`).

```text
MCP = interface/protocol/adapter
MCP != domain/business/AuthZ authority
```

The Agent and Plugin/MCP adapter do not own Product Master, identity, RBAC, persistence, or business rules.

### Known layering EXECUTION_DRIFT (resolved)

```text
application/external_capabilities/product_search_service.py
→ imports app.composition.product_composer
→ Composition Root

was DAVI_V1_EXTERNAL_CAPABILITY_LAYERING = EXECUTION_DRIFT
```

**RESOLVED** in `DAVI-ARCH-RUNTIME-001`: Application `search_products` now receives an injected `SearchProductsUseCase`; Composition/Interface (`build_search_products_use_case`) owns concrete wiring. Functional V1 behavior and contracts preserved. Regression: `test_product_search_service_does_not_import_composition_root`.

```text
DAVI_V1_EXTERNAL_CAPABILITY_LAYERING = RESOLVED
```

### GPT Actions = LEGACY_TRANSITIONAL

`/gpt-actions/v1` and `application/external_capabilities/catalog_service.py` (operationId-based “capabilities”) remain **`LEGACY_TRANSITIONAL`**. That operationId catalog is **not** the DAVI semantic capability authority.

## MCP resource — exact canonical value

```text
https://minhadelpi.com.br/apps/api-delpi/mcp
```

The exact value must match:

- protected-resource metadata `resource`;
- OAuth `resource` sent by the provider when applicable;
- Keycloak Audience mapper;
- JWT `aud` membership;
- plugin `mcp.json`;
- MCP resource-server validation.

Do **not** advertise a trailing slash to compensate for framework routing.

### Proven routing issue and fix

FastAPI/Starlette `Mount("/mcp")` + FastMCP `streamable_http_path="/"` produced an authenticated HTTP `307` from `POST /mcp` to `/mcp/`.

ChatGPT uses the canonical resource URL without a trailing slash. PLUGIN-005 fixed this with an **internal ASGI path rewrite** `/mcp` → `/mcp/` before the mount, preserving the externally advertised URL and preventing the HTTP redirect.

Required regression:

```text
POST /apps/api-delpi/mcp
→ never 307/308
```

## ChatGPT Origin / DNS-rebinding protection

FastAPI CORS is **not** the same control as FastMCP transport-security Origin validation.

PLUGIN-005 proved that the MCP transport returned `403 Invalid Origin` even while the API CORS list contained ChatGPT domains. The MCP transport-security allowlist must independently accept the provider Origins used by the connector:

```text
https://chatgpt.com
https://chat.openai.com
```

Required regression:

```text
POST /apps/api-delpi/mcp
Origin: https://chatgpt.com
without Bearer
→ 401 OAuth challenge
→ not 403 Invalid Origin
```

Do not disable DNS-rebinding protection to make the connector work.

## OAuth scopes

### Required in JWT `scope` (MCP resource server)

```text
openid profile email mcp:tools
```

| Kind | Scopes |
|---|---|
| Identity | `openid`, `profile`, `email` |
| MCP resource-binding | `mcp:tools` |

### Keycloak client scope — internal audience mechanism

```text
audience-delpi
```

`audience-delpi` remains Default on `mcp-api-delpi` and causes `aud` to contain `delpi-central`.

It is **not** a required string in the JWT `scope` claim. Keycloak Evaluate proved the access-token scope as:

```text
openid email profile mcp:tools
```

Do not modify Keycloak merely to make an internal client-scope name appear in JWT `scope`. Validate the security postcondition instead.

### MCP resource binding

For the proven Keycloak 26.0.7 configuration, the platform uses:

```text
client scope: mcp:tools
→ Audience mapper
→ Included Custom Audience:
   https://minhadelpi.com.br/apps/api-delpi/mcp
→ Add to access token: ON
```

Therefore the token used by DAVI must contain both audiences:

```text
delpi-central
https://minhadelpi.com.br/apps/api-delpi/mcp
```

Extra legitimate audiences, such as `account`, do not invalidate the token.

### Business authorization is separate

OAuth scopes and audiences bind identity/resource; they do not grant Product Master business access.

`search_products` continues to use the canonical backend authorization already owned by API DELPI. Do not expose internal permission names to the user or copy them into provider scopes/tool metadata.

## Token validation on `/mcp`

1. shared JWT validation → signature, issuer, exp, nbf, platform audience (`delpi-central`);
2. MCP adapter → exact MCP resource audience membership;
3. JWT `scope` contains `openid profile email mcp:tools`;
4. authenticated DELPI user context;
5. canonical business AuthZ in the existing search capability.

Ordinary DELPI tokens bound only to `delpi-central` are rejected on `/mcp`.

## Keycloak / ChatGPT client contract

| Field | Proven configuration |
|---|---|
| Client mode | `PREDEFINED` / ChatGPT **Cliente OAuth definido pelo usuário** |
| Client ID | `mcp-api-delpi` |
| Client authentication | ON / confidential |
| Token endpoint auth method | `client_secret_post` in the successful ChatGPT configuration |
| Standard Flow | ON |
| Direct Access Grants | OFF |
| Service Accounts | OFF |
| Implicit Flow | OFF |
| PKCE | S256 |
| Client scopes | `audience-delpi`, `mcp:tools`, `email`, `profile` as Defaults; `openid` requested by OIDC flow |
| Redirect URI | copy the **exact current URL generated by ChatGPT** |

### Redirect URI — important operational rule

Do not hardcode an old provider callback.

The successful ChatGPT custom-plugin flow generated a connector-specific callback with the pattern:

```text
https://chatgpt.com/connector/oauth/<connector-id>
```

The operator copied the exact value shown in **Configurações avançadas de OAuth** into Keycloak `Valid redirect URIs`.

Rules:

- exact match;
- no production wildcard;
- do not assume historical `connector_platform_oauth_redirect` values remain current;
- do not reuse GPT Actions callbacks such as `/aip/g-.../oauth/callback`;
- after recreating/re-registering a connector, re-read the provider-generated callback.

The exact connector id is operational/provider configuration and is intentionally not hardcoded in repository rules.

## ChatGPT registration flow that worked

1. Enable ChatGPT Developer Mode for the operator account/workspace.
2. Create a custom Plugin/App using the public MCP URL:

   ```text
   https://minhadelpi.com.br/apps/api-delpi/mcp
   ```

3. Authentication: OAuth.
4. Open advanced OAuth settings and verify discovered issuer/endpoints/resource.
5. Choose **Cliente OAuth definido pelo usuário** — not DCR/CIMD for this proven platform configuration.
6. Configure:
   - Client ID `mcp-api-delpi`;
   - client secret directly from Keycloak to provider configuration; never repo/chat/docs/log;
   - token endpoint authentication `client_secret_post`;
   - default scopes `openid`, `profile`, `email`, `mcp:tools`;
   - resource exact MCP URL.
7. Copy the provider-generated return URL into Keycloak and save the client.
8. Create/reconnect the Plugin.
9. After deployment or auth/metadata changes, use **Reconnect** when needed and refresh Plugin actions.
10. Acceptance evidence: ChatGPT shows the connection as connected and lists exactly the expected tool `search_products`.

## Why DAVI needs `mcp:tools` while TÉO/VISTA legacy bridges did not

DAVI is a remote MCP resource. Its token must be bound to the MCP resource URL in addition to the shared DELPI platform audience.

TÉO/VISTA historical GPT Actions bridges use their own HTTP/OpenAPI action contract and OAuth shape; they do not automatically inherit the DAVI MCP resource-binding scope.

Do not mechanically add `mcp:tools` or the DAVI resource audience to legacy GPT Actions clients. Reuse the **principle** (end-user OAuth + backend AuthZ), not product-specific token bindings.

## Product Master V1 boundary

`search_products` is read-only and externally projects only the approved fields:

```text
product_code
description
group_category
```

`customer_reference` and all non-allowlisted DTO fields are denied by default.

No stock, pricing, supplier, customer, sales, invoices, finance, SQL, generic proxy, writes, service account, or GPT-local RBAC are part of DAVI V1.

## MCP tool contract — PLUGIN-006 / 006A

Canonical MCP schema owner:

```text
app/interface/mcp/schemas.py
```

Application remains framework/transport independent; the temporary Pydantic schema placement under `application/external_capabilities` was corrected as `EXECUTION_DRIFT` in PLUGIN-006A.

`tools/list` for `search_products` advertises:

| Surface | Contract |
|---|---|
| Input `page` | integer, default `1`, minimum `1` |
| Input `page_size` | integer, default `50`, minimum `1`, maximum `50` |
| Input shape | flat `code` / `description` / `group_code` / `page` / `page_size`; `additionalProperties: false` |
| Output | typed page with `items[]` (`product_code`, `description`, `group_category`) + `page` / `page_size` / `total` / `total_pages` |
| Invalid args | safe `VALIDATION_ERROR` / `Invalid search parameters.` — no raw Pydantic/framework leakage |

### Deployment / live acceptance

Hardened contract deployment accepted on:

```text
DEPLOYED_SHA = d0c22a5cff5bfab0953a9b6d9f7047701b7ca79e
```

Observed after deployment:

```text
health = PASS
/mcp no-redirect = PASS
ChatGPT Origin = PASS
protected-resource metadata = PASS
container tools/list input bounds = PASS
container typed output schema = PASS
safe validation error = PASS
ChatGPT refreshed input schema = PASS
```

Provider UI did not visibly render the typed output schema during the observed action-details view, so:

```text
OUTPUT_SCHEMA_RUNTIME = PASS
OUTPUT_SCHEMA_UI = INCONCLUSIVE
```

Live business results nonetheless matched the approved output projection.

## Authenticated live Product Master acceptance

Authenticated DAVI calls were proven for:

```text
code = 10080022
→ one authoritative product result
→ only product_code / description / group_category

description = TERM. OLHAL M5
→ successful paginated result

group_code = 1008
→ successful paginated result
```

No `customer_reference`, stock, price, supplier, customer or finance fields were returned.

## Workspace Agent DAVI consumer

The Agent Studio layer is documented separately in:

- [openai-workspace-agent-davi.md](./openai-workspace-agent-davi.md)

Current private-development proof:

```text
DAVI app attached to agent = PASS
app auth mode = End-user account
product 10080022 preview = PASS
description search preview = PASS
unsupported stock/price guard = PASS
second-user identity isolation = PENDING
agent wider publication = PENDING
```

No new Keycloak client, OAuth scopes or backend permission were created for the Agent. The Agent consumes the same governed DAVI app/MCP connection.

## Evidence ladder

Do not collapse these into one `PASS`:

```text
SOURCE IMPLEMENTATION
LOCAL TEST
PUBLIC HTTP
OAUTH DISCOVERY
OAUTH USER CONNECTION
MCP INITIALIZE / TOOL DISCOVERY
AUTHENTICATED TOOL CALL
PROVIDER AGENT PREVIEW
BUSINESS AUTHZ NEGATIVE
PRODUCTION / WIDER PUBLICATION
```

Current operator/provider evidence (2026-09-16):

```text
DEPLOY_SMOKE = PASS
CHATGPT_OAUTH_CONNECTION = PASS
MCP_TOOL_DISCOVERY = PASS
TOOL_INVENTORY = search_products only
INPUT_SCHEMA_LIVE = PASS
OUTPUT_SCHEMA_RUNTIME = PASS
AUTHENTICATED_SEARCH_PRODUCTS = PASS
LIVE_FIELD_ALLOWLIST = PASS
DAVI_AGENT_PRIVATE_PREVIEW = PASS
BUSINESS_AUTHZ_NEGATIVE = PENDING
SECOND_USER_IDENTITY_PROOF = PENDING
MCP_RATE_POLICY = PENDING_OWNER_DECISION
WIDER_PUBLICATION = BLOCKED_BY_PENDING_GATES
```

## Rate limit

Gateway `location ^~ /apps/api-delpi/` has no proven MCP-specific `limit_req` policy.

```text
MCP_RATE_POLICY = PENDING_OWNER_DECISION
```

Rate policy belongs to the gateway owner; do not invent a domain/application limiter to close this gap.

## Plugin package

`api-delpi/integrations/openai-plugin/` remains the versioned package boundary.

Publication metadata such as homepage/privacy/terms may affect wider directory/workspace publication but does not replace MCP runtime/OAuth acceptance.

## Next capability expansion

DAVI capability growth must be contract-first and capability-by-capability.

Before adding any new tool, prove:

```text
owner
source of truth
real consumer/use case
READ | PREPARE | ACT classification
input contract
output allowlist
AuthN/AuthZ
idempotency/OCC/postcondition if write
observability/audit
tests
deploy evidence
provider discovery
positive + negative AuthZ acceptance
```

Do not expose stock, pricing, BOM, production, suppliers, customers, finance or writes merely by adding fields/endpoints to MCP. Each is a separate security/product decision.
