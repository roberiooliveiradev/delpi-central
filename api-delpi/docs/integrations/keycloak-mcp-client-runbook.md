# Keycloak runbook — API DELPI MCP / DAVI resource audience binding

> **Specialist brand:** DAVI — Especialista em Dados e Informações DELPI
> **Technical client id remains:** `mcp-api-delpi` (do not rename to `mcp-davi`)

> **KEYCLOAK_CONFIG = APPLIED_EVALUATE_PROVEN** on Keycloak 26.0.7.
> ChatGPT OAuth connection and MCP tool discovery were subsequently proven after PLUGIN-005 deployment.
> **MCP RESOURCE ISOLATION = PROVEN / PASS** (2026-09-17): shared `mcp:tools` no longer carries per-MCP Audience mappers.
> Vendor note: Keycloak 26.0.7 does not natively provide the required RFC8707-style `resource` → token audience binding used here; the platform uses **dedicated** Audience mapper on the MCP client (or dedicated client scope), plus shared generic scope `mcp:tools`.
> Shared onboarding: [`docs/10-guias-operacionais/mcp-chatgpt-plugin-onboarding-runbook.md`](../../../docs/10-guias-operacionais/mcp-chatgpt-plugin-onboarding-runbook.md).

## Goal

Access tokens used at:

```text
https://minhadelpi.com.br/apps/api-delpi/mcp
```

must contain **both** audiences:

```text
delpi-central
https://minhadelpi.com.br/apps/api-delpi/mcp
```

and must **not** contain another MCP resource (ex.: `…/transformometro-api/mcp`).

JWT `scope` claim:

```text
openid email profile mcp:tools
```

Keycloak client scope `audience-delpi` remains **Default** and causes `aud` to include `delpi-central`. It does not need to appear in the JWT `scope` string and the MCP resource server must not require it as a scope claim.

The MCP resource URL uses an exact string match with **no trailing slash**.

## Client

| Field | Value |
|---|---|
| Client ID | `mcp-api-delpi` |
| Mode | `PREDEFINED` / user-defined OAuth client in ChatGPT |
| Do not reuse | `delpi-central`, Portal public clients, `chatgpt-*` GPT Actions bridges, `mcp-transformometro`, `mcp-tv-dashboard` |
| Capability type | OpenID Connect |
| Access type | Confidential (`Client Id and Secret`) |
| Token endpoint auth | `client_secret_post` in the successful ChatGPT connector configuration |
| Standard Flow | ON |
| Direct Access Grants | **OFF** |
| Service Accounts | **OFF** |
| Implicit | OFF |
| PKCE | S256 required |
| Web origins | leave empty unless an explicit Keycloak/browser requirement is proven; MCP transport Origin allowlist is a separate control |

## Redirect URI — use the provider-generated current value

Do **not** hardcode historical callback URLs.

The successful ChatGPT custom-plugin flow generated a connector-specific return URL with the pattern:

```text
https://chatgpt.com/connector/oauth/<connector-id>
```

Operational procedure:

1. ChatGPT → custom Plugin/App → OAuth → **Configurações avançadas de OAuth**.
2. Select **Cliente OAuth definido pelo usuário**.
3. Copy the exact **URL de retorno** shown by ChatGPT.
4. Keycloak → Clients → `mcp-api-delpi` → Settings → `Valid redirect URIs`.
5. Replace bootstrap/historical callbacks with the exact current provider-generated URL.
6. Save.

Rules:

- exact URI only in production;
- no `https://chatgpt.com/*` wildcard after bootstrap;
- do not assume `https://chatgpt.com/connector_platform_oauth_redirect` is current;
- do not use GPT Actions callbacks such as `/aip/g-.../oauth/callback`;
- do not reuse TÉO (or any other Plugin) callback;
- recreating the connector may generate a new callback, so re-read the provider UI.

The exact connector id is provider configuration and must not be committed.

## Shared client scope `mcp:tools`

`mcp:tools` is a **shared generic** OAuth scope reused by authorized MCP clients (DAVI, TÉO, futuros).

```text
mcp:tools
≠
DAVI-only resource binding
≠
business authorization
```

Correct configuration:

1. Create (once) Client Scope `mcp:tools` if missing — Protocol `openid-connect`.
2. Assign `mcp:tools` to client `mcp-api-delpi` as **Default**.
3. **Do not** place DAVI (or any other) resource Audience mapper inside the shared `mcp:tools` scope.

### STALE pattern (do not reintroduce)

```text
client scope mcp:tools
→ Audience mapper mcp-api-delpi-resource-audience
→ Included Custom Audience = https://minhadelpi.com.br/apps/api-delpi/mcp
```

That pattern caused **cross-MCP audience leakage** (TÉO tokens also received `…/api-delpi/mcp`). Corrected in production 2026-09-17 by moving the resource Audience mapper off the shared scope onto the dedicated DAVI client configuration.

```text
KEYCLOAK SCOPE DESCRIPTION CLEANUP = TO_INVENTORY
```

(Admin UI description text may still imply DAVI-only binding; functional isolation is PROVEN. Update description when ops touch the scope.)

## Dedicated DAVI resource audience

On client `mcp-api-delpi` (client-level Audience mapper **or** a dedicated client scope owned by this client only):

| Field | Value |
|---|---|
| Mapper type | Audience |
| Name (example) | `mcp-api-delpi-resource-audience` |
| Included Custom Audience | `https://minhadelpi.com.br/apps/api-delpi/mcp` (**exact**) |
| Add to access token | ON |

