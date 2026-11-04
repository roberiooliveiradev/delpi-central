# 231 — DÉLIA · Migração integral para Pydantic AI, simplificação de orquestração e remoção do legado

**TASK_ID:** `DELIA-C3-PYDANTIC-AI-UNIFIED-INVESTIGATION-RUNTIME-MIGRATION-01`  
**DATE:** 2026-11-04  
**STATUS:** EXECUTED — see [doc 232](232-pydantic-ai-unified-investigation-runtime-execution-report.md); PRODUCTION_DEPLOY NOT_AUTHORIZED  
**REPOSITORY:** `roberiooliveiradev/delpi-central`  
**OBSERVED_HEAD_AT_PLANNING:** `bfa270939c5bed85023553be852c95cb7996063c` (reconfirm before work)  
**PRIMARY SOURCES:** doc 230 (framework inventory), 229 (systemic intelligence audit), 226 (semantic-once), 228 §§12–20 (RC-A/RC-B/RC-C/REF05), docs 192–196 (Engine B), 220 (Pydantic AI), canonical authorities and execution ledger.  
**EXECUTOR:** Cursor agent (Composer)  
**EXECUTION MODE:** **ONE END-TO-END ITERATION**, including implementation, removal, regression, local real-model evaluation, documentation, commit, push and report. Intermediate phases below are internal steps, NOT requests for new prompts/PO check-ins.  
**PRODUCTION DEPLOY:** NOT_AUTHORIZED.  
**LOCAL / GOVERNED HOMOLOGATION:** AUTHORIZED, using legitimate local credentials/configuration.  
**USER AUTHORIZATION:** Explicitly authorizes removal of LangGraph and redundant Application orchestration and migration to Pydantic AI, without repeated PO authorization gates for individual code removals. Does NOT authorize bypassing Core/domain AuthZ, Policy/Decision, Evidence verification, industrial safety, or action confirmation/idempotency.

> **Decision goal:** make Pydantic AI the unified semantic investigation runtime, reusing DÉLIA ports/adapters, evidence and authorization boundaries. Retire LangGraph from **active product runtime and product dependency tree** and delete superseded bespoke semantic sequencing/select/classify/retry implementation, based on concrete replacement coverage. Never delete legitimate business authority, evidence/verifiers, or security controls merely because they currently reside in a large orchestration file.

## 0. Mandatory canonical reanchor and frozen-decision resolution

Before touching code:

1. Record `git status --short`, `git rev-parse HEAD`, `git fetch origin`, `git rev-parse origin/main`; inspect concurrent staged/untracked work and use path-specific staging. Do not rewrite/squash other authors' commits.
2. Read Project Instructions and applicable `.cursor` files, then authorities in precise order: **16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → technical architecture → product spec → thematic specs → execution ledger**.
3. Read docs **192–196, 220, 226, 228, 229 and 230**, especially LangGraph's prior production activation, Pydantic AI adapter boundaries, semantic-once direction and the E4-R6 security regressions.
4. Identify canonical **phase, CP/RQ, consumers, ownership and contracts** at the actual HEAD. Preserve frozen product/security decisions; this plan represents a new user-requested change of *runtime implementation*, not an implicit cancellation of existing safety decisions. If authority requires a formal architectural decision, record it in the existing ADR/decision mechanism **within this same task**, with the explicit user authorization, before replacing implementation; do not silently overwrite the original decision.
5. For each mechanism: `EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY`, `REUSE_DECISION=REUSE|EXTEND|NEW`. Favor `REUSE/EXTEND`; an entirely new engine/registry/planner/store is **not** the requested solution.
6. Any genuinely irreconcilable authority or missing owner contract: mark `ARCHITECTURE_DECISION_REQUIRED` / `EXECUTION_DRIFT` with a precise blocker, not invented approval. Do all independent authorized steps in the same iteration.

**Evidence taxonomy:** `PROVEN/TO_INVENTORY/PLANNED/TARGET` for facts; `PASS/FAIL/PENDING/INCONCLUSIVE/TEST_NOT_RUN/STALE_EVIDENCE` for execution. Baseline code is not validated merely by docs; HTTP 200 is not a business outcome.

