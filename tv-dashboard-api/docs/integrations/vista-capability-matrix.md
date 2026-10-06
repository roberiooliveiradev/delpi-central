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
| **MCP** | Backend adapter **PROVEN** (`/mcp`, 10 tools sobre o mesmo `GptActionsDispatchService`: 5 READ + 1 DISCOVERY + 2 ANALYSIS `preview_data_block` + `suggest_change` + PREPARE + ACT); provisioning Keycloak `mcp-tv-dashboard` + go-live externo = **PENDING** |
| **GPT Actions** | Adapter compacto **GOVERNED_PREPARE_COMMIT_V2** (Builder-importable) |

```text
TV Dashboard domain (PresentationMutation / TvPresentationPatchV1)
  → canonical domain logic (TvPresentationWriteService)
    → VISTA specialist intelligence (vista_agent_intelligence.json +
      transport-neutral owner application boundary)
      → GptActionsDispatchService (shared, transport-neutral)
        → capability_surface canonical model (neutral names)
          → Actions adapter projection (parity_map inverse + envelope mechanics)
          → MCP adapter projection (neutral names; Actions semantics stripped)
        → HTTP domain API (UI editor)
        → GPT Action adapter (VISTA)
        → MCP adapter (PROVEN backend; external provisioning/go-live PENDING)
        → DÉLIA capability adapter (TARGET — not implemented)
```

**Unified owner boundary (VISTA-OWNER-UNIFIED-CAPABILITY-INTELLIGENCE-BOUNDARY-02):**
`capability_surface.py` declares the semantic surface **once** with neutral
capability names. `transport="actions"` derives its projection through the
inverse of the canonical `surface_parity.parity_map` registry plus the
Actions-only envelope mechanics (`commit_now`); `transport="mcp"` returns the
canonical surface with Actions-adapter annotations stripped and residual
`gpt_*` tokens rewritten to neutral names. A capability/intelligence change is
made **once** and rewrites both projections — there is no second list to drift.
`vista_agent_intelligence.json` is the single knowledge source; Actions gets a
compacted projection (budget), MCP gets the full MCP-primary document minus
Actions-envelope semantics.

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

## Governed write authorization (PROVEN — 2026-10-05, commit `7d1cc86c61`)

Canonical invariant for every **human-governed material write** (editor CRUD,
PresentationMutation, GPT Actions PREPARE/commit_now/COMMIT, MCP
`prepare_change`/`commit_proposal` — the latter two inherit the boundary by
delegating to the same dispatch):

```text
end-user principal (principal_type == "user")
  → bearer user credential
  → fresh effective Core RBAC (no cache, no stale fallback, fail closed)
  → required permission
  → resource/domain authorization (PlaylistAccessService) when applicable
  → canonical write boundary (TvPresentationWriteService)
```

- Keycloak = AuthN; Core API = effective platform RBAC; TV Dashboard =
  governed-write policy + resource AuthZ; VISTA/GPT Actions/MCP = adapters and
  consumers, never a permission source.
- Service principals are denied on all human-governed write surfaces
  (`PRINCIPAL_TYPE_DENIED` 403) and can never acquire orphan-playlist ownership
  via `PlaylistAccessService.try_claim_owner`.
- Revoked permission denies the next write even with a previously warm cache;
  Core unavailability fails closed (`AUTHZ_UNAVAILABLE` 503). **Reads are
  unchanged** — fresh RBAC is not applied globally.
- `capability_surface`, GPT confirmation, MCP metadata and provider scopes do
  not authorize writes.

**Bounded S2S exception (INTERNAL ADMIN):** `POST /data/openapi/sync` accepts
`X-Delpi-Service-Token` from `api-delpi` (producer:
`OpenApiConsumerNotifyService`) under effective `TV_MANAGE`. This does **not**
make service principals valid VISTA users and does not generalize to GPT
Actions, MCP, CRUD, PresentationMutation, template or builder writes.

## Source of truth

