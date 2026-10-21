# 73 — DÉLIA · Conversational Response Intelligence & Personality Integration

**Date:** 2026-10-21  
**Status:** `PRODUCT_FRONT_REGISTERED / SPECIFICATION_PENDING / IMPLEMENTATION_NOT_AUTHORIZED`  
**Trigger:** Product Master requests a new product front after observing real production interaction in DÉLIA MFE on 2026-10-21.  
**Baseline reviewed:** GitHub `main` at `b3c97249411e4cdb75741b80d757f89088d315fa` before this registration; ADR [58](./58-adr-llm-semantic-decision-ownership.md), cleanup [72](./72-orchestration-structural-cleanup-execution-report.md), track [README](./README.md) and execution plan [16](../../16-execution-master-plan.md). **Project Instructions/.cursor, full thematic personality specifications and ledger contents were not independently verified through this connector; reanchor is mandatory before contract/design/implementation.**

## 1. Product problem and observed evidence

After the `delia-api` deployment was updated, Product Master screenshots show owner access working on multiple real questions. However, technical consultation success does not necessarily complete the user's task or result in a conversational response.

| Observed question (21/10/2026) | Outcome visible in screenshots | Product quality gap |
|---|---|---|
| “Qual é o último processo alterado no transformômetro?” | TÉO selected, 10 records located, grounded fields include `codigo_processo=PROC-0080`, name and `updated_at` for one record | A field-by-field technical dump; answer should lead with the result and explain basis, **but must not assert global latest unless owner order/universe is proven** |
| “use o davi para 3 exemplos de terminal bandeira” | DAVI selected, activity counts 1 record in API DELPI, final text “Nenhum resultado encontrado” | Potential technical-envelope vs business-result confusion; exact cause and business outcome `TO_INVENTORY`, not automatic PASS |
| “pesquise 3 exemplos de terminal grupo 1008” | API DELPI selected and 3 records displayed (IDs/names) | Valid examples displayed but generic field/list presentation with little conversational framing |
| “o que tem na minhas playlists da tv?” | VISTA selected; 10 records displayed with names/descriptions and raw booleans (`True/False`) | Opaque booleans and verbose dump; should organize factual items in a useful, scoped summary with optional detail |

Screenshot evidence is **user-supplied visual observation**, not a stored raw trace or proof of full owner data, ordering or request contracts. Distinguish `TECHNICAL_SUCCESS`, `GROUNDED_OBSERVATION`, `TASK_OUTCOME` and `USER_FACING_QUALITY`.

## 2. Product outcome and behavioral intent

DÉLIA should answer the user's **actual question**, not merely present returned field names, database identifiers or provider envelopes. Default style: professional, natural, clear and concise; lead with the answer, contextualize only what is supported, offer an appropriate follow-up when useful, retain sources and limitations, adapt detail and proactivity to explicit user preferences. Do not fabricate a brand-new personality specification here: **reuse previously defined DÉLIA behavior/personality documents after locating and validating their canonical paths and authority** (`PERSONALITY_SPECS=TO_INVENTORY`). Distinguish communicative personality (presentation policy) from authorization, factual authority, evidence and task-result truth.

## 3. Bounded workstreams (product planning only)

**R1 — Outcome-aware response:** use existing Evidence/Outcome/typed goal/contracts to determine whether question was answered; differentiate empty business result, zero match, one discovery/envelope, unavailable authoritative source and genuinely successful task; ensure requested count/ordering/scope are checked against owner facts. No new outcome engine unless an existing equivalent is disproven.

**R2 — Human-readable grounded presentation:** render known factual claims naturally with source and uncertainty, descriptive labels instead of field names, optional technical detail (IDs, raw booleans/JSON). Preserve owner-provided fields, scope, timestamps and attribution. Do not convert a sampled record into a globally latest record.

