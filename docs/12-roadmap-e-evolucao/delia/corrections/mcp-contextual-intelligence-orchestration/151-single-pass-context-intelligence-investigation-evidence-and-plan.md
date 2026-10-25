# 151 — Single-Pass Context Intelligence Investigation — Evidence & Implementation Plan

**TASK_ID:** `DELIA-CONTEXT-INTELLIGENCE-SINGLE-PASS-CANONICAL-INVESTIGATION-01`
**Date:** 2026-10-25
**Mode:** REANCHOR → FULL DOCUMENTATION REVIEW → END-TO-END CODE INVENTORY → LOCAL RUNTIME CHARACTERIZATION → INDUSTRY BENCHMARK → THREE-WAY GAP ANALYSIS → COMPLETE IMPLEMENTATION PLAN → DOCUMENT → COMMIT → PUSH → ONE FINAL REPORT
**Type:** Read-only investigation. No code, prompt resource, model, infrastructure, schema, routing or deployment change was made.
**Brief:** [150 — single-pass-context-intelligence-investigation-brief](150-single-pass-context-intelligence-investigation-brief.md)
**Baseline:** `d3dfaa2ccaca9347849eda2358803887e859501c` (HEAD = origin/main at investigation time)

---

## 0. Scope statement

This document answers three questions with file:line evidence:

1. **Canonical expectation** — what the authority chain requires (docs 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25, plans 125/129/130/146/147/148, specs 93/96/103/149).
2. **Observed implementation** — what the HEAD code actually does, verified end-to-end `Frontend → API → Application → Orchestrator → ModelInvocationRequest → Adapter → LLM`.
3. **Industry pattern** — how agent platforms solve session history, context engineering, compaction, and memory (Ollama, OpenAI, Anthropic, LangGraph, Microsoft Agent Framework, MCP).

Outputs: factual diagnosis, transport map, per-stage context matrix, three-way comparison, reuse inventory, evidence-backed gap list, security/authority risk analysis, minimal architecture proposal per gap, closed implementation plan, decision register.

---

## 1. Executive factual diagnosis

### 1.1 How much history does the LLM actually receive?

| Layer | Verdict | Evidence |
|---|---|---|
| **Contract** | `ModelInvocationRequest.prior_context: tuple[ConversationContextTurn, ...]` transports chronological prior turns | `delia-api/app/application/model_invocation/contracts.py:29-88` |
| **Origin** | 100% client-side. `buildInteractionContext(turnsRef.current)` builds bounded `USER_INPUT`/`DELIA_RESULT` pairs from turns currently rendered in the MFE. React state only — no localStorage, sessionStorage, indexedDB, or conversation_id anywhere in `plugins/delia/src` | `plugins/delia/src/App.tsx:388-395`; `plugins/delia/src/api/interactionClient.ts:89-108`; grep `localStorage|sessionStorage|indexedDB|conversation_id` → 0 hits |
| **Bounds** | `INTERACTION_CONTEXT_CHAR_BUDGET = 16_384` aggregate, `INTERACTION_INPUT_CHAR_LIMIT = 16_384` per input. Frontend drops oldest complete pairs deterministically; backend re-validates the same aggregate bound | `interactionClient.ts:89-108`; `handle_interactive_turn.py:840-896` |
| **Backend validation** | Alternation `USER_INPUT→DELIA_RESULT`, must start with `USER_INPUT`, non-empty strings, admissible non-`FACT` epistemic classes, aggregate ≤ `MAX_INPUT_CHARS`. **Fail-closed wholesale reject — never server-side truncation** | `handle_interactive_turn.py:840-896`; `interaction_routes.py:467-514` |
| **Adapter wire** | `prior_context` → chronological `{"role":"user"|"assistant","content":...}` messages; current input → `user`; DELPI instruction → `system`. **No tools, no authority fields, no secrets, no CoT** | `openai_compatible_adapter.py` (`_request_payload`) |
| **Proven wire payload** | `TEST_NOT_RUN` — no sanitized live capture performed. Adapter unit tests (`test_adapter_maps_context_to_provider_roles_in_order`, no-context, no-tools) + direct code read prove intended serialization; the exact bytes on the wire are contract-equivalent but not runtime-captured | adapter tests in `delia-api/tests/` |
| **Effective history depth** | Bounded by char budget, not turn count. All pairs that fit in 16 384 chars, newest-first walk keeping complete pairs. On refresh/new-tab/context-loss: **zero turns — total history loss** | `interactionClient.ts`; App.tsx turns = React state |

### 1.2 Session identity, persistence, authorization

| Item | Verdict | Evidence |
|---|---|---|
| Session creation | New `InteractionSession` per request. `session_id` is correlation-only, generated per POST | `handle_interactive_turn.py:315-356` |
| Session persistence | **NONE.** Canonical decision `SESSION_PERSISTENCE=NONE`, `SESSION_SEMANTICS=REQUEST_SCOPED`, `CONTEXT_STORAGE=MFE_MEMORY_ONLY` — approved `ACCEPT_WITH_RESIDUAL` under C3-INTERACTION-CONTINUITY-01 | `docs/12-roadmap-e-evolucao/delia/21-data-and-state-model.md` §8 ledger paragraph |
| History authority | `CONVERSATION_HISTORY_AUTHORITY=NONE` — history is untrusted, non-authoritative, non-memory, non-FACT | doc 21 §8; `contracts.py` |
| AuthN | Bearer middleware per request | `interaction_routes.py` registered middleware |
| AuthZ | `delia.access`/superadmin via Core-resolved `PlatformAccessContext` in the use case. **Prior turns cannot confer permissions** | `handle_interactive_turn.py:315-356` |
| Multi-tab / reconnect | No server history → each tab/refresh starts cold. Queue, draft, turns all React-memory | `App.tsx` (no persistence layer) |

### 1.3 Effective Ollama context window — the critical numeric gap

| Item | Verdict | Evidence |
|---|---|---|
| Configured `num_ctx` | `OLLAMA_NUM_CTX=2048` in `infra/.env` and `infra/.env.prod.example` | `infra/.env` |
| Adapter forwards `num_ctx`? | **NO.** `_request_payload` builds OpenAI-compatible `messages` + `model` + `temperature`/`max_tokens`. No `options.num_ctx`, no `num_ctx` field — OpenAI-compat API may not accept it anyway | `openai_compatible_adapter.py` |
| Effective window | **INCONCLUSIVE pending runtime.** `OLLAMA_NUM_CTX` is a **server-side env var** for Ollama daemon defaults — if the daemon reads it, context = 2048 tokens. But official Ollama docs name `OLLAMA_CONTEXT_LENGTH` (not `OLLAMA_NUM_CTX`) as the env var; `num_ctx` is a Modelfile `PARAMETER` or per-request `options` in the **native** API. Whether `OLLAMA_NUM_CTX` is honored at all is `TO_INVENTORY` against the running daemon | docs.ollama.com/faq; docs.ollama.com/api/chat; github.com/ollama/ollama/issues/4447 |
| Char→token math | 16 384 chars context + up to ~16k chars stage blocks ≈ 8-10k tokens worst case in a single prompt — **4-5× over a 2048 window**. Ollama truncates silently from the left when over `num_ctx` | arithmetic on bounded constants |
| Token accounting | `prompt_tokens`/`completion_tokens` captured post-hoc into `UsageMetadata` when provider returns them. **No pre-call estimate, no budget enforcement, no truncation signal to the user** | `openai_compatible_adapter.py` usage mapping |

---

## 2. Complete context transport map

