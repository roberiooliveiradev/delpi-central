# Keycloak runbook — API DELPI MCP / DAVI resource audience binding

> **Specialist brand:** DAVI — Especialista em Dados e Informações DELPI  
> **Technical client id remains:** `mcp-api-delpi` (do not rename to `mcp-davi`)

> **KEYCLOAK_CONFIG = APPLIED_EVALUATE_PROVEN** (PLUGIN-004A live Evaluate on Keycloak 26.0.7).  
> ChatGPT connector end-to-end remains a separate go-live proof.  
> Vendor: [Keycloak MCP AuthZ Server](https://www.keycloak.org/securing-apps/mcp-authz-server) — Keycloak does **not** natively process RFC 8707 `resource` → `aud` on 26.0.7; use scope + Audience mapper workaround.

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

JWT ``scope`` claim (proven Evaluate output):

```text
openid email profile mcp:tools
```

Note: Keycloak client scope ``audience-delpi`` remains **Default** on the client and is what causes ``aud`` to include ``delpi-central``. It typically does **not** appear in the JWT ``scope`` string and must **not** be required by the MCP resource server as a scope claim.

Exact string match for the MCP URL — **no** trailing slash.

## Client

| Field | Value |
|---|---|
| Client ID | `mcp-api-delpi` |
| Mode | `PREDEFINED` |
| Do not reuse | `delpi-central`, Portal public clients, `chatgpt-*` GPT Actions bridges, `mcp-tv-dashboard` |
| Capability type | OpenID Connect |
| Access type | Confidential (Client Id and Secret) — matches ChatGPT predefined connector |
| Standard Flow | ON |
| Direct Access Grants | **OFF** |
| Service Accounts | **OFF** |
| Implicit | OFF |
| PKCE | S256 required |
| Valid redirect URIs | `https://chatgpt.com/connector_platform_oauth_redirect` (proven ChatGPT connector redirect; not GPT Actions `/aip/g-.../oauth/callback`) |
| Web origins | as required by ChatGPT connector |

## Client scope `mcp:tools`

1. Create Client Scope `mcp:tools` (Optional).
2. Protocol: `openid-connect`.
3. Mapper → **Audience**:
   - Name: `mcp-api-delpi-resource-audience`
   - Included Custom Audience: `https://minhadelpi.com.br/apps/api-delpi/mcp` (**exact**)
   - Add to access token: ON
4. Assign scope `mcp:tools` to client `mcp-api-delpi` (Optional or Default — prefer **Default** so ChatGPT always receives the binding when using this client).

## Keep existing `audience-delpi`

Do **not** remove or replace `audience-delpi`.  
It continues to map `aud` → `delpi-central` for shared api-delpi JWT validation.

Assign `audience-delpi` (Default) on `mcp-api-delpi` as for other platform clients.

It is an **internal Keycloak audience client scope**, not a required MCP JWT `scope` claim.

## Default client scopes on `mcp-api-delpi`

```text
openid (basic)
profile
email
audience-delpi   # aud → delpi-central (may be absent from JWT scope string)
mcp:tools        # aud → MCP resource URL (appears in JWT scope)
```

## Proof after configuration

1. Authorization Code + PKCE as a real DELPI user (no password grant / client_credentials).
2. Decode access token (claims only — never paste secrets):

```json
{
  "iss": "https://minhadelpi.com.br/auth/realms/delpi",
  "aud": ["delpi-central", "https://minhadelpi.com.br/apps/api-delpi/mcp", "account"],
  "scope": "openid email profile mcp:tools"
}
```

(`aud` may be string or array — membership is what matters. Extra audiences such as `account` are fine.)

3. Positive: `Authorization: Bearer <token>` against `/apps/api-delpi/mcp` is not rejected for audience/scope.
4. Negative: token with only `aud=delpi-central` (no MCP URL) → `401` on `/mcp`.

## Discovery note

After creating `mcp:tools`, it will **not** automatically appear in realm `scopes_supported` until Keycloak lists it; api-delpi advertises it in protected-resource metadata regardless.

## Secrets

Never commit client secret, admin password, or tokens.
