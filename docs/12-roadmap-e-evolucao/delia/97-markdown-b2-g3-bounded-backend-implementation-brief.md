# 97 — DÉLIA Markdown B2: G3 bounded implementation brief (CP-333)

**TASK_ID:** `DELIA-C3-MARKDOWN-B2-G3-CONTRACT-FIRST-IMPLEMENTATION-BRIEF-01`
**Date:** 2026-10-22
**Evidence HEAD:** `f9ac458e2ef46da0f09de838ea3339d76ae0ec1f` (GitHub `main` at briefing start). Revalidate HEAD, git status, worktrees, remote and all authorities before any Cursor runtime modification.
**Type:** DOCUMENTATION / ARCHITECTURE BRIEF ONLY. **No runtime code, flag or deploy changed.**
**Product decision:** Markdown B2 safe textual core may advance without internal L1 binding; external web links permitted only when safely admitted; Core owns platform AuthZ, Domain owns resource authority, Portal owns navigation; DÉLIA must not create privileged-link registry, private RBAC or synthesized internal routes. Prior L1-as-global-blocker statements are historical/superseded for this core slice.

## 1. Authority, phase and gates

Mandatory reanchor order: Project Instructions + `.cursor` / `AGENTS.md` → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → technical architecture → product spec → thematic 82, 83, 84, 90, 91, 96 → execution ledger (current SHA). The docs are already linked in the thematic trail, but this brief does **not** independently attest a current clean local working tree or live deploy. Resolve any conflict at higher authority before implementing.

CP-333 formal requirement (25 §5): safe textual Markdown `presentation.v2`, governed composition, secure links where admitted, clipboard and compatibility. G1/G2 independently `ACCEPT_WITH_RESIDUAL` (doc 89); prior L1 internal global blocker superseded by product decision of 2026-10-22; **G3 implementation brief is PREPARED FOR COORDINATION REVIEW, not self-approved**; G4 integration/browser QA `TEST_NOT_RUN`; CP-333 `PLANNED_NOT_PASS`. This document does not authorize production activation or phase advancement.

## 2. Owner and reuse gates

| Responsibility | Current owner / verified seam | EXISTING_EQUIVALENT | REUSE_DECISION |
|---|---|---|---|
| Existing structured safe projection | DÉLIA application/capability_provision `render_specialist_outcome` and current sanitizer | YES | EXTEND |
| Presentation envelope | DÉLIA application/interaction `compose_presentation(result)`; `serialize_result` | YES | EXTEND |
| Turn contract | Existing `InteractiveTurnResult` and typed governed attempt/result | YES | EXTEND only as needed, no untyped arbitrary dictionary crossing domains |
| Typed schema | `contracts/presentation-v2.proposal.schema.json` + v2 reader | YES | REUSE and promote contract only through G3 acceptance |
| Frontend parse and safety gate | `plugins/delia/src/api/presentation.ts` `parsePresentationV2` | YES | REUSE |
| Rich-text/code components | `ConversationMarkdown`, `ConversationCodeBlock` in `plugins/plugin-ui` | YES | REUSE |
| Data source and final rule | Domain API owners | YES | REUSE through existing provider-neutral boundary |
| Public URL admission | existing Markdown allowlist, outbound reference / source policy | YES for consumer; producer admission contract TO_INVENTORY | REUSE consumer; no arbitrary Markdown URL |
| Internal route and access | Portal navigation, Core live AuthZ + Domain authority | YES at platform ownership level | REUSE; internal links optional/future |
| New engine, model stage, standalone link RBAC | No legitimate need | YES existing presentation path | DO NOT CREATE |

Do not reuse Minha DELPI Chat runtime. No provider-specific conditional in planner.

## 3. Frozen shape and content constraints