```
USER types → App.tsx handleSubmit
  │  value ≤ 16 384 chars (INTERACTION_INPUT_CHAR_LIMIT)
  │  context = buildInteractionContext(turnsRef.current)  ← React state, newest-first pair walk
  │  workspaceContext = bounded ambient UI state (untrusted)
  ▼
submitInteractionTurn (interactionClient.ts:89-108)
  │  POST /api/delia/interactions/turns
  │  body: { input?, context[], workspace_context?, confirmation?, command? }
  │  Auth: bearer token
  ▼
interaction_routes.py:467-514  (parse)
  │  context[i] admits only {kind, content, epistemic_class?}
  │  kind ∈ {USER_INPUT, DELIA_RESULT}; unknown keys rejected
  ▼
HandleInteractiveConversationTurn (handle_interactive_turn.py:315-356)
  │  AuthZ: delia.access | superadmin  (Core PlatformAccessContext)
  │  validate input_text ≤ 16 384, validate prior_turns (840-896):
  │    alternation, non-empty, epistemic admissible, FACT rejected,
  │    aggregate ≤ 16 384 → wholesale fail-closed
  │  session = InteractionSession(uuid4())  ← NEW per request
  │  session.record(USER_INPUT)
  ▼
OperationalCapabilityOrchestrator.attempt (orchestration.py:3893+)
  │  ┌─ confirmation path → _attempt_confirmation (prior_turns ignored)
  │  ├─ _admit_conversational_turn     prior_turns=RAW + neutral owner_surfaces
  │  │                                 premise (d3dfaa2cc WP1; semantics live in
  │  │                                 instruction v19, not a static taxonomy)
  │  ├─ surface_inquiry → _surface_inquiry_attempt (deterministic projection, no model)
  │  ├─ prior_turns? → _understand_goal  prior_turns=RAW → _TurnGoal
  │  │      └─ prior_evidence_sufficient? → _prior_continuation_attempt
  │  │            ├─ committed → synthesis prior_turns=() + embedded OBSERVATION excerpt ≤2000c
  │  │            └─ probe     → same; fallthrough on insufficiency
  │  ├─ _select_target
  │  │      ├─ _select_group        prior_turns=() + prior_observation ≤800c in catalog block
  │  │      ├─ _select_capability   prior_turns=() + same observation (cold path)
  │  │      └─ _select_capability_with_goal  prior_turns=RAW (I02-R3B fused proposal)
  │  ├─ _index_probe / _propose_index_probe         prior_turns=RAW
  │  ├─ _propose_index_identifier / _bind_arguments_from_index  prior_turns=RAW
  │  ├─ _build_arguments            prior_turns=RAW + selections contract (spec 146/147)
  │  ├─ _resolve_missing_inputs / _select_resolver  prior_turns=RAW
  │  ├─ _clarification_question     prior_turns=NOT PASSED (intentional, deterministic fallback)
  │  ├─ _corroborate_attempt        comparison prior_turns=NOT PASSED
  │  ├─ _select_prepare_continuation  prior_turns=RAW
  │  ├─ _invoke_selected → owner call (DISCOVERY → CANDIDATE → READ | PREPARE→confirm→ACT)
  │  │      └─ _discover_candidate   folded query from prior_turns ≤4×120c;
  │  │                             _resolve_candidate()
  │  ├─ _select_candidate            prior_turns=RAW
  │  ├─ _propose_candidate_arguments prior_turns=RAW
  │  ├─ _judge_goal_evidence         prior_turns=RAW
  │  ├─ _assess_native_path          prior_turns=RAW
  │  ├─ _select_foreign_capability   prior_turns=RAW
  │  ├─ _invoke_foreign_evidence → _build_arguments  prior_turns=RAW
  │  └─ _synthesize_content          prior_turns=RAW
  ▼
invoke_model (per stage) → ModelInvocationRequest
  │  input_text = current input + stage block (≤ ~16k chars block)
  │  prior_context = prior_turns | () per stage
  │  epistemic_class=HYPOTHESIS; metadata={surface, input_kind, context_turn_count}
  ▼
openai_compatible_adapter → POST /v1/chat/completions
  │  system: DELPI instruction (versioned, per instruction_id)
  │  user|assistant: prior_context chronological (verbatim)
  │  user: current input_text + stage block
  ▼
LLM (Ollama qwen2.5:3b | Kimi-k3/OpenRouter per DELIA_LLM_*)
  │  response → JSON proposal → bounded revalidation → next stage
```

**Loss points (intentional, bounded):**
- `_select_group`/`_select_capability`: full transcript replaced by ≤800-char `prior_observation` (latest `DELIA_RESULT` with `epistemic_class=OBSERVATION`) embedded in the catalog payload — latency decision (Stage 05).
- `_clarification_question`, `_corroborate_attempt`: no prior turns at all.
- `_prior_continuation_attempt` synthesis: `()` + embedded excerpt ≤2000 chars (`MAX_RENDER_CONTENT_CHARS`).
- `_discover_candidate`: prior turns folded into ≤4×120-char discovery query; candidate resolution then runs with `()`.

**Loss points (structural, by design):**
- Page refresh / new tab / new conversation → zero prior turns (MFE-memory-only, canonical).
- Char-budget pair drop on the client — oldest complete pairs dropped first, silently (no marker to the model that history was truncated).

---

## 3. Stage-by-stage context matrix

| # | Stage (orchestration.py) | prior_turns | Goal (_TurnGoal) | Live catalog | Owner evidence | prior_observation | Workspace ctx | Bounded budget |
|---|---|---|---|---|---|---|---|---|
| 1 | `_admit_conversational_turn` (9414) | RAW | — | neutral premise | — | — | ✓ | shared turn deadline |
| 2 | `_understand_goal` (5949) | RAW | produces | — | — | — | ✓ | deadline |
| 3 | `_prior_continuation_attempt` (6122 synth) | `()`+excerpt | ✓ | — | prior OBSERVATION ≤2000c | embedded | — | deadline |
| 4 | `_select_group` | `()` | — | live groups | — | ≤800c | ✓ | deadline |
| 5 | `_select_capability` (cold) | `()` | — | live group caps | — | ≤800c | ✓ | deadline |
| 6 | `_select_capability_with_goal` | RAW | produces | live group caps | — | — | ✓ | deadline |
| 7 | `_propose_index_probe` (9836) | RAW | ✓ | — | — | — | ✓ | deadline |
| 8 | `_bind_arguments_from_index` (9879) | RAW | ✓ | index evidence | — | — | ✓ | deadline |
| 9 | `_propose_index_identifier` (9948) | RAW | ✓ | index evidence | — | — | ✓ | deadline |
| 10 | `_build_arguments` (10015) | RAW | ✓ | cap schema | owner evidence | — | ✓ | deadline |
| 12 | `_resolve_missing_inputs`/`_select_resolver` (5580) | RAW | ✓ | — | — | — | ✓ | deadline |
| 13 | `_clarification_question` (8323) | **NONE** | missing metadata | — | — | — | — | deadline |
| 14 | `_corroborate_attempt` (6583) | **NONE** | — | — | — | — | — | deadline |
| 15 | `_select_prepare_continuation` (6660) | RAW | ✓ | — | — | — | ✓ | deadline |
| 16 | `_invoke_selected` (10195) | — | ✓ | live descriptor | DISCOVERY/READ/PREPARE | — | — | deadline |
| 17 | `_discover_candidate` (10435) | folded ≤480c | ✓ | — | discovery outcome | — | — | deadline |
| 18 | `_select_candidate` (10614) | RAW | ✓ | — | candidate list | — | ✓ | deadline |
| 19 | `_propose_candidate_arguments` (10749) | RAW | ✓ | — | candidate evidence | — | ✓ | deadline |
| 20 | `_invoke_foreign_evidence`→`_build_arguments` (6458) | RAW | ✓ | — | foreign evidence | — | ✓ | deadline |
| 21 | `_select_foreign_capability` (6359) | RAW | ✓ | foreign catalog | — | — | ✓ | deadline |
| 22 | `_assess_native_path` (6270) | RAW | ✓ | — | native outcome | — | ✓ | deadline |
| 23 | `_judge_goal_evidence` (8956) | RAW | ✓ | — | all evidence | — | ✓ | deadline |
| 24 | `_synthesize_content` (8540) | RAW | ✓ | — | selected evidence | prior excerpts ≤12× (1568-1595) | ✓ | deadline |

