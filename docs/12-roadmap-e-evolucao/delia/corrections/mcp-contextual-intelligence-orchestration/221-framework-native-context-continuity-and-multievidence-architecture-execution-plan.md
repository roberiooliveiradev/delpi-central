# 221 — DÉLIA · Framework-native context, continuity and multi-evidence — architecture and executable simplification plan

> **EXECUTION REVIEW R1 (2026-11-03, coordination):** Sections 11–18 below are the controlling execution/acceptance overlay for this plan. Earlier sections 5/7/9 remain the detailed technical work breakdown and initial brief history, but are **not separate terminal deliverables**. Executor must complete authorized dependent work in one coordinated delivery, with factual implementation and local real-model E2E evidence. **No self-acceptance, no unauthorized override of frozen ADR/owner, no production deploy.** If a gate requiring independent architecture/product authorization blocks a dependent step, stop THAT step with `ARCHITECTURE_DECISION_REQUIRED`, complete independent safe steps, and report a specific blocker; do not silently implement it. This is a planning authorization, not supersession of 16, 58, 103, 219, 220, 20, 25, or ledger authority.

**Date:** 2026-11-03. **TASK_ID:** `DELIA-C3-FRAMEWORK-NATIVE-CONTEXT-CONTINUITY-MULTIEVIDENCE-PLAN-01`. **TYPE:** architecture/product execution plan; **NOT** code delivery, test acceptance, production deployment, phase advancement or unilateral supersession of frozen contracts.
**SOURCE SHA:** `6bac3df1af61b356fd38a6b76d905e48625b0e03` (origin/main inspected before authoring; reanchor immediately at implementation). **Owner:** DÉLIA Architecture/Coordination; executable portions by Devin on independently reanchored HEAD.
**AUTHORITY CHAIN:** HEAD/status → Project Instructions + .cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → 02 technical architecture → 24 product specification → applicable thematic sources → ledger.
**REFERENCES:** ADR 58; 103 (approved budget policy); 187–189; 191; 193–220 (especially 213, 219, 220); ledger M6/M7, DIAG, DIAG-E2E, DIAG-DECISIVE; .cursor/rules/{delia-execution-protocol,plan-construction,plan-execution,evidence-driven-execution,root-cause-generalized-fix}.mdc.
**PRODUCT DECISION:** prefer framework-native message/instruction/history processing and graph state mechanics over duplicative local commodity code, including removal of demonstrably redundant code. **SAFETY EXCEPTION:** framework features cannot replace Core/Domain authority, Evidence, Policy, Decision, security, or authoritative postcondition. **PRODUCTION_DEPLOY=NOT_AUTHORIZED**.

## 0. Status, evidence levels and hard conflict gates

| Finding | Classification | Source/outcome |
|---|---|---|
| Ollama Qwen3 4B + Pydantic AI + LangGraph local: single product structure `90260147` GROUNDED | PROVEN in prior real E2E | ledger DIAG-E2E |
| Second turn with `prior_turns`: repeated `invalid_structured_output` and gateway HTTP 504 | PROVEN occurrence; underlying formatting mechanism NOT YET PROVEN | ledger DIAG-E2E / DIAG-DECISIVE |
| In current adapter, `Agent(..., system_prompt=...)` plus nonempty hand-built `message_history` omitting system prompts | PROVEN in code | `delia-api/app/infrastructure/model_invocation/pydantic_ai_adapter.py` lines ~183–210 |
| Official Pydantic AI history behavior: nonempty `message_history` assumes existing system prompt; agent's new system prompt may not be generated; current-agent `instructions` is recommended; optional `ReinjectSystemPrompt` | DOCUMENTED framework behavior, actual installed-version payload requires live verification | https://pydantic.dev/docs/ai/core-concepts/message-history/ and https://pydantic.dev/docs/ai/core-concepts/agent/ |
| Existing scalar `_compare_records` cannot compare nested BOM hierarchies; comparison uses `vista.analyze` and is AuthZ-denied for local test user | PROVEN narrow execution/contract boundary; completeness of all alternative capabilities TO_INVENTORY | ledger + `orchestration.py` |
| The model received BOTH real product structures and compared them | TEST_NOT_RUN. Prior Qwen3 direct test received only one structure and correctly declined | DIAG-DECISIVE |
| Prior historical owner evidence can be treated as live FACT | FORBIDDEN by design; any reuse must be authorized, scope checked, revalidated | ADR 58 / evidence constraints |
| 16's historical 30s snapshot vs later doc 103 approved 60s / up to 3 calls / 300s maximum | DOCUMENTARY DRIFT REQUIRES RECONCILIATION BEFORE EDITING BUDGET POLICY | 16/103/20/ledger/runtime; never silently select either number |

**Do not call the adapter prompt/history hypothesis PROVEN until the exact installed Pydantic AI version and outgoing Ollama messages are verified with the same request/schema.** Preserve the two independent defect families: (A) model-call instructions/structured-output/timeout, and (B) multi-evidence composition/continuity.

## 1. Requirement ledger — closed scope

| RQ | Product outcome | Measurable acceptance |
|---|---|---|
| RQ-01 | A simple operational read still works with and without valid conversational history | Real authenticated Qwen3+DAVI results GROUNDED, original and sibling codes |
| RQ-02 | Every proposal gets its CURRENT trusted stage instructions even with nonempty history | Wire observation/test on installed Pydantic AI; no cross-stage instructions carried as authority |
| RQ-03 | Stage inputs contain only relevant, admissible, bounded context | stage matrices and comparable prompt token counts; no lost user-intended referent |
| RQ-04 | Retry/deadline/cancellation never causes runaway work or false 504 outcomes | real deadline trace, bounded attempts; terminal once; active execution bounded after disconnect |
| RQ-05 | Same-session references resolve user objectives without converting chat text to business FACT | A01→A02→A03, correction and missing/unknown negatives |
| RQ-06 | Investigations can analyze multiple authorized EvidenceFacts with traceable conclusions | verified pair of real product structures; positive, partial, conflict, nested/repeated hierarchy tests |
| RQ-07 | Model is semantic proposer, not Domain authority or unrestricted prose fact writer | validation rejects unsupported comparisons/fabrications; ADR 58/§6.145 preserved |
| RQ-08 | Remove redundant custom mechanics without replacing them with shadow abstractions | per-symbol KEEP/SIMPLIFY/REPLACE/REMOVE proof including all consumers and tests |
| RQ-09 | No migration of Chat runtime or new planner/agent/tool authority | static/behavioral architecture tests; no unauthorized writes |
| RQ-10 | Real-model and generalization outcomes justify release decision | stable SHA/config, repetition, latency/token metrics, owner postcondition and review |