**R3 — Personality/interaction integration:** inventory all canonical personality, behavior, tone, proactive interaction and user-adjustment specs; reuse approved frontend shared components in `plugins/plugin-ui` and DÉLIA composition. Behavior: warm/professional rather than anthropomorphic claim, concise answer-first, selective next-step invitation, no repetitive prompting. Accessibility, compact/docked and full-screen responsive views remain within frontend ownership.

**R4 — Evaluation and quality:** finite acceptance matrix with real TÉO/DAVI/API DELPI/VISTA plus hypothetical/no-tool, incomplete arguments/multi-turn, no-results, conflicting counts, fabricated data resistance, owner failures and privacy/security. Evaluate factual fidelity, task completion, presentation, latency and provenance at specific SHA/config/model. Capture existing NDJSON activity when permitted; HTTP 200 and owner count are not outcome PASS.

## 4. Frozen architectural boundaries / required decision

ADR 58 and ledger §6.145 maintain **`selection-only` grounded synthesis**: model selects/organizes evidence but **does not author unrestricted enterprise factual prose**. The Product Master goal of conversational grounded phrasing cannot silently overwrite it.

Before designing an implementation that lets an LLM phrase business facts, return to coordination for an **explicit new ADR**: identify existing legitimate Evidence/Synthesis/Outcome contract, owner/consumers, typed propositions or claim IDs, source-linked content, grounding and verification, redaction/trust, negative tests, fallbacks, and migration/rollback. Until approved, improve answer-first layout using existing deterministic projections only where semantics are preserved. Avoid topic-specific templates, regex intent rules, per-provider branches, a second planner, or another general orchestration refactor.

Ownership: LLM semantic understanding/communication proposals; DÉLIA Evidence/Policy/Decision/Work/Outcome and validated presentation; Domain API source of truth, Core AuthZ; MCP/A2A untrusted interoperability; plugin-ui shared render-only components. No model output or provider data grants authorization. Writes remain PREPARE/ACT gated; no ACT implied.

```text
EXISTING_EQUIVALENT=TO_INVENTORY
REUSE_DECISION=PENDING_REUSE_FIRST
PERSONALITY_SPECS=TO_INVENTORY
RICH_FACTUAL_PROSE=ARCHITECTURE_DECISION_REQUIRED
SELECTION_ONLY=FROZEN_UNCHANGED
IMPLEMENTATION_AUTHORIZED=NO
DEPLOY_AUTHORIZED=NO
I04_ACCEPTED=NO
C3_EXECUTED=NO
```

## 5. Finite proposed acceptance criteria (not yet implementation contract)

1. The response answers the requested question in natural Brazilian Portuguese **only when owner evidence supports it**; otherwise makes a specific, truthful limitation.
2. No unsupported “último”, ordering, totals, identities or comparisons derived from partial pages or provider wrapper counts.
3. Natural response presents codes/dates meaningfully; raw field names, UUIDs and booleans are available as evidence details, not forced into lead prose.
4. No-results and ambiguous cases are distinguished from tool/transport successes.
5. Persona follows previously approved documented defaults and direct user preference without changing source authority, AuthZ or factual claims.
6. Model/provider-neutral behavior without keyword patches; bounded regression against owner/fake/real model, preserved 30s global and 12s post-orchestration fallback.
7. UI exposes owner/provenance and allows optional detail; no regression to screen layout or accessibility.
8. Include negative tests for hallucination, prompt injection, untrusted owner content and material action attempts.

## 6. Next bounded step

**`DELIA-CONVERSATIONAL-RESPONSE-INTELLIGENCE-SPEC-01`** = reanchor → locate authoritative personality/behavior specs and existing Evidence/Outcome/synthesis + shared frontend contracts → reuse inventory → product-to-contract mapping → determine whether a separate factual-prose ADR is required → deliver finite implementation split by legitimate owners. No code, runtime, schema or stage change during this specification step. Execution needs distinct authorization after review.

This front is **separate** from closed Q01–Q03 semantic refactor and Structural Cleanup 01. Previous functional I04 gate and C3 state remain unpromoted.
