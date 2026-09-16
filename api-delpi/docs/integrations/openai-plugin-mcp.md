# DAVI / API DELPI — OpenAI Plugin + MCP

> **Documentation does not prove runtime.** Runtime/provider evidence is recorded separately and must be revalidated after material changes.

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
| Strategic target | OpenAI Plugin / ChatGPT App → remote MCP → semantic capability → existing use case |
| Legacy | `/gpt-actions/v1` = `LEGACY_TRANSITIONAL`; do not expand by default |
| V1 business tool | `search_products` (read-only Product Master) |
| MCP auth model | Transport requires OAuth |
| Resource audience | JWT `aud` must include exact MCP resource **and** `delpi-central` |
| Keycloak client | `mcp-api-delpi` — predefined/user-defined OAuth client |
| ChatGPT connection | **PROVEN** on 2026-09-16 after PLUGIN-005 deploy/reconnect |
| Tool discovery | **PROVEN** — ChatGPT UI lists `search_products` |
| Live business invocation | `PENDING` until an authenticated `search_products` result is captured |
| Rate limit | `MCP_RATE_POLICY = PENDING_OWNER_DECISION` |

## Architecture

```text
ChatGPT / Codex
  → OpenAI Plugin / App
  → OAuth Authorization Code + PKCE
  → Keycloak end-user identity
  → MCP Streamable HTTP  /apps/api-delpi/mcp
  → interface/mcp adapter
  → application/external_capabilities
  → SearchProducts use case
  → canonical backend AuthZ
  → authoritative source
```

The Plugin/MCP adapter does not own Product Master, identity, RBAC, persistence, or business rules.

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

It is **not** a required string in the JWT `scope` claim. Keycloak 26.0.7 Evaluate proved the access-token scope as:

```text
openid email profile mcp:tools
```

Do not modify Keycloak merely to make an internal client-scope name appear in JWT `scope`. Validate the security postcondition instead.

### MCP resource binding

Keycloak 26.0.7 did not provide the required native `resource` → token-audience binding for this integration. The proven platform configuration uses:

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
| Client scopes | `audience-delpi`, `mcp:tools`, `email`, `profile` as appropriate Defaults; `openid` requested by OIDC flow |
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
- do not assume the older `connector_platform_oauth_redirect` value;
- do not reuse GPT Actions callbacks such as `/aip/g-.../oauth/callback`;
- after recreating/re-registering a connector, re-read the current provider-generated callback.

The exact connector id is operational/provider configuration and is intentionally not hardcoded in repository rules.

## ChatGPT registration flow that worked

1. Enable ChatGPT Developer Mode for the operator account/workspace.
2. Create a custom Plugin/App using the public MCP URL:

   ```text
   https://minhadelpi.com.br/apps/api-delpi/mcp
   ```

3. Authentication: OAuth.
4. Open advanced OAuth settings and verify discovered issuer/endpoints/resource.
5. Choose **Cliente OAuth definido pelo usuário** — not DCR/CIMD for this platform configuration.
6. Configure:
   - Client ID `mcp-api-delpi`;
   - client secret directly from Keycloak to provider configuration; never repo/chat/docs/log;
   - token endpoint authentication `client_secret_post`;
   - default scopes `openid`, `profile`, `email`, `mcp:tools`;
   - resource exact MCP URL.
7. Copy the connector-specific redirect URL from ChatGPT into Keycloak and save the client.
8. Create/reconnect the Plugin.
9. After deployment or auth/metadata changes, use **Reconnect** and refresh the Plugin details.
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

## MCP tool contract (PLUGIN-006)

Canonical schema owner: `SearchProductsInput` / `SearchProductsOutput` in
`app/application/external_capabilities/product_search_schemas.py`.

`tools/list` for `search_products` must advertise:

| Surface | Contract |
|---|---|
| Input `page` | integer, default `1`, minimum `1` |
| Input `page_size` | integer, default `50`, minimum `1`, maximum `50` |
| Input shape | flat `code` / `description` / `group_code` / `page` / `page_size` — `additionalProperties: false` |
| Output | typed page with `items[]` (`product_code`, `description`, `group_category`) + `page` / `page_size` / `total` / `total_pages` |
| Invalid args | safe `VALIDATION_ERROR` / `Invalid search parameters.` — no Pydantic/framework leakage |

No OAuth, Keycloak, audience, Origin/routing, or `ENGINEERING_LMP_ACCESS` changes in this hardening.

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
BUSINESS AUTHZ NEGATIVE
PRODUCTION
```

Current operator/provider evidence (2026-09-16):

```text
DEPLOY_SMOKE = PASS
CHATGPT_OAUTH_CONNECTION = PASS
MCP_TOOL_DISCOVERY = PASS
TOOL_INVENTORY = search_products only
AUTHENTICATED_SEARCH_PRODUCTS = PENDING
BUSINESS_AUTHZ_NEGATIVE = PENDING
```

## Rate limit

Gateway `location ^~ /apps/api-delpi/` has no proven MCP-specific `limit_req` policy.

```text
MCP_RATE_POLICY = PENDING_OWNER_DECISION
```

Rate policy belongs to the gateway owner; do not invent a domain/application limiter to close this gap.

## Plugin package

`api-delpi/integrations/openai-plugin/` remains the versioned package boundary.

Publication metadata such as homepage/privacy/terms may block wider catalog publication but does not replace MCP runtime/OAuth acceptance.
