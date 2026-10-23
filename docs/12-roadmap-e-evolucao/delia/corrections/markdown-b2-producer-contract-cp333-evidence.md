# DÉLIA — Markdown B2 / Producer Contract / CP-333 — evidence and implementation gate

TASK_ID: DELIA-C3-MARKDOWN-B2-PRODUCER-CONTRACT-AND-CP333-01
Reviewed GitHub main HEAD: d63b8985c9db41f5bb4a0d22b0170e6112c3c1a2
Date: 2026-10-22
Status: INCONCLUSIVE FOR CONTRACT FREEZE; read-only review, no runtime modifications.

## Verified direct-source facts

1. `delia-api/app/application/interaction/presentation.py`: `PRESENTATION_CONTRACT_VERSION = "1"`. `compose_presentation(result)` emits `version`, `message_kind`, `semantic_status`, `grounding_status`, `blocks`, `allowed_interactions`. Allowed block kinds: text and notice; max 8 blocks and 16,384 chars per block. It reads governed `InteractiveTurnResult`, not arbitrary provider payload, and preserves the canonical message-kind and confirmation vocabulary.
2. `delia-api/app/application/interaction/handle_interactive_turn.py`: the serialized interaction field is `"presentation": compose_presentation(result)`, with legacy top-level fields retained. This is the confirmed producer/serialization edge.
3. `plugins/delia/src/api/presentation.ts`: the v2 reader is parse-only; version 2 requires a closed envelope of `version, message_kind, semantic_status, grounding_status, blocks, allowed_interactions`; v2 text blocks require `format = plain|markdown_safe` and `text`. The reader reports `not_v2|neutral_error|ok`. An unknown contract version does not coerce into v2. Malformed v2 returns neutral_error; calling layer must be traced before asserting user-visible fallback.
4. IMPORTANT discrepancy: `authorized_links` is NOT an allowed field in the examined v2 envelope or text block. It must NOT be added by the producer without a contract reconciliation/approved schema extension. The frontend comment explicitly says it does not invent authorized links.
5. The existing v1 producer does not emit v2 or `markdown_safe`; the v2 reader's presence is not runtime acceptance.

## Reuse gate

- Presentation composition: EXISTING_EQUIVALENT=YES; REUSE_DECISION=EXTEND existing `compose_presentation`.
- Interactive result/epistemic classification: YES; REUSE.
- Frontend typed v1/v2 readers: YES; REUSE.
- Frontend Markdown/code block: handoff reports implemented; runtime component and spec 96 verification remain TO_INVENTORY in this scoped connector review; DO NOT duplicate.
- Authorized link emission/admission: TO_INVENTORY due to missing v2 wire field; neither invent a new authority nor assume it is part of the producer contract.
- A second presentation engine: REUSE_DECISION=DO_NOT_CREATE.

## Boundaries and recommended finite implementation design (not authorized yet)

Preferred conditional direction: deterministic Markdown serialization of already-governed textual or structured presentation fields, emitted from the existing presentation boundary. Markdown is presentation, not factual synthesis and not an AuthZ channel. Preserve ADR 58 selection-only; no LLM stage added merely for formatting; no MCP/provider-specific branches. If content cannot be admitted, use existing plain path. Do not silently promote non-grounded data to grounded.

Before choosing version/format gates, resolve:
- Canonical docs 82/83/84/91/96 and CP-333 exact wording, owners, RQ/AC and phase against HEAD; current review has not fetched their verified canonical sections.
- How the MFE host selects `parsePresentationV2` and the response rendering gate; `presentationFault` and authorized-link transport, neither proven at this producer edge.
- Any prior frozen decision constraining Markdown tokens and link admission.
- JSON/NDJSON reader behavior on malformed v2, including no unauthorized link clickability.

No runtime code change, no deployment, no CP-333 acceptance claimed.

## Proposed bounded implementation package after contract gate