Postconditions:

```text
JWT scope contains mcp:tools
JWT aud contains https://minhadelpi.com.br/apps/api-delpi/mcp
JWT aud contains delpi-central
JWT aud does NOT contain https://minhadelpi.com.br/apps/transformometro-api/mcp
```

## Keep existing `audience-delpi`

Do **not** remove or replace `audience-delpi`.

It maps:

```text
audience-delpi client scope
→ aud contains delpi-central
```

It is an internal Keycloak audience mechanism, not a required MCP JWT `scope` claim.

## Default client scopes on `mcp-api-delpi`

The proven effective configuration contains:

```text
profile
email
audience-delpi   # aud → delpi-central; may be absent from JWT scope string
mcp:tools        # shared generic scope string only; NOT the resource audience mapper
```

OIDC requests `openid` through the authorization flow.

## Evaluate proof

Keycloak Admin Console → Clients → `mcp-api-delpi` → Client scopes → Evaluate produced a token with:

```text
azp = mcp-api-delpi

aud includes:
  - delpi-central
  - https://minhadelpi.com.br/apps/api-delpi/mcp
  - account

aud does NOT include:
  - https://minhadelpi.com.br/apps/transformometro-api/mcp

scope:
  - openid
  - email
  - profile
  - mcp:tools
```

Extra legitimate audiences such as `account` are acceptable. Membership of both required audiences **and isolation from sibling MCP resources** is what matters.

## ChatGPT registration procedure that succeeded

1. Enable ChatGPT Developer Mode.
2. Create custom Plugin/App.
3. Server URL:

   ```text
   https://minhadelpi.com.br/apps/api-delpi/mcp
   ```

4. Authentication: OAuth.
5. Advanced OAuth:
   - method: **Cliente OAuth definido pelo usuário**;
   - client id: `mcp-api-delpi`;
   - client secret: copied directly from Keycloak into ChatGPT, never into repo/chat/docs/log;
   - token endpoint auth: `client_secret_post`;
   - scopes: `openid`, `profile`, `email`, `mcp:tools`;
   - resource: exact MCP URL.
6. Copy the ChatGPT-generated return URL into Keycloak.
7. Save Keycloak client.
8. Create or **Reconnect** the ChatGPT Plugin.
9. After successful OAuth, ChatGPT must show the connected account and list the MCP tools:
   `search_products`, `discover_delpi_information`, `execute_delpi_information`.

## api-delpi env — DAVI candidate HMAC (DAVI-DYNAMIC-READ-002)

Opaque discovery→execute candidate tokens are HMAC-signed.

| Variable | Required? | Notes |
|---|---|---|
| `DAVI_CANDIDATE_HMAC_SECRET` | **Preferred for production** | Dedicated secret; never log |
| `API_DELPI_JWT_SECRET` / `JWT_SECRET` | Compatibility fallback | Used only when dedicated secret is empty |

Deploy operators should set `DAVI_CANDIDATE_HMAC_SECRET` in the api-delpi environment (compose already wires `${DAVI_CANDIDATE_HMAC_SECRET:-}`). Do not commit secret values. Rotating the dedicated secret invalidates outstanding candidate tokens (TTL is short).

## Proof after configuration

### Positive OAuth/resource proof

Authorization Code + PKCE as a real DELPI user must produce a token whose claims satisfy:

```text
iss = https://minhadelpi.com.br/auth/realms/delpi
azp = mcp-api-delpi
aud includes delpi-central
aud includes https://minhadelpi.com.br/apps/api-delpi/mcp
aud does NOT include https://minhadelpi.com.br/apps/transformometro-api/mcp
scope includes openid profile email mcp:tools
```

Never paste the raw JWT, refresh token, authorization code, cookies, or client secret into reports.

### Negative resource-binding proof

A token with only:

```text
aud = delpi-central
```

and no exact MCP audience must be rejected on `/apps/api-delpi/mcp`.

### Business AuthZ proof

OAuth success does not prove Product Master authorization. `search_products` must still pass the canonical backend business authorization for the authenticated DELPI user.

## MCP routing / Origin operational prerequisites

Keycloak can be perfectly configured while ChatGPT still fails after OAuth. Before changing Keycloak again, verify the MCP runtime:

```text
POST /apps/api-delpi/mcp
→ no 307/308 redirect

Origin: https://chatgpt.com
→ not 403 Invalid Origin
```

FastAPI CORS and FastMCP DNS-rebinding Origin validation are separate controls.

If the provider returns after OAuth with a generic connection error, inspect token exchange and MCP initialize/tools-list evidence before changing scopes, redirect, secret, or PKCE.

## Discovery note

Realm `scopes_supported` and MCP protected-resource `scopes_supported` are distinct surfaces.

Keycloak may advertise internal scopes such as `audience-delpi`; the MCP protected resource advertises only the scopes the resource server requires in JWT `scope`:

```text
openid profile email mcp:tools
```

## Sibling specialists (TÉO)

TÉO MCP uses the **same** shared `mcp:tools` and the **same** isolation rule with dedicated audience:

```text
https://minhadelpi.com.br/apps/transformometro-api/mcp
```

Do not mechanically copy GPT Actions OAuth clients. Do not put TÉO audience into shared `mcp:tools`.

See: `transformometro-api/docs/integrations/keycloak-mcp-client-runbook.md`.

## Secrets

Never commit or paste:

- client secret;
- Keycloak admin credentials;
- access/refresh tokens;
- authorization codes;
- authenticated cookies.
