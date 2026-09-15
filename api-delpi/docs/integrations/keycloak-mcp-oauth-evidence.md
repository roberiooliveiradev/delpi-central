# Keycloak / MCP OAuth evidence — API DELPI

> Captured during API-DELPI-PLUGIN-002; updated PLUGIN-003 / **PLUGIN-004A**.  
> **Documentation does not prove ChatGPT end-to-end go-live.**

## Source

| Item | Value |
|---|---|
| Observed at | 2026-09-15 |
| Discovery URL | `https://minhadelpi.com.br/auth/realms/delpi/.well-known/openid-configuration` |
| HTTP | 200 |
| Keycloak image (docker) | `quay.io/keycloak/keycloak:26.0.7` |
| Local gateway `/auth/` | 502 at capture time (prod public host used) |
| Vendor MCP guide | https://www.keycloak.org/securing-apps/mcp-authz-server |

No secrets were retrieved or committed.

## Discovery fields (non-secret)

| Field | Observed |
|---|---|
| issuer | `https://minhadelpi.com.br/auth/realms/delpi` |
| authorization_endpoint | `.../protocol/openid-connect/auth` |
| token_endpoint | `.../protocol/openid-connect/token` |
| jwks_uri | `.../protocol/openid-connect/certs` |
| userinfo_endpoint | present |
| registration_endpoint | `.../clients-registrations/openid-connect` |
| code_challenge_methods_supported | `plain`, **`S256`** |
| token_endpoint_auth_methods_supported | `private_key_jwt`, `client_secret_basic`, `client_secret_post`, `tls_client_auth`, `client_secret_jwt` (**no `none`**) |
| scopes_supported (Keycloak realm) | includes `openid`, `profile`, `email`, `offline_access`, `audience-delpi`, `roles`, … |
| authorization_response_iss_parameter_supported | `true` |
| client_id_metadata_document_supported | **absent** |
| `.well-known/oauth-authorization-server` (realm) | HTTP 404 |

Note: Keycloak realm `scopes_supported` listing `audience-delpi` is **not** the same as the MCP protected-resource `scopes_supported`. The MCP resource server advertises only JWT `scope` claim requirements: `openid`, `profile`, `email`, `mcp:tools`.

## Vendor contract revalidation (PLUGIN-003)

| Claim | Status |
|---|---|
| Keycloak natively processes RFC8707 `resource` → `aud` on 26.0.7 | **DISPROVEN** (vendor docs: not implemented; experimental later) |
| Official workaround = Optional client scope + Audience mapper | **PROVEN** (vendor MCP guide) |
| Example scope name `mcp:tools` | **PROVEN** (vendor docs) |
| `VENDOR_CONTRACT_DRIFT` | **NO** — workaround still current |

## Verdict matrix

| Probe | Status | Notes |
|---|---|---|
| PKCE_S256 | **PROVEN** | advertised in discovery; client configured S256 |
| OFFLINE_ACCESS | **PROVEN** (advertised) | scope listed; client enablement not proven |
| CIMD | **DISPROVEN** | not advertised |
| DCR | **INCONCLUSIVE** | registration endpoint present; not exercised |
| PREDEFINED_CLIENT | **SUPPORTED** | chosen mode |
| RESOURCE_PARAMETER | **IGNORED_BY_KEYCLOAK** | send anyway; Keycloak does not bind it natively |
| RESOURCE_TO_TOKEN_AUDIENCE | **WORKAROUND_APPLIED** | `mcp:tools` Audience mapper on `mcp-api-delpi` |
| ISSUER_IDENTIFICATION | **PROVEN** | |
| EVALUATE_TOKEN_SHAPE | **PROVEN** | PLUGIN-004A live Evaluate (below) |

## Client mode (PLUGIN-004A)

```text
MCP_CLIENT_MODE = PREDEFINED
MCP_CLIENT_ID = mcp-api-delpi
CLIENT_AUTH = client_id + client_secret
PKCE = S256
REDIRECT_URI = https://chatgpt.com/connector_platform_oauth_redirect
KEYCLOAK_CLIENT_SCOPES_DEFAULT = audience-delpi, mcp:tools, email, profile
KEYCLOAK_CONFIG = APPLIED_EVALUATE_PROVEN
CHAT_GPT_E2E = NOT_PROVEN
```

Operator reference: [keycloak-mcp-client-runbook.md](./keycloak-mcp-client-runbook.md).

## Live Evaluate token shape (PLUGIN-004A) — PROVEN

Keycloak Admin Console → Clients → `mcp-api-delpi` → Evaluate produced:

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

**Important:** `audience-delpi` does **not** appear in the JWT `scope` claim.  
That is expected: `audience-delpi` is an internal Keycloak client scope / audience mapper whose postcondition is `aud` contains `delpi-central`, not a string in `scope`.

## Target token validation mapping

```text
Keycloak client scopes (Default): audience-delpi + mcp:tools + email + profile
→ JWT scope typically: openid email profile mcp:tools
  (audience-delpi ABSENT from scope string — expected / proven)
→ aud includes delpi-central (via audience-delpi mapper)
→ aud includes https://minhadelpi.com.br/apps/api-delpi/mcp (via mcp:tools mapper)
→ api-delpi MCP transport:
     validate_token → aud contains delpi-central
     + MCP aud exact membership
     + JWT scope requires openid profile email mcp:tools
     (does NOT require audience-delpi in scope)
→ ENGINEERING_LMP_ACCESS for search_products (RBAC, not OAuth)
```

## Rate limit

`location ^~ /apps/api-delpi/` has **no** `limit_req`.

```text
MCP_RATE_POLICY = PENDING_OWNER_DECISION
```
