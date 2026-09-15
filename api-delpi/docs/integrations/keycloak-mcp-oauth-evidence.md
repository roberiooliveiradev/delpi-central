# Keycloak / MCP OAuth evidence — API DELPI

> Captured during API-DELPI-PLUGIN-002; updated PLUGIN-003. **Documentation does not prove runtime go-live.**

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
| scopes_supported | includes `openid`, `profile`, `email`, `offline_access`, `audience-delpi`, `roles`, … |
| authorization_response_iss_parameter_supported | `true` |
| client_id_metadata_document_supported | **absent** |
| `.well-known/oauth-authorization-server` (realm) | HTTP 404 |

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
| PKCE_S256 | **PROVEN** | advertised in discovery |
| OFFLINE_ACCESS | **PROVEN** (advertised) | scope listed; client enablement not proven |
| CIMD | **DISPROVEN** | not advertised |
| DCR | **INCONCLUSIVE** | registration endpoint present; not exercised |
| PREDEFINED_CLIENT | **SUPPORTED** | chosen mode |
| RESOURCE_PARAMETER | **IGNORED_BY_KEYCLOAK** | send anyway; Keycloak does not bind it natively |
| RESOURCE_TO_TOKEN_AUDIENCE | **WORKAROUND_DOCUMENTED / NOT_APPLIED** | configure `mcp:tools` Audience mapper — see runbook |
| ISSUER_IDENTIFICATION | **PROVEN** | |

## Client mode

```text
MCP_CLIENT_MODE = PREDEFINED
MCP_CLIENT_ID = mcp-api-delpi
REDIRECT_URI = TO_CONFIGURE
KEYCLOAK_CONFIG = NOT_APPLIED
```

Operator steps: [keycloak-mcp-client-runbook.md](./keycloak-mcp-client-runbook.md).

## Target token validation mapping

```text
scopes = openid profile email audience-delpi mcp:tools
→ aud includes delpi-central (audience-delpi)
→ aud includes https://minhadelpi.com.br/apps/api-delpi/mcp (mcp:tools mapper)
→ api-delpi: validate_token(delpi-central) + MCP aud membership + scope check
→ ENGINEERING_LMP_ACCESS for search_products
```

## Rate limit

`location ^~ /apps/api-delpi/` has **no** `limit_req`.

```text
MCP_RATE_POLICY = PENDING_OWNER_DECISION
```