| Concern | Canonical source |
|---|---|
| Domain rules / typed ops | `presentation_ops_content.json` + `presentation_mutation/` |
| Mutation engine | `PresentationPatchService` |
| Write boundary | `TvPresentationWriteService` |
| Resource AuthZ | `PlaylistAccessService` + Core RBAC |
| Capability metadata | `capability_surface.py` + catalog projection |
| Actions surface | `openapi_builder.py` → generated OpenAPI (**10** ops) |
| MCP surface | `interface/mcp` adapter → shared dispatch (**10** tools) |
| Neutral↔Actions parity registry | `vista_agent_intelligence.json` → `surface_parity.parity_map` (single source; both projections derive from it) |
| Proposal store | in-process → **ACCEPT_WITH_RESIDUAL** |
| GPT Instructions (stable-only) | `docs/gpt-actions/specialist-instructions.md` — **no** feature heuristics |
| Live agent directives (deploy) | `vista_agent_intelligence.json` → `capability_surface.agent_directives` (**compact** projection; GPT Actions ≤100 KiB) |
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

| Metric | Before V2 | After V2 | Current |
|---|---|---|---|
| Paths (Builder-visible) | 8 | **8** | **10** |
| Importable operations | 8 | **8** | **10** |
| Added | opaque proposal + confirmation on commit; `capability_surface` | contract evolution | `gpt_preview_data_model`, `gpt_inspect_data_model` |
| Removed from Builder | client `ops`/`planDigest` as commit authority | — | — |
| Legacy off-schema | `POST /data/copilot/*` → **410 Gone** | yes | yes |
| Remaining margin vs ≤30 | 22 | **22** | **20** |

## Capability taxonomy

| Kind | Capability | Actions | MCP |
|---|---|---|---|
| ENTITY (read) | playlist aggregate | `gpt_list_playlists`, `gpt_get_playlist_context` | `list_playlists`, `get_playlist_context` |
| WORKFLOW | presentation_change (PresentationMutation) | `gpt_suggest_change`, `gpt_preview_change`, `gpt_commit_change` | `suggest_change` (ANALYSIS), `prepare_change`, `commit_proposal` |
| ANALYSIS | data_route_search, data_block_preview, domain_intent_materialization | `gpt_search_data_routes`, `gpt_preview_data_block`, `gpt_suggest_change` | `search_data_routes`, `preview_data_block`, `suggest_change` |
| ANALYSIS | data_model_lifecycle | `gpt_preview_data_model`, `gpt_inspect_data_model` | `preview_data_model`, `inspect_data_model` |
| DISCOVERY | catalog | `gpt_get_catalog` | `get_catalog` |

**ANALYSIS notes (CURRENT):** search = owner-local discovery over `tv_data_routes.json` (query required; compact DTO + `paramSchema`; miss ≠ absence). Preview prefers `{operationId, params}`. Heuristics: `agent_directives.data_discovery`. MFE `GET /data/routes` is editor-only (not a GPT Action).

**Transform SoT (CURRENT):** `dataTransform = { steps: [...] }` only. VISTA writes via `set_data_transform` (typed step allowlist). Free M / DAX / SQL → `mForbidden`. Product M workbench is **off** (`mQuery.enabled`/`writeV2Enabled`/`advancedEditorEnabled`=false); legacy v2 scripts may still execute in dual-read for saved playlists. Heuristics: `agent_directives.data_transform`.

## Slide Intelligence (CURRENT)

Owner-local services (not new GPT Actions):

