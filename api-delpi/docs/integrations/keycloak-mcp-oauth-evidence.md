# Keycloak / MCP OAuth evidence — API DELPI

> Captured during API-DELPI-PLUGIN-002 and updated through PLUGIN-007 / DAVI Workspace Agent private preview.  
> **Documentation records evidence; it does not replace revalidation after code/provider/config changes.**

## Source

| Item | Value |
|---|---|
| Initial observed at | 2026-09-15 |
| Latest acceptance update | 2026-09-16 |
| Discovery URL | `https://minhadelpi.com.br/auth/realms/delpi/.well-known/openid-configuration` |
| Keycloak image observed | `quay.io/keycloak/keycloak:26.0.7` |
| MCP resource | `https://minhadelpi.com.br/apps/api-delpi/mcp` |
| Keycloak client | `mcp-api-delpi` |
| OpenAI Workspace Agents source checked | `https://help.openai.com/en/articles/20001143` |

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

## Vendor contract / platform decision

| Claim | Status | Notes |
|---|---|---|
| Keycloak 26.0.7 directly binds the OAuth `resource` parameter to token `aud` for this integration | **DISPROVEN / not used** | Platform uses client scope + Audience mapper |
| `mcp:tools` client scope + Audience mapper binds the MCP resource audience | **PROVEN** | Applied to `mcp-api-delpi` |
| `audience-delpi` provides `aud=delpi-central` | **PROVEN** | Existing platform audience mechanism |
| `audience-delpi` must appear in JWT `scope` | **DISPROVEN** | Evaluate token omitted it; resource server does not require it |
| Workspace Agent End-user account means per-user app authentication | **PROVEN vendor contract + configured** | current Agent Studio setting for DAVI |
| Agent instructions themselves grant app access | **DISPROVEN by provider contract** | app connection/auth remains separate |

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

## PLUGIN-006 / 006A — MCP contract hardening

Functional hardening commit:

```text
537e66cf7ca60cddfea0c506fcfdeed2564bf7d4
fix(api-delpi): harden DAVI MCP tool contract
```

Layering correction:

```text
98e825f291e511badc2f7fa3597e59ea367df6e5
fix(api-delpi): restore MCP schema layering
```

Result:

```text
page minimum = 1
page_size minimum = 1
page_size maximum = 50
additionalProperties = false
output schema = typed approved projection
validation error = VALIDATION_ERROR / Invalid search parameters.
raw Pydantic detail = not exposed
MCP Pydantic schema owner = interface/mcp
Application framework dependency = removed
```

## PLUGIN-007 — hardened production acceptance

Accepted deployed SHA:

```text
d0c22a5cff5bfab0953a9b6d9f7047701b7ca79e
```

The hardening/layering commits are ancestors of the deployed SHA.

| Evidence | Status | Notes |
|---|---|---|
| deployment / container recreate | **PASS** | canonical production flow, healthy container |
| `GET /apps/api-delpi/health` | **PASS** | `{"status":"online"}` |
| unauthenticated `/mcp` no-slash | **PASS** | 401, no redirect |
| `Origin: https://chatgpt.com` | **PASS** | 401 OAuth challenge, not 403 |
| protected-resource metadata | **PASS** | exact resource + `openid profile email mcp:tools` |
| container `tools/list` input schema | **PASS** | min/max + closed input schema |
| container `tools/list` output schema | **PASS** | approved typed Product Master projection |
| validation failures | **PASS** | safe `VALIDATION_ERROR`; no Pydantic leakage |
| ChatGPT action refresh | **PASS** | live UI shows updated input bounds |
| provider output-schema rendering | **INCONCLUSIVE** | observed UI did not visibly expose the typed output schema |
| live output projection | **PASS** | authenticated calls returned approved fields only |

## Authenticated business calls — PROVEN

The connected DAVI app successfully executed `search_products` with the current operator identity.

Proven queries included:

```text
code = 10080022
description = TERM. OLHAL M5
group_code = 1008
```

Observed result projection remained:

```text
product_code
description
group_category
```

Denied/non-returned fields included `customer_reference`, stock, price, supplier, customer and finance data.

## Workspace Agent DAVI private-preview evidence

A DAVI Workspace Agent draft was configured in Agent Studio as a consumer of the existing DAVI app.

Configured app authentication:

```text
End-user account / Conta do usuário final
```

No new Keycloak client, scope, audience or permission was created for the Agent.

Observed preview:

| Scenario | Status |
|---|---|
| Product `10080022` | **PASS** |
| Description search `TERM. OLHAL M5` | **PASS** |
| Request for stock + price | **PASS guard** — agent stated capability unavailable and did not invent data |
| Agent app connection | **PASS** |
| End-user account setting | **PASS** |
| Second DELPI user own-login proof | **PENDING** |
| User without Product Master business access | **PENDING** |
| Wider Agent publication | **PENDING** |

The already-connected operator account was reused in Agent preview, so no new login prompt was required. This proves connection reuse for the current user only; it does not prove cross-user identity isolation.

## Current identity invariant for Workspace Agent

```text
Agent instructions ≠ access grant
Agent persona ≠ access grant
Agent sharing ≠ access grant
OAuth scopes ≠ business RBAC

End-user account
→ each user authenticates/connects independently
→ API DELPI still performs final business AuthZ
```

Do not switch DAVI to an Agent-owned/shared account to avoid user login. That is a different authority model and requires explicit security/architecture approval.

## Agent Studio icon observation

On the Agent Studio UI observed on 2026-09-16, custom image/photo upload for the Agent avatar was not available to the creator. This is a provider-UI observation, not a security or architecture requirement.

Current provider documentation also describes an `icon` field in other Workspace Agent management surfaces, so do not generalize the observed Studio UI limitation as a permanent platform contract.

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
13. agent/app attachment and auth mode when Agent Studio is the consumer
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

No stock, price, supplier, customer, finance, SQL, generic proxy, writes, service account, or GPT-local/Agent-local RBAC are part of DAVI V1.

## Remaining go-live gates

```text
SECOND_USER_OWN_IDENTITY = PENDING
NEGATIVE_BUSINESS_AUTHZ = PENDING
MCP_RATE_POLICY = PENDING_OWNER_DECISION
WIDER_AGENT_PUBLICATION = PENDING
```

These do not invalidate private development/preview, but they block an organization-wide production claim.

## Rate limit

`location ^~ /apps/api-delpi/` still has no proven MCP-specific `limit_req` decision.

```text
MCP_RATE_POLICY = PENDING_OWNER_DECISION
```

This remains a gateway-owner decision and does not invalidate the OAuth/MCP/Agent private-preview proofs.