A. RED tests for v1 byte-for-byte compatibility, a grounded text block with admitted safe Markdown, non-grounded/clarification/confirmation cases, invalid token/link/HTML/code payloads, overlong content, unsupported format and plain fallback.
B. Extend existing composer/serializer with deterministic v2 opt-in only when frozen contract permits. Avoid new engine, registry, model step or provider branches.
C. Test actual JSON and NDJSON serialization, frontend parser/rendering, security controls, RQ/AC matrix and outcome on evaluated SHA/config.
D. Report factual evidence, docs and ledger; send to coordination for ACCEPT / REWORK decision. Deploy excluded from this documentary task.

## Current verdict

PRESENTATION_PRODUCER=compose_presentation version 1 (PROVEN)
PRESENTATION_CONSUMER_V2=parsePresentationV2 parse-only (PROVEN)
MARKDOWN_SAFE_BACKEND_EMITTER=NOT_IMPLEMENTED at reviewed producer (PROVEN)
AUTHORIZED_LINKS_WIRE=TO_INVENTORY; mismatch with conceptual brief
PRESENTATION_FAULT_WIRE=TO_INVENTORY
CP_333_ACCEPTANCE=NOT_PROVEN
GENERALIZATION_EVALS=TEST_NOT_RUN
RUNTIME_CHANGED=NO
DEPLOYMENT=NOT_APPLICABLE
ARCHITECTURE_DECISION_REQUIRED=YES_IF canonical CP-333 requires authorized_links outside current v2 contract or free factual prose
NEXT_BOUNDED_IMPLEMENTATION=BLOCKED_ON_CANONICAL_CONTRACT_RECONCILIATION; finite tests/package described above
REVIEW_RECOMMENDATION=INCONCLUSIVE pending formal CP-333 and thematic-spec verification


## Continuation audit — canonical reconciliation on 2026-10-22

Reviewed a newer GitHub main HEAD `ec5bc56ca953bb1b2518f27aa04b6df6b1aea5c3` (read-only snapshot; branch can move). Directly inspected `25`, thematic specs `82`, `83`, `84`, frontend report `91`, code-block spec `96`, proposed JSON Schema and actual Python/TypeScript presentation modules.

### Corrections to preliminary conclusions above

**Producer seam is two-layered, not `compose_presentation` alone** (doc 84 §4.3): `render_specialist_outcome` in capability_provision is the existing deterministic, sanitized structured-to-display projection to EXTEND for admitted typed Markdown; `compose_presentation` in interaction remains the existing serialization envelope to EXTEND for v2, preserving `InteractiveTurnResult.content` as readable plain legacy text. Do not introduce a second formatter. This replaces the simplistic earlier recommendation to extend only the envelope.

**Links are intentionally separate from the v2 envelope.** Doc 84 §2.1–§2.4 + the JSON Schema define the closed envelope without `authorized_links`; the frontend `ConversationMarkdown` receives a separate `authorizedLinks` input, currently `[]` from App (doc 91; spec 96). Therefore the earlier statement that `authorized_links` *must* be added to v2 as an envelope property is incorrect; that would violate the existing schema. The unresolved requirement is the governed L1 capability→structured typed link binding and its admissible delivery to the renderer, not an automatic new envelope field. `LINK_SOURCE_TYPED=L1_APPROVED_CONDITIONAL`; generic URL/href names are not enough and navigable link emission remains BLOCKED without owner disclosure contract.

**CP-333 is formally mapped** in `25-requirements-traceability.md` §5: Markdown textual only; `PLANNED`, not PASS. C/D/E richer charts/tables remain a separate traceability gap. Doc 83 reports G1 and G2 `ACCEPT_WITH_RESIDUAL`, G3 `BLOCKED`, G4 `TEST_NOT_RUN`, and no authorization for backend B2 runtime diff. Frontend-only renderer integration was separately authorized, not production B2.

**Three input classes frozen** in doc 84 §4.2: A — admitted typed `SpecialistOutcome.structured`, deterministic Markdown candidate; B — source-authored prestructured `content_text` remains plain; C — model/free prose/untrusted unstructured text remains plain. Never promote B/C to markdown merely on apparent syntax.