## 1. Why we are changing direction (grounded baseline)

The doc 230 inventory shows:

- `LangGraphCapabilityOrchestrator` is the current default for `DELIA_ORCHESTRATION_ENGINE=langgraph`, providing `StateGraph` stage sequencing, optional `Send` fan-out (`DELIA_SUBOBJECTIVE_FANOUT`, default OFF) and optional SqliteSaver (`DELIA_CHECKPOINT_DB`, default unset). An alternate Engine A `OperationalCapabilityOrchestrator._attempt` already sequences the same governed gates; they are mutually exclusive by config rather than double-running.
- `PydanticAiModelInvocationAdapter` is current default model transport via `ModelInvocationPort` and `InvokeModel`; it creates an `Agent` per structured model invocation but **registers no tools**. The production AI process is thus **not** currently a Pydantic AI investigation agent.
- Application's `OperationalCapabilityOrchestrator` contains semantic admission, goal interpretation, decomposition, filtering, per-sub classification, group/capability selection, argument proposals, candidate discovery, invocation, assessment, composition, retries and bespoke sequencing. Many stages re-ask the model before the first owner READ.
- Doc 229: ~20 instruction purposes, ~25 `self._propose` call sites, long failed comparisons (~175–300s), no source material satisfied, and partial drift from doc 226 semantic-once. Actual token totals were `NOT_MEASURED`.
- E4-R6: RC-A currently preserves explicitly declared `evidence_needed`; remaining risks include omitted dependencies and exact target matching REF05. RC-B owner selection and RC-C discovery-first are OPEN. Production acceptance is NOT_PASS.
- Source of code facts: `delia-api/app/composition/root_composer.py` (`_resolve_orchestration_attempt`), `app/infrastructure/orchestration/langgraph_engine.py`, `app/infrastructure/model_invocation/pydantic_ai_adapter.py`, `app/application/capability_provision/orchestration.py`, `app/application/interaction/handle_interactive_turn.py`, `app/infrastructure/config/settings.py`, `delia-api/requirements.txt`, docs 229–230.

**Hypothesis (must measure):** a bounded Pydantic AI tool-driven investigation using authorized semantic capability tools can replace repeated bespoke semantic selectors/arguments sequencing and the LangGraph stage graph, while preserving real owner READ, Evidence and safety. Pydantic AI cannot grant authorizations or verify enterprise facts by itself.

## 2. Target architecture: one semantic execution runtime, existing trusted boundaries

```text
HTTP interaction JSON / NDJSON (+ authenticated user context)
   -> existing Interaction Application use case, deadline, cancellation, activity sink
   -> existing Core live AuthZ / policy context, governed capability catalogue
   -> Pydantic AI Agent (semantic investigation; typed deps; bounded tool loop)
        -> toolset with SEMANTIC capabilities, supplied from approved live registry
        -> existing governed Application tools/ports (read; prepare/write only when allowed)
            -> existing owner routing + provider-neutral adapter
            -> MCP/OpenAPI discover -> candidate bind -> execute (protocol inside adapter/application)
            -> Domain API authority; Core live permissions; audit/idempotency/Policy for ACT
        <- structured owner outcomes + provenance, no raw authority claims
   -> existing DÉLIA Evidence / obligation verification / VerifiedCompositeEvidence
   -> existing Interaction grounding, presentation, NDJSON terminal contract
```

**Hard boundaries**:

- Pydantic AI Agent = **semantic proposal and investigation**. LLM tool calls are requests to governed DÉLIA capabilities, not authorizations; agent tool metadata cannot extend rights.
- Tools are **provider-neutral semantic operations**, not arbitrary HTTP endpoints, MCP raw tools, CSS selectors, execution scripts, bearer tokens or provider mechanics.
- Core authorization remains live and backend-first, Domain API is final source of business rules/data, DÉLIA Policy/Decision governs material writes, Automation Hub governs technical execution where applicable.
- Preserve `read != write`, `PREPARE != ACT`, `simulate != apply`, idempotency/audit/confirmation, secrets isolation, max execution stage, cancellations, tenant/user context and safety restrictions. Default toolset is READ-only; never expose write tools without the existing governance chain. User authorization here concerns *software migration*, not unconditional authority for business operations.
- Provider metadata, schemas, discovery and tool output are UNTRUSTED DATA. Return typed, validated observations; agent-generated narrative is not FACT.
- **Never remove** `VerifiedCompositeEvidence`, authoritative SourceRefs, provenance lineage, obligations/target binding checks, domain verifiers, owner-path-unbound fail-closed messages, or authenticated interaction projection.

