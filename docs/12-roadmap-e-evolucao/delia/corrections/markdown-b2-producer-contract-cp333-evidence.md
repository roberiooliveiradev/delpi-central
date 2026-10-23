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


## G3-RW-01 rework — leaf literal safety executed (2026-10-23)

TASK DELIA-C3-MARKDOWN-B2-G3-RW01-LEAF-LITERAL-SAFETY executed the bounded rework required by the independent review (df4008b44f), on base implementation 0602b5c6d0, after re-anchoring on origin/main (df4008b44f HEAD).

Fix (bounded to _md_leaf and immediate helpers): _MD_ESCAPE now escapes ALL CommonMark-escapable ASCII punctuation in leaf data (_MD_ESCAPABLE), and a new _MD_LINE_BREAKS translation normalizes CR, LF, CRLF and Unicode U+2028/U+2029 separators to a single space before emission. The guidance excerpt projection now routes through _md_leaf (previously a raw _MD_ESCAPE translate). Result: owner values and keys remain single-line literal text — embedded heading/list/quote/rule/fence/URL syntax cannot open new structures, links or autolinks. Escaped punctuation renders identically, so business values, identifiers, units and ordering display verbatim; the plain content body is byte-preserved (v1 parity unaffected — normalization applies only to the additive markdown projection).

