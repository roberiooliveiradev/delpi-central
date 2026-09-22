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

## Consequences

- Process Documentation is exposed as governed entity `process_document` via prepare/commit (no dedicated Action CRUD routes).
- Tasks and Interaction Room remain **DOMAIN_ONLY_BY_DESIGN** until a real TÉO use case + gate pass.
- DÉLIA↔TÉO integration stays **PLANNED** until a real adapter with user delegation exists.
- Legacy CRUD Action routes remain as HTTP PREPARE shims (`include_in_schema=False`) until consumers are cleared.
