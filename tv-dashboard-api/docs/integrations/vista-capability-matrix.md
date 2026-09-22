# VISTA Capability Matrix (canonical)

**Status:** CURRENT (HEAD-bound inventory + governance)  
**Owner:** `tv-dashboard-api` (TV Dashboard domain)  
**Persona:** VISTA = specialist capability for operational displays — **not** a parallel AI to DÉLIA.

This file is the **single canonical matrix** for VISTA surface exposure.  
Do not duplicate the full matrix in Instructions, Knowledge, or DÉLIA docs — link here.

## Architecture decision

| Role | Authority |
|---|---|
| **VISTA** | Specialist/capability de painéis operacionais / TV (`/gpt-actions/v1`) |
| **TV Dashboard** | Domain authority (playlists, slides, data blocks, PresentationMutation) |
| **Chat interno (Minha DELPI)** | Handoff only (`tv_dashboard_handoff`) — **não** muta TV; **não** é VISTA nem DÉLIA |
| **DÉLIA** | App standalone industrial — **≠** Chat; adapter TV = **TARGET** (mesmo contrato PresentationMutation; sem HTTP neste HEAD) |
| **MCP** | Adapter futuro (TARGET Plugin + remote MCP) — **não implementado neste HEAD** |
| **GPT Actions** | Adapter compacto **GOVERNED_PREPARE_COMMIT_V2** (Builder-importable) |

```text
Canonical domain capability (PresentationMutation / TvPresentationPatchV1)
  → TvPresentationWriteService
    → HTTP domain API (UI editor)
    → GPT Action adapter (VISTA)
    → MCP adapter (TARGET)
    → DÉLIA capability adapter (TARGET — not implemented)
```

**Rules**

- Capability parity ≠ transport parity.
- New typed presentation op ≠ new GPT Action.
- `VISTA capability ≤ authenticated user capability`.
- No generic proxy (`call_any_route`, SQL, arbitrary HTTP).
- Presentation writes: `gpt_preview_change` → opaque `proposal_handle` → `gpt_commit_change`.
- `gpt_commit_change` is **not** a generic executor (only server-side prepared proposals).
- Catalog informs; backend authorizes (`capability_surface` ≠ AuthZ).
- Nested block patches deep-merge (`style`/`frame`/`dataBinding`/`background`); explicit `null` clears.
- `/data/copilot/*` is **410 Gone**; Chat Copilot skill/tool and MFE dock are retired.
- Internal Chat TV intent → **handoff** (`tv_dashboard_handoff` direct answer → VISTA); never mint mutation tools.
- DÉLIA TV capability adapter = **TARGET** (same PresentationMutation contract; no code in this HEAD).

## Source of truth

| Concern | Canonical source |
|---|---|
| Domain rules / typed ops | `presentation_ops_content.json` + `presentation_mutation/` |
| Mutation engine | `PresentationPatchService` |
| Write boundary | `TvPresentationWriteService` |
| Resource AuthZ | `PlaylistAccessService` + Core RBAC |
| Capability metadata | `capability_surface.py` + catalog projection |
| Actions surface | `openapi_builder.py` → generated OpenAPI (**8** ops) |
| Proposal store | in-process → **ACCEPT_WITH_RESIDUAL** |
| GPT Instructions (stable-only) | `docs/gpt-actions/specialist-instructions.md` — **no** feature heuristics |
| Live agent directives (deploy) | `vista_agent_intelligence.json` → `capability_surface.agent_directives` |
| Data route NL discovery | `TvDataRouteDiscoveryService` + `docs/data-route-nl-suggest.md` |
| Chat TV intent | `tv_dashboard_handoff` (direct answer → VISTA; no mutation tool) |
| Instructions leak gate | `tests/test_vista_builder_instructions_budget.py` |
| Capability matrix | **this file** |
| DÉLIA TV adapter | TARGET (document only; consume PresentationMutation) |

## PREPARE / CONFIRM / COMMIT

```text
UNDERSTAND → READ CURRENT STATE → PREPARE (gpt_preview_change)
→ [direct] commit_now=true + confirmation → PREPARE+COMMIT same request
→ [confirm] SHOW USER → one conversational Confirma? → gpt_commit_change(handle)
→ AUTHORITATIVE READ-BACK → VERIFY → REPORT OUTCOME
```

