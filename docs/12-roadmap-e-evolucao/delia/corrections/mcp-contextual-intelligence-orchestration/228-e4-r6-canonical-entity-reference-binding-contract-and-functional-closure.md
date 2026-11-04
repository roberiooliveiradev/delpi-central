# 228 — DÉLIA · E4 R6 — canonical entity-reference binding and complete functional outcome

**Date:** 2026-11-03. **INPUT_SHA:** `af545421b9` (verified on main in coordination read). **DECISION_ID:** `DELIA-C3-E4-R6-ENTITY-REFERENCE-BINDING-DECISION-01`. **TASK_ID:** `DELIA-C3-E4-R6-CANONICAL-ENTITY-BINDING-AND-FUNCTIONAL-CLOSURE-01`. **Status:** `ARCHITECTURE_DIRECTION_APPROVED_WITH_GATES`; implementation unexecuted, no production deployment.

## 1. Reanchor / direct code proof

Read latest HEAD/status, .cursor rules, canonical 16→50→17→49→51→52→21→20→25, docs 02/24/42, ADR58, 103, 187–227, ledger. Phase/CP/NEXT are from actual HEAD, not this artifact. Concurrent unrelated repository changes must remain untouched.

Verified existing domain models at input SHA:
- `app/domain/evidence/model.py`: `EntityRef(entity_type, entity_id, source_system, label?, revision?)`, `EvidenceRef(evidence_id)`, `SourceRef(source_id, source_system, provider_name?, revision?, observed_at?)`. **Their documentation explicitly denies that refs are business authority or access grants.**
- `app/domain/interaction/model.py`: `SessionContext.entity_refs/evidence_refs/source_refs` and `InteractionTurn.evidence_refs/source_refs`; contextual refs are descriptive, not resolutions. Session is not source of truth/permission.
- `app/domain/planning/model.py`: existing `PlanStep.required_evidence_refs`, `PlanCandidate.evidence_refs/source_refs`.
- At R5, `_read_obligations_from_goal` regex-based numeric target builder was removed (git verified). `_TurnGoal` still uses semantic `business_subject` text without direct authoritative entity resolution. There is no demonstrated complete runtime passage from cross-turn scoped refs to live authorized target resolution. **Existing-equivalent YES for core reference types; live binding path PARTIAL/TO_INVENTORY.**
- This is NOT permission to declare `SessionContext.entity_refs` already populated correctly by production or to turn `business_subject` into an authoritative ref. Verify actual producers/consumers and transport request trust.

## 2. Architecture decision: REUSE canonical refs, don't create new truth