**Phase/CP rule:** C3 scope is contextual intelligence; use 16/ledger/25 on implementation HEAD for actual phase, CP and NEXT. Do not invent a new CP or advance phase because this document exists.

## 2. Ownership and target arrangement

```text
USER / SESSION (interaction entrypoint and bounded user history)
    |
    v
DÉLIA APPLICATION — owned semantic state + admission + goal + authorized context policy
    |           |                               |
    |           +--> EvidenceRefs/provenance ---+--> live Core AuthZ + Domain revalidation
    |           |
    v           v
Existing LangGraph graph (sequencing, Send fan-out, retry/resume/checkpoint where legit)
    |
    +--> Existing InvokeModel / ModelInvocationPort
              |
              v
       Pydantic AI infrastructure adapter
       - trusted stage instructions (always effective for current stage)
       - compatible message history/processor after Application selection
       - typed outputs; provider/model request + usage/timeout
              |
              v
         Ollama Qwen3 4B (real model)
    |
    v
 Governed proposal validation + Evidence composition + Policy/Decision + Outcome
    |
    v
 Factual renderer; user answer with evidence and explicit limitations
```

**One accountable owner per data class:** user/session text is conversational context; active investigation state/goal/subobjectives is DÉLIA Application state (LangGraph is implementation of sequencing/checkpoint, not a business authority); domain evidence belongs to its Domain API, DÉLIA stores only scoped refs/projections where allowed; model history is a transport projection for an invocation, never an independent source of truth; Personal Memory is outside authorization and outside this scope.

**Framework ownership:** Pydantic AI handles message protocol, current instructions, output transport/structured validation primitives, usage when supported, provider mechanics. LangGraph handles graph execution/state/checkpoint/resume already legitimate. DÉLIA retains admissibility, intent proposal validation, live catalog/capability checks, provenance, read/write gates, authoritative outcome and rendering. Do not let a Pydantic Agent's unrestricted tools or loops create a second planner.

## 3. Existing-equivalent, candidates and deletion policy

| Responsibility / present code | EXISTING_EQUIVALENT | REUSE_DECISION | Treatment after proof |
|---|---|---|---|
| `ModelInvocationPort` and `InvokeModel` | YES | REUSE | KEEP stable framework-neutral boundary; simplify payload fields only with all consumers |
| `PydanticAiModelInvocationAdapter` | YES | EXTEND | Fix instructions+history using installed official API; prefer `instructions` or proven `ReinjectSystemPrompt`, not both by default |
| Manual `ConversationContextTurn` → `ModelRequest/ModelResponse` | YES | REPLACE_OR_SIMPLIFY_PENDING_PROOF | Move pure protocol assembly into adapter framework-native facilities; avoid semantic deletion of trusted/untrusted tags; preserve external session contract |
| Duplicated trimming/history budgets/helpers in Application and adapter | YES/PARTIAL | CONSOLIDATE | Keep ONE admissibility policy in Application; only mechanical projection/token window in adapter; remove duplicates upon regression proof |
| LangGraph `StateGraph`/Send/checkpoint | YES | REUSE | KEEP; never create parallel persistent investigation store solely for prompt history |
| Domain `EvidenceFacts`, `OutcomeVerdict`, policy/validation | YES | REUSE/EXTEND | KEEP; do not replace with agent memory/model output |
| `_compare_records` scalar validation | YES (scalar) | REUSE | KEEP for eligible scalar cases; extend composition only for proven multi-evidence gap; no product-specific compare service |
| Custom generic model retries/timeout controls | YES/PARTIAL | SIMPLIFY_AFTER_CONTRACT | ONE effective governance policy at turn/stage; framework provider timeout/usage mechanics; eliminate duplicate internal retry loops if bounded equivalence proven |
| `_synthesize_content` frozen factual rendering | YES | REUSE | KEEP selection-only and owner-value factual copying; no open-ended factual text channel |
| Agent loops, new context orchestrator, new workflow/store | Existing owners already cover mechanics | NOT_APPROVED | NO NEW component; revisit only with ADR, real consumer and negative A/B |
| Pydantic AI history processing, usage limits, output modes | Framework native | ADOPT_BOUNDED | Feature-flagged local parity first; pinned installed API; no unchecked beta/SDK upgrade |

**Deletion gate:** map every candidate by SYMBOL → producer → actual consumers → contract → alternative framework primitive → behavior parity + safety tests → removal PR → residual search. `REMOVE` requires proof of zero required consumers and no loss of audit/evidence/compatibility; removing code that reappears in a new wrapper is NOT simplification. Clean Architecture forbids SDK imports outside Infrastructure. Unchanged legacy adapter remains explicit rollback until separate acceptance; do not carry a second live fallback planner.

## 4. Frozen decisions and collision handling

- ADR 58, 219 and 220: LLM proposes semantic interpretation, Application validates and gates; `MODEL_AUTHORED_FACTUAL_PROSE=NONE`; `EvidenceFacts` and `OutcomeVerdict` authoritative semantics are not delegated to model. Any violation: STOP `ARCHITECTURE_DECISION_REQUIRED`.
- 103's product budget decision and 16/20/runtime must be explicitly reconciled by highest authority and current PO-approved chronology **before** changing numerical budgets. This plan does NOT rewrite the global cap, 60s-per-call policy, 3-attempt cap or gateway config.
- `mcp:vista.analyze` owner/authorization remains intact; composition within DÉLIA cannot become an unapproved shadow owner of VISTA-exclusive business analytics. Compare against evidence already legitimately in DÉLIA is a different responsibility, to be contracted with owner and consumers.
- `prior_turns` may contain client-supplied untrusted text; never treat as instruction, source of identifiers, permission or FACT. Trusted `instructions` must never be assembled from user, tool metadata or raw evidence.
- Tool and MCP results remain untrusted; no autonomous ACT, cross-domain imports, unsafe secrets, or backend authorization bypass.

## 5. Execution roadmap — finite bounded work packages