## 3. Use native Pydantic AI capabilities (check pinned 2.50.0 API before implementation)

Map real Pydantic AI features to concrete needs, avoid inventing replacements:

| Existing mechanism | Target Pydantic AI capability / existing contract | Decision |
|---|---|---|
| Repeated `turn_goal` / per-sub classify | Typed Agent output + typed run dependencies / ongoing message history | Replace repeated interpretation; allow new reasoning on genuinely new evidence |
| `select_group` then `select_capability` | Registered, filtered semantic toolset / Agent tool choice (with schema and descriptions from approved catalog) | Replace bespoke multi-step selection if equivalent and safer |
| `arguments` / `candidate_arguments` | Native tool parameter schemas and typed validation (Pydantic) | Replace duplicated proposal layers; avoid unvalidated JSON |
| Candidate-bound `discover -> execute` | Governed semantic tool facade encapsulating the existing protocol and candidate binding | Keep technical mechanics outside the model |
| `_decompose_objective`, `SubObjectiveTracker` | Agent multi-step tool loop **plus retained obligation coverage verification** | Remove bespoke scheduler only if tests show equivalent coverage; reuse tracker/verifier for obligation bookkeeping when needed |
| Stage retries / repair | Pydantic AI built-in validation/retry **bounded by global TurnDeadline** | Consolidate overlapping retry layers; no unbounded model/tool retries |
| Interaction continuity | Controlled Pydantic AI history and existing session/context projection | No personal memory as authority; bounded, trusted summaries/evidence references |
| Framework graph / Send branches | Agent investigation sequence; only implement concurrency if necessary for real performance and safe dependencies | No invented new graph; if independent parallel calls needed use existing application primitives |
| SqliteSaver checkpoint | Existing DÉLIA authorized state/continuity contracts, if actually required | Do not introduce new persistence; prove parity or classify explicit residual |
| ModelInvocationPort | Existing port remains app/domain independent | Pydantic AI implementation behind infra port; avoid Agent imports in Domain/Application |
| Observability/usage | Existing ModelCallLedger / tracing + agent usage metrics when provided | Preserve true usage, lineage, timings, limits |

**Important:** A Pydantic AI Agent with tools is a new *usage mode* of already installed framework, not permission to build a second planner. Read Pydantic AI version-specific docs/source and tests before choosing `Agent`, `Toolset`, dependency injection, output validators, `UsageLimits`, message history, stream APIs or approvals. Native Pydantic AI SDK internals may only live in infrastructure adapters. Do not import `pydantic_ai` into Domain/Application.

## 4. Migration scope / deletion contract

**Intended removals after replacement tests pass**:

1. `app/infrastructure/orchestration/langgraph_engine.py` and exclusive graph builders, nodes, state, Send/reducers/checkpointers and dependencies **if all active runtime consumers and authoritatively required functionality have replacement parity**.
2. `DELIA_ORCHESTRATION_ENGINE` two-engine A/B selector, engine-specific settings, compose flags and boot wiring; stale LangGraph feature flags `DELIA_SUBOBJECTIVE_FANOUT`, `DELIA_CHECKPOINT_DB` removed or marked unsupported with fail-fast only after consumer review.
3. Framework dependencies no longer needed, including `langgraph`, `langgraph-checkpoint`, `langgraph-prebuilt`, `langgraph-sdk`, `langchain-*`, `langsmith`, `ormsgpack` and `xxhash` **only if dependency graph proves not needed elsewhere**. Evaluate lockfile/reproducible build effects, do not globally remove shared dependencies.
4. Bespoke **semantic orchestration** paths made obsolete: repeated per-sub `turn_goal`, multi-stage group/capability selectors, argument proposer variants, duplicate stage retry loops, Engine A stage sequencer, legacy `_propose` purposes and instructions resources no longer consumed, duplicate admission/synthesis routes, dead code and tests exclusively verifying retired implementation.
5. `pydantic_arggen` isolated evaluation branch if native Agent-tool arg validation replaces it and no legitimate consumer remains.
6. Legacy alternate model adapter if genuinely unused and replacement provides mandated failure/rollback operational story; otherwise explicitly document retained port-compatible fallback.