**EXISTING_EQUIVALENT=YES** for `EntityRef`/`EvidenceRef`/`SourceRef`/`SessionContext`; **REUSE_DECISION=REUSE/EXTEND` only bounded application binding.** New `TargetRef`, memory store, context engine, planner, entity matcher, registry, product-specific builder or migration is **NOT APPROVED**. Adding a small internal resolved-target collection or goal field is conditional on proving current consumers cannot transport the references; prefer existing DTO/port with explicit semantic distinction between candidates, validated reference descriptors and owner-backed results. Never claim an EntityRef itself proves an actual current entity or permission.

**Three trust stages (required):**
1. `RequestTargetCandidate` (conceptual, reuse existing fields where possible): literal/semantic referent from CURRENT user text or scoped conversation as untrusted candidate, preserving origin/turn order. Model may propose type/intent/relation. No regex business-ID inference, numerical arity assumption or owner identity claim.
2. `ScopedEntityRef` (conceptual existing `EntityRef` + proven session/turn binding): a descriptive pointer supplied by the legitimate interaction/owner evidence path. It is NOT authorization and may be stale or cross-user. No hallucinated refs from model. If ambiguous or unavailable, clarify or run legitimate capability discovery.
3. `ResolvedAuthorizedTarget` (conceptual resolved state **not a new Domain authority/type by default**): target descriptor confirmed by live capability/Domain result and current Core/Domain auth; carry owner, source, scope, evidence/provenance and completeness. Only this may seed source-specific factual evidence and comparison. Re-check on use; no chat text/LLM output as FACT.

**Owner chain:** Interaction Application supplies bounded conversation/session references already legitimately obtained; goal-understanding LLM proposes semantic operation and referent relationships only; Application binds proposed referents to scoped existing EntityRef if unambiguous; live Core/Domain/MCP authority validates access and factual target, existing subobjective/graph path carries result; Evidence verifier/Outcome determines answer; Pydantic AI handles typed proposal transport, LangGraph state/fan-in where proven. `EntityRef` is not capability authorization, `SourceRef` is not source authority, and `EvidenceRef` is not live evidence without dereference.

**No magical zero-LLM interpretation:** implicit `as duas` requires relevant, correctly ordered scoped references from earlier turns plus an intentional semantic relation proposal. When no legitimate refs exist, the deterministic runtime must not infer entities from prior prose; ask minimal clarification or authorized rediscovery, without blocking direct single-read. When a validated comparison goal has two valid scoped targets, avoid another unnecessary free-form decomposition and create only required authorized READ obligations using existing governed capability/arguments contract — not English/Portuguese hardcoded product query strings.

**Comparison goal robustness:** on Qwen3 `comparison_requested=False` but `goal_class=compare` or independently consistent typed proposal, follow existing semantic consistency/validation logic, do not introduce lexical keyword override. Correct contradictions with a bounded second semantic decision only when justified by tests and existing budget, never blanket retries. Persist no chain of thought.

## 3. Contract-first bounded execution sequence

**S0 reanchor + consumers:** inspect concrete producers of SessionContext / InteractionTurn / ConversationContextTurn, goal proposal/consumer, evidence results, authorized DAVI candidate tokens, LangGraph state. Trace one REAL A01→A02→A03 conversation to find where scoped refs are/aren't populated. Record inventory `YES/PARTIAL/NO`, do not infer runtime existence solely from types.

**S1 RED:** tests for two distinct refs across turns; same code/different owners; nonnumeric IDs; user correction; ambiguous `as duas` with 3+ prior entities; stale evidence; cross-session spoof; model proposal contradicting scoped refs; false `comparison_requested`; source count3 with wrong target; missing owner permission; nonexistent target; 5+ targets with no silent drop. Keep original read flows.

**S2 minimal binding:** use canonical EntityRef in existing bounded context/goal application contract; connect actual owner-backed structured evidence to future scoped references. A turn's assistant text, cached UI and model output alone do not create authoritative references. Use supported typed source/record refs and current request context only where proven. Adapt existing `_TurnGoal` or application request DTO when necessary; if breaking public shape/retention/authorization boundary, STOP with specific ADR/contract approval rather than silent change. Do not create a new generic reference service.

**S3 fulfil goal without needless decomposition:** once goal is validated and references are unambiguous, use existing subobjective tracker's typed needs and owner capability catalog to fulfill authorized READs. A model's free text is not an executable endpoint/selector. Reuse existing candidate selection/Domain API read and graph fan-in. No hardcoded product-specific instructions; no new planner.

**S4 full comparison correctness:** ensure requested target coverage is exact, independent of `sources>=2`; preserve EntityRef owners/source systems/scope/occurrence/cardinality and distinct codes across owners. Compare full records, hierarchy and units with deterministic verifier; false-common `10030012` must be rejected, true-common `10030015` included; partial/denied outcomes truthful, no model-generated factual prose (ADR58).

**S5 controlled model A/B:** repeat same-stage Qwen3 4B with same schema/prompt/context/temperature and recorded config, before/after binding corrections. If remaining model-origin failure persists, benchmark a larger model ONLY if already available and authorized locally as doc226/227 permits; log presence/config/quantization/latency p50/p95/real token usage/accuracy and cost envelope. No automatic model cutover, no generic timeout/retry inflation.

**S6 real acceptance:** repeat local real Keycloak/Core + DAVI/Domain + Ollama/Pydantic AI/LangGraph on final SHA: single-turn two-structure comparison, same-session A01→A02→A03 and correction, sibling case with unrelated entity type, ambiguous and unknown refs, AuthZ/revoked, stale prior evidence, concurrency/cancel; independent oracle on complete owner evidence, client-visible PT-BR grounded response reliably within gateway, no 504. Repeat minimum 5 original and 5 sibling unless genuine environment gate, and report any failures. Unit tests alone no acceptance.

**S7 regress/cleanup:** full relevant backend/adapter/graph/interaction/CRI/evidence/security tests and external outcomes on final SHA/config; prove code removed or simplified and no new parallel registry/planner/stores; update ledger and execution report; safe push main preserving concurrent modifications.

## 4. Measurable terminal gates

- `REF01` current user/session referent relationship correctly resolves to existing scoped EntityRefs, including correction, multiple entities and ambiguity.
- `REF02` Core/Domain validation authoritatively binds target at READ time; no model/cached text/SessionContext ref grants access.
- `REF03` existing contracts reused, no regex/product-specific builder or duplicate `TargetRef` service.
- `REF04` correct authorized READ obligations with exact source identities, no needless fourth compare subgoal; unrelated legitimate owner analytics remain allowed.
- `REF05` verifier compares EXACT intended sources, not just 2/3 collected; deterministic full oracle.
- `REF06` Qwen3 controlled stage reliability before/after and conditional model A/B are recorded.
- `REF07` client sees accurate, grounded, complete PT-BR comparison for single-turn and same-session in repeated final-SHA runs; no 504.
- `REF08` security (AuthZ, JWT delegation, isolation, injection, owner denial), concurrency, deadline, cancellation constraints and relevant regressions PASS on final SHA.
- `G04/G05/G07/G12` all PASS as doc221; otherwise `REWORK/INCONCLUSIVE/BLOCKED_WITH_EVIDENCE`.

**Approval:** Bounded extension of existing Application/context contracts with canonical EntityRef is approved as long as public contract, ownership, retention, frozen policies and security are unchanged. If actual consumer inventory shows missing legitimate persisted/session reference binding requiring new public schema/store/retention policy, return specific `ARCHITECTURE_DECISION_REQUIRED`, not a fabricated new type. **No production deployment or phase advance.**

## 5. Devin master instruction

**TASK_ID=DELIA-C3-E4-R6-CANONICAL-ENTITY-BINDING-AND-FUNCTIONAL-CLOSURE-01**. Reanchor main and all authorities. Execute doc228 S0–S7 as one authorized program. Before claiming missing reference capability, prove existing EntityRef/EvidenceRef/SourceRef/SessionContext producers and consumers. Bind scoped session references into semantic-goal handling without turning history/model into FACT. Validate/revalidate targets through live Core/Domain-capability owner; use existing graph to fulfill minimal authorized READ obligations without regex or product-hardcoded prompt building. Ensure comparison matches exact requested evidence and deterministic oracle, repeated same-session and single-turn real Qwen3+DAVI E2E with client-visible grounded responses and bounded latency. If 4B is still intrinsically unstable after correct reference binding, run already-authorized local available larger-model A/B; no cutover. RED→GREEN, full regression, adversarial/sibling, evidence, report, ledger, safe main push. Do not stop after diagnosis/first GREEN; report functional candidate only if REF01–REF08/G04/G05/G07/G12 pass; otherwise precise authority or infrastructure blocker. Production deploy not authorized.


## 6. Coordination review after S0 — continue same R6 task; correction of contract inventory (2026-11-03)

**INPUT_SHA:** `91716edd31`, verified main. **STATUS:** `S0_ACCEPTED_WITH_CORRECTION / R6_IMPLEMENTATION_PENDING`; NO new planning round. S0 commit updated **only the execution-ledger**, not runtime. **THE SAME R6 TASK MUST EXECUTE S1–S7** without returning S0-only as its terminal deliverable.

### Direct source correction (code checked at input SHA)

- `EntityRef`, `EvidenceRef`, `SourceRef`: **PROVEN** in `app/domain/evidence/model.py`.
- `SessionContext.entity_refs`: **PROVEN** in `app/domain/interaction/model.py`.
- `InteractionTurn.entity_refs`: **NOT PRESENT** in `app/domain/interaction/model.py` (contains `evidence_refs`, `source_refs`, but no `entity_refs`). The S0 ledger/report statement claiming an existing `InteractionTurn.entity_refs` is **FACTUAL_DRIFT**; do not implement it as if already existing.
- `handle_interactive_turn._grounded_result` currently writes only `source_refs` to `InteractionTurn` and `InteractiveTurnResult`; complete owner outcome exists as `attempt.outcome` only before projection; trace exact lifecycle before choosing where to project references.
- `GovernedCapabilityProvenance.source_refs` references source origin, **not specific business entity**. Never convert a source ref or transport capability name into an `EntityRef` without typed real owner-record validation.
- The runtime producer/consumer of `ConversationContextTurn.entity_refs`, actual serialization and whether client-supplied prior-turn fields are trustworthy MUST be verified; typed fields in a contract do not prove provenance. **A client could replay forged references** if server fails to correlate with authenticated session or fresh owner evidence.
- S0's notion of simply wiring `InteractionTurn.entity_refs` is not currently an existing field. A small additive **internal** field may be created if legitimate consumers require it, under existing doc228 approval, but only after producer/consumer/transport analysis and no change to public HTTP/session retention behavior; if public schema/retention changes are required, STOP the affected contract decision.

### Mandatory S1–S7 execution focus (no handoff loop)

1. Write RED tests for (a) accurate owner-backed entity refs at grounded turn close, (b) absence/partial/ambiguous owner data yields no fabricated ref, (c) binding references to the SAME authenticated session/turn source, (d) cross-user/session client spoof/replay cannot grant a verified referent, (e) corrected `as duas` reference order and three-entity ambiguity, (f) real two-tree result/negative AuthZ.
2. Prefer existing context/attempt/model objects and minimal additive internal projection to carry typed entities where they have **legitimate producer evidence**. Never create a new TargetRef/store/registry. Distinguish owner record codes (typed) from arbitrary extracted strings in model-created payload; owner still revalidates ref at read time.
3. Implement same R6 producer→consumer binding through existing Application boundaries, and prove exactly where grounded evidence is turned into scoped context, how `ConversationContextTurn` is reconstructed securely, and how reauthorization occurs on follow-up. Do not put untrusted user-provided entity_refs into an elevated trusted channel.
4. Reuse current semantic goal proposal and authorized capability selection; build READ obligations without another product-specific natural-language builder or numeric regex; if no generic typed requirement can be transported in the existing SubObjective/port, document the *minimal* additive internal contract with consumers and compatibility, then implement only if within bounded approval. No new planner.
5. Verify exact intended target set vs owner-backed source-set, preserve entity scope, owner and duplicate occurrence distinction; correct oracle and normal PT-BR response, no extra analysis owner unless legitimately requested.
6. Run final SHA real local Qwen3/Pydantic AI/LangGraph/Keycloak/Core/DAVI-typed outcome, both one-turn and same-session A01→A02→A03, with repeated, sibling, negative, unknown, revoked/cancel and gateway timing tests. Report **all** trials, stage failure taxonomy and exact authoritative proof; no lucky single 200.
7. Complete REG/REF01–REF08/G04/G05/G07/G12, cleanup, docs/ledger, safe main commit/push; report `FUNCTIONAL_ACCEPTANCE_CANDIDATE` only if ALL mandatory customer-visible outcomes verified. Otherwise precise governance/external blocker, not another S1-only inventory return.

**S0 ACCEPTED:** factual search for missing wiring; **S0 CONTRACT ASSERTION CORRECTED:** `InteractionTurn.entity_refs` not present. **CONTINUE_TASK:** `DELIA-C3-E4-R6-CANONICAL-ENTITY-BINDING-AND-FUNCTIONAL-CLOSURE-01`, stages S1–S7. **PRODUCTION_DEPLOY=NOT_AUTHORIZED**.


## 7. Coordination review after S2–S4 implementation at fe6f722a42 (2026-11-03)

**REVIEW STATUS:** `REWORK / EXECUTION_DRIFT` for referential trust and repeated product-specific goal strings. **CODE SHA:** `fe6f722a42`, verified current main at review. The R6 implementation added actual code, but S1/S5/S6/S7 and final real E2E are `TEST_NOT_RUN`; functional acceptance remains `NO`.

### Source-confirmed findings

- `interaction_routes._parse_context` accepts client-supplied `entity_refs` (bounded up to 8 per turn, required type/id strings), without cryptographic or live session-turn correlation. Formatting validation does NOT validate provenance.
- `HandleInteractiveTurn._validate_prior_context` checks kinds, epistemic class, alternation and character budget but does not attest that `entity_refs` were issued by the server as the grounded result of that same authenticated session. Accepting a client-echoed ref as "previous grounded ref" changes reference binding trust, even though downstream Domain AuthZ still validates access.
- `_subobjectives_from_session_refs` collects `prior_turns[].entity_refs`, sorts and takes first four with `[:4]`, not semantically selected exactly requested targets; this may silently drop requested targets and choose wrong ones if the conversation contains three or more. It creates a product-like fixed textual subgoal `"Consulte as informações completas de {entity_type} {entity_id}"` rather than carrying a typed authorized target through the real governed READ contract. This reintroduces the fragile string-builder pattern prohibited by docs 227–228.
- `_entity_refs_from_outcome` produces one root EntityRef from typed `_comparison_records(outcome)` and provenance specialist id. Confirm `source_system` semantics against authoritative owner/source record; the specialist/interoperability id is not automatically the canonical source system. A single `min(path)` root may be ambiguous if multi-root or mixed source results; do not invent a source identity.
- `InteractionTurn.entity_refs` now exists and is set for grounded results, but `InteractiveTurnResult` has no `entity_refs` field; `interaction_routes` returns `serialize_result(result)`. A user-facing projection carrying refs is **NOT verified or implemented** by this code.
- S1 RED tests, S5 exact target coverage, real E2E and full regressions were **not executed** (executor admits this). No user-facing functional result has been proven.

### Mandatory corrective sequence — same R6 task, no more intermediate documentation-only returns

**C1 TRUST FIRST (RED):** simulate forged `context[].entity_refs` in DELIA_RESULT, different session, actor swap, injected `OBSERVATION` labels, owner mismatch, original turn content/ref mismatch, stale/denied source and forged source_system. Prove these cannot activate authoritative target binding or cross-user context use; Domain/AuthZ must still deny real unauthorized READs. A ref returned to a client remains untrusted on replay unless explicitly server-attested/session-checked.

**C2 USE EXISTING SESSION PROVENANCE:** inspect real interaction session lifecycle, server-owned turns, `SessionContext` producers, context transport and authentication-scoped state. Prefer server-side lookup of already trusted refs by session/turn ID through existing legitimate Application interface; avoid adding persistence, public `entity_refs` echoes or opaque tokens by default. If the current runtime is genuinely stateless, the architecture decision must explicitly cover an additive, bounded, authenticated session-bound reference attestation/receipt using an established trusted mechanism, with expiry, replay prevention/scope and no secrets in prompts or logs. **Do not implement a new store, signing system, or public contract silently**. A mere ref list from client is NOT sufficient.

**C3 CANONICAL SOURCE REFS:** map root business record to real `EntityRef` fields with owner/domain metadata, not `specialist_id` as unproven source_system. Map multiple roots and missing/mixed record identities to explicit ambiguity/insufficient, not `min(path)` arbitrarily. No regex/no source ref elevation/no silent identity overwrite.

**C4 TYPED CONSUMER:** remove fixed textual `SubObjective.goal` business query builder; reuse/extend existing internal typed binding where real consumer exists. Distinguish a validated target set from all historical refs; when 3+ candidate entities exist, let the existing semantic model propose selection and validate against authorized scoped refs, or ask clarification. Never silently `[:4]` the sorted list. No new planner/engine/registry or endpoint selector.

**C5 CONTRACT GATE:** if server-owned session refs cannot be read and legitimate ref transport requires a new public request/response schema, expiry/retention, backend lookup or signed handle, STOP only the affected scope with `ARCHITECTURE_DECISION_REQUIRED`. Provide exact request/response, owner, consumers, threat model, session/actor binding, compatibility, limits, observability, expiry and revocation, and authorization checks for separate approval. Do independent C1/C3/C4 tests and fixes where safe. Do not use the absence of a transport to justify insecure client echo.

**C6 IMPLEMENT AND EVALUATE:** RED→GREEN, verify original and sibling product/other-owner references, same-session `A01→A02→A03`, direct single-turn, correction/ambiguity, mixed roots, spoof, owner revocation, timeout/gateway, model proposal variability, evidence full tree oracle, HTTP/NDJSON actual client output. Run full relevant suite and repeat trials on FINAL SHA. `REF01–REF08 / G04/G05/G07/G12` all mandatory.

**STOP CLASSIFICATION:** `EXECUTION_DRIFT` on unvalidated client-origin refs and text-hardcoded typed goals; `REWORK` until corrected. **PRODUCTION_DEPLOY=NOT_AUTHORIZED**. This review does not authorize expanding public APIs, storage, session retention or authority.


## 8. Coordination decision after §7 implementation at 65eacb396c (2026-11-03)

**INPUT_SHA:** \`65eacb396c\`, verified against main for DÉLIA sources; subsequent unrelated production-control changes were preserved. **REVIEW:** \`REWORK\`, with a genuine **cross-request provenance/continuity contract decision**; no functional acceptance. Coordination did not run local E2E.

### 8.1 Verified facts vs unsupported conclusions

1. **PROVEN:** \`HandleInteractiveConversationTurn.execute()\` constructs a fresh \`InteractionSession(session_id=uuid4())\` per HTTP request. Its module-level request-scoped/no-history note is consistent with the code. \`prior_turns\` come from incoming request context, parsed by \`interaction_routes._parse_context\` and checked for well-formed sequence, but not cryptographically or server-side correlated to prior issued result turns.
2. **PROVEN:** \`_entity_refs_from_outcome()\` now uses \`provenance.source_refs[0].source_system\`, instead of \`specialist_id\`. This removes the specific conflation of specialist transport and source-system, but does not prove a single unambiguous owner business root in multi-root/multi-source results. SourceRefs are source descriptors, never grants.
3. **PROVEN:** \`_subobjectives_from_session_refs()\` iterates \`reversed(prior_turns)\`, takes \`list(distinct.values())[:4]\`, and constructs \`SubObjective(goal=f"{ref.entity_type} {ref.entity_id}")\`. These are still **positional recency heuristics and text-synthesized READ goals**, not a genuinely typed target obligation or exact semantic referent selection. With 3+ prior entities, "as duas" is not guaranteed to resolve correctly; with 5+ it silently drops refs. Do not mark doc228 S4/REF01/REF03/REF04 complete.
4. **PROVEN:** \`InteractionTurn.entity_refs\` now receives internal owner-derived pointers. **NOT PROVEN / absent in reviewed response contract:** user-facing \`InteractiveTurnResult\` did not acquire an \`entity_refs\` field; the JSON path calls \`serialize_result(result)\`. There is no proven reference-echo field leaving HTTP, and no trust attestation for a replayed value.
5. **SECURITY PRECISION:** client-provided \`entity_refs\` can be treated as **untrusted semantic candidate data** for authorized discovery/READ, but **may not be promoted to a trusted "server-issued previous grounded reference"**. Live Domain/Core authorization still protects the requested READ; it does **not** validate that the read target represents the user's intended prior referent or that the echoed history is truthful.
6. **CONCLUSION:** absence of server session persistence makes *server-owned history lookup unavailable through the reviewed handler*, but does NOT logically prove that **new persistent storage is the only solution**. Other approaches (request-scoped candidates + clarification or existing attested continuation mechanism) need evaluation at their real boundary. No new store, signing scheme, token format or public API is silently approved.

### 8.2 Architecture decision — preserve stateless mode, choose the minimum honest continuity path

**DECISION_ID:** \`DELIA-C3-E4-R6-STATELESS-CONTINUITY-BOUNDARY-DECISION-01\`.
**APPROVED NOW:**
- Keep the current request-scoped/session-nonpersistent architecture by default. Do **not** add a server session DB or retention/migration just to rescue E4.
- Allow bounded client-carried context only as transient **untrusted candidates**, irrespective of whether it is well-typed or previously emitted by the DÉLIA UI.
- Use currently authorized discovery/resolver + live Core/Domain verification for proposed targets. Require accurate **semantic intent and exact intended target-set matching** before full comparison outcome. When "as duas" is ambiguous without a legitimate evidence-backed referent binding, ask a targeted clarification rather than silently compare recent four.
- If a model/legitimate owner can resolve explicit targets via the existing authorized request, compare them without relying on untrusted historic FACT. Do not force new persistence as a prerequisite for single-turn E2E.
- Fix source provenance/ambiguous roots and deny incorrect/fabricated refs; remove silent \`[:4]\` and string-generated subgoals. Only use a truly typed existing capability/arguments boundary; if missing, freeze a minimal additive **internal** contract with owner and consumers, not a second planner.
- Continue **independent** tests and single-turn E2E, and test same-turn continuation as honest clarification when provenance cannot be established.

**CONTRACT GATE REQUIRED FOR TRUSTED CROSS-REQUEST CONTINUITY:** If the product requirement is that "as duas" reliably refers to previously observed and validated entities **without reconfirmation**, the present stateless echo cannot prove origin/actor/session. First inventory existing trusted continuation/receipt/token infrastructure and current client contract. If a suitable mechanism already exists, **REUSE** through its owner, with subject, turn/conversation identity, bounded refs, TTL, anti-replay/scope, compatibility and server-side verification. If none exists, return a **single concrete architecture decision** contrasting: (A) stateless authenticated bounded receipt/attestation at an authorized existing boundary; (B) server-owned session state with explicit retention/cleanup/revocation; (C) untrusted context + clarification as an intentionally reduced UX. This requires product/security/contract approval before new public fields, persistence or signing. DO NOT assert "storage is mandatory" nor implement an ad hoc signer/cookie/database.

**FORBIDDEN:** taking \`context[].entity_refs\` plus \`kind=DELIA_RESULT\` plus \`epistemic_class=OBSERVATION\` as proof of prior DÉLIA issuance; treating successful Domain READ of the wrong entity as a grounded fulfillment of the intended comparison; adding any client echo field before the trusted/untrusted contract is explicit.

### 8.3 Evidence and completion obligations — continue one R6 task, no another documentation-only terminal

- RED tests: client-forged DELIA_RESULT/entity_ref; swapped actor/session; wrong owner system; 3/5 historical refs and "as duas"; a repeated/revoked source; mixed multi-root owner output; fabricated entity type; explicit two-target direct request; no referenced entities; broad sibling read. Ensure authenticated user permissions still apply at every actual Domain READ.
- Repair minimal SOURCE producer: choose an entity only if owner evidence confirms a singular typed business root and canonical source system, otherwise produce no entity ref or bounded ambiguity.
- Repair consumer: typed validated target set or explicit clarification (not reverse-and-take-first-four and not \`f"{type} {id}"\`). Do not issue uncontrolled owner requests from an untrusted echoed ref and call them authorized prior referents.
- Prove exact source-target reconciliation, no fabricated provenance and final factual verifier oracle. Do not mark \`sources>=2\` as exact coverage.
- Run full relevant RED→GREEN regression on final SHA; real local Keycloak/Core+DAVI/Domain+Qwen3 same-turn, and same-conversation with **declared continuity mode** (clarification or legitimately attested refs), client-visible response and gateway/cancel timings. Record all success/failure runs.
- Treat the existing E4-R6 \`REF01–REF08\` and \`G04/G05/G07/G12\` as \`NOT_PASS\` until outcome evidence. No production deploy, no phase advance.

**COORDINATION VERDICT:** \`R6_REWORK\`; \`CROSS_REQUEST_TRUSTED_CONTINUITY=ARCHITECTURE_DECISION_REQUIRED\` if required without clarification and no reusable attestation mechanism; \`PERSISTENCE_SPECIFICALLY_APPROVED=NO\`; \`CLIENT_ECHO_AS_AUTHORITY=NO\`.


## 9. Coordination verification after e1fb2dc330 — §8 candidate binding is NOT yet typed/authenticated

**Input SHA:** \`e1fb2dc330\`, verified identical to main when reviewed. **Status:** \`REWORK\`; no final-SHA real E2E or full regression demonstrated. Preserve this as SAME R6 task and do not open another planning phase.

**Verified code/test facts:**
- The consumer \`_subobjectives_from_session_refs\` requires exactly 2 distinct \`EntityRef\` candidates from \`prior_turns\` and no longer silently takes the most recent four. This is a valid bounded cardinality guard, not a provenance/identity proof.
- The method still constructs \`SubObjective(goal=f"{ref.entity_type} {ref.entity_id}")\`. The resulting \`SubObjective\` has no preserved typed \`EntityRef\` argument in this path. Describing a generated string as "typed-form goal" does not make it typed source binding; investigate the legitimate existing capability arguments/target contract and fix without a product-specific parser.
- The five new tests in \`test_multievidence_composition.py\` use synthetic \`_RefTurn\` objects and check two distinct, three ambiguous, repeated same ID, missing goal, empty turns; **they do not test two distinct forged references, cross-user/context substitution, owner disagreement, actual READ invocation, turn serialization or final outcome.**
- \`context[].entity_refs\` remains untrusted client request data. \`prior_context_turn_admissible\` and well-formedness checks are not proof that a \`DELIA_RESULT\` was generated for this actor/session. Exact two does not permit promotion to verified historical references.
- \`InteractiveTurnResult\` did not expose \`entity_refs\` in reviewed HTTP contract. Client echo path remains unproven; adding public fields requires explicit compatibility/security approval unless an already-governed transport exists.
- Never turn a successful Core/Domain READ of a syntactically supplied but incorrectly bound candidate into "as duas" full-goal success. Core/Domain enforces READ authorization, while the requested-target integrity must be checked separately.

**Execution authorization, same TASK:** \`DELIA-C3-E4-R6-CANONICAL-ENTITY-BINDING-AND-FUNCTIONAL-CLOSURE-01\`.
1. Add RED for **two distinct forged refs**, cross-actor and cross-session candidate replay, client-edited DELIA_RESULT, wrong type/source_system, missing ref projection, partial provenance, multi-root outcome, 3+ target ambiguity and no silent source omissions. Preserve upstream Core/Domain denial.
2. Verify actual \`serialize_result\` and NDJSON projection plus frontend continuity consumer. Do not assume \`InteractionTurn.entity_refs\` is magically serialized. If seamless authenticated continuity requires new public contract, signing or persisted state, STOP only that feature with a precise \`ARCHITECTURE_DECISION_REQUIRED\` (owner, producers/consumers, trust, TTL/replay, compatibility, retention, schema). In the meantime, untrusted client refs may only be *candidates*, with legitimate discovery/clarification and live owner checks; do not represent them as attested prior evidence.
3. Replace the \`f"{ref.entity_type} {ref.entity_id}"\` string transport with an existing **typed capability request/argument** path after inventory of actual consumers. If none can carry a typed target, report concrete smallest internal contract gate, not an unproven new planner, and execute all safe independent steps.
4. Verify comparison target set is the user-requested and owner-confirmed set, not merely \`len(refs)==2\` or \`sources>=2\`. Use deterministic verifier with real complete records, hierarchy/units/duplicates and Qwen3 false common/missing true common oracle.
5. Complete S1/S5/S6/S7: real authenticated Keycloak/Core+DAVI/Domain+Ollama Qwen3, same-conversation and single-turn repeated E2E, client-received HTTP/NDJSON response under gateway budget, full relevant regression on final SHA. Include all failed attempts, timings, tokens when available, tests and outcome status.
6. Do **not** return a documentation-only report or claim functional candidate if actual client delivery is not measured. No production deployment, no authority, retention or public API changes silently.

**Gate statuses at review:** \`EXACTLY_TWO_COUNT=PASS_CODE_INSPECTED\`; \`PROVENANCE_TRUST=FAIL/NOT_PROVEN\`; \`TYPED_READ_OBLIGATION=FAIL_CODE_INSPECTED\`; \`HTTP_ENTITY_REF_ROUNDTRIP=NOT_PROVEN\`; \`REF01–REF08/G04/G05/G07/G12=NOT_PASS\`; \`SEC01=previous executor-reported PASS, not rerun here\`; \`COORDINATION_TESTS=TEST_NOT_RUN\`.


## 10. R6 E2E benchmark review — subobjective→READ relevance/context boundary (2026-11-03)

**Input SHA:** \`91a8e86b9b\`, verified equal to main at review. **Reported execution:** task \`DELIA-C3-E4-R6-FUNCTIONAL-CLOSURE-DEPLOY-AND-E2E-01\`. **Verdict:** \`REWORK\` (client-grounded comparison failed); **no automatic model upgrade**; production deploy remains NOT_AUTHORIZED. Source and run status below are separate.

### 10.1 Verified/reported evidence

- **Verified from git diff:** \`handle_interactive_turn.py\` changed in R6 and the executor reports structural fix \`0c28844633\`: a module-level \`_entity_refs_from_outcome\` placed amid class methods had broken the HTTP handler; current class method layout repaired. Exact regression must run, syntax/AST alone is insufficient to prove functional HTTP turn.
- **Executor-reported model A/B, stage only:** qwen3 4B 5/5 valid decompositions, ~6.2s p50, ~229 tokens; qwen3 8B 3/5 valid, ~90–120s with two timeouts, ~1100+ tokens. The 8B is not a viable drop-in replacement in current tested compute. 5-sample stage success is not generalized model quality; it does weaken earlier assertion that the isolated 4B decompose schema is the sole failure.
- **Executor-reported live final SHA:** A03 \`decomposed=4\` → 3 completed/1 blocked, ~172s and client curl timeout at ~118s; no authoritative composition. B01 single-turn HTTP 200/48.6s NON_GROUNDED owner_query_miss. Server-side composition from PRIOR SHAs does not close current final-SHA gates.
- **Source-inspected execution seam (PROVEN):** \`_investigate_subobjectives::_run_sub()\` calls \`_governed_owner_path(sub.goal,... prior_turns=(), depth=depth)\` for every subgoal. \`_governed_owner_path\` starts fresh with \`_groups\` / \`_filter_groups_for_selection(input_text,...)\`; its \`goal\` is created only if \`prior_turns\` are present, so an empty context prevents the earlier interpreted parent goal from reaching this branch. The subgoal is represented by its model-proposed free-text \`goal\`; parent validated semantic constraints, target refs and authorized evidence/owner binding are not directly passed into the worker. \`_judge_goal_evidence\` invokes a separate model proposal using current goal/facts. Therefore relevance=irrelevant/empty_result may be due to missing parent semantics, selection/candidate/arggen, incomplete owner result or legitimate mismatch. This is a **bounded, testable mechanism**, not a proven exclusive root cause.
- **Source-inspected comparison seam:** \`_investigate_subobjectives\` collects successful attempts then uses \`_comparison_records(outcome)\` and root code to key \`sources\`; \`len(sources)>=2\` does not prove exact requested-target coverage, and success content is not necessarily a full owner-backed evidence tree. This remains a release gate.
- **Source-inspected goal classification:** \`_understand_goal\` is called in the pre-owner path only when prior_turns exist; verify other fallbacks that classify single-turn compare before assuming the semantic goal is consistently created. The B01 comparison=False case is a separate failing stage, not repaired by changing subgoal READ mechanics.

### 10.2 Coordination decision: reuse owner path, propagate validated semantic requirement without privilege

**EXISTING_EQUIVALENT=YES** for model invocation, semantic \`_TurnGoal\`, subobjective tracker, scoped ContextTurns, governed \`_governed_owner_path\`, capability selection, source facts and deterministic evidence verifier. **REUSE_DECISION=EXTEND** only the existing internal orchestration contract; **NO** new planner, dispatcher, provider, token store, shadow owner or product-specific string rules.

- Keep prior_turns client-provided and UNTRUSTED. Never solve context loss by copying the full earlier chat, client echo refs or fabricated model claims into a privileged session. Parent \`_TurnGoal\` remains a semantic proposal, not proof of business identity or access permission.
- Before refactoring, trace **the exact first wrong stage per subgoal**: parent intent/target, subgoal type, capabilities available, selection candidate, authoritative discover candidate, arggen, READ response completeness, goal_evidence_relevance projection/decision, resulting EvidenceFacts and tracker status. Use the SAME correlation across model stage/owner outcome, without logging credentials/raw confidential payload. Compare against known direct READ A01/A02 stage by stage on same authorized user/config.
- Minimal correction should make each already-validated subobjective retain its semantic *requirements and target candidates* across the existing governed owner-path boundary, while still executing live Core/Domain auth, discovery/resolution and domain-owned READ. Passing a typed requirement to an existing port can be permitted only with direct contract/consumer proof; no model-created endpoints/IDs as final authority. Do not copy the entire parent \`prior_turns\` into each worker as a blind fix, because it could trigger inappropriate prior-content continuation and introduce source-of-truth confusion.
- The relevance judge should compare actual owner EvidenceFacts to the **intended subobjective/parent requirement and scope**; do not bypass it globally, force relevant, or alter owner facts. Where the owner returned an explicitly scoped, complete result for the resolved candidate, verify the deterministic relationship first; only let LLM judge residual semantic correspondence per frozen policy.
- Avoid redundant compare subgoals if semantic objective already entails deterministic two-source fan-in and no separate owner analysis is required; preserve legitimate VISTA/TEO analytics where business owner is needed.
- Correct single-turn comparison classification with controlled stage tests, not keyword/regex overrides.
- Maintain effective end-to-end gateway deadline with useful margin, including concurrent provider cancellation. No nginx timeout-only fix, unbounded retries, broader delegated token scope or production deploy.

### 10.3 Immediate bounded implementation/testing — SAME E4-R6 scope

**TASK_ID:** \`DELIA-C3-E4-R6-SUBOBJECTIVE-READ-RELEVANCE-AND-DELIVERY-REWORK-01\`.

1. Reanchor HEAD, canonical authority chain, docs 221–228 and ledger. Check working tree and preserve unrelated production-control/engineering frontend edits.
2. Write RED tests using a reproduction of **subgoal accepted but owner evidence marked irrelevant/empty**, plus distinguish \`owner_query_miss\`, \`source_unavailable\`, incomplete result and true irrelevant. Assert correct source/target equality after authorized execution.
3. Trace parent→subgoal→\`_groups\`→capability select→discover/candidate→arggen→Domain execute→EvidenceFacts→relevance judgment. Identify where validated semantic information is discarded. Compare direct A01/A02 to same goals as subobjectives (paired run) rather than speculation.
4. Implement only the smallest internal bounded extension to reuse verified parent goal requirements in subobjective execution, and target candidate/scope where grounded, while preserving owner AuthZ and independent verification, not untrusted context elevation. This work must be actual runtime code and tests, not another inventory.
5. Confirm no unauthorized business source, transport provider metadata, model output or client history becomes FACT. Keep multiple legitimate owner pathways and negative/sibling generalization. Verify final comparison exact target-set coverage.
6. E2E: real Qwen3 4B + Keycloak/Core + DAVI/Domain + existing Pydantic AI/LangGraph, A01/A02/A03/A04 same-context and single-turn B01, plus missing/forged/unavailable/denied. Record per-stage event and tokens, wall-clock, actual client terminal, correctness vs full-tree oracle. Repeat; do not cherry pick one run. 8B no cutover.
7. Full regression backend/adapter/security/evidence and HTTP 500 handler class regression on final SHA; update ledger with outcome evidence and push main safely. Deploy only to an already-authorized non-production environment, with health SHA verification and rollback. **Production remains NOT_AUTHORIZED.**

**Acceptance:** no unsupported claim that 4B decompose is the sole blocker; no blanket relevance bypass; all \`REF01–REF08 / G04/G05/G07/G12\` on final SHA/config with real client-delivered grounded outcome. Otherwise precise \`REWORK/INCONCLUSIVE\`, or specific public contract security \`ARCHITECTURE_DECISION_REQUIRED\`, and do not self-accept.