**Cross-cutting:** one monotonic `TurnDeadline` shared across all stages + provider calls + retries (`turn_budget.py`); `MAX_GOVERNED_ATTEMPTS=2`; `LLM_CALL_MAX_ATTEMPTS=3`; ephemeral `_AttemptCheckpoint` (3431-3450) keyed by stage/invocation fingerprint (3494-3520) — replays completed non-mutating outcomes on retry, **refuses resume after first mutating invoke** (DISCOVERY/READ/ANALYSIS resumable only); checkpoint never persisted, never on wire.

---

## 4. Three-way comparison: canonical × implementation × market

| Dimension | Canonical (docs/rules) | Implemented (HEAD) | Market pattern | Delta |
|---|---|---|---|---|
| Session identity | `InteractionSession` V.O., request-scoped, correlation-only (doc 21 §8, APPROVED) | uuid4 per POST; `session_id` echoes into confirmation binding only | OpenAI `conversation_id`/`previous_response_id`; LangGraph `thread_id`+checkpointer; MS AF `AgentThread` | **Canonical chose ephemeral; market keeps durable threads. Gap = product decision, not defect.** |
| Authenticated history loading | `SESSION_PERSISTENCE=NONE`, `SESSION_STORAGE=DEFERRED`, `SESSION_RETENTION_POLICY=TO_INVENTORY` (approved residual) | Zero backend history. History = client POST body | All major platforms persist thread state server-side, load by authenticated identity | **GAP G1 — deferred by canon, blocks cross-device/resume** |
| Message order | Chronological pairs USER_INPUT→DELIA_RESULT | Enforced alternation, newest-first client walk | Same (chronological append) | Parity |
| Roles | 2 kinds only, non-FACT | `user`/`assistant` map 1:1 | user/assistant/system/tool | DELIA has no `tool` role — owner outcomes travel as `DELIA_RESULT` assistant text. Simpler, lossy for tool-trace UX |
| Serialization | Provider-neutral contract | OpenAI-compat messages; no tools/authority/CoT | OpenAI messages; Anthropic content blocks w/ tool_use/tool_result | Parity for current provider set |
| Conversation boundary | None server-side; UI = one live conversation | `turns` React state; queue; draft recovery | Thread/conversation object w/ lifecycle | G1 |
| Summary/compaction | Not specified | **None.** Char-budget pair drop only | OpenAI auto-compaction; LangGraph summarization nodes; MS AF `ChatReducer`+`HistoryProvider`; Anthropic context editing | **GAP G2 — no summarization, no omission marker to model** |
| Relevant excerpt selection | Bounded excerpts allowed | `prior_observation` ≤800c (latest OBSERVATION only); `_prior_result_excerpts` ≤12; folded discovery ≤4×120c | Embedding/lexical retrieval over full history | Partial — recency+class-gated, not relevance-ranked |
| Schema/source projection | Live catalog per request, never cached | `_groups()` live fetch each attempt; deterministic revalidation of every proposal | Tool manifests per call; dynamic tool loading | Parity — actually stronger (always fresh) |
| Stage context | Bounded per stage (doc 96, 103) | 23 stages mapped; 2 get NONE, 4 get reduced | Agent loops pass full state; LangGraph checkpointer threads everything | DELIA deliberately leaner — correct for 3B model, risky for referential chains at selection (G5) |
| Goal persistence | `_TurnGoal` per turn (LOOP-03R1) | Computed once/turn, threaded to ~15 stages; **not persisted across turns** — re-derived from transcript each turn | LangGraph typed state across turns; MS AF thread state | **GAP G6 — no typed carried-forward goal; continuation re-interprets prose** |
| Business subject | `business_subject`, `scope_constraints`, `answer_requirements`, `contract_subject` in `_TurnGoal` | Bounded, validated, degrades to neutral | Similar entity tracking in agent state | Parity intra-turn |
| Failed-attempt feedback | `relevance_feedback` bounded (MAX_MISMATCH_HINT_CHARS=240); no identical re-query | Fed back into `_build_arguments`/`_recover_relevance` | Tool-error echo + retry loops | Parity |
| Live capability catalog | Provider-neutral groups, DISCOVERY→CANDIDATE→READ | Fresh per request; proposals revalidated | MCP tools/list per session | Parity+ (freshness) |
| Evidence lineage | Owner outcomes authoritative; `prior_turn_evidence_only` marker; epistemic classes fail-closed | Enforced — `FACT` rejected, OBSERVATION-only continuation gate | Provenance varies; few enforce epistemic classes | DELIA stronger |
| Context budget & tokens | Char bounds (16 384 ×2) | **No token budget, no num_ctx, no pre-call estimate** | OpenAI `max_prompt_tokens`, auto-truncate/summarize; LangGraph `trim_messages` by tokens | **GAP G3/G4 — char≠token; silent provider truncation risk on Ollama** |
| Timeout/resume/cancel | Monotonic deadline; checkpoint resume non-mutating | Implemented (3431-3520); cancel probe; `MAX_GOVERNED_ATTEMPTS=2` | LangGraph interrupt/resume+checkpointer (durable); Temporal durable exec | DELIA ephemeral-only resume — parity intra-request, gap cross-request |
| Cross-model parity | Provider-neutral port | Single adapter `OPENAI_COMPATIBLE`; `DELIA_LLM_*` env swap (Kimi proved; A/B eval doc 147-ledger) | Any OpenAI-compat endpoint | Parity for OpenAI-shape; Anthropic-native needs 2nd adapter |
| Provider neutrality | Bounded context owns orchestration; owners own vocabulary/evidence | Enforced — no provider-specific wire fields | MCP = one provider family | Parity |
| Privacy | No secrets/CoT in prompt; bounded content | `guard_invocation_payload`; metadata minimal | Varies | Parity+ |
| Prompt injection | Prior context untrusted, non-authoritative | Contract-level marking; **but wire roles look identical to real history — model cannot distinguish injected transcript** | Delimiters/tagging, instruction hierarchy | **GAP G10 — residual, bounded by deterministic revalidation** |
| AuthZ | Prior turns never confer authority; Core-resolved context | Enforced in use case + per-owner bearer delegation | Standard | Parity+ |
| Safe re-query | No identical re-execution; resolver same-owner; budget-gated | Implemented | Dedup in agent loops | Parity |

---

## 5. Reusable mechanism inventory (EXISTING_EQUIVALENT=YES)

| Mechanism | Location | Reusable for |
|---|---|---|
| `ConversationContextTurn` + validation chain | `contracts.py`; `handle_interactive_turn.py:840-896` | Any new context channel — same shape/validation |
| `buildInteractionContext` pair-walk + budget | `interactionClient.ts:89-108` | Client-side compaction/selection upgrade in place |
| `prior_observation` bounded excerpt | `orchestration.py` (~800c, OBSERVATION-gated) | Pattern for relevance selection at other stages |
| `_prior_result_excerpts` | `orchestration.py:1568-1595` (≤12 bounded excerpts) | Selection-only synthesis reuse |
| `_context_folded_discovery_query` | `orchestration.py` (≤4×120c) | Reference resolution folding |
| `_TurnGoal` typed goal | `orchestration.py:5820-5987` | Extend with carried-forward fields if session persists |
| `_AttemptCheckpoint` + fingerprints | `orchestration.py:3431-3520` | Resume primitives already keyed deterministically |
| `TurnDeadline` + cancel probe | `turn_budget.py` | Shared budget across any new stage |
| `UsageMetadata` capture | `openai_compatible_adapter.py` | Extend for budget enforcement / forecasting |
| Epistemic admissibility fail-closed | `handle_interactive_turn.py`; `model.py` | Any new turn kind inherits validation |
| Selections contract (146/147) | `argument_validation.py` | Evidence-bound args already governed |
| Neutral `owner_surfaces` admission premise | `orchestration.py:9459` | **RESOLVED at HEAD** — d3dfaa2cc WP1 removed the static taxonomy; semantic rule lives in instruction v19 (was A1 `TO_INVENTORY` in plan 148) |
| `relevance_recovery` bounded re-invoke | `orchestration.py` (~9246) | Now fails closed on provider-layer exceptions (d3dfaa2cc WP3); `_TurnCancelled`/`_StageDeadlineExceeded` still propagate |