All packages use `E*.S*` plan-construction style, per-step baseline/ownership/RED→GREEN/real Qwen3 eval/review/rollback; no phase advancement until accepted. Sequence may be split across executor chats; never launch unbounded exploratory cycles.

### E0 — Freeze factual baseline and contract deletion map (bounded, read-only)

**E0.S1** Reanchor latest HEAD/status; identify installed pydantic-ai and langgraph versions and configured OpenAI-compatible Ollama output mode. Read 16→50→17→49→51→52→21→20→25, 58, 103, 187, 189, 191, 213, 219–220 and ledger. Reconcile 30s/300s drift as explicit decision gate, not local workaround. Record phase/CP/RQ.

**E0.S2** Read actual consumers only of `ConversationContextTurn`, `ModelInvocationRequest`, `_model_stage_proposal`, history construction and `TurnDeadline`; prepare concise symbol-level KEEP/SIMPLIFY/REPLACE/REMOVE matrix. No generic full-repo inventory. Capture A01 and A02 prior diagnostic traces, hashes of schemas and safe prompt roles. **Output:** bounded baseline with code SHA and contract/deletion candidates.

**Gate E0:** no runtime diff until installed SDK request role semantics are proved; unexpected frozen-decision conflict → `EXECUTION_DRIFT`.

### E1 — Correct current-stage instructions and structured-message parity (FIX-1A, top priority)

**E1.S1 RED:** using actual pinned Pydantic AI and real local Ollama Qwen3 (plus deterministic unit probe for exact protocol mechanics), reproduce identical `interaction_admission` and `turn_goal` schema/current question **with history empty vs nonempty** and capture effective outbound *roles, instruction presence, schema identity* (sanitized; no chain-of-thought). Test history from another stage or assistant answer must not supersede current trusted instruction.

**E1.S2:** compare Pydantic AI `Agent(instructions=stage_instruction)` vs `Agent(system_prompt=...)` plus `ReinjectSystemPrompt` if supported by the **installed** version, on a small pre-declared paired matrix. Choose the simplest mechanism that reliably places current trusted stage instructions on each invocation and respects prior history. Default candidate: `instructions`. Explicitly test provider behavior and structured-output shape. Do not introduce a new context service.

**E1.S3 IMPLEMENT:** smallest adapter-local change; no SDK import in Domain/Application, no new planner, no user/history text in instructions, no free fact prose. If framework output strategy for Ollama is incompatible, evaluate bounded native/tool/prompted strategies only if current mode fails with actual Qwen3; no undocumented option or blind upgrades.

**E1.S4 GREEN:** adapter parity (empty/nonempty/foreign-stage history, absent optional fields, nested args, fail-closed, provider errors); independent real Qwen3 paired eval with multiple repetitions, original A02 and unrelated/ambiguous turn. Record invalid structured proposal rate, outputs, tokens and latency. Restore baseline via explicit legacy rollback if necessary; no silent runtime fallback.

**Gate E1:** must demonstrate wire-level current instruction and statistically/operationally improved bounded proposal acceptance, not simply "test passes". If no improvement, isolate schema/provider strategy within E1, do not proceed as if solved.

### E2 — Simplify stage context and remove duplicate machinery (FIX-1B)

**E2.S1:** define **existing stage contract matrix**, not new engine: admission/goal = current turn + bounded semantic continuity only; selection = goal/live eligible catalog; arggen = schema + evidence-backed identifiers; evidence reasoning = verified projections; synthesis = governed facts/verdict. Explicitly classify purpose and trust level in present request fields if needed; do not pass raw full transcript to admission just because `message_history` exists.

**E2.S2:** prefer Pydantic AI framework-native message handling/history processors for *mechanical* message transformation after Application chooses allowed content. Do not persist SDK messages in Application. Avoid summarization by an LLM as a mandatory extra stage. Reuse current context budgets/projection helpers, deleting duplicate truncation/reconstruction branches once consumption is verified.

**E2.S3:** evaluate same prompt with zero/short/long history, topic change, cross-turn references and prompt-injection/tool-data decoys. Model must retain referents, objective and epistemic labels; cannot infer provenance from history. Demonstrate fewer/steady input tokens without losing business outcome.

**Gate E2:** paired outputs with stable schema, scope and business outcome; no "smaller context" if meaningful needed evidence/references were removed. REMOVE only with all consumer tests.

### E3 — Enforce one effective deadline/cancellation boundary (FIX-1C)

**E3.S1:** inspect real Flask/WSGI/worker/NDJSON streaming cancellation and synchronous `agent.run_sync` behavior; prove what can/cannot abort an in-flight Ollama request. Verify Pydantic AI timeouts/retry semantics, outer invocation retries and real provider socket deadlines. Reconcile approved global/individual settings; do not arbitrarily lower or raise them.

**E3.S2:** make cancellation/deadline contract effective across model call, retries, response/gateway and terminal state. Consider native async `agent.run` only if compatible with current server/worker and verified to improve cancellation; no cosmetic async wrapper or detached work. Guarantee bounded release and no duplicate terminal. If active request cannot be forcibly canceled by current provider, state exact limitation and enforce no new retries/work plus provider deadline/worker containment.

**E3.S3:** test forced timeout, disconnect, 504 prevention/terminal honesty, aborted request, slow Ollama, Core/MCP denial, provider unavailable, racing cancellation and retries; run real local model. Log actual duration and token usage when available, never fabricate missing usage.

**Gate E3:** no unbounded post-disconnect churn; deadlines govern *actual work*; explicit safety fallback preserved.

### E4 — Specify and implement bounded multi-evidence composition (FIX-2, separate architecture decision)

**E4.S1 CONTRACT FIRST / REVIEW GATE:** existing owner/consumer/contract inventory for `EvidenceFacts`, `GoalEvidenceJudgment`, `OutcomeVerdict`, subobjective tracker, scalar `_compare_records`, `InvokeModel`, `vista.analyze` and graph fan-in. Decide `EXISTING_EQUIVALENT` by responsibility: existing inference and Evidence owners YES; tree-composition equivalence TO_INVENTORY until proved. Specify minimal typed **proposal** over verified evidence references, comparisons/relations/limitations per item, non-equivalent units/scopes, hierarchy/repeats, error taxonomy, resource caps, lifecycle, compatibility/rollback and tests. Require coordination approval before runtime change; no implicit override of ADR 58 selection-only.