| Concern | Module | Status |
|---|---|---|
| Join keys for merge | `JoinPlanService` + `propose_join` + preview `joinHints` | **PROVEN** |
| Display format hints | `DisplayFormatHintsService` + `displayFormatHints` | **PROVEN** |
| Auto projection pós-bind | `VisualProjectionService` | **PROVEN** |
| Ready-slide quality gate | `ReadySlideQualityService` (params / projection / resolved.error) | **PROVEN** |
| Layout/theme recipes | `PresentationRecipeService` + `presentation_recipes.json` (incl. `TV_KPI_SERIES_TABLE`) | **PROVEN** |
| Compound ready slide | `agent_directives.compound_slide` + `write_quality` | **PROVEN** |
| Layout digest (geometry) | `LayoutDigestService` → `gpt_get_playlist_context.layoutDigest` | **PROVEN** |
| Filter digest (layering) | `FilterDigestService` → `filterDigest` + op `re_layer_playlist_filters` / recipe `TV_RELAYER_FILTERS` | **PROVEN** |
| Slide schematic preview | `SlidePreviewRenderService` + signed URL via `includePreview` (+ INFORMED `assetId` paste) | **PROVEN** (Action Surface Gate: **no** 9th Action) |
| Auto-layout / hierarchy VERIFY | `SlideAutoLayoutService.apply_post_create_layout` + `hierarchy_inverted` in layout quality | **PROVEN** |
| `add_blank_slide` atomic props | `durationSec` + `background` on create | **PROVEN** |
| Published templates via VISTA | `apply_published_slide_template` + seed `system-estoque-top5` / `system-oee-overview` | **PROVEN** |
| Editor focus reliability | TTL + grace `stale` + MFE heartbeat 30s | **PROVEN** |
| Layout perception directives | `agent_directives.layout_perception` | **PROVEN** |
| Filter layering / slide craft | `agent_directives.filter_layering` + `slide_craft` | **PROVEN** directives + digest/op |
| Visual selection (shape→visual) | `agent_directives.visual_selection` + `chartTypeHints` | **PROVEN** directives |
| Continuous review of existing | `agent_directives.continuous_review` | **PROVEN** directives |
| Playlist clarification / curation | `object_resolution` + `playlist_curation` | **PROVEN** directives |
| Branch / SI goals | `branch_scope` + `si_goals` | **PROVEN** directives |
| Media | `assetId` only; `mediaInventory.assets[]` + brand logos via `ensure_brand_logo_on_slide` | **PROVEN** inventory/seed; generic upload **TARGET** |
| MCP VISTA backend | `/mcp` + `interface/mcp` adapter → shared dispatch | **PROVEN** (incl. PREPARE `prepare_change` + ACT `commit_proposal`); go-live externo **PENDING** |
| DÉLIA TV adapter | `mcp_delia` | **TARGET** (same PresentationMutation; no code in this HEAD) |
| Eval corpus | `docs/gpt-actions/vista-ready-slide-eval-corpus.md` + `tests/fixtures/vista_ready_slide_corpus.json` | **PROVEN** gate (`test_vista_ready_slide_corpus_gate.py`) |

DTOs (internal): `JoinPlanProposal`, `FormatHint`, `PresentationRecipeId` in `domain/presentation_intelligence`.

Typed vs heuristic:

| Decision | Typed | Heuristic (directives/suggest) |
|---|---|---|
| merge step shape | `set_data_transform` schema | which keys → JoinPlanService |
| DisplayFormatSpec on text data bindings | `set_display_format` + compact `blockIndex.formatBindings` | copy proven sibling spec; verify materialization |
| Other format owners | editor authoring; typed VISTA target pending | legacy `valueFormat` remains compatibility |
| background/style/frame | patch/upsert schemas | recipe markers |
| image bytes | — | forbidden without assetId |

**Not applicable:** generic `search_records` / `prepare_record_change` (VISTA is not multi-entity CRUD).

**Image / preview note:** catalog still forbids dumping image **bytes** without `assetId`. Official slide schematic is exposed as **signed HTTPS URL** (`slidePreview.previewUrl`) via READ context — not catalog bytes and not a 9th Action.

## Action inventory