---

## 6. Evidence-backed gap list

| ID | Gap | Evidence | Severity |
|---|---|---|---|
| **G1** | No server-side conversation persistence or conversation identity. History is 100% MFE memory; refresh/tab-switch = total loss; no resume across devices; no authenticated history load possible | `CONTEXT_STORAGE=MFE_MEMORY_ONLY` (doc 21 §8 approved); grep = no storage layer; `session_id` per-request | **High** (product capability), canonical-deferred |
| **G2** | No compaction/summarization/relevance selection. Only deterministic pair-windowing; oldest dropped silently with no truncation marker to model | `buildInteractionContext` drops pairs; nothing signals omission | **Medium** — long conversations lose early context invisibly |
| **G3** | `OLLAMA_NUM_CTX` env efficacy unverified; adapter never forwards `num_ctx`; OpenAI-compat API may not accept it | `infra/.env`; adapter payload lacks options; official docs name `OLLAMA_CONTEXT_LENGTH` | **High** on local Ollama — likely running 2048 or model-default 4096 while prompts reach 8-10k tokens |
| **G4** | No token budget/pre-call estimate. Char bounds (16k+16k) ≠ token bounds; per-call worst case ≈32k chars ≈8-10k tokens | constants; no `trim`/estimate call; usage post-hoc only | **Medium-High** — silent left-truncation → wrong model output interpreted as capability failure |
| **G5** | Selection stages get `()` or ≤800c observation only. Referential follow-ups ("o segundo", "outros três desses") can misselect when prior OBSERVATION absent or insufficient; `_discover_candidate` resolves with `()` while `_invoke_selected` resolves with RAW — inconsistent | orchestration.py:4083-4085 comment; `_discover_candidate` (10435) vs `_invoke_selected` (10195) | **Medium** — mitigated by `_select_capability_with_goal`+goal, residual for non-OBSERVATION priors |
| **G6** | No typed carried-forward goal/conversation state. `_TurnGoal` re-derived per turn from prose transcript | `_understand_goal` per-request; no persistence | **Medium** — works but fragile; every stage re-pays interpretation cost |
| **G10** | Injected prior turns indistinguishable from real ones on the wire (same roles). Bounded by deterministic revalidation + untrusted instructions | adapter maps verbatim; no delimiter/tagging | **Low-Medium** — worst case = bad proposal revalidated away; AuthZ unaffected |
| **G11** | `epistemic_class` validated at ingress then dropped at wire — model sees plain role/content. Correct today (prevents self-labeling); noted as designed | adapter payload | Informational — correct |
| **G12** | `context` sent on confirmation turns is validated then ignored — harmless but wasted validation surface | App.tsx:391; `_attempt_confirmation` ignores prior_turns | Informational |

---

## 7. Security / authority risk analysis

| Vector | Current control | Residual |
|---|---|---|
| History forgery (client invents transcript) | Marked untrusted; non-authoritative; `FACT` rejected; all proposals revalidated against live surface; AuthZ from Core context only | Model may act on fabricated "prior" text → wrong capability picked; bounded — deterministic gates catch business falsity; no authority escalation possible |
| Prompt injection inside `DELIA_RESULT`/`USER_INPUT` history | Contract marks untrusted; instruction resources state prior text is never authority (orchestration_instructions.delpi.json) | Wire roles indistinguishable (G10); no delimiters. Bounded impact — worst = selection misdirection, still revalidated |
| Cross-user leakage | No persistence → no cross-session leak possible. Request-scoped everything | None today; becomes critical the moment G1 is implemented — user-scoped isolation + clear-on-switch required (doc 21:1888-1895) |
| Secrets in context | `guard_invocation_payload`; bounded metadata (3 keys); workspace context untrusted | Client could paste secrets into history — provider-side exposure same as any user input; acceptable |
| AuthZ via context | Impossible — `PlatformAccessContext` from bearer/Core only; pending-write digest binding; confirmation digests | None — architecture is sound |
| Confirmation replay | `proposal_digest`+`preview_fingerprint`+`session_id` bound; pending store; mutate-then-no-resume | Session_id is per-request → pending store keyed accordingly; digest binding is the real control — sound |
| Provider sees full transcript | Yes — verbatim prior turns go to whichever model is configured (Ollama local or OpenRouter/Kimi external) | Data-residency consideration when external provider active: prior DELPI evidence text leaves perimeter. **Not a code defect — a deployment/governance flag for the decision register** |

---

## 8. Minimal architecture proposals (per gap)

| Gap | Proposal | Owner | New contract? |
|---|---|---|---|
| G1 | **Session-owned history**: `ConversationSession` aggregate in delia-api (new bounded persistence — table or document), `conversation_id` on turn request/response, `GET /conversations/{id}/turns` for authenticated reload. Client sends `conversation_id` instead of full transcript; backend loads + validates its own history → **authentic history** | application/interaction + interfaces/http + infra persistence | YES — new repository port + route. Canon: `SESSION_PERSISTENCE=NONE` must be re-decided (doc 21 §8 residual `TO_INVENTORY`) |
| G2 | **Budgeted context assembly**: keep pair-window; add (a) truncation marker turn ("older turns omitted") — zero model cost, honest signal; (b) optional summarization stage when history exceeds budget — reuse `_propose` with new instruction_id; output = bounded `DELIA_RESULT` summary turn prepended | interactionClient + orchestration | Minor — marker as synthetic `DELIA_RESULT` or new optional context field |
| G3 | **Context-window declaration**: per-adapter `context_window_tokens` in config/env (`DELIA_LLM_CONTEXT_TOKENS`); adapter serializes `options.num_ctx` for native-Ollama path or documents the OpenAI-compat limitation; verify `OLLAMA_CONTEXT_LENGTH` vs `OLLAMA_NUM_CTX` on the running daemon | infrastructure/model_invocation + ops | Minor — config surface |
| G4 | **Token budget enforcement**: char→token estimator (conservative 1.8 tok/char PT-BR, or tiktoken-equivalent) in use-case before dispatch; enforce `context + input + stage_block ≤ budget × window`; fail-closed `CONTEXT_TOO_LARGE` with honest error instead of silent provider truncation | application/model_invocation + use case | YES — new error code + budget contract |
| G5 | **Uniform reduced-context contract**: one `_stage_context(input, prior_turns, goal)` helper producing the stage-appropriate slice (full RAW vs folded observation) — removes the `_discover_candidate` inconsistency and centralizes the "what does selection see" decision | orchestration | NO — internal refactor |
| G6 | **Carried-forward goal**: once G1 lands, persist last validated `_TurnGoal` on the conversation; inject as typed prior-goal hint into `_understand_goal` block instead of re-deriving from prose | orchestration + persistence | Minor — block payload extension |
| G10 | **Delimited untrusted transcript**: wrap serialized prior turns in explicit delimiters inside the user message (single `user` message containing marked-up history) OR keep roles but prepend instruction tag in stage block. Tradeoff: delimiter approach loses native role semantics; tag approach is zero-API-change | adapter + instruction resource | Minor — serialization format |
| — | **Provider-residency flag**: when `DELIA_LLM_PROVIDER` is external, surface a governed banner/flag that prior-turn text leaves the perimeter | ops + UI note | Doc/config only |

---

## 9. Closed implementation plan (work packages)

Ordering per brief: (1) session context & serialization → (2) goal/evidence per stage → (3) selection/compaction/budgets → (4) security → (5) generalization & measurement.

### WP-A — Token budget & context-window declaration (G3+G4) — **FOUNDATION, DO FIRST**