**E4.S2:** use **existing LangGraph fan-in/state** of completed subobjectives, Application evidence selection/provenance and `InvokeModel` for typed comparison proposal. Do NOT create `compare_products` service, new planner, autonomous Pydantic tools, provider branches or a VISTA shadow capability. Inference of relationships is HYPOTHESIS, not FACT; deterministic validation must trace each supported conclusion to authority and reject invalid or cross-scope comparisons. Retain VISTA where contractually necessary/authorized.

**E4.S3 RED→GREEN/E2E:** retrieve both full real structures 90260147 and 90260148 (plus hierarchy/repeated items/unknown product/unequal unit and unauthorized owner negative), run actual same Qwen3 on both structures, compare with independent deterministic reference, then same-session and single-turn DÉLIA E2E. This mandatory two-complete-structures model test was NOT executed in DIAG-DECISIVE. If Qwen3 cannot compare reliably under real budgets, do not falsely mark implementation PASS.

**Gate E4:** verify actual user outcome against Domain API, no hallucinated values, compositional ability generalizes to sibling scenarios.

### E5 — Governed continuity across turns (FIX-3)

**E5.S1:** map owner and lifecycle of session text, investigation/checkpoint state, evidence refs/hashes, validity TTL and AuthZ. Check whether existing LangGraph checkpoint stores can legitimately persist only DÉLIA-owned operational state. Never make checkpoint a duplicate Domain database or source of business FACT.

**E5.S2:** reuse minimal reference/provenance contract with live reauthorization/revalidation on dereference; preserve user-only semantic history; store no secret or uncontrolled payload. Prefer already accepted state owner and API. No new memory DB/registry, no Personal Memory as permission.

**E5.S3:** execute real Qwen3+real DAVI tests A01→A02→A03→A04 within same conversation ID, correction turns, session isolation, stale evidence, rights revocation, failed owner, budget and replay cross-user negatives.

**Gate E5:** follow-up uses correct validated targets/evidence, no leakage/no invalid replay, normal requests do not re-fetch unnecessarily without legitimate reason.

### E6 — Cleanup, architectural simplification and release gates

**E6.S1:** remove actually superseded code, flags, duplicate parsers, legacy message transformations, retry duplication and obsolete tests **only** after consumers are migrated and safety tests GREEN. Use original/changed code graph: `REMOVED_SYMBOLS`, `REMOVED_LOC`, `NEW_LOC`, unchanged behavior gates, residual search. Never delete audit/security logic merely because SDK validates JSON.

**E6.S2:** architecture check: framework imports Infrastructure only; one model adapter active per process; LangGraph still sequencing/checkpoint (not second planner); no new unauthorized catalog, tool authority, writes, persistence or REST bypass. Legacy rollback is retained only per frozen M7 requirement until separately authorized retirement.

**E6.S3:** full regression + local real-model E2E matrix original, sibling, complex, unknown, injected, AuthZ-denied, timeout, cancellation, multi-turn and comparison. Distinguish `PASS | FAIL | INCONCLUSIVE | TEST_NOT_RUN | STALE_EVIDENCE`. Validate configured actual SHA/model/SDK with warm/cold times, input/output tokens and business outcomes. Visual Portal QA independent, never imply by API 200. Explicit production release decision separate.

**Final gate:** `ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE`; no production deploy without PO authorization.

## 6. Tests matrix — RED/negative/generalization minimum

| ID | Scenario | Expected objective |
|---|---|---|
| CT01 | identical admission request with `prior_context=[]` vs nonempty | effective current instructions identical/complete; valid typed output |
| CT02 | history includes previous stage's assistant output, no system prompt | current stage instruction remains authoritative; prior output untrusted |
| CT03 | long/short history, cross-topic and referential follow-up | relevant referents retained, bounded input, no schema failure cascade |
| CT04 | malformed model output, missing required, optional omitted, wrong type | governed fail-closed errors; bounded retry only |
| CT05 | mid-call user cancellation / provider hang / gateway disconnect | no continued unbounded work, one terminal, measured timings |
| CT06 | owner AuthZ denied, stale prior evidence, user/cross-session confusion | no illicit reuse or access |
| CT07 | two complete actual BOM trees + deterministic reference | correct common/exclusive/repeated nodes, units, hierarchy, limitations |
| CT08 | one BOM absent/partial + contradictory or uncomparable records | honest insufficiency; no fabricated comparison |
| CT09 | real 3-turn A01→A02→A03, then correction A04 | stable conversation and verified comparison across turns |
| CT10 | unrelated owner read, no comparison, direct structural read | no regression or unnecessary graph loop |
| CT11 | injected MCP content/metadata, proposed ACT without permission | no instruction override; live gates unchanged |
| CT12 | alternative authorized capability/owner and unknown capability | provider-neutral planning and owner validations preserved |

Freeze exact local test questions before tuning; execute repeats sufficient to expose Qwen3 variance. Use both unit/contract tests and actual authenticated Ollama+MCP/Domain outcomes. A model's success at refusing missing evidence != successful comparison.

## 7. Explicit execution briefs / bounded Devin handoffs

**BRIEF A — E0+E1, IMMEDIATE:** `DELIA-C3-FRAMEWORK-NATIVE-INSTRUCTIONS-HISTORY-STABILIZATION-01`. Reanchor; prove exact wire behavior; implement adapter-local correction with official Pydantic AI current-stage instructions; RED/GREEN; real Ollama Qwen3; regressions; separate business and latency outcome; document and push. No new architecture; no deploy.

**BRIEF B — E2+E3, after A verdict:** `DELIA-C3-STAGE-CONTEXT-AND-BOUNDED-CANCELLATION-SIMPLIFICATION-01`. Reanchor; clarify drift 16 vs 103 before changing numeric limits; context stage policies on existing contracts; framework-native history processor only for mechanics; cancel/deadline handling; remove duplicated code with consumer proof; real-model paired tests; document and push. No deploy.

**BRIEF C — E4 SPEC ONLY:** `DELIA-C3-MULTIEVIDENCE-COMPOSITION-CONTRACT-ADR-01`. Reanchor and contract proof; produce full owner/consumer/data/validation/error/compat/rollback contract and architecture decision request for any frozen synthesis deviation; real-model two-tree capability A/B. **STOP FOR COORDINATION REVIEW BEFORE IMPLEMENTATION.**

