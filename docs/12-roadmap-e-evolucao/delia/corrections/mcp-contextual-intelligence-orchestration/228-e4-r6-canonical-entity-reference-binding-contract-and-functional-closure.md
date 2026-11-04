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


## 11. Coordination review at f37a1a2c08 — real composition achieved, final outcome not yet accepted (2026-11-03)

**Input:** \`f37a1a2c08\` = verified current main at review. **R6 task:** \`DELIA-C3-E4-R6-SUBOBJECTIVE-READ-RELEVANCE-AND-DELIVERY-REWORK-01\`. **Verdict:** \`ACCEPT_WITH_RESIDUAL\` for isolated path restoration only; \`FUNCTIONAL_ACCEPTANCE=NO\`, overall \`REWORK\`.

### Verified code change and executor-reported result

- **PROVEN (source):** \`_investigate_subobjectives\` accepts \`prior_turns\`, caller supplies those from parent, and \`_run_sub\` now passes \`prior_turns=prior_turns\` into governed \`_governed_owner_path\`. Context is untrusted; no live permissions are inferred from it. Existing executor-reported 52 relevant tests PASS, not independently rerun in coordination.
- **REPORTED (real probe correlation 3aa7e739):** Qwen3+Keycloak+DAVI completed 2 real owner READs, a third subobjective was blocked, deterministic composition logged \`differences_found sources=2\`, and server logged \`request_completed 200\` around 105–115s. This is meaningful positive progress against previous ~172s/timeout.
- **NOT PROVEN:** actual HTTP client received the full terminal body; exact two source identifiers are 90260147 and 90260148; full-record oracle equality and cardinality/occurrences; reliable repeated A01/A02/A03, single-turn B01, denied user, canceled client, sibling targets. The report itself acknowledges repetitions/oracle absent. A log \`request_completed 200\` is not a client receipt, and \`sources=2\` is not target-set proof.
- **PROVEN CODE SAFETY RISK:** \`_governed_owner_path\` now receives nonempty prior_turns for each \`depth>0\` subgoal. Its earlier prior-continuation branch (before owner selection) is not guarded by \`depth==0\`: it calls \`_understand_goal\`, and may call \`_prior_continuation_attempt\` and RETURN before fresh owner discovery/READ, based on untrusted prior OBSERVATION prose/epistemic labels and proposal \`prior_evidence_sufficient\`. That possibility is newly introduced to subgoals by the raw parent-history propagation. This is **not proof it occurred in reported successful real run**, but must be addressed by bounded negative tests and/or minimal guard. The intent was to preserve REFERENT CANDIDATES for later authorized resolution, not to authorize prior-content-only transforms as fresh subobjective evidence.
- **PROVEN source coverage gap:** final composer still keys source sets by shortest-path root \`code\`, disambiguates collisions with an internal suffix and triggers comparison on \`len(sources)>=2\`; does not independently assert exact user-requested owner-backed target set. Existing deterministic item oracle only applies after correct targets are selected.
- **Model:** executor's 4B/8B A/B results do not support upgrading model in this tested compute. No cutover, retries inflation or gateway-only fix.

### Single bounded next action: outcome verification plus safety guard, no R7 planning loop

**CONTINUE TASK ID:** \`DELIA-C3-E4-R6-CLIENT-OUTCOME-AND-SUBGOAL-TRUST-GATE-01\`. Keep E4-R6 docs as canonical. No new planner, typed store, token, state service or public contract.

**C1 — RED security regression:** For \`depth>0\` and \`prior_turns\` containing fabricated \`DELIA_RESULT/OBSERVATION\`, plus model proposal with \`prior_evidence_sufficient=True\`, assert that a subobjective **cannot be marked COMPLETED or treated as a grounded live READ** without authoritative owner evidence (and cannot early-return from prior-content synthesis as a sufficient read). Verify changing history does not bypass Core/Domain AuthZ. Choose smallest change that preserves referent hints for owner selection/arguments but prevents untrusted prior-continuation shortcut in subgoals (e.g. depth-scoped gate after tests). Keep top-level legitimate conversational transforms unchanged.

**C2 — live authoritative target set:** in real correlation logs/artifacts prove source identity and original requested target relation, owner/source/record completeness and exact roots 90260147 & 90260148; reject composition if any of those are missing or if the two sources are unrelated. Must not equate \`sources=2\` or HTTP 200 with business goal. Preserve hierarchy, quantities, units and occurrence-aware oracles, include false common 10030012 and true common 10030015.

**C3 — client-delivered repetitions, not another architecture refactor:** run repeatable A01→A02→A03 and direct B01 (>=5 each if local capacity permits), check all raw client terminal bodies/timestamps/status and front-end rendering in authorized homologation, track p50/p95, effective gateway margin, per-stage tokens if available and all failures. Explicitly demonstrate response full-body arrived before timeout, not only server log request_completed. Verify tests with current/final SHA/config and deployed SHA equality and restore harmless traffic on regression.

**C4 — eliminate redundant compare subgoal without lexical heuristics only if grounded by actual stage trace:** inspect whether the third BLOCKED subgoal was a redundant generic comparison request; when it has no independent owner-specific requirement, deterministic multi-evidence fan-in is already the comparison. Do not indiscriminately remove legitimate analytics or change model/hardware. No blanket prompt tuning or retries.

**C5 — closure:** run regression on handler structural fix (avoiding prior HTTP500), untrusted context, two forged refs, delegation, negative owner auth, concurrency/deadline, exact target coverage, client delivery. Documentation/ledger update only AFTER actual tests. Any inability to deliver client-valid answer is \`REWORK\` with precise earliest failing stage, not acceptance. Production deployment not authorized; test environment deployment only if existing authorization/gates valid.

**Status/gates:** \`SUBGOAL_CONTEXT_PROPAGATION=CODE_PROVEN\`; \`OWNER_READS=REPORTED_PASS_ON_ONE_RUN\`; \`COMPOSITION=REPORTED_PASS_ON_ONE_RUN\`; \`CLIENT_FULL_BODY=NOT_PROVEN\`; \`EXACT_TARGETS/ORACLE=NOT_PROVEN\`; \`PRIOR_CONTINUATION_SUBDEPTH_SAFETY=NOT_PROVEN\`; \`REF05–REF08/G04/G05/G07/G12=NOT_PASS\`; \`COORDINATION_TESTS=TEST_NOT_RUN\`.


## 12. E4-R6 §11 review at 95f9168ef3 — actual fan-in grounding bug, 4-source ambiguity, transport (2026-11-03)

**REVIEW_INPUT_SHA:** \`95f9168ef3\` (DÉLIA code diff inspected; main subsequently advanced with unrelated engineering/TV changes). **Verdict:** \`REWORK / EXECUTION_DRIFT\` on final aggregation trust semantics; not “only gateway timeout”. **Model:** retain existing qwen3:4b configuration. **PRODUCTION_DEPLOY:** NOT_AUTHORIZED.

### Exact code facts and architectural issue

1. **Subobjective trust gate implemented:** \`_governed_owner_path\` enters prior-continuation when \`depth==0\` only; at subdepth it still consumes untrusted \`prior_turns\` as semantic candidates and consults real owners. This is the intended isolation, subject to negative and regression evidence.

2. **Critical final projection / grounding mismatch (PROVEN by code inspection):** \`_investigate_subobjectives\` collects real \`attempt.outcome\` internally, then \`_subobjective_attempt_result\` constructs \`GovernedCapabilityAttempt(status=SUCCESS, content=concatenated_rendered_text, limitations=...)\` **without** \`outcome\` or \`provenance\`. \`HandleInteractiveConversationTurn\` handles any SUCCESS with \`attempt.outcome is None\` via \`_prior_continuation_result\`, which is intentionally \`NON_GROUNDED\`; it only calls \`_grounded_result\` if an authoritative outcome exists. Hence real READs + \`evidence_composition differences_found\` + server 200 **do not prove—and on this code path cannot furnish—the expected grounded final result**. This is an **implementation/contract mismatch**, not just a latency problem. Do NOT manufacture a \`SpecialistOutcome\` or a \`SourceRef\` from subgoal labels, provider metadata or model output. Reuse legitimate multi-source provenance and evidence projection already provided by the Application/Domain contracts; inventory exact owner/consumer methods, make one bounded internal contract extension only if needed. Composite output can only be GROUNDED if every factual source was truly authorized, lineage is retained, exact requested target set matches, and deterministic oracle passes. A successful owner request is not a fact qualification by itself.

3. **Four sources do not establish two intended target trees:** \`_investigate_subobjectives\` collects each completed source by \`root['code']\`, disambiguates collisions with \`#<index>\`, then runs composer whenever \`len(sources)>=2\`. The reported \`decomposed=4 / sources=4 / COMPLETED×4\` may contain redundant analysis, duplicates or unrelated roots. No proof in the report that all four correspond exactly to intended 90260147 & 90260148, or that hierarchy/occurrence/units were complete. Correctness gate must reconcile **requested target identities and authorized owner evidence** before comparing. Never silently select first two, drop evidence or overwrite repeated roots.

4. **Existing streaming is REAL and already owned:** \`interaction_routes._stream_interaction_turn\` implements opt-in \`Accept: application/x-ndjson\`, activity events, bounded queue, heartbeat, final \`turn_result\`/\`turn_error\`, and disconnect cancellation. It does **not** presently establish successful client receipt before 118s, nor guarantee that first chunks and a terminal body survive every proxy. No new streaming stack, no default transport contract switch or unapproved gateway-only timeout change. Verify actual Portal/UI client support and end-to-end response framing under gateway in homologation first.

5. **Evidence levels:** executor-reported correlation \`1eb1302e\` had \`decomposed=4\`, four owner READs and \`differences_found sources=4\`, server 200 near 105–115s, while curl had no complete body by its ~118s timeout. This is **SERVER_COMPOSITION_OBSERVED, CLIENT_OUTCOME=FAIL**; it does not establish isolated gateway cause. E2E completed body, grounded flag, source identity, target oracle and repeated runs remain missing. \`SEC01=PASS\` is executor-reported from 38 tests; coordination test run \`TEST_NOT_RUN\`.

### Decisive bounded implementation task (execute code and tests before any timeout increase)

**TASK_ID:** \`DELIA-C3-E4-R6-FANIN-PROVENANCE-TARGET-COVERAGE-AND-NDJSON-DELIVERY-01\`.

**FIX 1 — fan-in evidence contract (highest priority):** RED reproducing 2 real owner-backed completed READs + deterministic comparison gives \`GovernedCapabilityAttempt.SUCCESS\` without \`outcome/provenance\` and interaction \`NON_GROUNDED\`. Inventory existing \`SpecialistOutcome\` / \`GovernedCapabilityProvenance\` / \`EvidenceFacts\` / \`SourceRef\` multi-source projection contracts; REUSE/EXTEND least surface to retain source lineage and actual verified evidence through application interaction. Do NOT bypass \`if attempt.outcome is None\` as a blanket workaround and do NOT invent an owner result. Limit COMPOSITE-grounding to authoritative full verifiable evidence; partial/ambiguous denied/empty remains honest.

**FIX 2 — requested-target coverage:** RED expected {90260147,90260148} vs actual {wrong A,wrong B,additional source,deduplicated root}, multi-root and repeated occurrence. Preserve per-source owner provenance, exact root identity and hierarchy. If requested targets are not securely bound to source identities, do not declare complete comparison. Do not extract IDs from client prose/regex, nor infer AuthZ from prior turns. An additional owner-analytics task is only legitimate if requested and its contract is authoritative for that business fact.

**FIX 3 — bounded performance/delivery using existing transport:** Stage trace with timings/tokens across goal classify → decomposition → parallel READs → evidence fan-in → optional correspondence model → deterministic render → final interaction projection → HTTP/NDJSON gateway. Prove whether extra LLM stage is actually necessary for deterministic compare according to frozen doc222/ADR58; retain required model semantics, but avoid redundant model-composed factual narration. Confirm \`turn_result\` received by actual HTTP/NDJSON client and Portal/UI before timeout, with p50/p95 and failure counts, not merely upstream server 200. No blanket retries/worker-threads timeout or gateway-only changes. Evaluate gateway/NDJSON behavior as infrastructure *after* exact stage evidence, not as first workaround.

**FIX 4 — regression on final SHA:** handler HTTP500 structural, \`depth>0\` trust gate and forged history, SEC01, deadline/cancel, parallel worker context, owner Core/Domain AuthZ, single-turn B01 and multi-turn A01→A02→A03→A04, missing sources and sibling domains, Qwen3:4b local. Repeated live runs with exact client terminal body and independent deterministic oracle. Record SHA/config, current revision and evidence; only then classify G04/G05/G07/G12 and REF01–REF08.

**No production deploy;** only existing authorized test environment with rollback/observability. \`FUNCTIONAL_ACCEPTANCE_CANDIDATE\` requires correct *two intended authoritative targets*, full comparison, COMPOSITE grounding with real evidence lineage and delivery to user, repeatedly on final SHA. A grounded label with no authoritative evidence is a hard FAIL.


## 14. E4-R6 composite evidence implementation by coordination (2026-11-04)

**STATUS:** CODE_COMMITTED, TESTS_ADDED, runtime and live E2E **TEST_NOT_RUN** by coordination. User requested code implementation here and handoff of deploy/tests to Devin. No production deployment. Keep original authority chain, do not advance phase.

**Commits (main):**
- \`0509ac33aba7\`: additive internal \`VerifiedCompositeEvidence\` in existing \`application/interaction/contracts.py\`: two distinct owner-record roots, source-lineage per root, deterministic verdict, bounded multi-source projection; does not impersonate \`SpecialistOutcome\`.
- \`cd070a83eef2\` and \`670173868bf9\`: \`GovernedCapabilityAttempt.verified_composition\`, appended to preserve existing positional constructor behavior.
- \`4f00b3fcd897\`, \`35a59f69c3d4\`, \`f22abd4b4470\`: collection from genuine owner-backed SUCCESS outcomes, provenance per root, require exactly two distinct complete sources AND both tracked subgoals completed, refuse duplicate/partial/extra roots. Deterministic comparator no longer silently compares the first two of 3+ sources. Fan-in carries proof separately from specialist outcome.
- \`52e07362c9af\`: \`HandleInteractiveConversationTurn\` distinguishes \`verified_composition\` from ordinary \`outcome\` and ungrounded prior-continuation; emits OBSERVATION+GROUNDED only when typed aggregate proof exists, with source-lineage and no manufactured specialist metadata.
- \`f7f56b0ab534\`: targeted regression tests in \`test_verified_composite_grounding.py\` for no fabricated single specialist, duplicate/missing source rejection, composite grounded serialization, ordinary SUCCESS still non-grounded, 3-source verifier inconclusive, internal fan-in field.

**EXISTING_EQUIVALENT=YES; REUSE_DECISION=EXTEND.** This is the smallest internal carrier at Application/interaction seam; no new provider/store/planner/authority/token, no public request schema or retention modification. Output's existing \`provenance\` field now can represent verified composed lineage via \`to_projection\`, with \`source=None\`, source records and composition roots/verdict. Check actual Portal UI handling of \`source=None\` and additive \`composition\` during integration tests. Existing single-owner branch remains untouched.

**Important constraints and known residuals:**
1. The implemented **strict two-source gate** deliberately blocks older \`decomposed=3/4\` paths rather than falsely accept a first-two comparison. This may lead to truthful insufficient outcomes until semantic decomposition avoids redundant/non-target subobjectives; do not silently drop subgoals or loosen coverage. Two real owner roots do NOT alone prove these are the user's intended targets. A functional review must assert expected 90260147/90260148 with independent oracle and actual business scope.
2. This patch is **not yet runtime-verified**. New tests and all regression suites must be executed by Devin, with repairs to this bounded patch if necessary. No tests were run by coordination.
3. The NDJSON implementation already exists; validate that a complete \`turn_result\` traverses HTTP gateway and reaches Portal client, not simply upstream 200. Curl previously timed out at ~118 seconds.
4. Validate context guard (\`depth>0\` cannot synthesize prior history), bearer propagation, AuthZ, source completeness/multi-root handling, root-to-source correlation, false common 10030012 and true common 10030015.
5. Current \`SourceRef\` source metadata follows canonical business source but is a provenance descriptor, not authorization. \`VerifiedCompositeEvidence\` reflects deterministic owner-evidence observation; factual satisfaction of the user goal remains a **separate outcome gate**.

**NEXT EXECUTOR (Devin):** \`DELIA-C3-E4-R6-COMPOSITE-PATCH-HOMOLOGATION-E2E-01\` — reanchor HEAD, run tests and fix any actual failures, review diff/invariant, deploy only to existing authorized homologation, verify deployed SHA, Keycloak/Core+DAVI/Domain/Qwen3 4B E2E with JSON+NDJSON and user-facing UI, repeated target/oracle/gateway checks, rollback readiness; log exact PASS/FAIL and update ledger. Production remains NOT_AUTHORIZED. \`REF/G=NOT_PASS\` until client receives exact completed authoritative comparison.


## 15. E4-R6 homologation deploy + real E2E by Devin (2026-11-04)

**TASK_ID:** `DELIA-C3-E4-R6-COMPOSITE-PATCH-HOMOLOGATION-E2E-01`.
**ENV:** local governed stack (docker-compose.dev) — homologation; PRODUCTION_DEPLOY=NOT_AUTHORIZED.

### Commits (fixes on top of coordination patch)

- `05bfd091e3` — post-goal-binding decomposition gate for cold single-turn comparisons (B01 path: goal binds inside `_select_target` fused interpretation; early gate ran with `goal=None`). Extracted `_decomposed_investigation`; re-runs governed decompose after binding; regression test `test_cold_single_turn_comparison_reaches_verified_fan_in`.
- `d32a4dd065` — orchestration instruction resource v40: `subobjectives` now requires one acquisition subobjective per source and explicitly forbids analytical questions (common/exclusive/differences) as subobjectives.
- `e1d2de09f2` — `_acquisition_subobjectives`: under a comparison parent each proposed sub is classified by the SAME governed goal instruction; `compare`/`analyze`-class subs are answered by deterministic fan-in, never investigated. Undeclared/unclassifiable stays tracked (fail-closed); deps on delegated subs released. Unit tests: filter, fail-closed keep, undeclared keep, dep release.
- `0b2bd91fd5` — observability: `evidence_composition decision=insufficient` now logs sources/completed/objectives/reasons (previously invisible behind `delpi_source_unverified`).

### Tests (delia-api/.venv, HEAD final)

- `test_verified_composite_grounding.py` 6 PASS; `test_multievidence_composition.py` 19 PASS (incl. 4 new filter tests); `test_interaction_runtime.py` 146 PASS; `test_generic_multistep_orchestration.py` PASS; `test_specialist_interop_security/usecase` PASS; `test_delegated_credentials.py` (SEC-01) 38 PASS; `test_r1_instruction_resource.py` PASS.
- Full suite 2895 collected: 2892 PASS / **3 FAIL pre-existing at BASE** (`test_trickle_server_never_outlives_wall_clock_deadline` hang >90s — real adapter total-deadline gap in `pydantic_ai_adapter`; `test_normal_fast_provider_preserves_response_contract` — fake fixture missing ChatCompletion fields vs pydantic-ai 2.50.0 strict validation; `test_infra_and_env_carry_no_direct_delpi_wiring` — committed comment in `env.example` contains banned substring). None caused by this diff; files untouched by patch.

### Deploy

- `DEPLOYED_SHA=0b2bd91fd5333bfbc432c8c3633579de3ea7a7ca` verified via startup log `runtime_sha=` + health 200 through gateway `/apps/delia-api/`. Rollback: prior container `delpi-delia-api-prev-manual` retained + `DELIA_RUNTIME_SHA` revert + recreate.

### Real E2E (Keycloak+Core+DAVI+Qwen3:4b, JSON and NDJSON)

- Env fixes discovered: Keycloak container was down (502) — restarted; dev token needs `scope=openid` (password grant default lacks it → MCP 401 `MISSING_REQUIRED_SCOPE openid`).
- A01 `GROUNDED` ×3 runs (88–97s) with provenance `api-delpi`, full tree 90260147 incl. oracle codes — PROVEN.
- NDJSON transport delivers terminal `turn_result` past the 120s JSON gateway cutoff (`proxy_read_timeout 120s` on `/apps/delia-api/`): bodies received at 143.59s, 183.77s, 244.88s — PROVEN.
- Analytical-sub filter live-proven: run e63a9e03 decomposed=6 → so_3..so_6 `delegated_to_composition` (class=compare); run 4a945dea decomposed=6 → so_3/so_4/so_6 delegated (so_5 classified acquisition, kept).
- **NOT achieved:** client-visible GROUNDED comparison. Blocking evidence:
  - Run 9ca3cf18: two DAVI discover→execute READs COMPLETED (`execute_delpi_information` on 90260147 and 90260148 per api-delpi log, `goal_evidence_relevance=corresponds` both) yet composition returned `SOURCE_UNAVAILABLE` — source-collection rejected before `_compose_multi_evidence`; exact `comparison_*` reason NOT captured (observability line deployed after this run) — UNRESOLVED.
  - Run 4a945dea: sub-goal group selection misrouted all kept subs to `mcp:teo` (wrong specialist) → `insufficient sources=0 completed=0 objectives=3 reasons=[]` — gate correctly refused; 4B selection nondeterminism, pre-existing variance.
  - Earlier runs: subs selecting `execute_delpi_information` directly stalled at `candidate_token` (orchestrator-supplied state, needs discovery-first plan) → clarification → BLOCKED; A02 discovery ask-back variance; JSON runs >120s die at gateway (504) while server completes ~280s.
- Oracle: common 50220013/10030015/10080031, exclusive-147 50220014/10030019 verified inside A01 grounded content; full comparison oracle NOT PROVEN end-to-end.

### Gate status

`REF01–REF08/G04/G05/G07/G12=NOT_PASS`. FUNCTIONAL_ACCEPTANCE_CANDIDATE=NO — correct two-target comparison not delivered to client repeatedly. Remaining known blockers (bounded, next task): (1) unexplained collection rejection on run with 2 completed distinct-root DAVI reads (capture `reasons` via the new insufficient log on next repro); (2) sub-goal specialist/argument nondeterminism (TEO misroute, direct-execute `candidate_token` stall) in the governed chain — contract for subobjectives selecting the domain owner's discovery-first path.

## 16. Root-cause investigation — composite / specialist / discovery (2026-11-04)

**TASK_ID:** `DELIA-C3-E4-R6-COMPOSITE-ROOT-CAUSE-INVESTIGATION-01`.  
**MODE:** DIAGNOSTIC ONLY. **PRODUCTION_DEPLOY:** NOT_AUTHORIZED. **FUNCTIONAL_ACCEPTANCE:** NOT_YET_AUTHORIZED.  
**HEAD_AT_INVESTIGATION:** `f69639ef24` (main; homologation baseline `0b2bd91fd5` superseded by later main).  
**GATES PRESERVED:** `REF01–REF08/G04/G05/G07/G12=NOT_PASS`.

### RC-A — two completed READs rejected before composition — **PROVEN**

**FIRST_FAILURE_POINT:** `orchestration.py` → `_investigate_subobjectives` cardinality gate (~L7475–7480):

```text
len(sources) != 2
OR len(completed) != 2
OR len(tracker.objectives) != 2
OR any(obj.state != SUBOBJECTIVE_COMPLETED)
OR any(lim.startswith("comparison_"))
```

**ACTUAL (diagnostic + homologation alignment):** with two owner-backed SUCCESS READs (distinct roots, complete provenance) and a **third tracked acquisition** that does not enter `completed`, fan-in refuses composition. The insufficient log’s `reasons=` filter only includes `comparison_*` prefixes; the cardinality branch alone emits `evidence_composition_insufficient:…` **without** a `comparison_*` lim → **`reasons=[]`**. Sibling: a third SUCCESS clarify **with content** enters `completed` then emits `comparison_source_missing_or_incomplete`.

**EXPECTED:** when parent comparison has exactly two authorized evidence obligations fulfilled with distinct owner roots matching requested targets, composition proceeds; extra analytical obligations must already be delegated (or not tracked). Fail-closed for wrong/duplicate/partial roots remains.

**CAUSAL_MECHANISM:** intentional strict two-objective gate (§14) + residual that `_acquisition_subobjectives` / decompose can leave `objectives>2` (undeclared/misclassified keep — live so_5). Two good READs are necessary but not sufficient under this predicate.

**REPRODUCTION:** `delia-api/tests/test_e4_r6_composite_root_cause_diagnostics.py` — `test_rc_a_two_complete_reads_rejected_when_objectives_gt_two` (+ controls).

**MINIMAL_CORRECTION_CANDIDATE (proposal only):** (1) ensure acquisition set for comparison is exactly the two evidence READs (strengthen classify/decompose contract — no product hardcode); **and/or** (2) change eligibility to “exactly two complete distinct owner sources matching bound targets” without requiring `len(objectives)==2` when extra tracked subs are non-evidence; (3) log cardinality reasons as structured fields (`objectives_mismatch`, `completed_mismatch`) so `reasons` is never empty on this path. Do not loosen fail-closed for duplicate/wrong roots.

### RC-B — product-structure subs → `mcp:teo` — **PROVEN_PARTIAL / mechanism INCONCLUSIVE on stochastic path**

**FIRST_DIVERGENCE:** per-sub `_governed_owner_path` → `select_group` / `select_capability` on `sub.goal` text (parent `prior_turns` propagated since §10, but **no typed owner obligation**).

**OBSERVED:** run `4a945dea` kept 3 acquisitions; all group-selected `mcp:teo`; `sources=0`.

**EXPECTED_OWNER_BOUNDARY:** product structure READ is DAVI/Domain owner via live capability contract — not TEO methodology — without `if product → DAVI` hardcode.

**CAUSAL_MECHANISM (code-proven parts):** selection is model-proposed against group surfaces; decompose yields free-text goals; acquisition filter classification is a separate `_understand_goal` pass that can keep non-READ phrasing. **Not proven** as sole “4B hallucination” without controlled same-config selection A/B of identical surfaces.

**PROPOSED_MINIMAL_FIX:** reuse typed goal/business_subject + owner capability ranking already used for parent; constrain sub selection to groups whose live surface can satisfy the declared evidence need; optional bounded re-rank when selected group has zero invocable READ matching subject — no specialist-name branch.

### RC-C — execute without candidate_token state — **PROVEN**

**INVALID_TRANSITION:** model selects candidate-bound `execute_*` as capability target.

**CAUSE:** `_capability_requires_orchestrated_input` / `_capability_dead_end` treat `candidate_token` as orchestrator-only; direct pick is a typed dead-end. Bounded retry prefers discover when listed (`test_select_capability_retries_orchestrated_input_pick`). If execute stands (no alternative / retry fails), args/clarification or discover-inside-`_invoke_selected` may still stall. `_invoke_selected` **does** chain discover→token→execute when invoke is reached — stall is usually **before** successful chain or when discover returns no usable candidate.

**EXISTING_REUSE:** `_is_candidate_bound`, `_invoke_selected` / `_discover_candidate`, dead-end retry — `EXISTING_EQUIVALENT=YES`, `REUSE_DECISION=EXTEND` (prefer discover in sub plans; do not invent tokens).

**PROPOSED_MINIMAL_FIX:** for comparison acquisition subs, bias plan to discovery-first when group advertises candidate-bound READ (existing plan/`_discovery_capability` patterns); never accept model-supplied tokens; surface honest clarification when discover yields zero candidates.

### Shared root cause

**NOT_PROVEN as single cause.** RC-A is structural cardinality/filter coupling. RC-B is selection/context. RC-C is discovery-first contract at selection time. Shared *family*: per-sub free-text investigation without a typed two-target evidence plan. `REF/G` remain **NOT_PASS**.

### Correction order (coordination)

1. RC-A cardinality + acquisition filter (unblocks fan-in when READs already succeed).  
2. RC-C discovery-first on candidate-bound surfaces.  
3. RC-B specialist selection reliability (eval + bounded ranking).  
4. Expected-target oracle / REF05 (still separate — gate does not yet match requested entity ids).

## 17. RC-A fix — evidence obligations & composition eligibility (2026-11-04)

**TASK_ID:** `DELIA-C3-E4-R6-EVIDENCE-OBLIGATION-AND-COMPOSITION-ELIGIBILITY-FIX-01`.
**BASE_HEAD:** `1031a35c75`. **MODE:** MINIMAL FIX RC-A ONLY. **PRODUCTION_DEPLOY:** NOT_AUTHORIZED.
**EXISTING_EQUIVALENT:** YES. **REUSE_DECISION:** EXTEND (`_investigate_subobjectives` + same `_understand_goal` classifier as `_acquisition_subobjectives`).
**ABSTRACTION_GATE:** PASS — no new planner/obligation type/registry.

### Cause (from §16)

Gate required `len(tracker.objectives)==2` (and all COMPLETED / `completed==2`), rejecting two authoritative distinct-root READs when a leftover analytical/failed sub remained tracked; `reasons=[]` when no `comparison_*` lim.

### Correction

In `_investigate_subobjectives` (comparison fan-in):

1. Track obligation id on each completed attempt.
2. Skip provenance-less SUCCESS for goals classified as declared `analyze`/`compare` (composition auxiliary).
3. Eligibility = exactly two verified owner sources **and** every non-auxiliary tracked obligation either satisfied a source or already raised a structured `comparison_*` reject; incomplete material → `comparison_material_obligation_incomplete`.
4. Remove coupling to raw `len(objectives)` / `len(completed)` / all-COMPLETED.
5. Structured log: `declared_objectives`, `material_satisfied`, `eligible_sources`, `rejected_sources`, `reasons`.
6. Two-structure scope preserved (`sources==2`); `comparison_unexpected_material_source` if >2.

**Not changed:** RC-B specialist selection, RC-C discovery-first/candidate_token, REF05 expected-target binding (still NOT_PASS — no regex ID binding added).

### Tests

- RED/GREEN: `tests/test_e4_r6_rca_composition_eligibility.py` (T01/T02/T03/T05/T07/T08/T09/T11).
- Updated characterization: `test_e4_r6_composite_root_cause_diagnostics.py`.
- Regression: verified_composite, multievidence, interaction_runtime, multistep, delegated_credentials, cycle3, semantic_path — PASS on executor run.

### Homologation E2E

`TEST_NOT_RUN` / `INCONCLUSIVE` this window: no local governed stack (`127.0.0.1:8000` down); production deploy forbidden. Runtime proof of the corrected branch deferred to authorized homologation.

### Gates

`REF01–REF08/G04/G05/G07/G12=NOT_PASS`. `RC_A_STATUS=IMPLEMENTED` (unit/integration). `RC_B/RC_C/REF05` unchanged open. `FUNCTIONAL_ACCEPTANCE_CANDIDATE=NO`.

## 18. RC-A governed homologation + semantic safety (2026-11-04)

**TASK_ID:** `DELIA-C3-E4-R6-RCA-GOVERNED-HOMOLOGATION-AND-SEMANTIC-SAFETY-01`.
**REFERENCE_SHA / CODE_UNDER_TEST:** `151d5b8701`.
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED.

### Environment baseline

| Check | Result |
|---|---|
| Local `127.0.0.1:8000` | DOWN |
| Local Docker daemon (`/var/run/docker.sock`) | ABSENT / not running |
| srv-api `192.168.1.237` SSH | Network unreachable from executor WSL |
| Restore governed stack | BLOCKED (no authorized procedure completed this window) |
| E2E B01–B03 | `TEST_NOT_RUN` / `INCONCLUSIVE` |
| Model live Qwen3:4b | `TEST_NOT_RUN` |

### Synthetic regression (executor)

- `test_e4_r6_rca_composition_eligibility.py` PASS
- `test_e4_r6_composite_root_cause_diagnostics.py` PASS
- verified_composite / multievidence / interaction_runtime / multistep / delegated_credentials / specialist_interop_security PASS

### Semantic safety (synthetic adversarial) — **FAIL finding**

Suite: `tests/test_e4_r6_rca_semantic_safety_homologation.py`

| Case | Result | Notes |
|---|---|---|
| C01 true auxiliary | PASS | analyze/compare leftovers + 2 sources → compose |
| C02 true material third | PASS | incomplete material → reject + `comparison_material_obligation_incomplete` |
| C03 material reclass→analyze | **FAIL / FALSE_GROUNDED** | eligibility `_subgoal_is_composition_auxiliary` trusts later `analyze` and discards tracked material obligation; `VerifiedCompositeEvidence` emitted |
| C04 classifier exception | PASS | fail-closed |
| C05 analyze + external spec | **FAIL / FALSE_GROUNDED** | `goal_class=analyze` alone drops external-spec obligation |

**CAUSE:** `orchestration.py` → `_investigate_subobjectives` eligibility loop → `_subgoal_is_composition_auxiliary` → continue (skip material check).
**REPRODUCTION:** `test_c03_material_reclassified_analyze_must_not_ground`, `test_c05_analyze_phrasing_with_external_spec_dependency_blocks` (recorded as `xfail(strict=True)` pending rework; do not delete).
**SECURITY_IMPACT:** LLM classification can authorize ignoring a tracked material evidence obligation and still produce verified composite grounding.
**REWORK_REQUIRED:** YES — coordination-bounded; **no auto-fix in this task**.

### Verdict

```text
RC_A_VERDICT=FAIL
RC_A_RUNTIME_STATUS=BLOCKED_ENV / TEST_NOT_RUN
RC_A_SEMANTIC_SAFETY=FAIL
RC_A_GENERALIZATION=INCONCLUSIVE (no live model A/B)
FUNCTIONAL_ACCEPTANCE_CANDIDATE=NO
RC_B_STATUS=OPEN
RC_C_STATUS=OPEN
REF05_STATUS=NOT_PASS
REF01–REF08/G04/G05/G07/G12=NOT_PASS
```

Cardinality decoupling under *consistent* labels remains useful but **cannot be homologated as safe** until auxiliary classification cannot discard material obligations (e.g. persist acquisition-time obligation class; never re-promote material→auxiliary at eligibility without stronger contract).

## 19. RC-A definitive remediation + live E2E (2026-11-04)

**TASK_ID:** `DELIA-C3-E4-R6-RCA-DEFINITIVE-REMEDIATION-AND-LIVE-E2E-01`.
**REFERENCE_SHA (task):** `a99883ec1c`.
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED.

### Root cause (confirmed, then closed)

Eligibility-time `_subgoal_is_composition_auxiliary` re-invoked `_understand_goal` and could `continue` past incomplete tracked obligations when the later label was `analyze`/`compare` → false `VerifiedCompositeEvidence` (C03/C05).

### Correction (minimal owner surface)

File: `delia-api/app/application/capability_provision/orchestration.py`

1. **Removed** `_subgoal_is_composition_auxiliary` entirely.
2. After `_acquisition_subobjectives`, every remaining tracked objective is a **material** evidence obligation.
3. Eligibility evaluates verified sources + incomplete tracked oids only — **no fresh LLM classify** at fan-in.
4. True auxiliaries remain nonblocking because the **acquisition filter** (same governed classifier) already drops declared `analyze`/`compare` before the tracker.

`EXISTING_EQUIVALENT=YES` · `REUSE_DECISION=EXTEND` · no new planner/registry/obligation store.

### Synthetic gates

| Case | Result |
|---|---|
| C01 true auxiliary | PASS (real acquisition filter) |
| C02 true material third | PASS |
| C03 material→analyze reclass | **PASS** (xfail removed) |
| C04 classifier exception | PASS |
| C05 analyze + external-spec tracked | **PASS** (xfail removed) |
| S01–S16 adversarial | PASS (effects on `VerifiedCompositeEvidence` / no false GROUNDED) |

Also: `test_e4_r6_rca_composition_eligibility.py`, `test_e4_r6_composite_root_cause_diagnostics.py`, verified_composite, multievidence, interaction_runtime, multistep, delegated_credentials, specialist_interop_security, goal_evidence, semantic_path — PASS on focused runs.

Known baseline debt (pre-existing, not introduced): trickle wall-clock timeout; ChatCompletion structured-validation fixture.

### Homologation environment (restored)

Previous window blocked on sandboxed probes. With full host access:

| Check | Result |
|---|---|
| Docker daemon + `delpi-delia-api` | UP (healthy); bind-mount `delia-api:/app` |
| Gateway `:80` | UP; `/apps/delia-api/` → delia-api; `/auth/` → Keycloak |
| Keycloak + Core `/me` | OK when token minted via gateway Host=`localhost` (iss=`http://localhost/auth/realms/delpi`) |
| Ollama `qwen3:4b-instruct-2507-q4_K_M` | Present; cold load can exceed 60s |
| srv-api prod `192.168.1.237` | Not used (PRODUCTION_DEPLOY=NOT_AUTHORIZED) |