| Field | Value |
|---|---|
| Files | `delia-api/app/infrastructure/model_invocation/openai_compatible_adapter.py`, `delia-api/app/application/model_invocation/contracts.py`, `delia-api/app/application/interaction/handle_interactive_turn.py`, `delia-api/config.py`/settings, `infra/.env.prod.example`, tests |
| Contract | `ModelAdapter.context_window_tokens` (declared); `CONTEXT_TOO_LARGE` error; pre-call estimate `estimated_prompt_tokens(input, prior, block) ≤ declared_window` |
| Diff est. | ~200 lines + tests |
| RED tests | adapter declares window; use case rejects over-budget context/input with `CONTEXT_TOO_LARGE`; estimate uses conservative factor; usage still mapped post-hoc |
| Criteria | PASS = deterministic reject before dispatch when estimate>window; no silent truncation; Ollama `num_ctx` resolution verified (env name confirmed or corrected) |
| Deps | None; runtime verification of `OLLAMA_CONTEXT_LENGTH` on daemon |
| Risks | Char→token estimate too conservative → false rejects → tune factor; OpenAI-compat `num_ctx` unsupported → daemon-side config only |
| Release | Backend deploy; zero UX change until budget trips |
| NEXT | WP-B |

### WP-B — Session-owned conversation persistence (G1) — **REQUIRES CANON DECISION**

| Field | Value |
|---|---|
| Files | `delia-api/app/application/interaction/` (new `conversation_history.py` use case + port), `delia-api/app/interfaces/http/interaction_routes.py` (+`conversation_id`, `GET` route), `delia-api/app/infrastructure/persistence/` (repo impl), `plugins/delia/src/api/interactionClient.ts` + `App.tsx` (send id, hydrate on load), `plugins/delia/src/identity/` |
| Contract | `ConversationSession {id, owner_user_id, turns[InteractionTurn], created_at}`; turn POST accepts `conversation_id?`; response echoes it; GET requires `delia.access` + `owner==caller` |
| Diff est. | ~400 backend + ~150 frontend + migration |
| RED tests | create-on-first-turn returns id; subsequent turns append server-side; reload returns chronological turns; foreign-user GET → 403; cleared-on-logout path; FACT still rejected |
| Criteria | PASS = refresh preserves conversation; new-tab load; no client transcript needed for history (client may still send none); AuthZ isolation proven |
| Deps | **CANON DECISION**: reverse/extend `SESSION_PERSISTENCE=NONE` (doc 21 §8); persistence owner sign-off; retention policy (`SESSION_RETENTION_POLICY=TO_INVENTORY` → must be decided) |
| Risks | Largest WP — new schema; doc 21 forbids Chat tables — must be DELIA-owned conversation store; R7/Plan-148 concurrency → sequence after its WPs or isolate files |
| Release | Feature-flagged; MFE hydrates progressively |
| NEXT | WP-C, WP-D |

### WP-C — Compaction marker + summarization hook (G2)

| Field | Value |
|---|---|
| Files | `plugins/delia/src/api/interactionClient.ts` (marker turn when pairs dropped), `delia-api/app/application/capability_provision/orchestration.py` (optional summarize stage), `delia-api/config/orchestration_instructions.delpi.json` (new instruction_id — instruction-resource change requires own gate) |
| Contract | Marker: synthetic `DELIA_RESULT` turn `content="[contexto anterior omitido]"` OR wire-level `context_truncated: true` flag; summarization: bounded `_propose` producing summary ≤ N chars when `est_tokens > soft_budget` |
| Diff est. | ~80 frontend + ~120 backend |
| RED tests | marker emitted iff pairs dropped; summarize stage produces ≤budget turn; absent → marker still honest; never fabricates content |
| Criteria | PASS = model sees explicit omission signal; summary stage is optional (budget-gated), never hides evidence |
| Deps | WP-A (needs token estimate for soft_budget); instruction-resource change gated separately |
| NEXT | WP-D |

### WP-D — Stage-context uniformity + carried goal (G5+G6)

| Field | Value |
|---|---|
| Files | `delia-api/app/application/capability_provision/orchestration.py` |
| Contract | `_stage_context()` helper: RAW transcript for interpretive stages; folded observation for latency-critical selection; `()` only where context is provably useless (clarify/corroborate). `_TurnGoal` optionally seeded from persisted prior goal (WP-B dep) |
| Diff est. | ~150 lines refactor + tests |
| RED tests | `_discover_candidate` receives same context class as `_invoke_selected`; referential follow-up selects correctly with OBSERVATION-less priors; no stage loses context it previously had |
| Criteria | PASS = consistent context matrix; doc-96-style stage probe confirms referential selection |
| Deps | WP-A (budget math); WP-B for carried goal (optional — degrade to transcript re-derivation) |
| Risks | Touches orchestration core — R7/Plan-148 file. MUST sequence after 148 WPs or coordinate file-level |
| NEXT | WP-E |

### WP-E — Untrusted-transcript delimitation + residency flag (G10)

| Field | Value |
|---|---|
| Files | `openai_compatible_adapter.py` (history delimiter), `orchestration_instructions.delpi.json` (reinforce), config/docs for residency |
| Contract | Prior turns serialized inside a single delimited user message `<<<PRIOR_CONVERSATION untrusted>>>...<<<END>>>` (opt-in via adapter flag) OR per-turn tags; residency flag `DELIA_LLM_EXTERNAL=true` surfaced to UI |
| Diff est. | ~60 lines + instruction line |
| RED tests | injected "assistant" turn claiming authority still revalidated; delimiter present; role semantics preserved |
| Criteria | PASS = injection surface reduced without breaking chronology semantics |
| Deps | None hard; prefer after WP-A |
| NEXT | WP-F |

### WP-F — Measurement & generalization (cross-cutting closeout)

| Field | Value |
|---|---|
| Files | tests + `activity`/observability events; adapter-port conformance |
| Contract | `context_tokens_est` in UsageMetadata-adjacent observability; adapter conformance test: any `ModelInvocationPort` impl serializes same context semantics |
| Diff est. | ~100 lines |
| RED tests | observability emits estimate; second-adapter contract test passes (mock Anthropic-shape) |
| Criteria | PASS = token accounting visible per stage; provider swap requires only new adapter behind same port |
| NEXT | Decision register → coordination |

---

## 10. Decision register

**Coordination can approve directly (no canon change):**
- D1: WP-A token budget + window declaration (extends existing contract, fail-closed).
- D2: WP-C truncation marker (honest signal, zero authority change).
- D3: WP-D stage-context uniformity (internal refactor, same contracts).
- D4: WP-E delimiter + residency flag (serialization detail).
- D5: WP-F measurement (observability extension).

**Requires canonical/architecture authority:**
- D6: WP-B session persistence — must re-decide `SESSION_PERSISTENCE=NONE` + `SESSION_STORAGE=DEFERRED` + `SESSION_RETENTION_POLICY=TO_INVENTORY` (doc 21 §8 residual). New DELIA-owned schema needs data-persistence owner + security owner sign-off (user isolation, clear-on-switch rules doc 21:1888-1895).
- D7: Summarization instruction resource — new `instruction_id` needs the instruction-versioning gate (same process that versioned v16-v18).
- D8: External-provider data residency — governance decision on whether prior DELPI evidence text may leave perimeter when `DELIA_LLM_PROVIDER` is external.

**Inadmissible (do not propose):**
- History as authority / memory / FACT promotion.
- Any context path bypassing Core-resolved AuthZ.
- New planner/engine/registry/provider — everything above EXTENDs existing bounded mechanisms.
- Touching `orchestration.py` or `argument_validation.py` before R7/Plan-148 coordination (files under concurrent remediation).

**Already implemented (do not re-do):**
- Prior-turn transport contract + validation + fail-closed bounds.
- Per-stage context routing with intentional reductions.
- Checkpoint resume for non-mutating work; monotonic deadline.
- Epistemic admissibility + untrusted-history marking.
- Live-catalog freshness + deterministic proposal revalidation.
- Evidence-bound arguments (specs 146/147) and goal recovery (147).
- `prior_observation`, excerpts, folded-query mechanisms (§5).

**Explicit TEST_NOT_RUN / TO_INVENTORY carried forward:**
- Sanitized live wire capture of adapter payload (`TEST_NOT_RUN` — env not probed; adapter tests are the evidence).
- `OLLAMA_NUM_CTX` vs `OLLAMA_CONTEXT_LENGTH` efficacy on the running daemon (`TO_INVENTORY` — WP-A first action).
- Real cross-model wire parity beyond OpenAI-compat (`TEST_NOT_RUN` — single adapter exists).

