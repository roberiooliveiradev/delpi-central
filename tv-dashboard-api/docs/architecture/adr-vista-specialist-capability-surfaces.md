# ADR — VISTA specialist capability surfaces (GPT Actions / MCP)

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
7h. **Chat handoff only (2026-09-22):** Internal Chat no longer mutates TV. Skill/tool `tv_dashboard_copilot` removed; content bundle `tv_dashboard_handoff` detects TV intent and returns a **direct answer** pointing users to **VISTA**. MFE modal is catalog-only («Fontes de dados»). Builder `POST …/turn` with `message` → `422 NL_TURN_RETIRED`. DÉLIA TV adapter remains TARGET on PresentationMutation (no runtime in this epic).
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
- Internal Chat: TV intent → VISTA handoff only (no mutation tool).
- DÉLIA TV adapter = documental TARGET on PresentationMutation; zero runtime coupling in this HEAD.

## Amendments / supersessions

### 2026-10-05 — MCP backend adapter implemented (supersedes item 9 in part)

The MCP adapter was subsequently implemented: `/mcp` mount, `interface/mcp`
adapter and **8 semantic tools** (6 READ + `prepare_change` + `commit_proposal`)
delegating to the same `GptActionsDispatchService` — no new domain or AuthZ
authority was created (the "keep application core adapter-ready" intent of
item 9 held). What remains **PENDING** is external provisioning: Keycloak
client `mcp-tv-dashboard`, provider/gateway go-live — see
[`../integrations/openai-plugin-mcp.md`](../integrations/openai-plugin-mcp.md).
DÉLIA TV capability adapter remains TARGET.

### 2026-10-05 — Governed-write authorization contract (commit `7d1cc86c61`)

Human-governed material writes now require, before permission/resource
authorization: an **end-user principal** (`principal_type == "user"`), a bearer
user credential and **fresh effective Core RBAC** (`load_user_rbac(force_refresh=True)`
— bypasses the permission cache, no stale fallback, fails closed when Core is
unavailable). Service principals are denied on every governed write surface and
cannot acquire orphan-playlist ownership via `try_claim_owner`. Bounded
exception: `POST /data/openapi/sync` remains an explicit INTERNAL ADMIN S2S
contract (`X-Delpi-Service-Token`, `TV_MANAGE`). Ownership unchanged:
Keycloak = AuthN, Core = effective RBAC, TV Dashboard = governed-write policy,
`PlaylistAccessService` = resource AuthZ, `TvPresentationWriteService` =
canonical writer. Reads and the shared `delpi_auth` defaults are unchanged.

### VISTA-OWNER-UNIFIED-CAPABILITY-INTELLIGENCE-BOUNDARY-02 — unified owner
### intelligence/capability boundary (Actions + MCP over one canonical source)

`capability_surface.py` was restructured as a **transport-neutral canonical
capability model** (neutral names = the MCP tool names, which carry no
transport prefix). Each adapter projects from it:

- `transport="mcp"` returns the canonical surface; the `agent_directives`
  projection neutralizes Actions-adapter annotations (`(Actions: …)`
  parentheticals are dropped, residual `gpt_*` tokens are rewritten through
  the canonical parity map) and strips the Actions `write_flow` mechanics
  (`surface`/`note`/`additive`/`destructive`) plus Actions-envelope metadata
  (`action_surface_budget`). Result: **zero** `gpt_*` callable names, **zero**
  `commit_now`, **zero** `additive_single_shot` in the MCP contract; the only
  `gpt_*` occurrences live inside `surface_parity.parity_map`, the canonical
  non-callable registry of Actions↔neutral names.
- `transport="actions"` maps every capability name through the inverse of
  `surface_parity.parity_map` and injects the Actions-only envelope
  (`commit_now` single-shot) — derived, never hardcoded a second time.

`vista_agent_intelligence.json` remains the single knowledge source; both
transports project the same `agent_directives` (Actions-compacted for the
~100 KiB envelope). `gpt_suggest_change` is now exposed on MCP as
`suggest_change` (ANALYSIS) over the shared
`PresentationCommandPlannerService`/`PresentationSuggestOpsService`
materializer — it never persists and never authorizes. MCP surface is now
**10 tools**; only `gpt_get_slide_preview_png` remains Actions-only
(asset fetch helper, `not_exposed_in_mcp`).

Owner-side quality corrections were also hardened:
`SlideLayoutQualityService` now evaluates **every** gradient endpoint of the
effective slide background (worst-ratio fail-closed, unknown/image
backgrounds never guessed), theme backgrounds resolve from canonical recipe
tokens, and `SafeAutoFixService` overlap relayout is **all-or-nothing** under
subset scope — a coordinated fix is never partially applied through
per-block filtering. DÉLIA runtime is unchanged.

## Addendum — VISTA-LIVE-EDITOR-VISUAL-VERIFICATION-003

Canonical visual evidence (`slidePreview.rendered`, `canonical_stage`) is produced
**only** by the authenticated user's live TV Dashboard editor — the visible
stage DOM (`resolveSlideExportTarget` + `captureSlideElementToPngDataUrl`),
captured on demand via a targeted `visual_capture_request` over the existing
presentation realtime WS and uploaded through `PUT …/rendered-preview` with
`source=editor_live` + `clientId` provenance.

- No autonomous renderer exists: the `tv-dashboard-render-worker`
  (Chromium/Playwright sidecar) is **RETIRED — not current runtime**; no
  background browser, no server-side screenshot engine, no second
  renderer. The name survives here only as decision history.
- Editor closed / focus stale → `rendered.status=unavailable`,
  `failureCode=EDITOR_NOT_OPEN`; structure/data/schematic remain available.
- Visible slide ≠ requested slide → `EDITOR_SLIDE_NOT_OPEN` (the backend never
  switches the user's slide).
- Missing/stale artifact with a live editor → `pending` /
  `EDITOR_CAPTURE_PENDING` (bounded resend ~8 s; caller retries bounded).
- MCP `ImageContent` only when `status=ready` **and** `source=editor_live`;
  artifacts without verified live-editor provenance never project as pixels.

Addendum — VISTA-MCP-IMAGE-DELIVERY-004 (host delivery):

- Server-side wire is **PROVEN** spec-compliant: real Streamable-HTTP
  `tools/call` emits `content=[TextContent, ImageContent]` +
  `structuredContent` with `mimeType=image/png`
  (`tests/test_mcp_streamable_http_wire.py`).
- `CHATGPT_APP_IMAGE_DELIVERY = FAIL_OBSERVED` — in the observed ChatGPT
  custom-app/connector runtime, `TextContent` + `structuredContent` were
  delivered but the image block did not reach the model (real VISTA
  invocation; corroborated by OpenAI Dev Community reports).
- `OPENAI_MCP_IMAGECONTENT_SUPPORT = INCONCLUSIVE` — current OpenAI docs
  describe tool-result `content` as model-visible without explicitly
  declaring `ImageContent` unsupported; the observed gap is a host
  runtime delivery gap (`HOST_RUNTIME_DELIVERY_GAP`), not a proven
  official contract. No workaround (base64-as-text, extra tool/action,
  vision service) is introduced.
- `VISUAL_RENDER` remains `TEST_NOT_RUN` until a host delivers the image
  block to a multimodal model and the model inspects actual pixels.
