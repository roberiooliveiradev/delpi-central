# Keycloak / MCP OAuth evidence — API DELPI

> Captured during API-DELPI-PLUGIN-002. **Documentation does not prove runtime go-live.**

## Source

| Item | Value |
|---|---|
| Observed at | 2026-09-15 |
| Discovery URL | `https://minhadelpi.com.br/auth/realms/delpi/.well-known/openid-configuration` |
| HTTP | 200 |
| Keycloak image (docker) | `quay.io/keycloak/keycloak:26.0.7` |
| Local gateway `/auth/` | 502 at capture time (prod public host used) |

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

## Verdict matrix

| Probe | Status | Notes |
|---|---|---|
| PKCE_S256 | **PROVEN** | advertised in discovery |
| OFFLINE_ACCESS | **PROVEN** (advertised) | scope listed; client enablement not proven |
| CIMD | **DISPROVEN** | `client_id_metadata_document_supported` not advertised |
| DCR | **INCONCLUSIVE** | `registration_endpoint` present; Keycloak typically requires initial access token; not exercised |
| PREDEFINED_CLIENT | **SUPPORTED** | standard Keycloak mode; required for ChatGPT/Codex until CIMD exists |
| RESOURCE_PARAMETER | **INCONCLUSIVE** | no live token issuance with `resource=` inspected |
| RESOURCE_TO_TOKEN_AUDIENCE | **DISPROVEN** (for MCP URL→`aud`) | platform tokens use `audience-delpi` → `aud` includes `delpi-central`; MCP resource URL is not proven as token audience |
| ISSUER_IDENTIFICATION | **PROVEN** | issuer matches public realm URL |

## Client mode decision

```text
MCP_CLIENT_MODE = PREDEFINED
```

Reason: CIMD not advertised; DCR not proven safe/open; predefined Authorization Code + PKCE is the legitimate Keycloak path.

### Predefined client requirements (do not auto-create here)

- Standard Flow ON
- Direct Access Grants OFF
- Client credentials / service accounts OFF
- PKCE enforced (S256)
- Valid redirect URIs for ChatGPT/Codex callbacks (from OpenAI current docs when configuring)
- Default scopes: `openid profile email audience-delpi`
- Audience mapper via scope `audience-delpi` → `aud` includes `delpi-central`
- No secrets in git

## Token validation mapping (current)

```text
OAuth resource advertised = {PUBLIC_BASE_URL}/apps/api-delpi/mcp
→ Keycloak issues access token with aud=delpi-central (via audience-delpi)
→ api-delpi validates KEYCLOAK_ISSUER + KEYCLOAK_AUDIENCE + signature + exp (+ nbf if present)
→ MCP middleware also requires OAuth scopes openid profile email audience-delpi
→ Core RBAC loads user permissions
→ ENGINEERING_LMP_ACCESS authorizes search_products
```

Strict RFC 8707 resource-audience binding for the MCP URL remains **BLOCKED** until Keycloak is configured and proven to mint that audience. Do not locally rewrite `aud`.

## Rate limit

Gateway `location ^~ /apps/api-delpi/` does **not** set `limit_req zone=api_zone` (unlike `/core-api/`).

```text
MCP_RATE_POLICY = PENDING
```