---

## 11. Conclusion

DÉLIA's context handling is **architecturally disciplined and bounded by design**: every turn is request-scoped, every context channel is validated fail-closed, authority never flows through history, and stage-level reductions are intentional and documented (doc 96). The real gaps are **not** safety defects — they are **capability ceilings**: no persistence (G1, canon-deferred), no token-awareness (G3/G4 — the most urgent, because char-bounded prompts can silently overflow a 2048-token Ollama window), no compaction (G2), and no typed cross-turn goal (G6).

The minimal path is WP-A first (declare the real window, enforce budgets honestly — small diff, highest information value), then the canonical decision on WP-B (persistence is the only item needing authority reversal), then WP-C/D/E/F as bounded extensions of mechanisms that already exist (§5).

**Next interaction = architectural decision on D1-D8 + implementation authorization. No further inventory is needed.**


## 12. Independent coordination review — 2026-10-25

**REVIEW_VERDICT=ACCEPT_WITH_RESIDUAL for single-pass INVENTORY, NOT implementation approval.** Read-only document 151 and ledger at `e3055a0565` inspected independently. Runtime wire capture and Ollama effective context-window remain `TEST_NOT_RUN/TO_INVENTORY`; claims about actual prompt truncation are risks, not proven production symptoms. `SESSION_PERSISTENCE=NONE` is canonical and not open for implicit reversal.

**Decision D1 / WP-A: APPROVE_DIRECTION_WITH_CONTRACT_REVIEW.** First measure effective Ollama daemon/context window using authorized local, read-only probe; confirm environment name and runtime behavior; then compare actual assembled request size by stage and measured input tokens. Avoid an unconditional `CONTEXT_TOO_LARGE` fail-closed response that degrades users when the current history can be reduced safely within existing contracts. Prefer bounded, deterministic preservation order and stage-specific budgets as a proposal, with explicit testable no-silent-truncation guarantee. Proposed `ModelAdapter.context_window_tokens` is a *new contract property* and must pass abstraction/owner/compatibility gate before implementation; estimate is not true tokens. No new generic context engine.

**Decision D2 / WP-C: CONDITIONAL.** A synthetic `DELIA_RESULT` containing `[contexto anterior omitido]` could violate turn-pair semantics, be misinterpreted as assistant evidence, and lack provenance. Prefer an explicit typed non-authoritative omission indicator **only if supported by existing wire contract**, else submit smallest contract amendment before writing. Summarization instruction_id requires separate authority/version gate; do not autoadd LLM call or treat summary as fact.

**Decision D3 / WP-D: APPROVE_CHARACTERIZATION, IMPLEMENTATION_CONDITIONED ON WP-A AND HEAD.** Red/green prove context preservation, budgets, role semantics and not adding latency to 23 stages; `_stage_context()` helper is not approved merely because convenient. Reuse present `prior_turns`, `_TurnGoal`, prior_observation, evidence/projection; avoid a second state machine. Current goal re-derivation is bounded approved behavior, not necessarily defect.

**Decision D4 / WP-E: CONTRACT_REVIEW_REQUIRED.** Flattening prior user/assistant messages into one delimited user text loses role semantics and can strengthen prompt injection by conflation. Preserve typed roles with adapter/provider mapping; identify actual exploit before inventing delimitation layer. Residency flag and outbound prior context to external providers require governance/privacy decision, not just UI banner. No external-model evaluation.

**Decision D5 / WP-F: APPROVE_DIRECTION, REUSE_EXISTING OBSERVABILITY.** Stage-level context bytes, estimated tokens clearly labeled, actual usage if provider available, omission/truncation reasons and provider context ceiling; protect secrets/PII. No new telemetry system or fake measured token values.

**Decision D6 / WP-B: NOT AUTHORIZED.** Document 21 §8 explicitly freezes request-scoped session and MFE-memory-only; backend conversation DB, conversation_id, migrations, GET, retention and new ports are out of scope without canonical reversal, owner, retention and privacy authority. Do not piggyback persistence on WP-A/C/D.

**Overall:** Investigative coverage accepted with residuals. One bounded implementation task may be approved first: `WP-A0 RUNTIME CONTEXT WINDOW & PRE-FLIGHT SIZE CHARACTERIZATION` (read-only local probe and trace, followed by decision on WP-A contract), optionally WP-F measurements that reuse the current ledger. All other WPs remain design gated. Local model success still not guaranteed after context fixes; evaluate against locked baseline. No deploy from investigation alone.


## 13. Implementation evidence — WP-A + WP-F (2026-10-25, task `DELIA-C3-CONTEXT-WINDOW-BUDGET-OBSERVABILITY-FULL-IMPLEMENTATION-01`)

First approved Context Intelligence implementation, executed after the §12 review: WP-A0 runtime characterization → contract gate → RED → minimal implementation → GREEN → local-model evaluation → full regression. No new engine, planner, memory, registry, provider, or session contract; every mechanism EXTENDs an existing owner.

### 13.1 WP-A0 — effective runtime context window (measured, not inferred)

| dimension | value | evidence method |
|---|---|---|
| model loaded | `delia-json:latest` (FROM qwen2.5:3b blob + custom template) | `ollama show --modelfile`, `/api/show` |
| parameter size / quantization | 3.1B / Q4_K_M | `/api/ps` details |
| declared model context | 32768 (`qwen2.context_length`) | `/api/show` model_info |
| daemon default runner ctx | **4096** | `/api/ps` `context_length` after plain load |
| effective window (pre-fix) | **4096** | empirical: 900/1100-word prompts ⇒ `prompt_eval_count` 3532 OK; ~4300-token prompt ⇒ **2050** — truncation keeps ~ctx/2, not ctx |
| truncation destructiveness | system instruction destroyed | over-window request with `system: reply ZZTOP` ⇒ `prompt_tokens=2050`, generic prose reply (directive lost) |
| `num_ctx` via `/v1` OpenAI-compat | **ignored** (top-level and `options.num_ctx`) | identical 2050 readings |
| `num_ctx` via native `/api/*` | **honored** | `options.num_ctx=8192` ⇒ runner reloads at 8192, `prompt_eval_count=4098` for ~11.7k-token input |
| daemon env | `OLLAMA_NUM_CTX`/`OLLAMA_CONTEXT_LENGTH` **absent** — repo `.env` values never reach the ollama service env block | `docker exec delpi-ollama env` |

**Runtime fix applied to the eval daemon (sanctioned local config):** `PARAMETER num_ctx 8192` baked into `delia-json` via `ollama create` — `/api/ps` now reports `context_length=8192`, `/v1` accepts a 4432-token prompt verbatim, VRAM 2.4GB. The defect was never "the model cannot" — it was *silent halving of over-window prompts*, which destroyed the JSON-only system directive and produced `invalid_structured_output` on the largest stages.

### 13.2 WP-A — contract gate and implementation

```
EXISTING_EQUIVALENT=YES (bounded request contract, adapter port, ledger, usage mapping)
REUSE_DECISION=EXTEND
OWNER=app/application/model_invocation (request/result contracts, use-case boundary)
CONSUMERS=InvokeModel (all three call sites), orchestration._propose, direct-answer invoke
CANONICAL_CONTRACT=ModelInvocationRequest/Result, ModelInvocationPort, ConversationContextTurn
```

Contract additions (minimal, additive-only):

