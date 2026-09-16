# Keycloak / MCP OAuth evidence — API DELPI

> Captured during API-DELPI-PLUGIN-002 and updated through PLUGIN-005 / DAVI operational activation.  
> **Documentation records evidence; it does not replace revalidation after code/provider/config changes.**

## Source

| Item | Value |
|---|---|
| Initial observed at | 2026-09-15 |
| Operational acceptance update | 2026-09-16 |
| Discovery URL | `https://minhadelpi.com.br/auth/realms/delpi/.well-known/openid-configuration` |
| Keycloak image | `quay.io/keycloak/keycloak:26.0.7` |
| MCP resource | `https://minhadelpi.com.br/apps/api-delpi/mcp` |
| Keycloak client | `mcp-api-delpi` |
| Vendor MCP guide | https://www.keycloak.org/securing-apps/mcp-authz-server |

No secrets, raw tokens, authorization codes, or authenticated cookies are committed here.

## Discovery fields (non-secret)

| Field | Observed |
|---|---|
| issuer | `https://minhadelpi.com.br/auth/realms/delpi` |
| authorization_endpoint | `.../protocol/openid-connect/auth` |
| token_endpoint | `.../protocol/openid-connect/token` |
| jwks_uri | `.../protocol/openid-connect/certs` |
| userinfo_endpoint | present |
| registration_endpoint | present |
| code_challenge_methods_supported | includes **`S256`** |
| token_endpoint_auth_methods_supported | includes `client_secret_post` |
| scopes_supported (realm) | includes `openid`, `profile`, `email`, `offline_access`, `audience-delpi`, roles, etc. |
| client_id_metadata_document_supported | not advertised in observed discovery |

Realm `scopes_supported` and MCP protected-resource `scopes_supported` are separate contracts. The MCP protected resource advertises only the JWT-scope requirements of the MCP resource server:

```text
openid
profile
email
mcp:tools
```

## Vendor contract revalidation

| Claim | Status | Notes |
|---|---|---|
| Keycloak 26.0.7 directly binds the OAuth `resource` parameter to token `aud` for this integration | **DISPROVEN / not used** | Platform uses client scope + Audience mapper |
| `mcp:tools` client scope + Audience mapper can bind the MCP resource audience | **PROVEN** | Applied to `mcp-api-delpi` |
| `audience-delpi` provides `aud=delpi-central` | **PROVEN** | Existing platform audience mechanism |
| `audience-delpi` must appear in JWT `scope` | **DISPROVEN** | Evaluate token omitted it; resource server no longer requires it |

## Keycloak client configuration — proven shape

```text
CLIENT_ID = mcp-api-delpi
CLIENT_MODE = PREDEFINED / user-defined OAuth client in ChatGPT
CLIENT_AUTH = client_id + client_secret
TOKEN_ENDPOINT_AUTH = client_secret_post
STANDARD_FLOW = ON
DIRECT_ACCESS_GRANTS = OFF
SERVICE_ACCOUNTS = OFF
IMPLICIT_FLOW = OFF
PKCE = S256
```

Effective client scopes include:

```text
profile
email
audience-delpi
mcp:tools
```

OIDC authorization requests `openid`.

## Redirect URI evidence

An earlier working assumption used:

```text
https://chatgpt.com/connector_platform_oauth_redirect
```

The actual ChatGPT custom-plugin registration UI later generated a connector-specific return URL with the pattern:

```text
https://chatgpt.com/connector/oauth/<connector-id>
```

The operator copied the exact current provider-generated URL into Keycloak `Valid redirect URIs`, after which the connector proceeded correctly.

Evidence classification:

```text
HISTORICAL_CALLBACK_ASSUMPTION = SUPERSEDED
PROVIDER_GENERATED_EXACT_CALLBACK = PROVEN
```

The connector id is intentionally not recorded because it is provider configuration, can change when the connector is recreated, and is not a reusable platform constant.

## Live Evaluate token shape — PROVEN

Keycloak Admin Console → Clients → `mcp-api-delpi` → Client scopes → Evaluate produced:

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

Extra legitimate audiences such as `account` are acceptable. Required membership is:

```text
delpi-central
https://minhadelpi.com.br/apps/api-delpi/mcp
```

## Token validation mapping