**Prohibited blanket deletion:** Do NOT delete `OperationalCapabilityOrchestrator` or its large file en bloc merely because it contains old sequencing. Extract/retain legitimately owned application behavior (capability catalogue, permissions, decision gates, candidate protocol boundary, observer/evidence, source/target matching, confirmations, audit, activity, cancellation). Minimize replacement surface and **net new architecture**. Removing legacy means removing *replaced responsibilities*, not erasing application business controls.

**Gate for each deletion (internal, automatic; no new PO request):** code/consumer inventory -> replacement mapping -> equivalence tests -> deletion -> residual search -> complete regression -> local real outcome. A failure is reason to fix implementation within the same iteration, not to keep an unused duplicate forever. If parity fundamentally cannot be proven within legitimate authority, mark exactly what remains and why; never fabricate PASS.

## 5. Single-iteration execution choreography (all phases executed by Devin)

### Phase 0 — Reanchor + baseline + contract locks

- Recheck Git HEAD/status and canonical documents, inspect any newer PR/commit since plan creation.
- Freeze a baseline benchmark at BASE_SHA in local/test environment: E01 conceptual SIPOC, E02 single product READ `90260147`, E03 compare `90260147` vs `90260148`, E04 third mandatory external evidence, E05 candidate-bound discovery, E06 owner unavailable, E07 conversational follow-up, E08 cross-domain semantic capability, E09 denial/no-authz, E10 NDJSON terminal/cancel; where feasible run 3+ variants of task wording/model trial. Record config/model, provider cold/warm, traces, latencies and actual usage if available.
- Inventory every active consumer of LangGraph, Application orchestration, Pydantic AI adapter and flags (doc 230 is baseline, not substitute for HEAD). Log baseline failures honestly (`material_satisfied=0` may remain).
- Verify contracts: `SupportsGovernedCapabilityAttempt`, `SupportsGovernedStageGates`, `ModelInvocationPort`, `InvokeModel`, `GovernedCapabilityAttempt`, `VerifiedCompositeEvidence`, `SubObjective`, `SourceRef`, Interaction turn/ActivityEvent/NDJSON, workspace/auth/max_execution_stage, owner routes/discovery/candidate, source-target validation.
- Add regression characterization tests (no product modifications) **before** replacement. Confirm RED/expected failures for the shortcomings under migration.
- Inventory license/package version/API features and runtime provider compatibility (Qwen3:4b local vs prod provider model must not be conflated).

### Phase 1 — Introduce unified Pydantic AI investigation behind existing port

- Extend existing infrastructure Pydantic AI integration to support **one bounded investigation** with dynamically supplied, sanitized semantic tools. Use the existing Application port or extend it narrowly; avoid creating a new public service, agent registry, planner runtime or provider branch.
- Construct model-visible tools from **allowed capability contracts** with safe names/descriptions/schema and identity-free minimum data. Tool exposure must be filtered by live Core AuthZ, capability availability, allowed execution stage and Policy; tool execution rechecks Core/domain authority.
- Tool implementation delegates to existing governed application handler/port and existing adapter; tool execution returns typed result with authoritative provenance/source/target identity or typed error/limitations. Reject unknown tool id, invalid args, missing candidate, ambiguous target, forged provider metadata, expired permissions; no hidden model-side invoke.
- Untrusted tool outputs remain data; never instructions. Bound output sizes/context; preserve source reference without copying credentials. Do not send token/secrets to model.
- Return a typed investigation result with status, references to received evidence, unmet obligations and agent usage metadata. Agent summary is not final accepted grounded answer.

### Phase 2 — Consolidate semantic stages into tool-driven investigation