**BRIEF D — E4 IMPLEMENT, conditional on approved C:** `DELIA-C3-GOVERNED-MULTIEVIDENCE-COMPOSITION-IMPLEMENTATION-01`. Implement only approved contract, reuse existing graph state and model port; RED/GREEN, two-tree actual Qwen3 E2E, regression/negative; document/push. No deploy.

**BRIEF E — E5+E6, after D verdict:** `DELIA-C3-CROSS-TURN-STATE-CONTINUITY-AND-REDUNDANCY-REMOVAL-01`. Reanchor; existing owner/checkpoint and refs; implement revalidation; remove redundant code/contracts after consumers migrate; real multi-turn, safety, token/latency outcome; document/push. No deploy.

Each report MUST include: TASK_ID, BASE_HEAD, EVALUATED_SHA, FINAL_SHA, origin_main, clean/dirty tree, AUTHORITIES_READ, CP/RQ, owner/consumers/contract, EXISTING_EQUIVALENT/REUSE_DECISION, ALLOWED/FORBIDDEN files, RED/GREEN, real_model_eval config & outcome, deletions/new code, risk/rollback, test status, commit/push verified, residuals/NEXT, production deploy NOT_AUTHORIZED.

## 8. Code impact — candidates, not unverified mandates

**Primary adapter:** `delia-api/app/infrastructure/model_invocation/pydantic_ai_adapter.py` (`Agent` creation, messages, `run_sync`, output/exception map).
**Application model caller:** `delia-api/app/application/capability_provision/orchestration.py` (`_model_stage_proposal`, `_admit_conversational_turn`, goal/selection/arggen, `_compare_records`, `_synthesize_content`, evidence fan-in).
**Interaction:** `delia-api/app/application/interaction/handle_interactive_turn.py` and existing turn-budget/context contracts; actual symbols and locations reverify.
**Graph:** `delia-api/app/infrastructure/orchestration/langgraph_engine.py` and existing state/checkpoint consumers; reverify SHA and installed versions.
**Tests:** existing Pydantic AI adapter, stage/interaction, architecture isolation, evidence/CRI, LangGraph and E2E harness. Do not rewrite mocks to conceal real-model failure.
**FORBIDDEN by default:** Core/Keycloak permissions; Domain API facts; business owner logic; Automation Hub; production config/release; Chat runtime; any new persistence/migration; deletion of governance/evidence validators.

## 9. Approval and review milestones

- **Approved product direction:** use existing frameworks, simplify or delete proven redundant local code, prioritize functioning baseline over ad hoc complexity.
- **Authorized implementation path:** E0/E1 and bounded E2/E3 corrections **subject to reanchor, safety and real eval**; contract-impact gates apply, no unilateral frozen-contract revision.
- **Conditional architecture approval required:** E4 typed multi-evidence contract; any change from selection-only synthesis; E5 if storage/retention or public conversation contracts change.
- **Release:** no production deployment or production cutover under this plan. M7 residuals (Portal visual, VISTA delegated access, Qwen3 variability) remain explicit rather than self-accepted.
- **No infinite diagnostics:** E0/E1 must close the current-stage instruction hypothesis as confirmed/refuted in one bounded experiment; use the result to implement the smallest correct fix or flag `EXECUTION_DRIFT` with exact evidence.

## 10. Authoritative external references (informative; not runtime proof)

- Pydantic AI, message history & `ReinjectSystemPrompt`: https://pydantic.dev/docs/ai/core-concepts/message-history/
- Pydantic AI, `instructions` vs `system_prompt`: https://pydantic.dev/docs/ai/core-concepts/agent/
- Pydantic AI, typed output modes: https://pydantic.dev/docs/ai/core-concepts/output/
- LangGraph, persistence/checkpointers: https://docs.langchain.com/oss/python/langgraph/persistence
- LangGraph, state / format prompt on demand: https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph

Framework docs may be newer than the pinned installed version. Executor must verify compatibility at evaluated SHA; no unsupported API assumptions.

**ARCHITECTURE STATUS:** `PLAN_RECORDED / PARTIAL_EXECUTION_DIRECTION_AUTHORIZED / E4_ARCHITECTURE_DECISION_REQUIRED / TEST_NOT_RUN_IN_THIS_PLANNING_TASK`. No user-facing acceptance or phase change implied.

## 11. R1 independent review — defects in initial delivery plan and corrective controls

**REVIEW_STATUS=REWORK_PLAN_EXECUTION_CONTRACT / PLAN_REVISED, NOT RUNTIME_ACCEPTED.** Baseline review SHA: `9627895060f3a0a786bd5ad217c585f42cf619de` (reanchor on execution); initial plan's splitting E0–E6 into five separately returned tasks did not ensure user-facing end-to-end outcome. R1 closes that orchestration gap without waiving frozen authority. All earlier details remain applicable except where this R1 overlay explicitly **tightens execution and acceptance**.

| Initial omission / risk | R1 correction |
|---|---|
| E1 could be returned as "done" before A01→A02→A03 | Single integrated acceptance includes actual multi-turn and two-tree comparison |
| E4 only spec, optional D execution in another chat | Execute contract-authorized implementation after approval gate in the same overall program; request decision only if needed, never silently bypass |
| No committed cleanup/LOC result mandatory | Require per-symbol before/after removal with consumer and substitution evidence |
| Schema failure cause could be assumed from framework docs | Verify exact outgoing stage instructions/roles under pinned SDK in local wire trace; preserve alternative hypotheses |
| One-structure model test erroneously called D1 | Full two-tree real-Qwen3 comparison with independent deterministic oracle mandatory |
| Narrative "prior_turns cause" was overclassified | Control same input/schema with empty/nonempty history and repeated paired trials; report probability, no causal overclaim |
| Gateway 504 treated as a simple numeric budget mismatch | Trace worker/WSGI/NDJSON/HTTP cancellation, call-level provider timeouts, queue/time spent, terminal/outcome semantics |
| Real E2E can be blocked on VISTA denial | Test authorized DAVI-composition path separately, do not grant permission or claim VISTA unnecessary for VISTA-owned actions |
| Framework replacement could create shadow state planner | Explicit owner data-class map, state/wiring proof and removal of duplicate implementations |
| Green unit tests might be treated as business outcome | Real local authenticated E2E with complete structures, semantic correctness, latency/tokens and safety gates |

