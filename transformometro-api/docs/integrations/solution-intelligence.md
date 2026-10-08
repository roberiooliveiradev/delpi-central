# TÉO × Core Solution Intelligence V1

## Ownership

- **Core API** = authority for apps, plugins, manifests, versions, routes,
  transversal RBAC and usage tracking.
- **Plugin domain** = authority for its own data and rules.
- **TÉO** = conversational consumer — never a registry, never a copy.

```text
Core API (apps/app_manifests/app_versions/app_routes)
→ safe projection (GET /solutions)
→ CoreSolutionCatalogGateway (Bearer forward, user parity)
→ SolutionCatalogService
→ get_solution_catalog / get_solution_context (MCP + GPT Actions)
```

## Visibility != Access

`KNOWLEDGE VISIBILITY != ACCESS AUTHORIZATION` is the central rule:

- `GET /solutions` returns ALL active registered apps with an
  `accessible` flag — it is NOT filtered to `/me/apps`.
- `accessible` is computed by `AppAuthorizationService.filter_app_ids`
  in Core — Core owns the policy, TÉO only reports it.
- Catalog knowledge never grants plugin data reads, writes or
  execution. Those still require the plugin's own AuthZ.

## Safe projection

Exposed: id, name, description, icon, type, category, version, active,
basePath, routes (path/label/icon/order/showInMenu), permissions
(code/name/description — already user-visible via /me/apps), features,
dependencies, accessible, updatedAt, recentVersions, evolution.

Never exposed: backend/security/healthcheck/observability/entry/metadata
manifest blocks, actor identities, permission UUIDs, checksums, RBAC
graph, user lists, personal usage.

## Evolution

`evolution` is a structural manifest diff between version snapshots —
`basis: CALCULATED` (version/description/routes/permissions/features
added/removed/changed). Release purpose is never inferred; without an
explicit source it is UNKNOWN.

## Recommendation intelligence

Agent directive (`teo_agent_intelligence.json → solutions`):

```text
UNDERSTAND NEED → get_solution_catalog → get_solution_context
→ CLASSIFY FIT → RECOMMEND
REUSE_EXISTING | EXTEND_EXISTING | INTEGRATE_EXISTING
| NEW_CAPABILITY_CANDIDATE | TO_INVENTORY
```

The catalog is never filtered to accessible apps — "accessible=false"
still means the solution exists and must be evaluated before building a
duplicate.

## Dynamic property

REGISTER/UPDATE PLUGIN IN CORE → TÉO sees it on the next catalog call.
No TÉO deployment, no parallel registry, no static JSON.

## Surfaces

| Surface | Route/tool |
|---|---|
| Core (session-auth) | `GET /solutions`, `GET /solutions/{id}` |
| GPT Actions | `gpt_get_solution_catalog`, `gpt_get_solution_context` |
| MCP | `get_solution_catalog`, `get_solution_context` |

All read-only (`x-openai-isConsequential: false`), Bearer-forwarded —
never service-account impersonation.