- `ModelInvocationPort.context_window_tokens: int | None` — adapter-declared **effective** input window (runtime-honored value, never nominal model capacity). `None` = unknown → enforcement OFF rather than guessing.
- `ContextBudgetObservation` (contracts.py) — window, input_chars, estimated_input_tokens, generation_reserve_tokens, prior_turns_included/omitted, reduction_reason, budget_status (`within_budget|reduced|rejected`). Carried on `ModelInvocationResult` and on `ModelInvocationError` for rejects.
- `context_budget.py` — pre-call policy at the use-case boundary: estimate `ceil(chars/2.5) + ADAPTER_OVERHEAD(260) + generation_reserve`; reduce **only untrusted prior history**, oldest first in complete USER_INPUT/DELIA_RESULT pairs (alternation invariant preserved, verified); instruction/schema/current input are never touched; mandatory overflow → `ModelInvocationError(CONTEXT_TOO_LARGE)` **before dispatch**, mapped to the interaction-level `CONTEXT_TOO_LARGE` (HTTP 400) — a typed failure, never a fabricated answer.
- `DELIA_LLM_CONTEXT_TOKENS` — settings → adapter ctor → port property. Env passthrough added to both compose files + env examples (dev/prod). Provider-specific mechanics stay in infra config; Domain/Application see only an int.
- Not retryable (`CONTEXT_TOO_LARGE` is not a recoverable code) — deterministic reject.

### 13.3 WP-F — observability (reuses `ModelCallLedger`, no new telemetry)

`ModelCallObservation` + projection now carry per stage: `error_code`, `lineage_version` (instruction lineage), `context_window_tokens`, `input_chars`, `estimated_input_tokens` (labeled estimate), `generation_reserve_tokens`, `prior_turns_included`, `prior_turns_omitted`, `context_reduction_reason`, `context_budget_status` — alongside the already-reported `input_tokens`/`output_tokens` (provider actuals only, never fabricated) and `duration_ms`. `record_error` gained `error_code`/`context_budget` params; both call sites (`_propose`, direct-answer `_invoke`) pass them.

Live wire evidence (real Ollama + real specialists): stage rows show est ≈ 1.4–2.0× actual (conservative over-estimate by design); `long_history` turn with 14.5k chars of prior context ⇒ admission/turn_goal `reduced`, `prior_turns_omitted=2`, `in=6`, `prior_turns_omitted_for_window`; stages that do not route prior context show `in=0/om=0`.

### 13.4 Assembled prompt sizes by stage (measured on the live chain)

| stage | input_chars | est tokens | actual prompt tokens |
|---|---|---|---|
| interaction_admission | ~4.8k | ~2.2k | ~1.1k |
| turn_goal (with 14.5k history) | ~18k | ~6.9k | ~3.5k |
| select_group | ~13.3k | ~5.6k | ~3.2k |
| select_capability | ~5.7k | ~2.5k | ~1.4k |
| native_assessment | ~3.6k | ~1.7k | ~0.9k |
| foreign_selection | ~7.5k | ~3.3k | ~1.9k |
| index_probe | ~2.2k | ~1.1k | ~0.5k |
| arguments | ~9–17k | ~3.7–6.7k | 1.8–4.7k |
| candidate_arguments | ~3k | ~1.3k | ~0.6k |

Largest observed actual prompt: **4670 tokens** (`arguments`) — exceeds the pre-fix effective window (4096); it is exactly the class of prompt that was being halved to ~2050. Under the fixed window all stages report `within_budget` or `reduced`, zero truncation.

### 13.5 Verification and regression

- RED→GREEN: `tests/test_context_budget.py` (9 tests) — within/reduce/reject, pair-boundary preservation, mandatory overflow → `CONTEXT_TOO_LARGE` before dispatch (spy proves zero port calls), unknown window → no enforcement, ledger projection fields, retry idempotence, odd-first-turn defensive drop.
- Focused: context_budget + model_invocation + real adapter + observability + interaction/orchestration suites — green; one pre-existing env failure (`http_timeout_maps_to_504`) unchanged.
- Full backend: **2 failed / 2316 passed** — only the two known environmental failures (`g4` fixture, `http_timeout_maps_to_504`); no new failures.
- Architecture gates: `audit_architecture_phase3`, `audit_platform_guardrails`, `audit_backend_boundaries` — 0 findings. Diff scan: no provider names, no business strings, no secrets in app changes.

### 13.6 Local-model evaluation (authorized local model only)

10-scenario HTTP matrix on the live chain (`DELIA_LLM_CONTEXT_TOKENS=8192`, `delia-json` num_ctx 8192, GPU): **zero `invalid_structured_output`, zero truncation events, zero fabricated content**. `three_records` and `o2` completed the full 10-stage chain GROUNDED (honest empty-collection answer — argument fidelity, not context, is the residual), `long_history` reduced+completed, `subject_switch` completed, `write_ineligible` → surface listing (zero ACT), `insufficient`/`pino`/`documental`/`direct_read` honest NON_GROUNDED, `vista_question` → live surface listing. The three-real-records business outcome remains gated by 3B per-stage argument fidelity — **context loss is no longer the blocker**; no outcome improvement is claimed beyond this.

### 13.7 Remaining residuals / next WP

- `DELIA_LLM_CONTEXT_TOKENS` must be materialized per deployment (dev .env / prod .env); without it enforcement is OFF by design (no false rejects on an unmeasured bound).
- Server-side default window remains a deployment concern: `OLLAMA_CONTEXT_LENGTH` passthrough exists in compose; baking `num_ctx` per model (as done in eval) is the per-model alternative — whichever production adopts must be recorded.
- Omission is silent toward the model but **explicit in observability** (turn counts + reason). No synthetic marker turn was added — D2 remains conditional on a typed contract.
- Still excluded: WP-B persistence (canon-frozen), WP-C summarization, WP-D mass refactor, WP-E flattening, model switch.


## 14. Independent review — WP-A/WP-F a1f6c57236 (2026-10-25)

**VERDICT=ACCEPT_WITH_RESIDUAL (implementation foundation), NOT RELEASE ACCEPT.** GitHub diff and active HEAD `a1f6c57236e64171920df31e5daa60010bbe603d` reviewed statically; no independent local Docker/Ollama/pytest re-execution. Executor evidence: 9/9 WP tests, backend 2316 PASS / 2 FAIL env, 10-scenario eval (zero reported ISO/truncation and false positives), three real records **NOT PROVEN**. `DEPLOY=BLOCKED`.

**Verified in code:** `InvokeModel` central budget; reduce untrusted `prior_context` oldest complete pairs only; typed `context_too_large` before dispatch when mandatory estimate exceeds declared window; optional `ModelInvocationPort.context_window_tokens`, additive `ContextBudgetObservation`, projection into existing call ledger; provider-specific mechanics outside Domain/Application; no session persistence. Measured daemon 4096→8192 and Ollama Modelfile change are executor-reported **EVAL ENV ONLY**, not GitHub-tracked production runtime change.

**R1 — estimation is not hard no-truncation guarantee:** `CHARS_PER_TOKEN_ESTIMATE=2.5`, `ADAPTER_OVERHEAD_TOKENS=260` are approximations. Tokenization can vary by content/model; exact wire request includes adapter-generated system directive and message framing not precisely tokenized. Saying 'no silent truncation' must be constrained to probed workloads/config, not universal proof. Recommend conformance property tests with adversarial unicode/JSON/long role messages, and adapter token-count if available; fallback on unknown window must be visible.

**R2 — reservation mismatch risk:** `apply_context_budget` reserves `request.generation_config.max_output_units or 512`, but real adapter sends `request.generation_config.max_output_units or self._default_max_output_units` as `max_tokens`. If adapter default exceeds 512, the pre-call arithmetic reserves less than the real requested generation max. Owner/contract review, RED test, and smallest correction required before claiming bounded-window integrity.

**R3 — declaration/runtime config parity:** `DELIA_LLM_CONTEXT_TOKENS` is optional and unknown disables enforcement. Model context 8192 was baked into a model in a local eval daemon, not delivered through committed prod infrastructure configuration; declared window may not match server effective window after restart/host migration/provider change. Release requires runtime parity verification/health or explicit bounded fallback; do not silently assume `DELIA_LLM_CONTEXT_TOKENS=8192` makes daemon 8192.

**R4 — content preservation:** dropping pairs changes referential continuity; counts/reason are observable but the model is not told that history was omitted. A typed non-authoritative omission marker remains D2 separate design decision; do not append forged `DELIA_RESULT`. Goal cross-stage consistency and session persistence not solved by this WP.