**Fallback** doc 84 §2.5: unknown version with independently validated safe legacy content → render_legacy; malformed v2 → neutral_error without silent downgrade; structurally valid v2 with renderer failure on admitted content → inert literal text; valid plain → literal text; no admissible content → neutral_error. Keep legacy `content` as plain human-readable output (doc 84 §2.6), not raw Markdown. `presentationFault` belongs to the frontend parse/render fault handling; verify its exact consumer wiring before asserting an API field.

**Positive evidence**: `plugins/delia/src/api/presentation.ts` parses explicit v2 block `format=plain|markdown_safe`, closed allowlist, `not_v2|neutral_error|ok`; backend `presentation.py` emits v1 only. Spec 96 §9–10 and report 91 describe renderer/code block implemented frontend with B2 OFF. No backend emission or runtime G3 acceptance is proven.

### Approved direction, but not authorization

EXISTING_EQUIVALENT=YES for both projection and envelope.
REUSE_DECISION=EXTEND `render_specialist_outcome` (projection) + EXTEND `compose_presentation` (envelope), REUSE `ConversationMarkdown`/`ConversationCodeBlock` and existing parser.
NEW_PRESENTATION_ENGINE=PROHIBITED.
MARKDOWN_LINKS=L1_CONDITIONAL, emission blocked until typed source binding.
MODEL_GENERATED_FACTUAL_PROSE=NOT_APPROVED.
ARCHITECTURE_DECISION_REQUIRED=YES if implementation proposes no-link runtime B2 contrary to D1/D6/D7, invents a new link source, or changes fact synthesis.
G3_TASK_BRIEF_APPROVED=NO; BACKEND_RUNTIME_DIFF=NOT_AUTHORIZED.
TESTS_IN_THIS_CONTINUATION=TEST_NOT_RUN (direct-source documentary inspection only).
DEPLOYMENT=NOT_APPLICABLE.

### Finite next bounded gates

1. Revalidate HEAD and the primary authority chain `16→50→17→49→51→52→21→20→25` plus ledger, and reconcile any new coordination review/ledger status.
2. Confirm the owner-published L1 mural capability semantics and binding (per doc 83 §0.8 / doc 90) or return to coordination. Do not bypass Domain owner or substitute generic URL fields.
3. Freeze G3 bounded requirements/AC per CP-333, producing only the existing two-layer extension path; only after approval implement RED→GREEN of v1 parity, v2 schema, input classes A/B/C, fail-closed fallback, JSON+NDJSON, governed links, code blocks inert, negative policy, full-page/dock QA and outcome.
4. Independent review and explicit rollout gate. No deployment in this documentary task.

STATUS=CANONICAL_FINDINGS_RECONCILED; IMPLEMENTATION_AUTHORIZATION=NO; CONTRACT_REVIEW=ACCEPT_WITH_RESIDUAL (historical G1/G2 independent decision, not self-accepted here).


## Superseding Product Master decision — 2026-10-22

The earlier statement that L1 internal binding must be completed before any G3 B2 core implementation is **SUPERSEDED**. Public HTTPS links may be clickable only when admitted under source/URL policy; internal links are optional and must not create DÉLIA-owned authorization. Core and Domain govern effective destination access; Portal handles navigation. No parallel permission system. G3 formal brief, allowed v2 producer contract, compatibility, negative tests and QA remain mandatory. Frontend/body and Markdown B2 runtime status are unchanged by this documentary update. Historical sections above remain trace evidence, not operative gates.


## G3 bounded implementation — executed, pending independent review (2026-10-23)

`DELIA-C3-MARKDOWN-B2-G3-IMPLEMENTATION-01` executed the approved I0–I3 boundary after formal coordination approval (doc 97 §10, commit `8252f1ea5a`; spec reconciliation `d11ef7ac88`).

Factual results: MUST-FIX `PROCESSING_TIMEOUT` reconciled in the v2 schema enum; RED→GREEN `test_presentation_v2_markdown_emission.py` (23 tests); `render_specialist_outcome_rich` + `RenderedSpecialistOutcome` (Category A deterministic Markdown only — B/C stay plain by construction); `compose_presentation` emits `version="2"`/`markdown_safe` solely for admitted projections; frontend zero-diff verified by real-envelope round-trip through `parsePresentationV2`. Backend 2004/2004, delia 336/336, scoped regression 288/288, 15 negative checks PASS, schema conformance PASS, JSON/NDJSON safe.

