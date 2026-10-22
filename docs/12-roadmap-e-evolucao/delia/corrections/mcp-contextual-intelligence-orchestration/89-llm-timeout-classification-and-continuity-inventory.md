# 89 — LLM Timeout Classification & Continuity Foundation (CP1+CP2)

`TASK_ID=DELIA-C3-LLM-TIMEOUT-CLASSIFICATION-AND-CONTINUITY-FOUNDATION-01`

Canonical reference: [doc 88](./88-governed-model-timeout-checkpoint-resume-architecture-decision.md)
(CP1 inventory + CP2 contract correction only — CP3/CP4 not implemented).

## 1. Proven defect

`GovernedCapabilityAttempt(status=SOURCE_UNAVAILABLE)` was returned for
internal deadline causes — `_StageDeadlineExceeded(model_timeout)` and
`TurnBudgetExhausted` / `turn_budget_exhausted` — which the interaction
layer then rendered as "Fonte indisponível. Não consegui consultar os
dados da DELPI", blaming a source that was never consulted. The
production incident capture (doc 87) showed exactly this user-visible
lie.

## 2. CP1 — error-classification trace

Full chain (before → after):

```text
LLM provider slow / stage deadline
  → _StageDeadlineExceeded(model_timeout) | TurnBudgetExhausted
  → SOURCE_UNAVAILABLE   [DEFECT]  →  PROCESSING_TIMEOUT [FIXED]
  → HandleInteractiveConversationTurn terminal branch
  → DELPI_SOURCE_UNAVAILABLE_MESSAGE  →  DELPI_PROCESSING_TIMEOUT_MESSAGE
  → message_kind SOURCE_UNAVAILABLE   →  PROCESSING_TIMEOUT
  → ActivityPhase.BLOCKED/state=BLOCKED → state=FAILED (honest)
  → InteractiveTurnResult → presentation v1 → NDJSON → MFE badge
  → MFE: "Fonte indisponível"          →  "Processamento interrompido"
```

Owners along the chain:

| Responsibility | Canonical source |
|---|---|
| attempt status taxonomy | `capability_attempt.py` `GovernedCapabilityStatus` |
| deadline machinery | `interaction/turn_budget.py` (`TurnDeadline`, `stage_timeout`) |
| stage timeout raising | `orchestration.py` `_propose` → `_StageDeadlineExceeded` |
| attempt classification | `orchestration.py` `attempt()` boundary catch |
| terminal surface | `interaction/handle_interactive_turn.py` `_source_terminal_result` |
| message kinds | `interaction/presentation.py` closed kind set |
| wire | `InteractiveTurnResult` → `presentation` v1 → NDJSON stream |
| MFE render | `plugins/delia` `presentation.ts` closed union + `DeliaAssistantMessage.tsx` `SEMANTIC_STATE` (render-only) |

Unchanged real-source sites (verified correct):
`_error_attempt` (MCP transport/authz errors), empty-surface-with-
provider-failures (orchestration.py ~4906), `plan_validation_failed`
(~5303), `foreign_source_unavailable` (~5619).

Provider-down model invocation (`ModelInvocationError` non-timeout)
never reached the defect: it maps to `MODEL_UNAVAILABLE`/`MODEL_TIMEOUT`
at the HTTP boundary — already technically honest.

## 3. CP1 — continuity inventory (what CP3 may reuse)