The backend currently emits `presentation.version="1"` (source: `delia-api/app/application/interaction/presentation.py`). The MFE has a parse-only v2 reader: closed envelope `version/message_kind/semantic_status/grounding_status/blocks/allowed_interactions`, text block `kind=text, format=plain|markdown_safe, text`, notice block `kind=notice, role=owner_hint, text`. Max 8 blocks, 16,384 characters each. `authorized_links` is NOT a field of that closed envelope; do not add it silently. Frontend renderer has separate `authorizedLinks` prop (currently empty until admitted links exist).

Content classes per doc 84 §4.2:
- A: typed admitted `SpecialistOutcome.structured` → eligible for deterministic Markdown projection (presentation only; original leaf values, IDs, units, order, coverage and epistemic status preserved).
- B: owner `content_text` preformatted but without admitted typed structure → plain, verbatim.
- C: free model prose/status/unstructured output → plain, inert, even if it resembles Markdown.
- User style preference cannot authorize new facts/actions/links, nor force Markdown on B/C.
- Do not enable Markdown from `result.content` lexical guesses.

Legacy `content` remains human-readable plain text from same facts, not raw Markdown source. Do not duplicate source hints or expose private identifiers. Keep `confirmation_request`, `message_kind`, `allowed_interactions`, provenance, limitations, grounding, epistemic class, work gating, policy, idempotency and audit unchanged.

Fallback:
1. v1/absent v2 + independently valid safe legacy text → legacy plain.
2. Unknown contract version + safe bounded legacy text → legacy plain; otherwise neutral_error.
3. Invalid schema v2 / unsafe unadmitted content → neutral_error, no silent downgrade.
4. Valid admitted v2 with markup lexer failure → inert literal text, not HTML.
5. v2 plain → literal.
6. v2 markdown_safe valid → token allowlist renderer.

Allowed Markdown token subset from doc 84: paragraphs, emphasis, bounded headings, nested lists max 4, blockquotes, inline/fenced code inert, horizontal rule, and **only verified admitted links**. Exclude HTML, images, tables/GFM, Mermaid, remote media, arbitrary embedded controls/execute and unsupported nodes. Copy derives from approved tokens to readable plain text.

### Links in this bounded implementation

**External public HTTPS:** permit only when URL is verified/admitted by an explicitly legitimate trusted reference or source contract. Never infer from model text, untrusted owner payload or generic `url/href/*_url` names. Validate scheme, hostname, encoding, no secret query params, no javascript/data/blob/file/attachment schemes, no automatic opens; render in new tab with noreferrer/noopener. If producer has no proven admissible public-URL input at the owner boundary, emit **zero clickable links** in the initial slice and record deferred source binding, without blocking safe text Markdown.

**Internal Minha DELPI:** no new DÉLIA-private link service, RBAC, route construction, link lookup, or permission checks. Display legitimate internal references as plain text until optional official Portal/Core route contract is available; live access is decided by Core/Domain on navigation. No internal clickable link admission required for core B2 completion.

The prior doc 84 L1 conditional decision remains historical for a separate future navigation integration and may not be reconstructed as a blocker for core B2.

## 4. Bounded implementation order / files

**I0 — contract freeze/test RED**: validate current canonical authority, schema vs TS reader, owner output projection and `InteractiveTurnResult` propagation. Add RED tests characterizing A/B/C, schema, fail-closed behavior, security, v1 compatibility. If a typed field must be propagated from `SpecialistOutcome`, define owner/consumer/error/bounds/transport first; no generic `structured: Any` leak to frontend.

**I1 — backend projection**: minimally EXTEND the existing `render_specialist_outcome` deterministic projection (anticipated file `delia-api/app/application/capability_provision/orchestration.py`; exact seam reverify) to carry safe structured content projection alongside existing plain text through existing domain/application contract. No new formatter/service/registry.

**I2 — backend contract emitter**: EXTEND `delia-api/app/application/interaction/presentation.py` and actual serializer to select version 2 only for admitted typed structured response; emit `format=markdown_safe` only in that case, else emit plain/v1 in backward-compatible way according to the frozen schema. Maintain readable legacy content, notice and outcome fields; do not turn v2 on globally by config guess. Change schema/types/tests if strictly necessary, with explicit compatibility evidence.