## 12. ONE coordinated Devin delivery / non-negotiable finish contract

**COORDINATED_TASK_ID:** `DELIA-C3-FRAMEWORK-NATIVE-CONTEXT-AND-MULTIEVIDENCE-ENDTOEND-DELIVERY-01`
**EXECUTOR:** Devin. **TASK TYPE:** integrated authorized execution, anchored to doc 221 R1, not five "analysis and return" handoffs.
**PRODUCT OUTCOME:** User can (a) query 90260147, (b) query 90260148 in the SAME conversation, (c) request "compare the two structures", and (d) receive a comprehensible grounded, complete-enough comparison of common/exclusive components, quantities, hierarchy and genuine limitations. Also single-turn compound questions must work, without provider-specific or product-code hardcoding.
**DEFAULT USER:** local Keycloak `user@local.com` via legitimate auth + live Core AuthZ, only after confirming previously authorized test account state. No RBAC modifications; no account `rober`. Do not persist passwords or tokens.
**TARGET RUN:** real local Qwen3/Ollama + real Pydantic AI adapter + existing LangGraph engine + live DAVI MCP/Domain API + current DÉLIA HTTP session. No fake model or injected fixture substitutions in user-outcome acceptance.
**EXECUTION CONTROL:** E0→E1→E2→E3→E4-ADR gate→E4 implement if approved→E5→E6, without returning a terminal delivery report after E1, E2 or E3. Record intermediate evidence/checkpoints in GitHub as necessary; continue proactively within allowed scope.

**STOP / ESCALATE ONLY IF:** high-authority contract collision, material security/owner/scope contradiction, indispensable explicit PO decision, unavailable external authoritative access, or genuine technical blocker after bounded reproduction and alternative approaches exhausted. Then emit `ARCHITECTURE_DECISION_REQUIRED`, `EXECUTION_DRIFT` or `INCONCLUSIVE` with exact offending contract, evidence, lowest blocked step and independent work already completed; do **not** report an overall successful implementation. A framework feature incompatibility alone is not permission to stop early; try the documented compatible alternative within existing adapter and keep factual result. Never bypass denied AuthZ.
**PO APPROVAL BOUNDARY:** user approved simplifying/replacing/deleting local redundant mechanics, preserving legitimate owners, gates, business contracts and safety. This does NOT silently approve changing ADR 58 §6.145 synthesis restriction, implementing a second analytics owner, adding migrations/stores, expanding retention, or creating broad agent tools. For such change, stop at scoped gate with a complete draft ADR and alternatives, but finish unblocked work.
**EXIT:** either `FUNCTIONAL_ACCEPTANCE_CANDIDATE` only after all mandatory gates PASS, or `BLOCKED_WITH_EVIDENCE`/REWORK/INCONCLUSIVE. "Code merged", "1420 tests green", "model answered one structure", "HTTP 200", "docs updated", "model refused absent structure" are never the final outcome.

## 13. R1 implementation detail by ownership

### E1 — Pydantic AI instructions/history and output validity

- Capture paired baseline for **the same exact question**/stage/schema/model/settings/provider state with and without `prior_context`; inspect outgoing Pydantic request `messages` including **current trusted system/developer instruction presence** (sanitized). Distinguish system prompt, `instructions`, `ReinjectSystemPrompt` and any history processors by installed-version API. Protect against stale system instructions from previous stages.
- Verify `Agent(... system_prompt=...)` current behavior with nonempty `message_history`. If current-stage instruction omitted, fix using **official** Pydantic AI `instructions` or precisely justified reinjection compatible with Ollama; avoid duplicate instruction injection. If not omitted, investigate actual schema/serialization/JSON output strategy before rewriting.
- Model structured-output choices (native/tool/prompted) only inside adapter with explicit paired Qwen3 A/B; do not introduce Pydantic tools that execute Domain/MCP directly. Keep governed validation as final semantic/safety validator. Separate wire/schema rejection from Application contract rejections and provider/transport failures.
- Make paired evaluation include >=3 repetitions per scenario if environment available; record invalid output type and actual input/output tokens when reported. A history-free successful run is control, not proof of causal source. Include adversarial history injection and stage instruction conflict tests.

### E2 — stage-context responsibility, contract reduction and deletion

- Specify **admissible context by purpose**, showing actual contract inputs/outputs and trusted/untrusted source tags: admission = current question + necessary turn-reference; goal = current goal and corrections; selection = goal + live authorized catalog; arggen = schema + authorized evidence-backed identifiers; comparison = verified multi-source evidence; synthesis = verdict + selected owner facts; recovery = bounded unresolved objective and failure reason.
- Use built-in Pydantic AI message processing only for adapter-level mechanical serialization/filtering after Application has approved context. The model/protocol layer must not decide user authority, provenance, factual validity or owner admissibility. Avoid optional "summarize all history" LLM call or a separate ContextService without equivalent/consumer proof.
- Review `ConversationContextTurn`, `ModelInvocationRequest.prior_context`, custom model message converters, `_fit_json_block` and token-budget helpers **by actual consumer**; classify each `KEEP|SIMPLIFY|REPLACE|REMOVE`. Explicitly delete obsolete conversion/trimming/retry helpers and tests only where framework equivalent and real regressions prove parity. Do NOT erase user-facing session contract merely because SDK has messages.
- Keep goal identity, correction references and meaningful context; do not simply set `prior_turns=()` across stages. If a stage needs no history, document why and test referential follow-up.

### E3 — deadline/retry/cancellation and response lifecycle

- Treat later PO doc 103 as binding product decision **unless** reanchor finds higher-authority conflict; reconcile 16 snapshot vs doc 103 with ledger/current runtime as explicit `DOCUMENTARY_DRIFT` gate. Do not quietly rewrite numeric policy.
- Draw one timeline across model `run_sync`/provider socket timeout, Pydantic internal output retries, Application `_model_stage_proposal` outer retries, `TurnDeadline`, gateway read/stream timeout, worker execution, disconnect/cancel observable flag and final terminal. Distinguish max attempts per *logical model call* from higher-level turn/recovery attempts and model-internal structured output correction loops. One request may not invisibly multiply retries.
- Implement only the smallest verified fixes in existing Infrastructure/Interaction/Application boundaries. Consider native `await agent.run` only if actually compatible with deployed stack and cancellation; never a detached asynchronous invocation leaving orphan model calls. If in-flight cancellation isn't possible, ensure provider timeout and bounded work, no retries after cancel, terminal once; document exact residual.
- Test at least: repeated structured invalid output, slow provider, drop client connection, model timeout, owner denial, expiring global deadline, concurrent requests and user stop action. No 504 caused by avoidable 5–6 proposal retry churn; honest error/continuation must conform to stream contract.

