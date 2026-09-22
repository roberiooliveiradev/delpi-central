# VISTA Capability Matrix (canonical)

**Status:** CURRENT (HEAD-bound inventory + governance)  
**Owner:** `tv-dashboard-api` (TV Dashboard domain)  
**Persona:** VISTA = specialist capability for operational displays — **not** a parallel AI to DÉLIA.

This file is the **single canonical matrix** for VISTA surface exposure.  
Do not duplicate the full matrix in Instructions, Knowledge, or DÉLIA docs — link here.

## Architecture decision

| Role | Authority |
|---|---|
| **DÉLIA** | IA / experiência de orquestração da DELPI |
| **VISTA** | Specialist/capability de painéis operacionais / TV |
| **TV Dashboard** | Domain authority (playlists, slides, data blocks, Copilot ops) |
| **MCP** | Adapter futuro (TARGET Plugin + remote MCP) — **não implementado neste HEAD** |
| **GPT Actions** | Adapter compacto **GOVERNED_PREPARE_COMMIT_V2** (Builder-importable) |

```text
Canonical domain capability (TvCopilotPatchV1)
  → Application / write services
    → HTTP domain API (UI)
    → GPT Action adapter
    → MCP adapter (TARGET)
    → DÉLIA capability adapter (PLANNED — not proven)
```

**Rules**

- Capability parity ≠ transport parity.
- New typed Copilot op ≠ new GPT Action.
- `VISTA capability ≤ authenticated user capability`.
- No generic proxy (`call_any_route`, SQL, arbitrary HTTP).
- Presentation writes: `gpt_preview_change` → opaque `proposal_handle` → `gpt_commit_change`.
- `gpt_commit_change` is **not** a generic executor (only server-side prepared proposals).
- Catalog informs; backend authorizes (`capability_surface` ≠ AuthZ).

## Source of truth

| Concern | Canonical source |
|---|---|
| Domain rules / typed ops | `tv_copilot_content.json` + Copilot services |
| Write boundary | `TvPresentationWriteService` |
| Resource AuthZ | `PlaylistAccessService` + Core RBAC |
| Capability metadata | `capability_surface.py` + catalog projection |
| Actions surface | `openapi_builder.py` → generated OpenAPI (**8** ops) |
| Proposal store | in-process → **ACCEPT_WITH_RESIDUAL** |
| GPT Instructions | `docs/gpt-actions/specialist-instructions.md` |
| Capability matrix | **this file** |

## PREPARE / CONFIRM / COMMIT

```text
UNDERSTAND → READ CURRENT STATE → PREPARE EXACT CHANGE (preview)
→ SHOW USER → EXPLICIT CONFIRMATION → COMMIT(proposal_handle, confirmation)
→ AUTHORITATIVE READ-BACK → VERIFY → REPORT OUTCOME
```

- `gpt_suggest_change` = NL planner (does **not** mint proposal).
- `gpt_preview_change` = PREPARE + mint opaque handle (`persisted=false`).
- `gpt_commit_change` = ACT (`proposal_handle` + `confirmation` + `Idempotency-Key` only).
- Explicit confirmation ≠ AuthZ.
- Technical 2xx ≠ business outcome.

## GPT ACTION SURFACE BUDGET

Documented project guardrail: prefer **≤ ~30 importable operations**.

| Metric | Before V2 | After V2 |
|---|---|---|
| Paths (Builder-visible) | 8 | **8** |
| Importable operations | 8 | **8** |
| Added | opaque proposal + confirmation on commit; `capability_surface` | contract evolution |
| Removed from Builder | client `ops`/`planDigest` as commit authority | — |
| Legacy off-schema | `POST /data/copilot/apply-patch` (non-persisting planner) | yes |
| Remaining margin vs ≤30 | 22 | **22** |

## Capability taxonomy

| Kind | Capability | Actions |
|---|---|---|
| ENTITY (read) | playlist aggregate | `gpt_list_playlists`, `gpt_get_playlist_context` |
| WORKFLOW | presentation_change (TvCopilotPatchV1) | `gpt_suggest_change`, `gpt_preview_change`, `gpt_commit_change` |
| ANALYSIS | data_route_search, data_block_preview | `gpt_search_data_routes`, `gpt_preview_data_block` |
| DISCOVERY | catalog | `gpt_get_catalog` |

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
