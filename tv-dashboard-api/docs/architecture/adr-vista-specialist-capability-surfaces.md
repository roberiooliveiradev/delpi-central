# ADR — VISTA specialist capability surfaces (GPT Actions / future MCP)

**Status:** DECIDED  
**Date:** 2026-09-22  
**Context:** Align VISTA GPT Actions with the platform capability-driven pattern proven on TÉO, without copying Transformômetro entity CRUD.

## Decision

1. **VISTA** is a **specialist capability** for operational TV displays — not a parallel conversational AI and not domain authority.
2. **`tv-dashboard-api`** remains the domain authority. Typed ops live in
   **PresentationMutation** (`presentation_mutation/` + `presentation_ops_content.json`).
   Writes go through **`TvPresentationWriteService`** (same boundary as the UI).
3. **Capability parity ≠ transport parity.** Fifteen typed presentation ops do not become fifteen GPT Actions.
4. **New typed presentation op ≠ new GPT Action.** Prefer catalog descriptor + existing `preview`/`commit`.
5. Canonical matrix: [`../integrations/vista-capability-matrix.md`](../integrations/vista-capability-matrix.md).
6. Forbidden: generic Action proxies; SQL/HTTP arbitrary execution; local GPT RBAC; service-account impersonation of end users.
7. **GPT Actions V2 (2026-09-22):** Writes use opaque server-side proposals — `gpt_preview_change` mints `proposal_handle`; `gpt_commit_change` accepts only `proposal_handle` + `confirmation` (+ `Idempotency-Key`). Lifecycle: `GOVERNED_PREPARE_COMMIT_V2`. Importable ops remain **8**.
7a. **Additive single-shot (2026-09-22):** For `confirmationPolicy=direct`, `gpt_preview_change` accepts `commit_now=true` + confirmation (+ idempotency header or body `idempotency_key`) to PREPARE+COMMIT in one Action. Destructive policy ignores `commit_now`. Invented handle aliases (`latest`, …) → `PROPOSAL_NOT_FOUND`.
7b. **Compound PlanCompiler (2026-09-22):** Catalog ops declare `produces`/`consumes`. Server topo-sorts declaration order; preview mints synthetic IDs; ACT binds real resources. Optional `as` / `playlistRef` / `slideRef` / `sectionRef`. Unsatisfiable plans → `DEPENDENCY_UNSATISFIABLE`.
7c. **PresentationMutation owner (2026-09-22):** Deep-merge nested block patches (`style`/`frame`/`dataBinding`/`background`). HTTP `/data/copilot/*` → **410 Gone**. Chat skill/tool `tv_dashboard_copilot` and MFE Copilot dock retired. **DÉLIA** may consume the same mutation contract via a future capability adapter — **TARGET only (no code in this epic)**.
7d. **Alias cleanup (2026-09-22):** Removed transitional `tv_copilot_patch_service` / `execution_context` / `plan_compiler` re-exports and `TvCopilotPatch*` type aliases. Canonical imports: `presentation_mutation`. Builder path: `to-presentation-ops` (`to-copilot-ops` → 410).
7e. **Naming hygiene (2026-09-22):** Renamed remaining catalog/planner modules and JSON from `tv_copilot_*` to `presentation_*` / `presentation_ops_content.json` (`PresentationOpsContentService`, planners, nested contract, telemetry). No second mutation path.
7f. **Deployable agent intelligence (2026-09-22):** Mutable VISTA behavior (`object_resolution` ALTER_EXISTING_BEFORE_CREATE, `screenshot_parity` PRINT_TO_TYPED_SLIDE_PARITY, modes, write_flow, anti_patterns) lives in `vista_agent_intelligence.json` → `capability_surface.agent_directives` via `gpt_get_catalog`. GPT Builder Instructions stay **stable-only** (identity + authority + invariants + “obey agent_directives in full”). Evolving heuristics = API deploy, not re-paste Instructions. **Forbidden:** expanding Builder Instructions with feature heuristics (regression gate in `test_vista_builder_instructions_budget.py`).
7g. **Owner-local data route discovery (2026-09-22):** `TvDataRouteDiscoveryService` ranks the TV allowlist for GPT `gpt_search_data_routes` and MFE `POST /data/routes/suggest`. Chat AI is **not** authority for TV suggest. Search requires NL query (no catalog dump). Preview accepts `{operationId, params}` validated against `paramSchema`. Live heuristics: `agent_directives.data_discovery` (`OWNER_LOCAL_ROUTE_DISCOVERY`).
8. **Do not adopt TÉO entity surface** (`search_records` / `prepare_record_change`) — VISTA is playlist/presentation workflow, not multi-entity CRUD.
9. **MCP** remains TARGET (Plugin + remote MCP). Do not create MCP in this change; keep application core adapter-ready.
10. **Proposal store:** in-process with **ACCEPT_WITH_RESIDUAL** for current single-replica runtime.

## Consequences

- Builder must **REIMPORT** OpenAPI and **REPLACE** Instructions after V2.
- Client-supplied `ops` + `planDigest` are no longer commit authority.
- Confirmation is enforced server-side (`CONFIRMATION_REQUIRED`).
- Catalog projects `capability_surface` (incl. live `agent_directives`) for discovery; AuthZ stays backend-first.
- Builder Instructions are **stable-only**; mutation heuristics evolve via API deploy (`vista_agent_intelligence.json`).
- Legacy `POST /data/copilot/*` returns **410 Gone** (successor: `/gpt-actions/v1`).
- DÉLIA TV adapter = documental TARGET on PresentationMutation; zero runtime coupling in this HEAD.