| Mechanism | Exists? | Owner/source |
|---|---|---|
| Turn/session persistence | **NO** | `handle_interactive_turn.py:7` — "Request-scoped only: no session persistence"; `InteractionSession`/`InteractionTurn` are domain value objects rebuilt per request; prior context arrives client-supplied via `context`→`prior_turns` |
| Activity persistence | **NO** | `ActivityEventSink` → in-memory queue → NDJSON stream; events die with the request |
| Streaming reconnect | **NO** | `_stream_interaction_turn` is one-shot; a "done" without terminal record just ends |
| Checkpoint/resume engine | **NO** | nothing exists |
| Governed retry | **NO** | no retry on deadline paths (by design); plan/recovery retries exist bounded elsewhere (repair-once) |
| Correlation/traceability | **YES** | `correlation_id` end-to-end; stage decision logs; `InteractiveTurnResult` bounded contract |
| Stage progress observability | **YES** | `orchestration stage=<id> decision=<d>` logs + `ActivityPhase`/`ActivityState` vocabulary |
| Idempotent owner calls | **PARTIAL** | reads are naturally idempotent; writes ride confirmation tokens — but no replay framework |
| Automation Hub | external substrate — not yet inspected for reuse (future CP3 decision) |

**Recommendation for CP3:** there is no legitimate in-repo
persistence/lifecycle mechanism today. A checkpoint contract would be a
new typed surface — per doc 88 CP3, if no legitimate mechanism exists
the correct stop is `ARCHITECTURE_DECISION_REQUIRED`. Candidates to
reuse if authorized: `InteractiveTurnResult` (bounded result shape),
`prior_turns` context contract (client-supplied continuity), Activity
event vocabulary (progress resume display), `correlation_id` (join key),
`TurnDeadline`/`stage_timeout` (bounded re-attempts). **Not** to persist:
chain-of-thought, prompts, credentials, presumed authorizations.
Resume must re-run AuthZ/contract validation — never trust stored
capability selections as grants.

## 4. CP2 — minimal fix

New enum member `GovernedCapabilityStatus.PROCESSING_TIMEOUT`
("an internal processing deadline — stage timeout or turn-budget
exhaustion — interrupted the attempt; `error_code` preserves the
observed cause `model_timeout|turn_budget_exhausted`"). One status, not
two: the turn budget IS a timeout, and a single member is the smallest
extension (doc 88: no parallel taxonomy).

Changed classification sites (4):
- `orchestration.py` `attempt()` `_StageDeadlineExceeded` catch
- `orchestration.py` `attempt()` `TurnBudgetExhausted` catch
- `orchestration.py` ~5747 budget-skipped identifier path
- `orchestration.py` ~6876 prior-continuation deadline

Interaction layer:
- `DELPI_PROCESSING_TIMEOUT_MESSAGE` — "O processamento da sua
  solicitação demorou além do limite e a tentativa foi interrompida.
  Não identifiquei uma falha na fonte de dados — nenhum dado
  operacional foi verificado. Você pode tentar novamente." (truthful:
  interrupted, no source blame, no fake continuity promise)
- `PROCESSING_TIMEOUT` added to the terminal branch; emits
  `ActivityPhase.BLOCKED` + `ActivityState.FAILED` (the attempt failed;
  not "blocked by a source")
- `_source_terminal_result` processing-timeout branch →
  `MESSAGE_KIND_PROCESSING_TIMEOUT` + `delpi_source_unverified`
  limitation (still true: no data verified)

Presentation contract: `PROCESSING_TIMEOUT` added to the closed
`_KNOWN_MESSAGE_KINDS` (additive, contract v1 — old clients see an
unknown kind and degrade neutral, never a wrong badge).

Frontend (render-only, no prose inference):
- `plugins/delia/src/api/presentation.ts`: union + `KNOWN_MESSAGE_KINDS`
- `DeliaAssistantMessage.tsx`: `SEMANTIC_STATE.PROCESSING_TIMEOUT` =
  "Processamento interrompido" / warning / `TimerOff`

## 5. Tests

RED → GREEN (new):
- `test_pre_mcp_timeout_never_blames_source` — select_capability
  timeout, zero MCP calls, `PROCESSING_TIMEOUT` kind + message,
  content never contains source-failure wording
- `test_turn_budget_exhausted_is_terminal_processing_timeout`
- `test_real_mcp_failure_stays_source_unavailable` — transport error
  keeps `SOURCE_UNAVAILABLE` + `error_code=mcp_timeout` (sibling)
- `test_insufficient_evidence_is_not_technical_failure` — SUCCESS +
  `insufficient_evidence` (distinct class)