Public links: zero emitted — no admitted public-URL source exists at the producer boundary (registered deferral, `AC26_PARTIAL / PUBLIC_LINK_EMISSION_DEFERRED` per doc 97 §5); internal links remain inert and deferred.

STATUS=IMPLEMENTATION_EXECUTED_PENDING_INDEPENDENT_REVIEW; IMPLEMENTATION_AUTHORIZATION=G3_APPROVED_2026_10_23; CP-333=PLANNED_NOT_PASS (executor does not self-accept); G4_BROWSER_QA=TEST_NOT_RUN; PRODUCTION_DEPLOYMENT=NO.


## Independent G3 review — commit 0602b5c6d0 (2026-10-23)

**REVIEW_VERDICT=REWORK (bounded security hardening; not architecture drift).** Direct inspection of `origin/main=0602b5c6d02dbb1ad606667e6161c48c358823c5` and producer code confirms the approved two-layer projection, typed transport, v2-only gated emission and backend/frontend test assets. Cursor reports 2004/2004 backend, 336/336 DÉLIA, 23/23 focused and 15/15 negatives; these results were reported, not independently rerun in this GitHub-only review. No production deploy.

**Finding G3-RW-01 (content-to-Markdown structural boundary):** `delia-api/app/application/capability_provision/orchestration.py` `_md_leaf(value)` currently calls `str(value).translate(_MD_ESCAPE)`, but `_MD_ESCAPE` only escapes backslash, star, underscore, backtick and square brackets. Embedded CR/LF and other Markdown line-start syntax are not normalized or encoded. Untrusted owner field content such as `descricao: "ordinary\\n# Attacker Heading\\n- bullet"` can flow through `_md_format_structured` into a Markdown document where the leaf creates additional headings/list items. Frontend HTML execution protection does not, by itself, satisfy the frozen contract that owner leaves remain literal data and cannot choose the presentation hierarchy. Security/business semantic promotion risk; exploitation by multiline values must be characterized with real `ConversationMarkdown` token tests before declaring PASS.

**Bounded required rework:** (1) Add failing tests for CR, LF, CRLF, Unicode line separators, headings `#`, list markers `- `/`1. `, `>` quote, horizontal rule, fenced code and URL-like markup embedded in owner values AND owner keys; verify literal fidelity and no new structural nodes or navigable links using the existing frontend lexer/renderer. (2) Reuse existing Markdown literal/escape utilities where contractually suitable; otherwise correct only `_md_leaf` and immediate deterministic projection helpers, retaining meaningful text (e.g. safe line-break normalization). Do not corrupt ID/quantity/unit/ordering, introduce new framework/formatter or convert arbitrary owner prose to markup. (3) Confirm v1 byte parity, v2 schema, JSON/NDJSON, all scoped backend/frontend negative tests and no side-effect. (4) Record exact SHA/config and results; if unable to keep literal fidelity and representation simultaneously, STOP for coordination.

**Other acceptance residuals:** G4 actual browser QA and full-page/dock accessibility remain TEST_NOT_RUN. `PUBLIC_LINK_EMISSION_DEFERRED` due to missing owner-admitted URL; internal L1 deferred by Product Master. AC22 format adaptation is incomplete and must remain PARTIAL, not silently credited. The executor's reported `TASK_VERIFIED_COVERAGE_PCT=backend contract 100%` is not the canonical task completeness calculation when mandatory RQs are PARTIAL/TEST_NOT_RUN; recalculate conservatively only after rework and G4.

**REUSE_GATE:** YES; EXTEND existing producer only. **CP-333=PLANNED_NOT_PASS; G3_IMPLEMENTED_PENDING_REWORK; G4=TEST_NOT_RUN; PROD_DEPLOY=NO.** NEXT bounded: G3-RW-01 leaf literal Markdown boundary; then independent review and G4. No second design/inventory cycle.