**I3 — frontend integration only if real gap**: reuse `parsePresentationV2`, `ConversationMarkdown` and `ConversationCodeBlock`; no styling, parser or component API rewrite. If no incompatibility, zero frontend diff. Test real consumer including v1/v2 and streaming.

**I4 — integration/QA/review**: protocol and security eval, real Portal full-page/dock QA where supported, independent acceptance and deployment separately approved. Production rollout not part of this implementation task unless later authorized.

Proposed files to inspect/test (not preauthorizing every edit): 
`delia-api/app/application/capability_provision/orchestration.py`,
`delia-api/app/application/interaction/presentation.py`,
`delia-api/app/application/interaction/handle_interactive_turn.py`,
`delia-api/app/application/interaction/contracts.py` (confirm path),
`docs/12-roadmap-e-evolucao/delia/contracts/presentation-v2.proposal.schema.json`,
`plugins/delia/src/api/presentation.ts`,
`plugins/delia/src/ui/DeliaAssistantMessage.tsx`,
`plugins/plugin-ui` existing components/tests. No migration, additional model calls, MCP provider code or new backend service unless a reviewed conflict proves necessity.

## 5. RQ/AC traceability (all CP-333 requirements preserved)

Existing B2-RQ01–RQ25 documented in spec 83 §10 and AC01–AC30 §11. Do not erase, silently merge, or mark waived due to new product decision.

| Group | RQ | AC evidence |
|---|---|---|
| Contract, types, versions, compatibility | 01,02,05,09,18,23,25 | 01,07,08,17,23,28,30 |
| Factual source and governance | 03,06,07,16,19,20,24 | 09,10,11,12,18,21,22,24,29 |
| Renderer/reuse/accessibility/code/copy | 04,08,10,11,12,13,17,22 | 02,03,04,05,13,14,15,16,19,20,27 |
| Links and external security | 14,21 | 06,25,26 |
| Observability/evidence | 15 | 11,18,20,29 |

Link-specific AC25: for the **core** implementation, prove invented/internal-unauthorized URLs never become navigable, and internal reference remains inert without a platform navigation contract; future official Portal integration requires its own acceptance. AC26: public admitted HTTPS URL opens new tab safely; unverified URL remains text; if no approved public-URL producer exists, record `AC26_PARTIAL / PUBLIC_LINK_EMISSION_DEFERRED` and request a bounded follow-up—do not fabricate a passing runtime test. Classify every applicable RQ individually in implementation report. Any semantic change to CP-333 acceptance requires coordination review rather than silently calling reduced scope PASS.

## 6. Required executed tests and evaluations

- RED→GREEN: v1 output parity; v2 schema validation including message/interaction allowlists, oversized/unknown keys; JSON and NDJSON paths, malformed frames, partial stream, cancellation.
- A/B/C input permutations, no model/mcp Markdown interpretation, no changes to owner values, ordering, counts, units, IDs, temporal/coverage limitations, epistemic status and provenance.
- XSS/adversarial: `<script>`, `onerror`, `svg`, `iframe`, `javascript:`, `data:`, `blob:`, relative and spoofed schemes, unicode confusables, nesting/code giant strings, metadata prompt injection, path traversal.
- Confirmation/denial/source unavailable/processing timeout; READ vs PREPARE/ACT; never convert displayed code to execution, never lose typed confirmation or authorizations.
- External verified HTTPS vs unverified URL; internal unverified/unsupported path inert; no internal authorization claims.
- Copy fidelity, links labels, source hints dedupe, malformed admitted Markdown falls back literal, invalid v2 fails closed neutral.
- Full backend suite + frontend unit/typecheck/build/federation + Portal full-page/dock on real consumer with accessibility keyboard/SR/zoom 200%, dark/light; stale/unavailable QA `TEST_NOT_RUN`.
- No paid LLM local eval: use Ollama exclusively if a real model is necessary; deterministic no-model tests preferred. Model/version, SHA/config and safety/generalization/outcome evidence explicit.