**NEXT BOUNDED STEP:** close R2 via contract-first, characterize R1 and R3 with local-only tests/config evidence, preserve current mechanism and avoid new token-engine/provider hooks; independent re-eval on frozen SHA/daemon config. Do not deploy; result 3 real records remains unproven and no model-capacity conclusion should exclude residual argument fidelity/context errors without trace evidence.


## 15. Contract hardening — R1–R4 (2026-10-25, task `DELIA-C3-CONTEXT-BUDGET-CONTRACT-HARDENING-AND-LOCAL-REVALIDATION-01`)

Executed against the §14 review verdict `ACCEPT_WITH_RESIDUAL`. Corrections target the four flagged residuals; every change stays inside the already-authorized owners (no new engine/planner/registry/provider/memory).

### 15.1 R2 — generation reserve parity (CLOSED)

Root cause: `apply_context_budget` reserved `request.generation_config.max_output_units or 512`, while the adapter sent `request.generation_config.max_output_units or self._default_max_output_units` as `max_tokens`. An adapter default above 512 would make the wire request larger than the reserved budget.

Minimal contract extension: `ModelInvocationPort.default_max_output_units: int | None` — the adapter's configured default generation cap, i.e. what is actually sent when the request omits `max_output_units`. `InvokeModel._enforce_context_budget` resolves the reserve as `request max_output_units → adapter default → 512 floor`, so the pre-call arithmetic now reserves exactly what the wire may request. Both adapters (real + deterministic test) expose the property; the real adapter normalizes the value (int, non-bool, >0) the same way as `context_window_tokens`. RED→GREEN: 5 tests covering request-explicit, adapter-default, absent-limit floor, reserve-consumes-window reject, and invalid adapter default.

### 15.2 R1 — estimator conformance (CORRECTED + MEASURED)

The `chars/2.5` linear estimate was measured against 21 payload classes on the governed local model (`/v1` `usage.prompt_tokens`):

| class | chars | actual tok | old est/act |
|---|---|---|---|
| PT-BR / EN prose | 4080 / 1720 | 1222 / 542 | 1.34 / 1.27 |
| JSON schema | 4694 | 1591 | 1.18 |
| unicode accents | 2220 | 1782 | **0.50** |
| emoji / ZWJ emoji / flags | 1100 / 2100 / 2200 | 1141 / 3041 / 2440 | **0.39** / — / — |
| symbol-heavy | 1860 | 1182 | **0.63** |
| technical identifiers | 3480 | 2281 | **0.61** |
| pure digits / dense codes | 3000 / 3599 | 3041 / 3640 | **0.34** / **0.35** |
| base64-like | 3000 | 2256 | **0.57** |
| business-evidence JSON | 3325 | 1597 | **0.83** |
| long message / multi-turn | 26407 / 1530 | 4443 / 343 | 2.38 / 1.78 |
| doc evidence / injection-as-data | 1920 / 1650 | 612 / 417 | 1.25 / 1.58 |

Underestimation was material on exactly the classes DÉLIA traffic contains — product codes and dense identifiers reach ~1.01 tok/char, 3.4× above the old factor. A single linear factor cannot bound both prose (~0.30) and dense codes (~1.0) without false-rejecting legitimate large mandatory prompts (the real `select_group` stage is ~13k chars / ~3.2k actual tokens).

**Minimal correction:** `estimate_text_tokens` sums structural per-class weights per whitespace-delimited run — non-ASCII 1.55, ASCII digit 1.20, ASCII uppercase 0.65, ASCII lowercase 0.36 (0.65 when the run is longer than a normal word, since dense runs tokenize like identifiers), whitespace 0.30, mergeable structural punctuation 0.45, rare symbols 1.00 — × 1.12 global margin. The run-level split matters: the first version flagged a whole whitespace-sparse string as dense, which over-priced minified JSON payloads containing prose and produced a live false-reject of `select_group` (est 8177 vs actual 3166 → `CONTEXT_TOO_LARGE`); per-run detection prices prose-valued JSON strings as prose while still covering base64/dense-code runs. Result on the measured corpus: **zero underestimates**, worst-case margin 1.11 (base64-like); live stages re-verified dispatching (`select_group` est 6213, `within_budget`). The bound remains labeled heuristic, not a measurement; `UsageMetadata` stays the only actual count. Conformance is frozen as 23 tests — the corpus plus recorded actuals — so any future weight weakening fails the suite.

### 15.3 R3 — declaration/runtime parity (CLOSED via versioned config + gate)

Verified in the eval daemon (Ollama 0.40.8): `delia-json` carries `PARAMETER num_ctx 8192` in its Modelfile — `/api/ps` reports `context_length=8192` **after a daemon restart** (baked blob persists in the `ollama_data` volume), and `DELIA_LLM_CONTEXT_TOKENS=8192` in the app env — declared == effective.

Versioned config fix: the `ollama` daemon service in both compose files now passes `OLLAMA_CONTEXT_LENGTH` (default 4096, the measured daemon default — the earlier `.env.dev.example` claim of 2048 was wrong; `OLLAMA_NUM_CTX` goes to the chat app service, not the daemon). Env examples (dev/prod) now state the parity requirement explicitly: `DELIA_LLM_CONTEXT_TOKENS` must equal the effective window the daemon honors (`OLLAMA_CONTEXT_LENGTH` or per-model `num_ctx`); declaring more than the runtime honors re-opens silent truncation.

Residual condition (ops, not code): `DELIA_LLM_CONTEXT_TOKENS` is an application declaration — the application cannot probe the provider window over the OpenAI-compat API. Deploy gate: whoever sets the declared window must have verified the effective runtime value (per-model `num_ctx`, daemon `OLLAMA_CONTEXT_LENGTH`, or provider limit). The ledger's est-vs-actual divergence is the detective control: a runtime honoring less than declared shows `input_tokens` collapsing toward ~ctx/2 on large prompts.

### 15.4 R4 — history reduction integrity (VERIFIED, residual documented)

New tests prove: reduction removes exactly the oldest complete `USER_INPUT`/`DELIA_RESULT` pairs — the surviving history is a verbatim suffix of the original (no reordering, splitting or rewriting); chronological order and `user`/`assistant` roles are preserved; `input_text`, `instruction_content`, `generation_config` and `expected_fields` are never touched; the adapter receives the reduced request, not the original (spy-verified); omission count/reason are observable per stage.

Characterized risk (documented, mechanism unchanged): a referential follow-up can lose its antecedent when the pair is omitted; the model is not told history was removed — it sees a shorter conversation and may answer honestly-insufficient rather than fabricate (observed: `long_history` completed reduced, honest). A typed non-authoritative omission marker remains decision D2 for coordination — no synthetic `DELIA_RESULT` was forged and none will be.

### 15.5 Regression caught and fixed

The WP-F `instruction_version` projection key violated the response leak-guard (`test_response_does_not_leak_provider_or_authority_internals` forbids the substring `instruction`). Projection key renamed to `lineage_version` (the value is `instruction_lineage.version`); internal observation field unchanged. GREEN.

### 15.6 Local re-evaluation (frozen config)

`delia-r7-eval-local` on the working tree: `DELIA_LLM_CONTEXT_TOKENS=8192`, `delia-json` num_ctx 8192, Ollama 0.40.8 GPU. 10-scenario HTTP matrix on the final estimator: zero `invalid_structured_output`, zero truncation, zero fabricated content. All stages report `within_budget` or `reduced`; the single `rejected` event is the recovery-leg `select_group` inside `write_ineligible` whose mandatory payload genuinely exceeded budget (est 8411) — typed `context_too_large`, recorded with `error_code`, turn completed honestly with zero ACT. `three_records`/`o2` and the other scenarios returned honest insufficiency/empty-source answers (3B per-stage variance); `long_history` reduced in complete pairs across stages (om 2–8, suffix-verified) and completed. Business outcome for three real records remains unmet — first divergent stage is `arguments`-side fidelity on the 3B model, not context. Estimate ratio on live traffic: ~1.4–2.0× actual for prose stages, higher for dense history (conservative over-estimate, never under).