### E4 — multi-evidence governed composition (contract gate and execution)

- First map consumers and legitimate owners for current source data (DAVI/Domain), external analytical owner (VISTA), scalar `_compare_records`, `EvidenceFacts`, `OutcomeVerdict`, subobjective tracker, LangGraph fan-in and `InvokeModel`.
- **ARCHITECTURE DECISION REQUIRED** for exact typed compare composition contract: input collection of verified per-source evidence refs, scopes/hierarchical paths, units, quantities, cardinality/duplicates, completeness/truncation, owner version/TTL, failure/denial and correlation; output proposed per-claim evidence refs plus validation status, comparison alignment, uncertainty and limitations. AuthZ is live at dereference; JSON numbers vs material codes preserved; strict normalized units, ordered/repeated BOM nodes cannot be collapsed silently.
- Prefer existing graph fan-in and Pydantic typed output **through `InvokeModel`**, not an unrestricted LLM tool loop and not a new comparison provider. A model *proposes* candidate correspondences; deterministic validation/cross-check guarantees every stated business difference has owner-backed evidence. Preserve ADR 58/§6.145 no model-authored factual prose; if adequate human explanation requires semantic phrasing beyond frozen selection-only rules, submit separate ADR and negative safety E2E before implementing. Composition is not a replacement for VISTA-exclusive analytics; no permission assumptions.
- **Mandatory preliminary capability test:** fetch BOTH complete structures in local real context; run Qwen3 standalone with the two complete authorized projections; measure correct similarities/differences against deterministic oracle. This is not a runtime implementation substitute. The prior D4 single-tree refusal does NOT satisfy it.
- Complete E4 implementation once contract has been explicitly approved. If approval cannot be obtained in the execution session, stop the affected implementation at that gate, leave precise ready-to-approve contract and continue any independent safe steps. Do not report full solution working.

### E5 — cross-turn continuation and evidence reference lifecycle

- Separate (1) conversation semantics, (2) investigation state (goal/subobjectives/retries/checkpoints), (3) authority evidence refs/owner revalidation. Pydantic `message_history` transports relevant dialogue; LangGraph stores/checkpoints existing operational state if legitimate; Domain remains factual owner.
- Evidence re-use via existing reference/provenance representations only after authorization/identity, relevant ownership, TTL/version, scope/completeness and revocation checks. Do not persist unbounded raw payload, secret, tool output or business truth in chat memory. On stale/insufficient evidence, refetch through authorized owner or report limitation.
- Test full same-session conversation with genuine `conversation_id`; client-supplied injected prior text never proves identifiers/roles; cross-session and cross-user leakage negative; retry/resume and topic switch. Avoid representing repeated owner read as inherently wrong: revalidation is often required.

### E6 — remove/merge old code and verify end-to-end

- Explicit file/symbol delta: removed custom message assembly or duplicated budget/prompt code **only** after native framework replacement proven; delete obsolete flags and dead wrappers rather than carrying parallel path. Show `REMOVED_SYMBOLS`, `REMOVED_LOC`, `ADDED_LOC`, `NET_LOC`, actual consumer migration, dependency changes and residual search results. A larger safe refactor is allowed if it demonstrably reduces conceptual ownership and is covered by tests; "smaller diff" is not a reason to preserve duplicate authority.
- Confirm SDK imports remain Infrastructure, one inferred model runtime active, LangGraph sequencing without second planner, no framework-owned Domain authority, no user-facing Chat runtime reuse, no hardcoded products or regex routing, no safety/security removed.
- Run full relevant regression on **final evaluated SHA**, not an earlier intermediate HEAD, including isolated adapter tests, orchestration, CRI/evidence, security, LangGraph, interaction/stream and API. Missing dependencies/mount fixtures are environment outcomes not excuses to claim PASS; reproducibly fix local harness if legitimate.
- Run local real-model authenticated user E2E **on final evaluated SHA/config**, with Ollama Qwen3, actual DAVI/Domain, same conversation A01→A02→A03→A04, single-turn complex comparison, original/sibling/unknown code, evidence partial, AuthZ denial, prompt injection, interruption; measure latency by stage, retries, usage, provenance and business difference accuracy. Compare against reference oracle. Portal visual QA can remain `TEST_NOT_RUN` only if screenshot/login dependency prevents it and is an explicit release residual; API acceptance cannot be inflated to production release.

## 14. R1 objective final acceptance matrix — ALL mandatory

| Gate | Positive acceptance | Negative / boundary acceptance |
|---|---|---|
| G01 AUTHENTICATION | Local `user` legitimate Keycloak/Core session with test authority | no RBAC mutation or borrowed personal account |
| G02 FRAMEWORK_WIRE | trusted stage instruction present when history empty/nonempty; Pydantic typed schema valid | stale assistant/system instructions do not override current stage |
| G03 REAL_SINGLE_READ | 90260147 and 90260148 grounded through real DAVI | unknown/nonexistent product not invented |
| G04 MULTITURN | same conversation ID: A01→A02→A03→A04 reaches grounded compare | context switch/referential ambiguity doesn't invent identifiers |
| G05 SINGLE_TURN_COMPOUND | query both structures and compare in one user turn | partial structure yields honest caveat |
| G06 TWO_TREE_MODEL_ORACLE | same Qwen3 receives both full structures, comparison checked by deterministic oracle | model hallucination never treated as FACT |
| G07 EVIDENCE_COMPOSITION | proposed comparison aligns hierarchies, quantity units, repetition and scope; refs attributable | unauthorized, truncated, different-scope information not joined |
| G08 RELIABILITY | bounded retries and provider call time; no avoidable gateway 504 | disconnect/cancel no unbounded server churn |
| G09 STATE_SECURITY | live revalidation of references/identity; no leaked context | cross-user, stale owner, prompt injection tests fail closed |
| G10 FRAMEWORK_SIMPLIFICATION | framework-native mechanisms replace redundant custom mechanics, with deletes documented | no hidden duplicate planner/registry/authority introduced |
| G11 REGRESSION | full relevant suite PASS on final SHA/config, no invented exclusions | negative cases, contracts and security intact |
| G12 BUSINESS_OUTCOME | answer conveys correct similarities/differences and explicit limitations in natural PT-BR, with evidence | HTTP 200/structured-only/model refusal alone cannot count as completion |