- `test_processing_timeout_maps_kind` — serialization edge

Existing-coverage anchors kept green: authz denial
(`test_domain_authz_denial_is_truthful`), owner unavailable,
`mcp_protocol_error` → SOURCE_UNAVAILABLE, record-not-found → RESULT.

Updated assertions (deadline causes): test_execution_ceiling_turn_budget
(8), stage05_multiturn_latency (2), conversational_intelligence_recovery
(2), real_product_owner_read_and_budget_rework (2 + 1 set),
r45_selection_timeout_rework (set), i02r1, i02r3 (2), i02r2_index_probe,
r1_r3_none_selection, r2_selection_quality, stage03_discovery_guidance,
i01_contextual_knowledge_continuity (set).

## 6. Real evaluation (dev, real wiring)

- Forced boundary in `delpi-delia-api` container — real `Settings`,
  real `McpCapabilityProvider` (davi/teo/vista), `turn_budget_seconds=0`:
  `attempt.status=PROCESSING_TIMEOUT`, `error_code=turn_budget_exhausted`;
  handler result `message_kind=PROCESSING_TIMEOUT`, `NON_GROUNDED`,
  content = the interrupted-processing message. `EVAL_PASS`.
- Live P1/P2 reruns (natural): model-side selection variance routed to
  `openapi:delpi`/no-group → honest NON_GROUNDED conversational answers,
  no source-blame; one run hit the bounded conversational-timeout
  message honestly.
- Natural wire-visible PROCESSING_TIMEOUT not captured (depends on
  model latency sampling); the forced boundary + unit coverage prove
  the path.

## 7. Report fields

```text
BASE_HEAD=cff65bb63b165b (origin/main at worktree creation)
FINAL_HEAD=980e3dbeb75f4fdc3ac0afaac543b2de51c29ce7
ORIGIN_MAIN=980e3dbeb75f4fdc3ac0afaac543b2de51c29ce7
PUSH_VERIFIED=YES (ff cff65bb63b..980e3dbeb7)

ERROR_MAPPING_BEFORE=model/budget deadline → SOURCE_UNAVAILABLE
ERROR_MAPPING_AFTER=deadline → PROCESSING_TIMEOUT (+error_code preserved);
    real MCP failure → SOURCE_UNAVAILABLE; authz → AUTHZ_DENIED
ERROR_CONSUMERS=handle_interactive_turn(terminal), presentation.py,
    NDJSON stream, plugins/delia presentation.ts + DeliaAssistantMessage
INTERACTION_CONTRACTS=InteractiveTurnResult.message_kind +
    presentation.v1 closed kinds (additive, backward-compatible)
STREAMING_CONTRACTS=ActivityPhase.BLOCKED + ActivityState.FAILED
FRONTEND_CONSUMERS=closed union extended; unknown→neutral preserved

CHECKPOINT_EXISTING_EQUIVALENT=NO (request-scoped only)
RETRY_EXISTING_EQUIVALENT=NO (on deadline paths)
RESUME_EXISTING_EQUIVALENT=NO
BACKGROUND_EXECUTION_EXISTING_EQUIVALENT=NO
RESULT_DELIVERY_EXISTING_EQUIVALENT=NDJSON activity stream (in-memory only)

REUSE_DECISION=EXTEND(closed enum + kind sets; no new taxonomy)

MODEL_TIMEOUT_CLASSIFICATION=PROCESSING_TIMEOUT + error_code=model_timeout
TURN_BUDGET_CLASSIFICATION=PROCESSING_TIMEOUT + error_code=turn_budget_exhausted
MCP_SOURCE_CLASSIFICATION=SOURCE_UNAVAILABLE (unchanged)
AUTHZ_CLASSIFICATION=AUTHZ_DENIED fail-closed (unchanged)
INSUFFICIENT_EVIDENCE_CLASSIFICATION=SUCCESS + insufficient_evidence (unchanged)

BACKEND_REGRESSION=PASS (full suite; 2 documented pre-existing exclusions:
    mounted-doc schema collection error + stale 504 test vs soft-land)
FRONTEND_REGRESSION=PASS (64 tests incl. new kind badge + parse)
CRI_ON_OFF=PRESERVED (no CRI paths touched)
REAL_MODEL_EVALUATION=PASS (forced boundary + natural runs)
REAL_MCP_EVALUATION=PRESERVED (unit: real transport failure keeps SOURCE_UNAVAILABLE)
SECURITY_NEGATIVES=PRESERVED (no ACT, no authority change, no prose inference)

CHECKPOINT_IMPLEMENTED=NO
RESUME_IMPLEMENTED=NO
PRODUCTION_ACTIVATION=NO
I04_ACCEPTED=NO
C3_EXECUTED=YES

EXECUTOR_VERDICT=ACCEPT_WITH_RESIDUAL
NEXT_TASK=CP3 — architecture decision required before any checkpoint
    substrate (no legitimate persistence exists today); see §3
```


