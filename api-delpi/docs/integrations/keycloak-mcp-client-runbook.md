# Keycloak runbook — API DELPI MCP / DAVI resource audience binding

> **Specialist brand:** DAVI — Especialista em Dados e Informações DELPI  
> **Technical client id remains:** `mcp-api-delpi` (do not rename to `mcp-davi`)

> **KEYCLOAK_CONFIG = APPLIED_EVALUATE_PROVEN** on Keycloak 26.0.7.  
> ChatGPT OAuth connection and MCP tool discovery were subsequently proven after PLUGIN-005 deployment.  
> Vendor note: Keycloak 26.0.7 does not natively provide the required RFC8707-style `resource` → token audience binding used here; the platform uses client scope + Audience mapper.

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
| Do not reuse | `delpi-central`, Portal public clients, `chatgpt-*` GPT Actions bridges, `mcp-tv-dashboard` |
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
- recreating the connector may generate a new callback, so re-read the provider UI.

The exact connector id is provider configuration and must not be committed.

## Client scope `mcp:tools`

1. Create Client Scope `mcp:tools`.
2. Protocol: `openid-connect`.
3. Mapper → **Audience**:
   - Name: `mcp-api-delpi-resource-audience`
   - Included Custom Audience: `https://minhadelpi.com.br/apps/api-delpi/mcp` (**exact**)
   - Add to access token: ON
4. Assign `mcp:tools` to client `mcp-api-delpi` as **Default** for the current DAVI configuration.

This scope has two externally relevant postconditions:

```text
JWT scope contains mcp:tools
JWT aud contains https://minhadelpi.com.br/apps/api-delpi/mcp
```

Do not treat `mcp:tools` as business authorization.

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
mcp:tools        # aud → exact MCP resource; appears in JWT scope
```

OIDC requests `openid` through the authorization flow.

## Evaluate proof

Keycloak Admin Console → Clients → `mcp-api-delpi` → Client scopes → Evaluate produced a token with:

```text
aud includes:
  - delpi-central
  - https://minhadelpi.com.br/apps/api-delpi/mcp
  - account

scope:
  - openid
  - email
  - profile
  - mcp:tools
```

Extra legitimate audiences such as `account` are acceptable. Membership of both required audiences is what matters.

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
9. After successful OAuth, ChatGPT must show the connected account and list the MCP tool `search_products`.

## Proof after configuration

### Positive OAuth/resource proof

Authorization Code + PKCE as a real DELPI user must produce a token whose claims satisfy:

```text
iss = https://minhadelpi.com.br/auth/realms/delpi
aud includes delpi-central
aud includes https://minhadelpi.com.br/apps/api-delpi/mcp
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

## Legacy specialists

Do not mechanically copy the DAVI `mcp:tools` scope to TÉO/VISTA legacy GPT Actions clients. DAVI requires MCP-resource audience binding because it is a remote MCP resource; legacy GPT Actions bridges have a different external contract.

## Secrets

Never commit or paste:

- client secret;
- Keycloak admin credentials;
- access/refresh tokens;
- authorization codes;
- authenticated cookies.
