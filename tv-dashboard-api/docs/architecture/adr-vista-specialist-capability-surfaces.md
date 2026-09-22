# ADR — VISTA specialist capability surfaces (GPT Actions / future MCP)

**Status:** DECIDED  
**Date:** 2026-09-22  
**Context:** Align VISTA GPT Actions with the platform capability-driven pattern proven on TÉO, without copying Transformômetro entity CRUD.

## Decision

1. **VISTA** is a **specialist capability** for operational TV displays — not a parallel conversational AI and not domain authority.
2. **`tv-dashboard-api`** remains the domain authority. Typed ops live in **TvCopilotPatchV1** (`tv_copilot_content.json`). Writes go through **`TvPresentationWriteService`** (same boundary as the UI).
3. **Capability parity ≠ transport parity.** Fifteen typed Copilot ops do not become fifteen GPT Actions.
4. **New typed Copilot op ≠ new GPT Action.** Prefer catalog descriptor + existing `preview`/`commit`.
5. Canonical matrix: [`../integrations/vista-capability-matrix.md`](../integrations/vista-capability-matrix.md).
6. Forbidden: generic Action proxies; SQL/HTTP arbitrary execution; local GPT RBAC; service-account impersonation of end users.
7. **GPT Actions V2 (2026-09-22):** Writes use opaque server-side proposals — `gpt_preview_change` mints `proposal_handle`; `gpt_commit_change` accepts only `proposal_handle` + `confirmation` (+ `Idempotency-Key`). Lifecycle: `GOVERNED_PREPARE_COMMIT_V2`. Importable ops remain **8**.
7a. **Additive single-shot (2026-09-22):** For `confirmationPolicy=direct`, `gpt_preview_change` accepts `commit_now=true` + confirmation (+ idempotency header or body `idempotency_key`) to PREPARE+COMMIT in one Action. Destructive policy ignores `commit_now`. Invented handle aliases (`latest`, …) → `PROPOSAL_NOT_FOUND`.
7b. **Compound PlanCompiler (2026-09-22):** Catalog ops declare `produces`/`consumes`. Server topo-sorts declaration order; preview mints synthetic IDs; ACT binds real resources. Optional `as` / `playlistRef` / `slideRef` / `sectionRef`. Unsatisfiable plans → `DEPENDENCY_UNSATISFIABLE`.
8. **Do not adopt TÉO entity surface** (`search_records` / `prepare_record_change`) — VISTA is playlist/presentation workflow, not multi-entity CRUD.
9. **MCP** remains TARGET (Plugin + remote MCP). Do not create MCP in this change; keep application core adapter-ready.
10. **Proposal store:** in-process with **ACCEPT_WITH_RESIDUAL** for current single-replica runtime.

## Consequences

- Builder must **REIMPORT** OpenAPI and **REPLACE** Instructions after V2.
- Client-supplied `ops` + `planDigest` are no longer commit authority.
- Confirmation is enforced server-side (`CONFIRMATION_REQUIRED`).
- Catalog projects `capability_surface` for discovery; AuthZ stays backend-first.
- Legacy `POST /data/copilot/apply-patch` may remain as non-persisting planner off the GPT façade.