- Replace admission + redundant parent/subgoal reinterpretation with the smallest semantic decision sequence consistent with docs 226 and task complexity. A simple conceptual request should take a proportional conversational path; operational questions take the governed tool path; semantic uncertainty may justify further model calls.
- Agent uses tool availability and verified tool outcomes to progress without manually chained `select_group -> select_capability -> arguments` for each sub, except any genuinely necessary specialized capability boundary.
- Preserve parent intent, entities, targets, required sources, prior verified evidence and incomplete needs through the investigation. If model omits `evidence_needed`, compare outcome against original parent request and existing trusted obligation/binding contracts where possible; **do not treat empty declaration as proof of completeness**. If impossible to verify, honest `NON_GROUNDED/INCONCLUSIVE` rather than fabricated completeness.
- Discovery-first with candidate-bound owner capabilities is encapsulated in governed tools; user asks for business action, not token/protocol. Obtain candidate from real discovery, bind scope, authorize and execute read; never fabricate token.
- Remove per-sub `turn_goal` only when final requirements stay complete and generalizable; do not hardcode product codes, providers, TÉO, DAVI, tool names or keywords.
- Keep explicit deadline, cancellation, bounded iterations/tool calls, usage ceilings, model/provider retries and idempotent owner invocation; prevent infinite exploration and fan-out explosion.
- Retain human-confirmation semantics for write/ACT even when the agent requests them; no automatic L4/L5 elevation.

### Phase 3 — Evidence, outcomes and presentation parity

- Tool results include real owner outcome and SourceRefs, provenance lineage, effective identity binding and limitations; prevent `SPECIALIST_OUTCOME` or discovery metadata from being treated as business facts.
- Reuse existing `VerifiedCompositeEvidence` and composition boundary: common/exclusive items and quantities from verified two source structures; verify requested targets `90260147` and `90260148` against authority, not merely two distinct roots. Third-source dependencies must remain unsatisfied until actually verified.
- Preserve deterministic owner-miss/non-grounded messages, user-visible limitations, interaction result epistemic_class/grounding_status, CRI projection and NDJSON terminal. No model free-form narrative may override a missing owner/evidence gate.
- For factual answers let agent format or propose only within already verified evidence envelope. The final trusted presentation comes from current interaction outcome path.

### Phase 4 — Replace sequencing; remove LangGraph and superseded code

- Swap `root_composer` default wiring to unified Pydantic AI investigation via existing Application interface; update configuration for only one active investigation runtime. No side-by-side duplicate permanent planner/engine.
- Confirm entrypoints JSON/NDJSON/single READ/compare/conversational/continuation all execute **without** importing or invoking LangGraph.
- Resolve opt-in Send fan-out, SqliteSaver checkpoint/resume consumers: either equivalent behavior using already authorized DÉLIA contracts or record that optional feature is not available in the new runtime and explicitly test fail-safe/unconfigured behavior. Never claim durable resume solely from in-memory history.
- Remove graph package and selective transitive pins, obsolete imports, tests, configs, env references, docs advertising active graph, eval scripts only for retired behavior, unnecessary legacy instructions, alternate sequencer and duplicate selectors/arggen only **after** functional parity. Keep test scenarios and convert tests from implementation-based assertions to behavior-based conformance where possible.
- Run residual search through app, tests, infra, compose, lockfiles, docs/ADRs and feature flags. Historical docs remain historical; annotate deprecation rather than rewriting history. `0 search results` alone is not proof of no consumer.

### Phase 5 — Tests, security/generalization evaluations and local live runs