Token-level evidence (shared renderer dependency marked): generated hostile structured data (embedded Attacker Heading, injected bullet, forged quote, horizontal rule, fenced code, bracketed link, bare https URL, www host, email, hostile key with ForgedKeyHeading) was lexed with marked.lexer inside plugins/plugin-ui resolution context: top-level tokens are only the projector-owned list nodes; STRUCTURAL_FOUND empty (zero heading/blockquote/code/table/hr/html tokens); LINKS empty (zero link tokens — escaping the scheme colon https\: breaks GFM autolink detection, verified by direct probe: https\:// produces no link token; www\. and user@example\. produce no autolink either). An earlier probe of the previous escape set proved marked still formed a link token from bracket-escaped input and bare URLs — the full-punctuation escape is what neutralizes it at the source.

RED to GREEN: 11 new adversarial tests failed before the fix (multiline values and keys, CR/LF/CRLF/Unicode separators, headings, lists, quotes, rules, fences, URL-like markup); focused suite 36/36 GREEN after the fix. One pre-existing assertion updated (literal script tag is now emitted escaped — strictly safer, no html token; display fidelity verified modulo backslash strip).

Regression and security: scoped backend regression 288/288; full backend suite 2017/2017; delia 336/336 plus tsc clean; 15/15 negative checks PASS (secrets redaction, depth/list/char bounds, fail-closed non-str/oversize/int markdown, NDJSON single-line); real v2 envelope carrying escaped hostile markdown round-trips through parsePresentationV2 to status ok with the markdown_safe source extracted. Residual search: every owner datum entering markdown passes _md_leaf; zero synthesized links; zero authorized_links in backend; zero eval/innerHTML. v1 byte parity preserved (plain content untouched); v2 schema unchanged; JSON/NDJSON compatible; no side effects outside the leaf escaping path.

STATUS=RW01_EXECUTED_PENDING_COORDINATION_REVIEW; IMPLEMENTATION_DIFF=orchestration.py(_md_leaf,_MD_ESCAPABLE,_MD_LINE_BREAKS,guidance excerpt routing)+test_presentation_v2_markdown_emission.py(+13 tests); CP-333=PLANNED_NOT_PASS; G4_BROWSER_QA=TEST_NOT_RUN; PRODUCTION_DEPLOYMENT=NO.


## Independent coordination review — G3-RW-01 (2026-10-23)

Reviewed implementation commit `082a8bda30382610a6b9f01c8e646e3efa4b91b0` directly via GitHub commit diff after the executor's report. Changed files: orchestration producer, focused tests, this evidence document, and ledger; no frontend/contract/runtime rollout diff beyond bounded leaf fix.

**VERDICT=ACCEPT_WITH_RESIDUAL** for G3-RW-01 only: the original defect in `_md_leaf` is addressed by escaping CommonMark ASCII punctuation and normalizing CR/LF/CRLF/U+2028/U+2029 in owner leaves. Guidance excerpt also uses the same mechanism. Reported token-level marked evidence includes no unauthorized heading/list/link/HTML from hostile leaves; 36/36 focused, 2017/2017 backend, 336/336 frontend and 15/15 negative tests are executor-reported PASS, **not independently rerun** by this GitHub review. No claim of G4 or browser QA completion.

**Residuals:** G4 actual Portal full-page/dock authenticated browser QA and accessibility TEST_NOT_RUN; AC22 user-requested style adaptation PARTIAL; AC26 public source-backed external link path DEFERRED (zero links emitted under current producer policy); CP-333 completeness and acceptance PENDING. Canonical coverage must count only fully IMPLEMENTED requirements, never `PASS_BACKEND`/PARTIAL/PENDING as completed globally. No production deployment or phase advancement is authorized by this review.

**NEXT_BOUNDED=G4 integration and independent acceptance review**, with existing real producer→JSON/NDJSON→typed consumer→plugin-ui renderer tests, mixed-version/fallback, owner-hostile data, clipboard, a11y, responsive dock/full-page, source/evidence parity and negative security on actual evaluated SHA/config. If authenticated browser runtime unavailable, report TEST_NOT_RUN; do not invent a visual PASS or deploy without separate authorization. Do not reopen G3 architecture except on new evidence.


## G4 integrated homologation — producer→consumer on evaluated HEAD (2026-10-23)

TASK `DELIA-C3-MARKDOWN-B2-G4-INTEGRATED-ACCEPTANCE-01` executed on `origin/main=090a817e56` (post RW01 acceptance a1e8ff36a3 + unrelated doc-103 commits), working-tree SHA evaluated with the three G4 test assets added. Executor role: integration/QA/evidence — no product-code change, no CP-333 self-acceptance.

**Reuse gate:** all responsibilities mapped to EXISTING_EQUIVALENT — `render_specialist_outcome_rich`, `RenderedSpecialistOutcome`, `compose_presentation`, `InteractiveTurnResult`, `presentation.v2` schema, `parsePresentationV2`, `ConversationMarkdown`, `ConversationCodeBlock`, `DeliaAssistantMessage`, existing sanitization. Zero new emitters/parsers/renderers; `ARCHITECTURE_DECISION_REQUIRED=NO`.

**Contract integration tests added (harness only):**
- `delia-api/tests/test_g4_integrated_homologation.py` — 21 tests over the REAL producer chain SpecialistOutcome → RenderedSpecialistOutcome → GovernedCapabilityAttempt → InteractiveTurnResult → compose_presentation → v2 envelope → JSON/NDJSON serialization: admitted structured/guidance outcomes emit `markdown_safe`; plain/conversational/records outcomes stay v1; hostile leaves stay literal; PROCESSING_TIMEOUT supported; malformed/oversized/non-string markdown fails closed to v1; grounding/provenance/epistemic/limitations preserved; zero links synthesized; v1/v1-client byte parity.
- `plugins/delia/src/api/__fixtures__/g4-wire-envelopes.json` — real producer-emitted v1/v2 envelopes serialized to wire JSON.
- `plugins/delia/src/api/g4Homologation.test.tsx` — 14 consumer-side tests: real fixture → `parsePresentationV2` → real `ConversationMarkdown` DOM + `conversationMarkdownToPlainText` clipboard projection; hostile values produce no navigable anchors/HTML/structural tokens; enabled=false literal `<p>` path preserved; clipboard text preserves IDs/order/units.

**Regression on evaluated HEAD:** backend focused 36/36 (markdown emission), G4 backend 21/21, G4 consumer 14/14, security negatives 15/15 (g3-negative-checks), full backend suite 2043 collected — all dots, zero failures, delia vitest 29 files/350 tests PASS, plugin-ui vitest 380 files/2315 tests PASS, `tsc --noEmit` clean, `vite build` + federation expose bundle OK. Token-level re-proof with the real `marked.lexer` (plugin-ui resolution): hostile RW01 corpus → top-level tokens only projector list nodes; STRUCTURAL=0, LINK=0.

**Authenticated browser QA (real stack, Keycloak SSO, user `e2e-delia`, `delia.access`+owner read grants):** environment initially had NO interaction handler wired (upstream `infra/.env` pointed DELIA_LLM_* at an external endpoint refused by the dev egress gate — `handler_not_configured` 503 observed end-to-end with honest frontend degradation + draft preservation, which is itself a PASS for the fail-closed error path). Harness-only fix: dev container env pointed at local Ollama (`DELIA_LLM_BASE_URL=http://ollama:11434/v1`), real `OpenAICompatibleModelInvocationAdapter` — no code change, local model only, zero paid calls.

Live results (Playwright, deployed MFE+API at HEAD):
- SSO login + deep route `/apps/delia`: PASS.
- Real conversational turn (NDJSON frames → `turn_result` v1 → rendered text): PASS — "Meu nome é DÉLIA.", `presentation.version=1`, NON_GROUNDED/HYPOTHESIS preserved.
- Real governed attempt → `mcp:vista`/`mcp:teo` provider_invoke → GROUNDED OBSERVATION records outcome (7 registros, IDs/excerpts verbatim): PASS — correctly emitted v1 plain (records shape is NOT an admitted markdown projection — fail-closed toward plain verified live).
- Governed attempt → owner AUTHZ denial → `PRECONDITION_REQUIRED` + `owner_hint` notice, zero privileged content: PASS.
- Clarification flow (missing capability inputs → typed question): PASS.
- `invalid_model_output` typed turn_error → honest "Resposta da DÉLIA inválida" + draft preserved: PASS (observed with weak local models).
- Clipboard real copy (navigator.clipboard.readText: 17/90/168/763 chars across turns): PASS.
- Evidence/details surface present (9–21 nodes): PASS.
- Keyboard Tab reaches interactive element; 420px dock same-turn identity; 320px zero horizontal overflow; 200% zoom no crash: PASS.
- `?delia-demo=markdown_code` fixture gate: correctly CLOSED in the deployed production-mode asset (negative control — the QA hook is unreachable in deployed builds).

**Markdown live-render = TEST_NOT_RUN.** No admitted structured/guidance outcome was reachable in this environment: the records-shaped owner result is intentionally not a markdown projection, and weaker local models (qwen2.5 1.5b/3b/delia-json system variant) repeatedly selected conversational/records/clarification paths. This is an environment/model-capability limitation, not a contract defect — the v2 path is proven by the 35 contract/integration tests above including the real emitted envelope through the real consumer renderer. No visual PASS is claimed for live markdown.

**Link policy:** zero links emitted everywhere (no admitted public source-backed URL; internal L1 deferred); `authorizedLinks=[]` at every seam; token-level proof zero link tokens; no parallel authority/navigation system. `PUBLIC_LINK_EMISSION=DEFERRED` unchanged.

**Residual search (current HEAD):** no `innerHTML`/`dangerouslySetInnerHTML`/`eval` in the DÉLIA ConversationMarkdown path (MarkdownDocument.tsx is a different legacy component not referenced by plugins/delia); every owner datum reaches markdown only via `_md_leaf`; no URL synthesis (http/https appear only in a technical-token redaction list); `authorized_links` absent in backend.

**RQ/AC reconciliation (conservative — PARTIAL/TEST_NOT_RUN earn no credit):** 20/25 RQ IMPLEMENTED (RQ08, RQ11, RQ20, RQ21, RQ25 PARTIAL); AC: 25 PASS / 5 PARTIAL (AC15, AC16, AC22, AC26, AC30). TASK_VERIFIED_COVERAGE_PCT = 20/25 = 80%.

**Post-push rebase note:** before push, origin/main advanced to 5cd91fbd (doc-104 retry isolation + production 60/3/300 activation commits — markdown seams `_md_*`/presentation untouched by the upstream diff). This commit was rebased onto it; focused suites re-verified on rebased SHA `daa5c9e725`: backend focused+G4 57/57, consumer G4 14/14. Full-suite counts above were recorded at 090a817e56.

**STATUS=G4_EXECUTED_READY_FOR_COORDINATION_REVIEW_WITH_RESIDUAL** — contract+integration+security+live-v1/error/governed-degradation paths proven on the evaluated SHA; live markdown render TEST_NOT_RUN (environment); CP-333=PLANNED_NOT_PASS, executor does not self-accept; PRODUCTION_DEPLOYMENT=NO.

**Material residuals:** (1) live full-page/dock markdown_safe render — TEST_NOT_RUN, requires environment with an admitted Category-A outcome (stronger local model or stubbed deterministic provider admission is NOT acceptable as evidence); (2) AC22 user style adaptation PARTIAL; (3) AC26 public link emission DEFERRED; (4) AC15/16/30 SR/dark-mode/reduced-motion not exercised; (5) `delia-json` Ollama variant + e2e user grants are dev-environment harness state, not product changes.

**NEXT_BOUNDED_STEP:** coordination reviews this homologation; if live markdown browser evidence is required for CP-333, provision a staging environment whose model reliably emits admitted structured outcomes (or accept contract-level evidence per spec 83).
