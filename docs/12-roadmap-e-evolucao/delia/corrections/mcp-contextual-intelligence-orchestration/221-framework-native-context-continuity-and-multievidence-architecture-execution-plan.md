# 221 — DÉLIA · Framework-native context, continuity and multi-evidence — architecture and executable simplification plan

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