```text
Keycloak client scopes:
  audience-delpi
  mcp:tools
  email
  profile

→ JWT scope:
  openid email profile mcp:tools

→ aud includes delpi-central
→ aud includes exact MCP resource URL

→ api-delpi MCP transport:
     shared JWT validation
     + platform audience
     + exact MCP resource audience
     + scopes openid profile email mcp:tools

→ authenticated DELPI user
→ canonical backend business AuthZ for search_products
```

OAuth scopes/audiences are **not** business RBAC.

## PLUGIN-005 — post-OAuth connection failure diagnosis

Before the runtime fix, two independent blockers were proven after authentication:

| Probe | Status before fix |
|---|---|
| Authenticated `POST /mcp` through FastAPI `Mount("/mcp")` + FastMCP path `/` | **307** → `/mcp/` |
| MCP transport Origin `https://chatgpt.com` / `https://chat.openai.com` | **403 Invalid Origin** |

The first connection attempt could not identify which blocker fired first because production request logs for that timestamp were unavailable. Both were independently reproducible and both prevented MCP initialize/tool discovery.

### Fix

Commit:

```text
55ea8994e56565ae6f08468c2a6005db348f939f
fix(api-delpi): evitar 307 e Origin 403 no MCP do ChatGPT
```

Changes:

1. internal ASGI rewrite of exact `/mcp` to mount-compatible `/mcp/` **without HTTP redirect**;
2. ChatGPT connector Origins added to FastMCP DNS-rebinding transport-security allowlist;
3. regression tests for no redirect and accepted ChatGPT Origins.

The advertised MCP resource remains exactly:

```text
https://minhadelpi.com.br/apps/api-delpi/mcp
```

## Post-deploy acceptance — 2026-09-16

Deployed application SHA used for the accepted smoke:

```text
307db6e05d40ecefb5d0a9e11c86c39e143850f8
```

The PLUGIN-005 fix commit is an ancestor of that deployed SHA.

| Evidence | Status | Notes |
|---|---|---|
| deployment / container recreate | **PASS** | canonical production flow, healthy container |
| `GET /apps/api-delpi/health` | **PASS** | `{"status":"online"}` |
| unauthenticated `/mcp` no-slash | **PASS** | 401, no `Location`, no 307/308 |
| `Origin: https://chatgpt.com` | **PASS** | 401 OAuth challenge, not 403 |
| `Origin: https://chat.openai.com` | **PASS** | 401 OAuth challenge, not 403 |
| protected-resource metadata | **PASS** | exact resource + `openid profile email mcp:tools` |
| ChatGPT reconnect | **PASS** | UI displayed successful connection |
| authenticated account identity in ChatGPT | **PASS** | connector displayed connected DELPI account |
| MCP tool discovery | **PASS** | ChatGPT UI lists `search_products` |
| tool inventory | **PASS** | expected V1 tool visible; no evidence of extra business tools |
| authenticated `search_products` business result | **PENDING** | run product query acceptance separately |
| negative business AuthZ | **PENDING** | requires user without canonical access |

This is the first provider-side evidence that OAuth + MCP initialize/tool discovery succeeded end-to-end.

## Operational lesson: do not debug OAuth by changing Keycloak blindly

A successful or partially successful OAuth flow can still fail during MCP initialize/tool discovery. The proven diagnostic order is:

```text
1. protected-resource metadata
2. provider-generated callback exactness
3. token exchange evidence if available
4. /mcp no-slash routing behavior
5. MCP transport Origin / DNS-rebinding validation
6. JWT platform audience
7. JWT MCP resource audience
8. JWT scopes
9. MCP initialize
10. tools/list
11. business AuthZ
12. business result projection
```

Do not change scopes, redirect, secret, PKCE, or Keycloak mapper by trial-and-error when the failing layer has not been identified.

## Product Master V1 external projection

Approved response projection remains:

```text
product_code
description
group_category
```

Denied by default:

```text
customer_reference
all non-allowlisted DTO fields
```

No stock, price, supplier, customer, finance, SQL, generic proxy, writes, service account, or GPT-local RBAC are part of DAVI V1.

## Rate limit

`location ^~ /apps/api-delpi/` still has no proven MCP-specific `limit_req` decision.

```text
MCP_RATE_POLICY = PENDING_OWNER_DECISION
```

This remains a gateway-owner decision and does not invalidate the OAuth/MCP tool-discovery proof.