Acceptance thresholds: ALL mandatory critical RQs IMPLEMENTED; AC required PASS; no security drift, no authority change, no material residual in producer; exact SHA/config and outcome evidence recorded. Test-green alone != CP-333 PASS.

## 7. Stop conditions

STOP → `EXECUTION_DRIFT` or `ARCHITECTURE_DECISION_REQUIRED` if: authority disallows current phase; source binding requires Core or Domain changes not in approved scope; output requires factual synthesis beyond ADR 58; plain-v2 mixed version clients lose data; model output becomes privileged Markdown or new fact; global flags/links bypass authorization; no safe typed structured projection can be carried; G1/G2 current approval differs from reviewed history; consumer needs new API or schema incompatible with closed reader; any material write gate changes.

Do not redefine contract on the fly. Revert accidental unapproved changes, preserve unrelated WIP and report decision issue for coordination.

## 8. Git, observability and expected report

Cursor (after G3 coordination approval) must reanchor, produce minimal RED/GREEN, residual-search, contract diff, docs/ledger factual updates, small coherent commits, ff/rebase-safe push to main and verify remote commit. Do not autonomously deploy. Emit:

```text
DÉLIA EXECUTION REPORT
TASK_ID=DELIA-C3-MARKDOWN-B2-G3-IMPLEMENTATION-01
BASE_HEAD=
FINAL_HEAD=
ORIGIN_MAIN=
PUSH_VERIFIED=
CURRENT_PHASE=
CP_RQ=CP-333; B2-RQ01..25
AC_MATRIX=B2-AC01..30 per-case PASS/FAIL/PENDING
EXISTING_EQUIVALENT=YES
REUSE_DECISION=EXTEND existing projector+composer; REUSE frontend
V2_CONTRACT=
PRODUCER_TAPS=
LEGACY_CONTENT_PARITY=
FORMAT_ADMISSION=
PUBLIC_LINK_POLICY=
INTERNAL_LINKS_INERT=
CORE_DOMAIN_AUTHORITY=
FACTUAL_SELECTION_ONLY=
GROUNDING_PROVENANCE=
PREPARE_ACT_GATES=
JSON_NDJSON=
NEGATIVE_SECURITY=
FRONTEND_QA=
MODEL_PROVIDER=NONE_OR_OLLAMA
EVALUATED_SHA_CONFIG=
FILES_CHANGED=
TESTS_EXECUTED=
RQ_COVERAGE=
AC_COVERAGE=
RESIDUAL_SEARCH=
DOCUMENTATION_LEDGER=
OUTCOME_EVIDENCE=
STOP_DRIFT=
RECOMMENDATION_FOR_COORDINATION=
```

## 9. Briefing verdict

`G3_BRIEF_PREPARED=YES`;
`G3_APPROVED_BY_COORDINATION=PENDING`;
`CP333_ACCEPTED=NO`;
`B2_RUNTIME_IMPLEMENTATION=NOT_STARTED`;
`B2_PRODUCTION_ACTIVATION=NOT_AUTHORIZED`;
`INTERNAL_L1_BLOCKS_CORE=NO`;
`NEXT=coordination G3 review → implementation prompt to Cursor`.

This document is a bounded execution brief, **not** a replacement for code review or the future execution prompt.


## 10. Architecture / Coordination decision — G3 bounded approval (2026-10-23)

**Review input:** Cursor gate report `DELIA-C3-MARKDOWN-B2-G3-IMPLEMENTATION-01`, inspected at `a530bc12dcfe5456425d4d6b2ffb475b373d9fec`, with ledger §6.383 recording STOP due to previously pending approval. Direct GitHub review reconfirmed v1 emitter, v2 proposal schema, existing frontend reader and the canonical CP-333 scope.

**COORDINATION_VERDICT_ON_GATE_REPORT=ACCEPT**: STOP was correct and runtime diff was zero.