Deploy model: **code live via bind-mount + `docker restart delpi-delia-api`** (dev homologation compose). `DELIA_RUNTIME_SHA` env still shows older `0b2bd91fd5` until image rebuild — runtime code path verified by in-container grep of §19 / absence of `_subgoal_is_composition_auxiliary`.

### Live E2E (real interaction path)

Probe: `delia-api/scripts/e2e_rca_compare_probe.py` (password grant → gateway issuer → Core `/me` → `POST /interaction/turns`).

Observed (direct API base inside container; NDJSON + JSON):

| Run | HTTP | grounding | Notes |
|---|---|---|---|
| compare NDJSON | 200 | terminal `turn_result` present (~236s) | keepalives/activity delivered |
| compare JSON | 200 | **NON_GROUNDED** | `delpi_source_unverified`; content refuses unverified source |
| third-spec JSON | 401 once (token TTL) / remint added | — | remint-per-turn in probe |

Server log (authoritative for RC-A eligibility under live model):

```text
stage=evidence_composition decision=insufficient
declared_objectives=6|4 material_satisfied=0 eligible_sources=0
reasons=['comparison_material_obligation_incomplete','comparison_source_missing']
```

**FALSE_GROUNDED_COUNT (executed live set): 0**  
Independent oracle 90260147/90260148 item codes: **NOT_REACHED** — owner READs did not satisfy material sources (`material_satisfied=0`). Blocker class: **RC-B/RC-C / owner acquisition**, not RC-A false composition.

### Residual risks

1. Acquisition-time **declared** `analyze`/`compare` still drops subs before tracking. C05 production safety for “analyze phrasing + mandatory external third source” that the model declares as analyze at acquisition remains an **ARCHITECTURE residual** (no keyword heuristic; no new obligation schema this task). Tracked obligations (fail-closed keep / explicit read) are safe under §19.
2. Gateway `proxy_read_timeout 120s` still truncates long **JSON** responses; NDJSON remains the durable client path.
3. Functional E4-R6 acceptance still blocked on RC-B, RC-C, REF05.

### Verdict

```text
RC_A_VERDICT=PASS_SYNTHETIC + LIVE_NO_FALSE_GROUNDED
RC_A_SEMANTIC_SAFETY=PASS (C01–C05, S01–S16)
RC_A_LIVE_COMPARISON_ORACLE=NOT_REACHED (owner reads unsatisfied)
RC_B_STATUS=OPEN
RC_C_STATUS=OPEN
REF05_STATUS=NOT_PASS
FUNCTIONAL_ACCEPTANCE_CANDIDATE=NO
PRODUCTION_DEPLOY=NOT_AUTHORIZED
```
