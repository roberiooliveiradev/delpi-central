# API DELPI — OpenAI Plugin + MCP

> **Documentation does not prove runtime.**

## Status

| Item | Value |
|---|---|
| Strategic target | OpenAI Plugin → MCP → semantic capability → existing use cases |
| Legacy | `/gpt-actions/v1` = `LEGACY_TRANSITIONAL` |
| V1 business tool | `search_products` (read-only Product Master) |
| Custom UI | Not required / not shipped |
| Go-live | `GO_LIVE_PENDING` |

## Architecture

```text
ChatGPT / Codex
  → OpenAI Plugin (integrations/openai-plugin/)
  → MCP Streamable HTTP  /apps/api-delpi/mcp
  → interface/mcp adapter
  → application/external_capabilities (provider-neutral)
  → SearchProducts use case
  → backend AuthZ (ENGINEERING_LMP_ACCESS)
  → authoritative DELPI source
```

Legacy Custom GPT Actions share the same `external_capabilities` search/projection.

## Tool contract — `search_products`

Inputs: `code?`, `description?`, `group_code?`, `page?` (>=1), `page_size?` (1..50; default 50).

Output fields only: `product_code`, `description`, `group_category` + pagination (`page`, `page_size`, `total`, `total_pages`).

Annotations (metadata only — not AuthZ): `readOnlyHint=true`, `destructiveHint=false`, `openWorldHint=false`.

## Field allowlist

Approved: `product_code`, `description`, `group_category`.  
Denied by default: `customer_reference` and every other Product DTO field.

## AuthN / AuthZ

- OpenAI account / plugin metadata / MCP annotations are **not** authority.
- User JWT via Keycloak (OAuth 2.1 authorization-code + PKCE expected by MCP clients).
- Product search AuthZ remains `ENGINEERING_LMP_ACCESS` (unchanged).
- Service account / client credentials / internal service token: **forbidden** on `/mcp`.

## OAuth / MCP requirements

MCP resource server exposes RFC 9728 Protected Resource Metadata:

- `GET /apps/api-delpi/.well-known/oauth-protected-resource`
- Unauthenticated `/mcp` → `401` + `WWW-Authenticate` with `resource_metadata`

Canonical resource candidate: `{PUBLIC_BASE_URL}/apps/api-delpi/mcp` (override with `MCP_RESOURCE_URL`).

Platform access tokens today use audience `delpi-central` (`KEYCLOAK_AUDIENCE`). Full RFC 8707 resource-indicator audience binding for the MCP resource URL requires Keycloak configuration and is **not assumed proven** until live discovery + token inspection pass.

| Probe | Status until live Keycloak proof |
|---|---|
| PKCE_S256 | `NOT_PROVEN` |
| OFFLINE_ACCESS | `NOT_PROVEN` |
| RESOURCE_INDICATOR | `NOT_PROVEN` |
| ISSUER_IDENTIFICATION | `NOT_PROVEN` (env: `KEYCLOAK_ISSUER`) |
| MCP_CLIENT_MODE | `INCONCLUSIVE` (prefer predefined Keycloak client if CIMD/DCR unavailable) |

If Keycloak cannot satisfy MCP OAuth: `AUTH_MCP_COMPATIBILITY = BLOCKED` — do not work around with service accounts.

## Rate limit

Owner: gateway. `/apps/api-delpi/*` inherits the existing api-delpi zone.  
`MCP_RATE_POLICY = TO_DEFINE_BEFORE_GO_LIVE`.

## Plugin package

Path: `api-delpi/integrations/openai-plugin/` (not Portal `plugins/`).

## Developer-mode test procedure

1. Deploy HTTPS endpoint + metadata.
2. Configure Keycloak OAuth client compatible with MCP (CIMD / DCR / predefined).
3. Load plugin package in ChatGPT developer mode.
4. OAuth login as DELPI user.
5. Tool scan → only `search_products`.
6. Authorized search PASS; unauthorized FAIL-CLOSED; allowlist PASS.

## Go-live preconditions

See task brief §38. Until all items PASS in production: `GO_LIVE_PENDING`.

## Migration — Custom GPT Actions

Keep `/gpt-actions/v1` while useful. Do not expand Actions. Do not treat as strategic surface. Catalog requires JWT auth only; search still requires `ENGINEERING_LMP_ACCESS`. Raw permission codes are not exposed in external payloads.
