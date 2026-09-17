# Keycloak runbook — Transformômetro MCP / TÉO resource audience binding

> **Specialist brand:** TÉO — Especialista em Transformação Digital  
> **Technical client id:** `mcp-transformometro` (do not rename to `mcp-teo` / do not reuse `chatgpt-transformometro`)  
> **Surface:** FULL CRUD (READ + PREPARE + ACT) — not DAVI READ-only.

> Status: **DOCUMENTED — APPLY IN PRODUCTION** (ops). Code expects this contract; live Keycloak apply is manual.

## Goal

Access tokens used at:

```text
https://minhadelpi.com.br/apps/transformometro-api/mcp
```

must contain **both** audiences:

```text
delpi-central
https://minhadelpi.com.br/apps/transformometro-api/mcp
```

JWT `scope` claim:

```text
openid email profile mcp:tools
```

Keycloak client scope `audience-delpi` remains **Default** and causes `aud` to include `delpi-central`. It does not need to appear in the JWT `scope` string.

MCP resource URL uses exact string match with **no trailing slash**.

## Client

| Field | Value |
|---|---|
| Client ID | `mcp-transformometro` |
| Mode | `PREDEFINED` / user-defined OAuth client in ChatGPT |
| Do not reuse | `delpi-central`, Portal clients, `chatgpt-transformometro`, `mcp-api-delpi` |
| Capability type | OpenID Connect |
| Access type | Confidential (`Client Id and Secret`) |
| Token endpoint auth | `client_secret_post` (same proven pattern as DAVI) |
| Standard Flow | ON |
| Direct Access Grants | **OFF** |
| Service Accounts | **OFF** |
| Implicit | OFF |
| PKCE | S256 required |

## Redirect URI

Do **not** hardcode historical GPT Actions callbacks (`/aip/g-.../oauth/callback`).

1. ChatGPT → custom Plugin/App → OAuth → advanced settings.
2. Select user-defined OAuth client.
3. Copy exact **return URL** (`https://chatgpt.com/connector/oauth/<connector-id>`).
4. Keycloak → Clients → `mcp-transformometro` → Valid redirect URIs → paste exact URI.
5. No `https://chatgpt.com/*` wildcard after bootstrap.

## Client scope `mcp:tools`

1. Reuse existing Client Scope `mcp:tools` if already created for DAVI **or** create equivalent.
2. For **this** client, ensure an Audience mapper (or client-specific mapper) with:
   - Included Custom Audience: `https://minhadelpi.com.br/apps/transformometro-api/mcp` (**exact**)
   - Add to access token: ON
3. Assign `mcp:tools` to `mcp-transformometro` as **Default**.

Postconditions:

```text
JWT scope contains mcp:tools
JWT aud contains https://minhadelpi.com.br/apps/transformometro-api/mcp
JWT aud contains delpi-central
```

`mcp:tools` is **not** business authorization. Backend RBAC remains authority.

## Keep `audience-delpi`

Do not remove. It maps `aud` → `delpi-central`.

## Default client scopes on `mcp-transformometro`

```text
profile
email
audience-delpi
mcp:tools
```

## ChatGPT Plugin registration

1. Developer Mode → custom Plugin/App.
2. Server URL:

   ```text
   https://minhadelpi.com.br/apps/transformometro-api/mcp
   ```

3. OAuth: client `mcp-transformometro` + secret from Keycloak Credentials.
4. Discover tools (expect 20 FULL CRUD tools).
5. Smoke: READ (`get_catalog`) → PREPARE (`validate_improvement_package`) → ACT only after confirmation.

## Bridge policy

| Client | Surface | Status |
|---|---|---|
| `chatgpt-transformometro` | Custom GPT Actions `/gpt-actions/v1` | **LEGACY_TRANSITIONAL_BRIDGE** — keep until MCP parity proven live |
| `mcp-transformometro` | Plugin / Agent MCP `/mcp` | **TARGET** for agents |

## Env (API)

Optional override:

```text
MCP_RESOURCE_URL=https://minhadelpi.com.br/apps/transformometro-api/mcp
PUBLIC_BASE_URL=https://minhadelpi.com.br
KEYCLOAK_ISSUER=<realm issuer>
```

## Reference

- Mirror proven DAVI runbook: `api-delpi/docs/integrations/keycloak-mcp-client-runbook.md`
- Product MCP docs: `transformometro-api/docs/integrations/openai-plugin-mcp.md`
