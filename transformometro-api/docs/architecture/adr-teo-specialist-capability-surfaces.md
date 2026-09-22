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

## Consequences

- Process Documentation is exposed as governed entity `process_document` (0 new Action operations).
- Tasks and Interaction Room remain **DOMAIN_ONLY_BY_DESIGN** until a real TÉO use case + gate pass.
- DÉLIA↔TÉO integration stays **PLANNED** until a real adapter with user delegation exists.
