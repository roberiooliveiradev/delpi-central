# VISTA / TV Dashboard — OpenAI Plugin + MCP (governed READ + PREPARE/ACT)

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
5 READ + 1 DISCOVERY + 2 ANALYSIS + 1 PREPARE + 1 ACT = exactly 10 tools
native ops (upsert_data_model, bind_visual, migrate_data_sources_to_model,
upsert_data_source, patch_data_source_params, apply_safe_layout_fixes, …)
= vocabulary inside prepare_change.ops[] — never per-op tools
resources / prompts = FORBIDDEN
legacy primitive names (preview_change, commit_change) = FORBIDDEN as tools —
the governed envelope exposes them only as prepare_change / commit_proposal;
suggest_change is exposed as ANALYSIS over the shared canonical planner
(GptActionsDispatchService → PresentationCommandPlannerService), never a
transport-specific interpreter
```

Tools:

| Tool | Class | Delegates to |
|---|---|---|
| `list_playlists` | READ | `GptActionsDispatchService.list_playlists` |
| `get_playlist_context` | READ | `GptActionsDispatchService.get_playlist_context` (slide snapshots include `designAudit` — owner layout issues) |
| `get_catalog` | DISCOVERY | `GptActionsDispatchService.get_catalog` |
| `search_data_routes` | READ | `GptActionsDispatchService.search_data_routes` |
| `inspect_data_model` | READ | `GptActionsDispatchService.inspect_data_model` |
| `preview_data_model` | READ | `GptActionsDispatchService.preview_data_model` (inline candidate never persisted) |
| `preview_data_block` | ANALYSIS | `GptActionsDispatchService.preview_data_block` (`semanticDigest` + `visualRecommendation` + `joinHints`/`formatHints`, never persisted). Targets a persisted `data_source` block (or `operationId`+params); visual blocks such as `chart_view` are not preview targets → 422 |
| `suggest_change` | ANALYSIS | `GptActionsDispatchService.suggest_change` → `PresentationCommandPlannerService.plan` → `PresentationSuggestOpsService.materialize` (NL → typed ops + clarification/policy; never persists, never authorizes) |
| `prepare_change` | PREPARE | `GptActionsDispatchService.preview_change` (commit_now=False) |
| `commit_proposal` | ACT | `GptActionsDispatchService.commit_change` |

**Owner quality loop (§6.133):** `prepare_change` runs the owner's
deterministic safe corrections inside the candidate before it is returned —
issues the plan *introduced* are auto-corrected (safe-area/frame clamp,
overlap relayout, min font, context-aware contrast, hierarchy); the
explicit catalog op `apply_safe_layout_fixes` widens that to every
`safeAutoFix` issue on the slide. Corrections appear in `diff` +
`safeFixesApplied` evidence; issues with no provably-safe fix stay
visible in `candidatePreview.designAudit`. One governed write — never a
hidden second ACT.

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

**Governed-write authorization boundary (2026-10-05):** `prepare_change` and
`commit_proposal` inherit the human-governed write gate of the shared dispatch —
end-user principal (`principal_type == "user"`), bearer user credential and
**fresh effective Core RBAC** (`load_user_rbac(force_refresh=True)`: bypasses
permission cache, no stale fallback, fails closed when Core is unavailable)
before permission and `PlaylistAccessService` resource checks. Service
principals are denied twice: at MCP transport (401) and downstream at the
dispatch gate (`PRINCIPAL_TYPE_DENIED` 403) — defense in depth, not duplicated
authority. `POST /data/openapi/sync` is the explicit service-token
material-write exception covered by this authorization boundary — it is not
part of the MCP surface. Service-principal read behavior is unchanged and
remains outside this write-hardening workstream.

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

## Parity map + coexistence

GPT Actions and MCP expose the **same** `GptActionsDispatchService` — semantic
parity is total; only transport names differ.

| GPT Actions op | MCP tool | Class |
|---|---|---|
| `gpt_get_catalog` | `get_catalog` | READ |
| `gpt_list_playlists` | `list_playlists` | READ |
| `gpt_get_playlist_context` | `get_playlist_context` | READ |
| `gpt_search_data_routes` | `search_data_routes` | READ |
| `gpt_inspect_data_model` | `inspect_data_model` | READ |
| `gpt_preview_data_model` | `preview_data_model` | READ |
| `gpt_preview_data_block` | `preview_data_block` | ANALYSIS |
| `gpt_suggest_change` | `suggest_change` | ANALYSIS |
| `gpt_preview_change` | `prepare_change` | PREPARE |
| `gpt_commit_change` | `commit_proposal` | ACT |

Semantic differences:

- `get_playlist_context` accepts optional `slide_id`, `data_source_id` and
  `include_runtime` — focused inspection of a persisted legacy `data_source`
  (binding, transform, dependencies, consumers, and bounded runtime evidence)
  is nested in playlist context, not exposed as a standalone tool.
- `gpt_preview_change` accepts `commit_now=true` as an HTTP shortcut; MCP has
  no commit_now — PREPARE is never ACT. Additive commits still call
  `commit_proposal` explicitly.
- `gpt_suggest_change` is exposed on MCP as `suggest_change` — the shared
  `PresentationCommandPlannerService` is transport-neutral ANALYSIS
  (NL → typed ops + clarification; never persists, never authorizes), so both
  adapters project the same canonical materializer.
- `gpt_get_slide_preview_png` remains Actions-only — it is an asset fetch
  helper (`not_exposed_in_mcp` in the canonical `surface_parity` registry);
  on MCP the equivalent evidence arrives via `get_playlist_context` READ.
- The MCP catalog projection carries **no** `gpt_*` callable names and no
  Actions-envelope mechanics (`commit_now`, `confirmation.confirmed`,
  `additive_single_shot`, `action_surface_budget`): the
  `agent_directives` MCP projection neutralizes `(Actions: …)` annotations
  and rewrites residual `gpt_*` tokens through the canonical parity map.
  `surface_parity.parity_map` ships unchanged as the single non-callable
  registry of Actions↔neutral names.

### Coexistence / rollout

Both surfaces stay live. Transport preference is **client configuration**
(connector choice in the provider), not a backend flag:

```text
rollout : Actions connector → MCP connector (same Keycloak realm, mcp-tv-dashboard)
rollback: MCP connector → Actions connector — no code change, no data loss
```

### Safe fallback rules

| Stage | Cross-transport fallback |
|---|---|
| READ | Allowed when identical semantics/auth context are proven |
| PREPARE (before proposal_handle exists) | Allowed — no material side effect |
| ACT / uncertain ACT outcome | **FORBIDDEN** — never replay a mutation across transports; reconcile authoritative state first (UNKNOWN_OUTCOME → read-back → retry only via same key/transport) |

Client-side rules live in `vista_agent_intelligence.json` → `write_flow_mcp`
(idempotency key stability, unknown outcome, error-is-not-empty). The section
is canonical and projected into `agent_directives` for `transport="mcp"`
(MCP-primary envelope); the Actions projection omits it — the Actions catalog
envelope is already at its byte ceiling and carries `write_flow` (Actions
variant) instead.

### VISTA client migration (MCP3)

- `specialist-instructions.md` carries **two paste variants**: MCP-primary
  block and Actions block — paste exactly one, matching the configured
  connector.
- Keycloak client `mcp-tv-dashboard` (confidential, Auth Code + PKCE) —
  provisioning PENDING; see section below.
- Provider: configure the MCP connector URL
  `https://minhadelpi.com.br/apps/tv-dashboard-api/mcp` with OAuth —
  discovery via `/.well-known/oauth-protected-resource`.
