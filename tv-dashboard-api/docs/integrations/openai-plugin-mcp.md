# VISTA / TV Dashboard — OpenAI Plugin + MCP (READ surface)

> Documentation does not prove runtime. Evidence is classified; revalidate after material deploy/auth changes.

Shared onboarding (novos MCPs):
[`docs/10-guias-operacionais/mcp-chatgpt-plugin-onboarding-runbook.md`](../../../docs/10-guias-operacionais/mcp-chatgpt-plugin-onboarding-runbook.md)

## Specialist identity

| Field | Value |
|---|---|
| Short name | **VISTA** |
| Full name | VISTA — Especialista em Painéis Operacionais DELPI |
| Mission | Painéis operacionais / programações / telas / DataModels no TV Dashboard |
| Role | Conversational specialist = **MCP consumer over canonical application services** |

```text
VISTA capability ≤ authenticated user capability
ChatGPT confirmation ≠ authorization
MCP ≠ Domain API
MCP ≠ RBAC
MCP ≠ generic proxy
AuthZ final = backend / GptActionsDispatchService / PlaylistAccessService
```

## Technical identities

| Surface | Technical id |
|---|---|
| MCP server name | `tv-dashboard` |
| Keycloak client | `mcp-tv-dashboard` (PENDING provisioning) |
| MCP endpoint / resource | `https://minhadelpi.com.br/apps/tv-dashboard-api/mcp` |
| Protected Resource Metadata | `https://minhadelpi.com.br/apps/tv-dashboard-api/.well-known/oauth-protected-resource` |
| OIDC issuer | `https://minhadelpi.com.br/auth/realms/delpi` |

## Architecture

```text
Workspace Agent / ChatGPT Plugin (VISTA)
  → OAuth Authorization Code + PKCE
  → Keycloak end-user identity (mcp-tv-dashboard)
  → MCP Streamable HTTP /apps/tv-dashboard-api/mcp
  → interface/mcp adapter (context rebuild only)
  → GptActionsDispatchService (same as /gpt-actions)
  → canonical AuthZ + domain services
  → Postgres tv-dashboard
```

No HTTP loop: tools call the dispatch service directly — never `/gpt-actions` over HTTP.

## Surface policy (MCP2)

```text
VISTA_MCP_SURFACE = GOVERNED_WRITE_V1
6 READ + 1 PREPARE + 1 ACT = exactly 8 tools
native ops (upsert_data_model, bind_visual, migrate_data_sources_to_model,
upsert_data_source, patch_data_source_params, …) = vocabulary inside
prepare_change.ops[] — never per-op tools
resources / prompts = FORBIDDEN
legacy primitive tools (suggest_change, preview_data_block,
preview_change, commit_change) = FORBIDDEN as tools
```

Tools:

| Tool | Class | Delegates to |
|---|---|---|
| `list_playlists` | READ | `GptActionsDispatchService.list_playlists` |
| `get_playlist_context` | READ | `GptActionsDispatchService.get_playlist_context` |
| `get_catalog` | READ | `GptActionsDispatchService.get_catalog` |
| `search_data_routes` | READ | `GptActionsDispatchService.search_data_routes` |
| `inspect_data_model` | READ | `GptActionsDispatchService.inspect_data_model` |
| `preview_data_model` | READ | `GptActionsDispatchService.preview_data_model` (inline candidate never persisted) |
| `prepare_change` | PREPARE | `GptActionsDispatchService.preview_change` (commit_now=False) |
| `commit_proposal` | ACT | `GptActionsDispatchService.commit_change` |

## Governed write envelope

```text
prepare_change(target, ops[], catalogVersion?)
  → canonical preview pipeline (catalog validation, policy, diff)
  → opaque proposal_handle (HMAC-signed, actor-bound, TTL, single-use)
  → canCommit / risk / confirmationPolicy / sideEffectHints
  → NOTHING persisted (no revision change, no write port call)

commit_proposal(proposal_handle, idempotency_key, confirmation=true)
  → actor binding (AUTHZ_DENIED cross-user)
  → Idempotency-Key required (REPLAY / CONFLICT / IN_PROGRESS)
  → explicit confirmation required (tool invocation ≠ confirmation)
  → canonical commit + postcondition verification
  → status VERIFIED / OUTCOME_NOT_VERIFIED / typed failure
```

`TV_WRITE` permission is enforced by the application on both tools.

## OAuth transport requirements

Access tokens used at `/mcp` must contain:

```text
aud: delpi-central + https://minhadelpi.com.br/apps/tv-dashboard-api/mcp
scope: openid profile email mcp:tools
```

- `audience-delpi` is an internal audience mapper — never an OAuth `scope` claim.
- Internal service tokens (`internal-service`) are rejected on `/mcp` with 401.
- Unauthenticated calls return `401` + `WWW-Authenticate: Bearer realm="mcp", resource_metadata=…`.
- `/mcp` (no slash) is rewritten internally to `/mcp/` — no provider-breaking 307.
- DNS-rebinding/Origin protection via FastMCP `TransportSecuritySettings`
  (`TV_MCP_ALLOWED_HOSTS`, `TV_MCP_ALLOWED_ORIGINS` override defaults).

## Configuration

| Env | Purpose | Default |
|---|---|---|
| `TV_DASHBOARD_API_ROOT_PATH` | public app root (mount prefix) | `/apps/tv-dashboard-api` |
| `PUBLIC_BASE_URL` | public origin for resource URL derivation | unset → canonical `minhadelpi.com.br` |
| `MCP_RESOURCE_URL` | explicit resource/audience override (per-env) | unset |
| `MCP_PREDEFINED_CLIENT_ID` | Keycloak client override | `mcp-tv-dashboard` |
| `KEYCLOAK_ISSUER` | authorization_servers in metadata | unset |
| `TV_MCP_ALLOWED_HOSTS` | DNS-rebinding host allowlist (csv) | `minhadelpi.com.br` + localhost |
| `TV_MCP_ALLOWED_ORIGINS` | Origin allowlist (csv) | `https://minhadelpi.com.br` + localhost |

No enable/disable flag — mount is unconditional, matching the TÉO/DAVI
convention (surface is OAuth-gated; absence of traffic is the off state).

## Keycloak provisioning (PENDING)

Required on `mcp-tv-dashboard` (confidential, Authorization Code + PKCE):

1. client scope `mcp:tools` (generic, shared with other MCP clients);
2. **dedicated** audience mapper emitting `https://minhadelpi.com.br/apps/tv-dashboard-api/mcp` into `aud` — never reuse `audience-delpi`, never place resource audience inside shared `mcp:tools`;
3. audience mapper bound to this client's specific scope only;
4. redirect URIs for the Plugin/Workspace Agent;
5. verify issued token: `aud` contains both `delpi-central` and the MCP resource, `scope` contains `mcp:tools`.

Until provisioning evidence exists, status is **PENDING** — do not mark live.

## GPT Actions coexistence

`/gpt-actions/v1/changes/preview` and `/gpt-actions/v1/changes/commit` remain
the same canonical flow — MCP exposes the identical dispatch services through
the governed envelope. VISTA client migration is MCP3 scope.
