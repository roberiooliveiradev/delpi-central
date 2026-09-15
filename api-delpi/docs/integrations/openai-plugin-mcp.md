# API DELPI — OpenAI Plugin + MCP

> **Documentation does not prove runtime.**

## Status

| Item | Value |
|---|---|
| Strategic target | OpenAI Plugin → MCP → semantic capability → existing use cases |
| Legacy | `/gpt-actions/v1` = `LEGACY_TRANSITIONAL` |
| V1 business tool | `search_products` (read-only Product Master) |
| Custom UI | Not required / not shipped |
| MCP auth model | **A — transport requires OAuth** before `tools/list` |
| OAuth contract (code) | Implemented (metadata + securitySchemes + challenges) |
| Keycloak compatibility | Partial evidence — see [keycloak-mcp-oauth-evidence.md](./keycloak-mcp-oauth-evidence.md) |
| Go-live | `GO_LIVE_BLOCKED` until predefined client + e2e PASS |

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

`securitySchemes` (OpenAI tool metadata): `oauth2` with scopes `openid profile email audience-delpi` only.  
Never advertise RBAC permission codes as OAuth scopes.

## Field allowlist

Approved: `product_code`, `description`, `group_category`.  
Denied by default: `customer_reference` and every other Product DTO field.

## AuthN / AuthZ

- OpenAI account / plugin metadata / MCP annotations / securitySchemes are **not** authority.
- Auth model **A**: HTTP Bearer required for entire `/mcp` transport (including initialize/tools/list).
- Unauthenticated `/mcp` → `401` + `WWW-Authenticate` with `resource_metadata`, `error`, `error_description`.
- Tool-level `_meta["mcp/www_authenticate"]` emitted on Unauthorized tool results (OpenAI linking contract).
- User JWT via Keycloak (authorization-code + PKCE S256).
- MCP also requires OAuth scopes: `openid profile email audience-delpi`.
- Product search AuthZ remains `ENGINEERING_LMP_ACCESS` (unchanged).
- Service account / client credentials / internal service token: **forbidden** on `/mcp`.

## OAuth / MCP requirements

Protected Resource Metadata:

- `GET /apps/api-delpi/.well-known/oauth-protected-resource`
- scopes_supported = `openid profile email audience-delpi`

Canonical resource: `{PUBLIC_BASE_URL}/apps/api-delpi/mcp` (override `MCP_RESOURCE_URL`).

Token audience today: `delpi-central` via Keycloak scope `audience-delpi`.  
RFC 8707 MCP-URL audience: **not proven** — see evidence doc. Do not rewrite `aud` locally.

| Probe | Status |
|---|---|
| PKCE_S256 | `PROVEN` |
| CIMD | `DISPROVEN` |
| DCR | `INCONCLUSIVE` |
| PREDEFINED_CLIENT | `SUPPORTED` → **chosen mode** |
| RESOURCE_TO_TOKEN_AUDIENCE (MCP URL) | `DISPROVEN` |
| ISSUER_IDENTIFICATION | `PROVEN` |

## Rate limit

Owner: gateway. Live nginx `location ^~ /apps/api-delpi/` has **no** `limit_req`.

```text
MCP_RATE_POLICY = PENDING
```

## Plugin package

Path: `api-delpi/integrations/openai-plugin/` (not Portal `plugins/`).  
`homepage = TO_CONFIGURE` until canonical website/privacy/terms URLs are owned.

## Application boundary

`product_search_auth` uses canonical `delpi_auth.request_context` / `authz_core` — accepted api-delpi pattern (same as `@require_*`). No new RBAC matrix.

## Developer-mode / Inspector

Manual until deployed + predefined client configured. Record `TEST_NOT_RUN` until executed.

## Go-live preconditions

Remain blocked until: predefined client configured, OAuth login PASS, HTTPS MCP smoke, 401/403/allowlist PASS, ChatGPT developer-mode PASS, rate policy decided.