## 8. Coordination independent static review — 2026-10-22

**Verdict: ACCEPT_WITH_RESIDUAL (CP1+CP2 only).** Confirmed published HEAD `7ac1e1bef8e74493820877996e2f2a3976de488a`, report 89, changed-file inventory and static `PROCESSING_TIMEOUT` consumer references via GitHub. The executor's full regression/real-container outcomes are reported evidence; `INDEPENDENT_RUNTIME_REEXECUTION=TEST_NOT_RUN`. CP3/CP4 continuity remains NOT_IMPLEMENTED.

**CP2 accepted:** typed timeout/budget causes no longer need to masquerade as data-source failure; `GovernedCapabilityStatus.PROCESSING_TIMEOUT` is propagated to the interaction `message_kind` and MFE semantic-state contract. Real owner errors and denial remain separate. The new user copy truthfully states that the attempt was interrupted, without falsely promising ongoing work. A forced zero-budget path verifies classification, not real asynchronous recovery or a natural pre-MCP timeout through the full browser/prod path.

**CP1 scope caveat:** evidence supports `NO` checkpoint persistence, durable stream replay and resume **in the inspected request-scoped DÉLIA interaction path**. It does **not** yet prove absence of a legitimate reusable mechanism across Automation Hub, platform Work, Portal or existing shared contracts. The report explicitly says Automation Hub is external and not inspected. For the architecture decision use `EXISTING_EQUIVALENT=TO_INVENTORY` across ownership boundaries; do not generalize local absence into ecosystem-wide NEW authorization. `REUSE_DECISION=TO_DECIDE` for durable continuity.

**Requirements carried into CP3:** one user turn ID; typed, non-sensitive stage checkpoints (no chain-of-thought); revalidate live Core AuthZ and Domain authority; bounded retries; idempotency/dedup/cancellation/expiry; no automatic ACT replay; lifecycle beyond the 30s synchronous transport only through a real authorized substrate; UI says CONTINUING only if backend actually owns persistent work. C3 model selection remains LLM-driven, not regex/provider heuristics. Separate the upstream processing error from the authoritative owner/business outcome.

**Bounded next step:** architecture/ownership/reuse decision for `Interaction logical execution continuity`, including exact source contracts, consumers, persistence and job lifecycle; do not implement queue/worker/engine before proving the reuse gate. Test a timeout at `arguments` after selection and demonstrate whether the valid prior selection can be resumed without repeating that LLM stage. Any write replay requires gate review. Production incident stays open until deployed SHA, CRI state and original Portal questions are verified.

`CP1=ACCEPT_WITH_RESIDUAL`; `CP2=ACCEPT`; `CONTINUITY_EXISTING_EQUIVALENT_ECOSYSTEM=TO_INVENTORY`; `CP3=ARCHITECTURE_DECISION_REQUIRED`; `PRODUCTION_DEPLOY=NOT_VERIFIED`; `I04_ACCEPTED=NO`.