**G3_BOUNDED_IMPLEMENTATION_APPROVAL=APPROVED_FOR_CURSOR** for I0–I3 + local tests and evidence, subject to current HEAD and canonical reanchor. This is a prospective explicit coordination approval for the bounded Markdown-safe backend producer contract, NOT a retroactive assertion of G3 implementation or CP-333 pass.

**Required first implementation gate (MUST-FIX):** reconcile `PROCESSING_TIMEOUT` from `presentation.v1` with the proposed v2 JSON Schema and `plugins/delia/src/api/presentation.ts` known message-kind allowlist; use existing canonical message vocabulary, no novel status. Write failing contract tests before changes. If schema/consumer contract cannot be reconciled additively, STOP and request coordination decision. No invalid v2 emitting unknown kinds.

**Allowed boundary:** `render_specialist_outcome` existing governed deterministic projection; minimal typed additive transport through actual application result contract; `compose_presentation` versioned serializer; required tests/schemas. No new registry, engine, model stage, provider branch or second RBAC. v1/legacy plain parity and metadata preserved. Class A admitted structured → Markdown deterministic; B/C plain inert. Public HTTPS links: emit only with legitimate admitted source, otherwise zero clickable links (not a blocker to text Markdown); internal Minha DELPI links deferred, never synthesize routes or authorize in DÉLIA. Existing v2 closed envelope DOES NOT include `authorized_links`; no unilateral schema expansion.

**Mandatory gate evidence:** RED→GREEN for status vocabulary, unknown-version/schema, malformed v2 neutral-error, valid renderer failure inert fallback, JSON+NDJSON, bounds/sanitization, XSS, grounding/provenance, confirmation/READ-PREPARE-ACT invariants, version migration/rollback, and existing full backend/frontend regressions. G4 browser QA/independent review remains separate, as does production deployment. No paid external LLM calls during local development; if a real model is required use Ollama only.

**Execution status after this decision:** `G3_TASK_BRIEF_APPROVED=YES`; `G3_IMPLEMENTATION=AUTHORIZED_NOT_EXECUTED`; `G4=TEST_NOT_RUN`; `CP-333=PLANNED_NOT_PASS`; `PRODUCTION_ACTIVATION=NO`; `I04_PHASE_UNCHANGED`. Executor must not self-accept; return SHA/config/tests/RQ-AC evidence for independent review.

**NEXT_BOUNDED_STEP:** Cursor resumes `DELIA-C3-MARKDOWN-B2-G3-IMPLEMENTATION-01` from current main, starts with I0 RED tests including PROCESSING_TIMEOUT, then I1/I2 minimal backend implementation, I3 frontend only if genuine contract mismatch, docs/ledger factual updates, commit/push and execution report. No deploy.

## 11. Execution record — G3 bounded implementation completed, pending independent review (2026-10-23)

`DELIA-C3-MARKDOWN-B2-G3-IMPLEMENTATION-01` executed I0–I3 inside the §10 approved boundary (ledger §6.384, spec 83 "G3 bounded implementation" section):

- `PROCESSING_TIMEOUT` reconciled additively in the v2 schema enum; RED suite (23 tests) → GREEN 23/23.
- I1: `RenderedSpecialistOutcome` + `render_specialist_outcome_rich` (Category-A-only deterministic Markdown projection, same sanitization/bounds; owner metacharacters escaped; zero synthesized links); typed transport `markdown_content` → `presentation_markdown`.
- I2: `compose_presentation` emits `version="2"` + `markdown_safe` only for admitted projections; legacy v1 envelope unchanged otherwise.
- I3: frontend zero-diff; real emitted envelope verified against `parsePresentationV2` (`status:"ok"`).
- Evidence: backend 2004/2004, delia 336/336, scoped regression 288/288, 15 negative checks PASS, schema conformance PASS, JSON/NDJSON safe.

`G3_IMPLEMENTATION=EXECUTED_PENDING_INDEPENDENT_REVIEW`; `G4=TEST_NOT_RUN`; `CP-333=PLANNED_NOT_PASS`; `PRODUCTION_B2=OFF`; executor did not self-accept — returned to coordination for independent review.