| operationId | Type | Capability | MCP tool |
|---|---|---|---|
| gpt_get_catalog | READ/DISCOVERY | discovery | `get_catalog` |
| gpt_list_playlists | READ | playlist entity | `list_playlists` |
| gpt_get_playlist_context | READ | playlist entity + `layoutDigest` + `filterDigest` + `designAudit` + `mediaInventory` + `dataModels[]`/`blockIndex[].modelId`/`focusedBinding` (DataModel addressability, survives budget downgrade); optional `includePreview` → `slidePreview` | `get_playlist_context` |
| gpt_search_data_routes | ANALYSIS | data discovery | `search_data_routes` |
| gpt_preview_data_block | ANALYSIS | data preview + `semanticDigest` + `visualRecommendation` | `preview_data_block` |
| gpt_preview_data_model | ANALYSIS | data model preview (never persisted) | `preview_data_model` |
| gpt_inspect_data_model | ANALYSIS | data model inspection | `inspect_data_model` |
| gpt_suggest_change | ANALYSIS | NL → typed ops + clarification (never persists/authorizes) | `suggest_change` |
| gpt_preview_change | WORKFLOW PREPARE | mint proposal | `prepare_change` |
| gpt_commit_change | WORKFLOW ACT | common commit | `commit_proposal` |

`gpt_get_slide_preview_png` is the single Actions-only exclusion (asset fetch
helper, recorded in `surface_parity.not_exposed_in_mcp`; equivalent evidence
on MCP via `get_playlist_context` READ).

## Action Surface Gate (before new Action)

1. Real capability? 2. Owner proven? 3. Real consumer?  
4. Equivalent operation exists? 5. Fits catalog typed op?  
6. Fits preview/commit workflow? 7. Creates generic proxy?  
8. Increases surface unnecessarily?

### Gate decision — slide preview (2026-09-23)

| Option | Decision |
|---|---|
| 9ª Action `gpt_get_slide_preview` | **Rejected** — equivalent READ already via `gpt_get_playlist_context?includePreview=true&slideId=` |
| Asset GET `/gpt-actions/v1/slide-previews/{token}` | **HTTP only** (signed TTL); **not** Builder-importable |
| Vision consumption of `previewUrl` | Validate in GPT Builder smoke (`gpt-builder-go-live.md`); fallback = `layoutDigest` + user attach |

Importable operations are **10** today (two DataModel ops added after this
gate decision). Margin vs ≤30 = **20**.

## MCP / DÉLIA

| Surface | Status |
|---|---|
| MCP VISTA | **PROVEN** backend (`/mcp` mount + 10 semantic tools on shared dispatch; service-token rejected at transport; no `gpt_*` names or `commit_now` in the callable contract). External provisioning (`mcp-tv-dashboard`) / provider go-live = **PENDING** |
| DÉLIA → VISTA Actions | **NONE** — target is capability/core adapter, not Actions HTTP |

## Proposal store residual

| Item | Value |
|---|---|
| Type | in-process, HMAC-opaque handle |
| Binding | actor + playlist target + ops + catalogVersion + baseRevision + TTL |
| Suitability | single replica uvicorn → **ACCEPT_WITH_RESIDUAL** |
| Review trigger | workers/replicas > 1 or cross-process prepare/commit |

## Display format bridge (2026-09-25)

`DisplayFormatService` remains the formatting authority. VISTA reads persisted
`blockIndex.items[].formatBindings[]`, discovers canonical presets in
`gpt_get_catalog.displayFormatCatalog`, and sends `DisplayFormatSpec` through
`set_display_format` in the existing PREPARE/COMMIT actions. The semantic target is
`blockId` + `owner` (`contentRunDataRef` or `textProjection`) + `field`; repeated
content-run fields require `occurrence`. No new GPT Action or client formatter exists.

The current typed mutation covers the active text binding owners. The editor
also stores canonical specs in `kpiOptions.displayValueFormat`,
`kpiProjection.metrics[].displayFormat`, `chartOptions.displayValueFormat`,
`chartOptions.displayCategoryFormat`, `tableOptions.displayValueFormat`,
`tableProjection.columns[].displayFormat`, and canvas table cells/dataRefs.
These owner-specific slots are **not yet addressable** through
`set_display_format`; legacy `valueFormat`/`format` fields stay readable.
Consequently, generic display-format mutation is **PARTIAL**, and an
authenticated READ→PREPARE→COMMIT→READ→enrich regression is still required
before marking the end-to-end capability PROVEN.