**End-state truth table:**
- `FUNCTIONAL_ACCEPTANCE_CANDIDATE` only if G01–G12 PASS on same final SHA/runtime with proof links; reviewer independently issues ACCEPT/ACCEPT_WITH_RESIDUAL/REWORK.
- `ACCEPT_WITH_RESIDUAL` may still be appropriate for nonblocking Portal visual/VISTA permission scope issues, but missing G04/G05/G06/G07/G12 is BLOCKING for the user's requested solution.
- `TEST_NOT_RUN` on mandatory real-model E2E is **not** a successful delivery.
- Model variance: report repeats, failure rates and worst-case; do not hide one failed run behind a successful one.
- No production deployment is permitted even if all G gates PASS without separate release authorization.

## 15. R1 failure classification and efficient recovery without endless cycles

If a stage fails, record `FIRST_FAILED_BOUNDARY`, `ATTEMPTED_FIX`, `EVIDENCE`, `CANDIDATE_ALTERNATIVES`, `NEXT_SAFE_CHANGE`; apply the next minimal framework-supported alternative **within the same bounded E-step**, re-run original, sibling and negative. Do not return terminal merely to ask to diagnose again. Do not tune prompt, model, schema and budget simultaneously.

Stop only on actual governance/business approval gate, owner denial, exhausted local infrastructure ability, irreducible SDK incompatibility, or repeatable blocked business prerequisite after reasonable bounded alternatives. Never claim no work can proceed merely because VISTA denies: independently exercise admissible local evidence composition if authorized.

## 16. R1 documentation, versioning, concurrency and Git hygiene

At each executable step: reanchor new HEAD/dirty worktree, preserve concurrent work, identify ALLOWED_FILES/FORBIDDEN_FILES, contract impact, test preconditions; record outputs and diff. Rebase/push `main` safely with no unrelated edits. If doc 16's phase/NEXT conflicts with a later task ledger, disclose drift and follow authority, never silently claim advancement. Write report in established corrections directory, update ledger after genuine verification. No secrets, raw JWT/password, full company payloads or chain-of-thought in docs/logs.

Mandatory report keys: `TASK_ID`, `BASE_SHA`, `EVALUATED_SHA`, `FINAL_SHA`, `ORIGIN_MAIN`, `PUSH_VERIFIED`, `AUTHORITIES_READ`, `CP_RQ`, `OWNER_CONSUMERS_CONTRACT`, `EXISTING_EQUIVALENT`, `REUSE_DECISION`, `REMOVED_SYMBOLS`, `REMOVED_LOC`, `ADDED_LOC`, `TEST_MATRIX_G01_G12`, `REAL_QWEN3_E2E`, `LOCAL_AUTHZ`, `MODEL_PROMPT_WIRE_EVIDENCE`, `LATENCY_TOKENS`, `SECURITY_NEGATIVE`, `BUSINESS_OUTCOME`, `GAPS_DRIFT`, `ROLLBACK`, `REVIEW_VERDICT_REQUEST`, `NEXT`, `PRODUCTION_DEPLOY`.

## 17. R1 Devin master prompt — full executable contract

> **EXECUTE THE COMPLETE AUTHORIZED PROGRAM, NOT JUST BRIEF A.** Reanchor HEAD/.cursor and sources 16→50→17→49→51→52→21→20→25 plus ADR 58, 103, 187–220 and ledger. Follow doc 221 sections 11–18 as controlling review overlay. Implement E0–E3 autonomously using framework-native Pydantic AI/LangGraph responsibilities. Replace/delete locally redundant code with mapped consumer parity and safety gates, without creating a new planner or context engine. Prove actual outbound instructions with and without history and fix the observed structured-output instability on REAL local Ollama Qwen3. Restore bounded effective timeout/retry/cancellation. Prepare E4 multi-evidence typed contract, perform actual Qwen3 comparison using BOTH real BOM trees and oracle; obtain coordination decision for any frozen-contract impact; once approved, complete E4–E6 and all G01–G12 REAL E2E acceptance on the final SHA. Continue through legitimate implementation failures with bounded corrective iterations; do not return early as "planning complete", "tests green" or "one query grounded". Only return full functional acceptance with evidence, or a precise true governance/external/technical blocker with completed independent steps. Never bypass auth, forge tests, change frozen policy silently or deploy production. Report in canonical docs/ledger, commit and push only validated authorized diffs.

## 18. R1 reviewer/adversarial checklist

- Does latest `origin/main` contain planned code or competing PR work requiring reanchor?
- Was exact Pydantic AI wire behavior proved, not inferred from docs?
- Did multiple internal retries hide in one framework `Agent.run`?
- Are history messages correctly classified (trusted user vs untrusted tool/assistant) and scoped?
- Is framework-native history management not a second conversation database?
- Did all legitimate security/owner/instruction gates survive simplification?
- Are removal symbols truly gone and not re-created under new names?
- Is LangGraph doing real state/fan-in rather than only renamed custom loops?
- Did two real product structures reach the model together, with valid source refs?
- Are Qwen3 comparisons validated against deterministic evidence before user display?
- Can a corrected follow-up continue the same investigation without pretending previous model prose is Domain fact?
- Are HTTP, streaming/NDJSON and post-disconnect behavior actually bounded?
- Was local real E2E successful on **the same final SHA** as final tests?
- Are authorization-dependent VISTA scenarios kept separate from direct-authorized DAVI/Evidence objectives?
- Does the answer look like an intelligible business comparison, not raw JSON, empty, fabricated, or purely descriptive field dump?

**R1 STATUS:** `EXECUTION_PLAN_REVIEWED_AND_TIGHTENED`; **RUNTIME_IMPLEMENTATION=NOT_DONE_BY_THIS_DOC**; **TESTS=TEST_NOT_RUN_IN_PLAN_REVIEW**; **PRODUCTION_DEPLOY=NOT_AUTHORIZED**.