- `gpt_suggest_change` = NL planner (optional; skip when intent is already typed).
- `gpt_preview_change` = PREPARE + mint opaque handle; with `commit_now=true` +
  `confirmation` when aggregated `confirmationPolicy=direct` → PREPARE+COMMIT
  in one Action (`commit_now_applied=true`, `status=VERIFIED`).
- **Compound plans (PROVEN):** PlanCompiler topo-sorts typed ops (`produces`/
  `consumes`, optional `as`/`*Ref`); preview uses synthetic IDs; ACT binds real
  IDs. Declaration order may be shuffled.
- Destructive (`confirmationPolicy=confirm`): `commit_now` is ignored; use
  `gpt_commit_change` with the **exact** `proposal_handle` after one user OK.
- Never invent handles (`latest` etc.) → `PROPOSAL_NOT_FOUND`.
- Explicit confirmation ≠ AuthZ. Technical 2xx ≠ business outcome.

## GPT ACTION SURFACE BUDGET

Documented project guardrail: prefer **≤ ~30 importable operations**.

| Metric | Before V2 | After V2 |
|---|---|---|
| Paths (Builder-visible) | 8 | **8** |
| Importable operations | 8 | **8** |
| Added | opaque proposal + confirmation on commit; `capability_surface` | contract evolution |
| Removed from Builder | client `ops`/`planDigest` as commit authority | — |
| Legacy off-schema | `POST /data/copilot/*` → **410 Gone** | yes |
| Remaining margin vs ≤30 | 22 | **22** |

## Capability taxonomy

| Kind | Capability | Actions |
|---|---|---|
| ENTITY (read) | playlist aggregate | `gpt_list_playlists`, `gpt_get_playlist_context` |
| WORKFLOW | presentation_change (PresentationMutation) | `gpt_suggest_change`, `gpt_preview_change`, `gpt_commit_change` |
| ANALYSIS | data_route_search, data_block_preview | `gpt_search_data_routes`, `gpt_preview_data_block` |
| DISCOVERY | catalog | `gpt_get_catalog` |

**ANALYSIS notes (CURRENT):** search = owner-local discovery over `tv_data_routes.json` (query required; compact DTO + `paramSchema`; miss ≠ absence). Preview prefers `{operationId, params}`. Heuristics: `agent_directives.data_discovery`. MFE `GET /data/routes` is editor-only (not a GPT Action).

**Not applicable:** generic `search_records` / `prepare_record_change` (VISTA is not multi-entity CRUD).

## Action inventory

| operationId | Type | Capability |
|---|---|---|
| gpt_get_catalog | READ | discovery |
| gpt_list_playlists | READ | playlist entity |
| gpt_get_playlist_context | READ | playlist entity |
| gpt_search_data_routes | ANALYSIS | data discovery |
| gpt_preview_data_block | ANALYSIS | data preview |
| gpt_suggest_change | WORKFLOW PREPARE | NL → typed ops |
| gpt_preview_change | WORKFLOW PREPARE | mint proposal |
| gpt_commit_change | WORKFLOW ACT | common commit |

## Action Surface Gate (before new Action)

1. Real capability? 2. Owner proven? 3. Real consumer?  
4. Equivalent operation exists? 5. Fits catalog typed op?  
6. Fits preview/commit workflow? 7. Creates generic proxy?  
8. Increases surface unnecessarily?

## MCP / DÉLIA

| Surface | Status |
|---|---|
| MCP VISTA | **NONE** this HEAD (architecture allows future adapter without duplicating rules) |
| DÉLIA → VISTA Actions | **NONE** — target is capability/core adapter, not Actions HTTP |

## Proposal store residual

| Item | Value |
|---|---|
| Type | in-process, HMAC-opaque handle |
| Binding | actor + playlist target + ops + catalogVersion + baseRevision + TTL |
| Suitability | single replica uvicorn → **ACCEPT_WITH_RESIDUAL** |
| Review trigger | workers/replicas > 1 or cross-process prepare/commit |