**Minimum automated groups** (use actual filenames on HEAD; add/adjust tests as necessary):
- ModelInvocationPort/Pydantic AI adapter structured output, errors, timeout, usage, message history and provider variants.
- Interactive admission, conversational, owner READ, surface, follow-up, JSON/NDJSON activity, terminal delivery, cancellation, deadline.
- Capability catalog dynamic selection, dynamic tool schema/args, cross-domain semantic routing, ambiguous referent, foreign specialist mismatch (RC-B).
- MCP discovery-first candidate-bound execute and no token guess (RC-C); retries, missing discovery, empty candidate, owner errors.
- RC-A C01–C05, S01–S16, acquisition T01–T16 and new **missing evidence_needed** negative tests; material obligations persist through tool loop.
- REF05 exact requested target/root mapping and independent oracle; no swapped/unrelated root acceptance.
- VerifiedCompositeEvidence fan-in provenance, SourceRef lineage, no model factual hallucination, insufficient/denied source fail-closed.
- AuthN JWT/Core, per-tool live AuthZ, Domain authority, policy/confirmation/idempotency/audit/prep-vs-act, adversarial tool metadata/prompt injection, credential isolation, high-risk OT/Safety no unsafe ACT.
- Local model generalization with unrelated capabilities: never hardcode product-structure comparison for success; test 10+ semantic variants across selected scopes where feasible; record exact run count, success/fail and reasons.
- Concurrent/partial calls, deadline budget, retry ceiling, interrupted request, duplicate tool execution, terminal NDJSON exactly once, zero false GROUNDED in executed negative set.
- Full test suite (backend and relevant frontends/consumer integration) including build/typecheck, dependency install from scratch and startup without graph packages.
- Record baseline known debts separately and do not call tests PASS merely because unrelated suites were skipped.

**Local governed E2E mandatory**: using the established `docker-compose.dev` stack with Keycloak, Core `/me`, gateway, Domain/DAVI or legitimate MCP, Ollama `qwen3:4b-instruct-2507-q4_K_M` when configured; verify exact binary/code SHA and model config *after* rebuild, no stale `DELIA_RUNTIME_SHA` label. Run E01–E10 via actual `POST /interaction/turns`, both JSON and NDJSON where applicable; record HTTP, semantic choice, tools invoked, real source roots, provenance, grounding, client terminal, token usage (real if provider reports), cold/warm model and time to first owner READ. No write actions.
- If baseline environment lacks owner data/candidate API, do not spoof the owner. Demonstrate with a real authorized test owner if available and classify unsupported oracle `NOT_REACHED`; still complete safe code/test migration and report business outcome honestly.
- Reproduce candidate-bound discovery path with real owner when available; otherwise use typed fake owner in integration and distinguish synthetic from live.
- Compare **before/after** calls, token counts, latency and task outcomes on same config whenever possible. No invented improvement percentages.

### Phase 6 — Iterative closure, cleanup, documentation and commit

- For any FAIL in authorized scope: isolate first failing stage, reproduce RED, fix minimal owner code, rerun focused test, run regression, repeat local live case; do not stop after first error, but avoid unrelated redesign.
- If new feature outside existing authority is necessary, record `ARCHITECTURE_DECISION_REQUIRED` and preserve safe partial progress rather than overriding contractual or safety constraints. Do not seek routine PO signoffs for every deletion: explicit user authorization covers migration and removal of obsolete implementation.
- Update canonical ADR/decision for retiring LangGraph production sequencing and activating Pydantic AI investigation, indicating impacts to historic docs 192–196 and 230, and superseded flags/rollback. Do not silently erase history.
- Add the factual outcome section to docs 228/229/230 as needed **without changing past evidence**, or create a separately numbered execution report and update ledger. Contract changes should be documented with consumers/security/compatibility and migration notes.
- Stage only task paths, check `git diff --cached`, run residual search, commit with coherent scoped changes, rebase safely on concurrent `origin/main`, push `main`, verify SHA and clean/staged state; keep rollback by Git SHA and config if genuinely supported (do not claim rollback to removed graph without rebuilding old image).

## 6. Quantified acceptance criteria (functional, not just tests)

