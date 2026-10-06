# ADR — TÉO specialist capability surfaces (DÉLIA / MCP / GPT Actions)

**Status:** DECIDED  
**Date:** 2026-09-22  
**Context:** Capability parity & surface governance after Process Documentation and related Transformômetro evolutions.

## Decision

1. **DÉLIA** is the DELPI AI / orchestration experience. **TÉO** is a **specialist capability** of transformação digital — not a parallel conversational AI product.
2. Transformômetro remains the **domain authority**. TÉO adapters (MCP, GPT Actions, future DÉLIA) only project governed capabilities.
3. **Capability parity ≠ transport parity.** One domain outcome may map to different tool/operation shapes per surface.
4. **New domain capability ≠ new GPT Action route.** Prefer `EXISTING_CATALOG_ENTITY` / existing operations. Action Surface Gate is mandatory; budget documented in [`../integrations/teo-capability-matrix.md`](../integrations/teo-capability-matrix.md).
5. Canonical matrix source: **`teo-capability-matrix.md`** (this ADR does not duplicate the full table).
6. Forbidden: generic Action/MCP proxies; local TÉO RBAC; service-account user impersonation on specialist surfaces; independent TÉO LLM/orchestrator/conversation store.
7. **GPT Actions V2 (2026-09-22):** Builder-visible writes use shared `GovernedWriteOrchestrator` — `gpt_prepare_record_change` / specialized PREPARE → opaque `proposal_handle` → `gpt_commit_proposal`. `commit_proposal` is **not** a generic proxy (executes only server-side prepared proposals). Lifecycle: `GOVERNED_PREPARE_COMMIT_V2`. Importable ops: **18** (was 21).
8. **MCP Surface V2 (2026-09-22):** Plugin/Agent tools use the same capability core — `prepare_record_change` + specialized `prepare_*` → `commit_proposal`. Lifecycle: `CAPABILITY_GOVERNED_V2`. Registered tools: **20** (was 33). Mechanical entity PREPARE/ACT pairs removed from discovery. MCP is a **capability adapter**, not DÉLIA internal authority. New CRUD entity ≠ new MCP tool. Business workflows keep semantic PREPARE.
9. **Diagnostic V1 MCP surface (2026-09-29):** Diagnostic capabilities exposed MCP-natively — `get_diagnostic`, `list_diagnostics_by_revision`, `prepare_create_diagnostic`, `prepare_manage_diagnostic` (13 closed actions) — all through the same governed `commit_proposal`. Registered tools: **24**. Zero GPT Actions operations (MCP_ONLY). See [`../domain/diagnostic-v1.md`](../domain/diagnostic-v1.md).
10. **Explicit confirmation hardening (2026-09-29):** MCP `commit_proposal` requires `confirmation` in the schema with **no default** — omitted confirmation never means confirmed. Bridge and legacy `tool_act_*` helpers propagate explicit confirmation; `GovernedActionsFacade.commit_proposal` remains the CONFIRMATION_REQUIRED authority. Confirmation ≠ AuthZ; fresh Core AuthZ still revalidates on ACT.
11. **Tool Surface Rationalization V1:** capability growth follows `business capability → semantic family → typed action → canonical use case`, not `Portal route → new tool`. Specialized PREPARE ops/tools were consolidated into semantic families with closed `action` enums: `collaboration` (tasks + interaction rooms), `evidence`, `meeting_minute`, `diagnostic`, `governed_operation` (revision activation, dashboard recalc, improvement package, shared-resource cost). `execution_policy` stays per-capability/action — never per-tool. Registered MCP tools: **19** (was 28); importable GPT Actions: **17** (was 22). `commit_proposal` remains the single ACT gate. Pre-family names are tombstoned (`MCP_LEGACY_REMOVED_TOOLS`); legacy bridge wrappers remain for internal callers only — never discoverable.

## Consequences

- Process Documentation is exposed as governed entity `process_document` via prepare/commit (no dedicated Action CRUD routes).
- Tasks and Interaction Room are exposed via the `collaboration` family (`collaboration_read` / `prepare_collaboration_change` / `gpt_collaboration_read` / `gpt_prepare_collaboration_change`) — typed actions delegating to `TaskCommandUseCases` / `InteractionRoomUseCases`; binary attachments stay `platform_blocked`.
- DÉLIA↔TÉO integration stays **PLANNED** until a real adapter with user delegation exists.
- Legacy CRUD Action routes remain as HTTP PREPARE shims (`include_in_schema=False`) until consumers are cleared.
- New Portal capability ⇒ new typed `action` in an existing family by default; a new tool/operation only by exception (real business boundary, Abstraction Gate).