| AC | Condition | Required evidence |
|---|---|---|
| AC-01 | Pydantic AI native Agent + governed semantic tool calls is active end-to-end | call trace + test |
| AC-02 | LangGraph absent from active application composition and runtime packages | import/boot/requirements scan + fresh image |
| AC-03 | No legacy Engine A/Engine B parallel sequencer or duplicate semantic selector remains where replaced | consumer mapping + residual search |
| AC-04 | Core/Domain/AuthZ/Policy/Decision/write gates unchanged in authority and tested | adversarial integration |
| AC-05 | Owner tools obtain authentic READ outcomes, not metadata-as-fact | verified source results |
| AC-06 | RC-A positive/negative and missing-evidence tests: zero false verified composition | security suites |
| AC-07 | RC-B dynamic owner selection works without hardcoding specialist; generalizes to other owners | integration + live outcome |
| AC-08 | RC-C real discover→candidate→execute works or is accurately blocked by external owner | probes + typed result |
| AC-09 | REF05 binds both requested roots correctly and independent oracle comparison holds; if external owner blocked, NOT_PASS | oracle evidence |
| AC-10 | Full interaction contracts JSON/NDJSON, CRI, non-grounded handling, continuity and turn deadline preserved | consumer tests |
| AC-11 | At least matched baseline/after trace for calls, latency, actual tokens where available; usage NOT_MEASURED otherwise | run metadata |
| AC-12 | Full regression + build + fresh dependency/bootstrap, no new critical FAIL | logs and SHA |
| AC-13 | Real DÉLIA local governed E2E with active new runtime and exact SHA | API/NDJSON traces |
| AC-14 | 10+ cross-phrasing/domain trials where feasible; count and safety/task results separated | eval report |
| AC-15 | Historical docs and ledger updated, no phase advanced by documentation alone, commit/push verified | commit/ledger |

**Exit verdicts:** `ACCEPT` only if migration and required product outcome proof are satisfied; `ACCEPT_WITH_RESIDUAL` if technical migration passes but independent owner/oracle unavailable, with tests demonstrating safety and explicit remaining RC-B/C/REF05; `REWORK` for regression, false grounding or missing governance; `INCONCLUSIVE` for unavailable evidence. **No false PASS** for API 200, clean boot, or synthetic tool calls.

## 7. Explicit non-goals and guardrails

- Not migrating Minha DELPI Chat/agents, Portal, other plugins or Domain services into DÉLIA.
- Not inventing an in-house framework to replace LangGraph. Pydantic AI runtime is the selected implementation; Domain/Application remain framework-independent.
- Not using raw MCP/Pydantic tool metadata as permission, nor exposing all providers/operations dynamically without Core/AuthZ and policy filtering.
- Not assuming automatic tool loop solves missing `evidence_needed`, wrong target, owner mismatch, missing discovery or insufficient domain facts.
- Not adding arbitrary production timeouts merely to hide a slow model, or conflating cold load with application overhead.
- Not deleting safety checks, audit, idempotency, live AuthZ, outcome verification, forced clarification, or fail-closed denials as "legacy gates."
- Not using persistent model history as authorized business truth, nor making LangGraph removal synonymous with deleting all continuity.
- Not performing production deployment. Local/homologation only, no data writes.

## 8. Required final report template

```text
DÉLIA EXECUTION REPORT — PYDANTIC AI UNIFIED MIGRATION
TASK_ID:
BASE_HEAD:
FINAL_HEAD:
ORIGIN_MAIN:
PUSH_VERIFIED:
GIT_STATUS:
AUTHORITIES_READ:
CP_RQ:
DECISION_RECORD:
EXECUTION_DRIFT:
EXISTING_EQUIVALENT:
REUSE_DECISION:
PRODUCT_RUNTIME_BEFORE:
PRODUCT_RUNTIME_AFTER:
PYDANTIC_AI_VERSION:
AGENT_TOOLSET_INTERFACE:
EXISTING_PORTS_REUSED:
REMOVED_LANGGRAPH_FILES:
REMOVED_LANGGRAPH_DEPENDENCIES:
REMOVED_LEGACY_ORCHESTRATION:
PRESERVED_APPLICATION_AUTHORITIES:
RETAINED_LEGACY_WITH_REASON:
CONTRACT_CHANGES:
LLM_CALLS_BEFORE_AFTER:
TOKENS_BEFORE_AFTER:
LATENCY_BEFORE_AFTER:
TIME_TO_FIRST_OWNER_READ:
MODEL_CONFIG:
EVALUATED_SHA:
LOCAL_DEPLOY_SHA:
LIVE_E2E_SCENARIOS:
REAL_OWNER_READS:
DISCOVERY_FIRST_RESULT:
RC_A_SAFETY:
RC_B_OWNER_SELECTION:
RC_C_CANDIDATE_PROTOCOL:
REF05_TARGET_ORACLE:
FALSE_GROUNDED_COUNT:
AUTHZ_SECURITY_EVALS:
GENERALIZATION_EVALS:
FULL_BACKEND_REGRESSION:
CONSUMER_INTEGRATION_TESTS:
BOOT_WITHOUT_LANGGRAPH:
NDJSON_TERMINAL:
DOCUMENTS_UPDATED:
LEDGER_UPDATED:
RESIDUAL_SEARCH:
UNRESOLVED:
ROLLBACK_SHA_AND_PROCEDURE:
VERDICT:
FUNCTIONAL_ACCEPTANCE_CANDIDATE:
PRODUCTION_DEPLOY: NOT_AUTHORIZED
```

## 9. Implementation instruction to Devin

**Execute this entire migration as one bounded assignment**, not a proposal-only deliverable: reanchor → characterize baseline → implement Pydantic AI native governed tool investigation → simplify semantic flow → replace the sequencer → safely delete superseded LangGraph/bespoke code and unused dependencies → tests and security eval → real local DÉLIA E2E → iterate until all authorized and feasible checks are satisfied → docs/ADR/ledger → commit/push main → factual report.

The user has explicitly authorized software refactor and deletion. Do not interrupt for repeated routine PO approvals or leave an unneeded duplicate engine merely for convenience. **However, full migration does not permit removing legitimate auth/security/evidence gates or inventing success when the real owner service is inaccessible.** Keep phases within this task to preserve causal attribution and easy local rollback.

**Success is a working governed investigation runtime that makes genuine progress on real user tasks, not simply "LangGraph removed" or "Pydantic AI Agent constructed."**


---

## Continuidade canônica — 2026-11-04 — Pydantic AI Native-First (doc 235)

**Status histórico desta task 231: EXECUTED; não reabrir nem reescrever a evidência de migração.** A execução original está nos docs 232–234; LangGraph foi aposentado, Pydantic AI `Agent` + tools já integra o produto, porém **aceite funcional completo segue INCONCLUSIVE** sem E2E no evaluated SHA. O próximo passo não é criar novo planner, decompositor, comparador hardcoded ou infraestrutura paralela.

**NOVA DIREÇÃO DE CONTINUIDADE:** [doc 235 — Consolidação Pydantic AI Native-First / Agente Investigativo Generalista](235-pydantic-ai-native-first-generalist-investigation-consolidation-plan.md) (**TASK_ID** `DELIA-C3-PYDANTIC-AI-NATIVE-FIRST-GENERALIST-INVESTIGATION-CONSOLIDATION-01`; `STATUS=PLANNED`). Documento 235 é o **plano executável sucessor** e prevalece sobre recomendações desta task histórica quanto à próxima implementação de inteligência semântica. Preservar hierarquia canônica superior e contrato de Evidence, Policy, Domain e AuthZ.

Objetivo de continuidade: o usuário expressa objetivo; Pydantic AI investiga dinamicamente via capabilities governadas (A→B→análise→C, com MCPs e owners distintos), pede esclarecimentos e retoma contexto quando necessário, produz síntese com claims/evidence refs, e a DÉLIA verifica os fatos/outcomes. Comparação de estruturas é **cenário de avaliação, não um fluxo fixo**. Priorizar toolsets, schemas tipados, deps, history, tool loop, validação, usage/limits, observabilidade e mecanismos nativos efetivamente disponíveis na versão instalada. Remover seletores/finalizadores/retries/instruções próprios somente com prova de consumidores e equivalência; **nenhuma lógica de agente duplicada**.

**Infraestrutura de teste:** rebuild em ambiente **local isolado** é autorizado; rebuild/deploy em produção não. Doc 234 registra Docker/Ollama/API disponíveis, mas runtime local obsoleto; homologação no SHA novo é obrigatória, sem reutilizar scripts/volumes/contexto produtivos. Sem prova real: `TEST_NOT_RUN/INCONCLUSIVE`, nunca `PASS`.

**Reanchor:** HEAD/git status → Project Instructions/.cursor → 16→50→17→49→51→52→21→20→25 → arquitetura/specs → docs 226, 228–235 → ledger. O plano 235 é continuidade, não avanço de fase por documentação.
