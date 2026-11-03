# 217 — Implementação experimental composta: retrieval + LLM tool selection + progressive exposure

**Status:** EXPERIMENT_APPROVED_BY_COORDINATION / CODE_NOT_IMPLEMENTED / PROD_SWITCH_NOT_APPROVED.  
**Date:** 2026-11-02. **Observed main HEAD:** `9064fa62f77240d2644f28c0b83846ffbb935718`; revalidate.  
**Task:** `DELIA-C3-COMPOSABLE-TOOL-SELECTION-EXPERIMENT-01`.  
**Authority:** Project Instructions/.cursor → 16→50→17→49→51→52→21→20→25 → architecture → product spec → thematic docs → execution ledger. Docs 210–216 are existing reference; do not reset S2–S6 or promote catalog snapshot to production.

## 1. Decision and hypothesis

Implement an **isolated, configurable, provider-neutral tool-selection experiment**, reusing the current single LangGraph orchestration and MCP versioned JSON snapshot. The user requests best **combination of three complementary functions**, NOT three orchestration frameworks:
1. **Retrieval** of semantically relevant capability candidates from the approved snapshot (lexical/semantic hybrid when justified; compare simple BM25/fuzzy first and LlamaIndex ObjectIndex/tool retrieval as library candidate).
2. **LLM selection** from the bounded candidate set (evaluate LangChain `LLMToolSelectorMiddleware` for compatibility with existing `InvokeModel`/LangGraph; if tied to a second `create_agent` runtime or introduces circular dispatch, use existing selection port with equivalent model-neutral structured contract and document NOT_ADOPT of middleware).
3. **Progressive exposure** of only selected tool definitions and full JSON schema for arggen (evaluate Pydantic AI `PreparedToolset` / `DeferredLoadingToolset` behind existing adapter, NOT a new Pydantic agent execution engine; if native machinery cannot be reused without second agent, extend existing semantics and document NOT_ADOPT of integration).

**Critical:** do not install all three by default; adoption per role requires actual consumer/boundary and measured benefit. Library names do not replace architecture or authority. No special-case CAIO/SURI/TEO or corpus keywords.

## 2. Sources and reuse proof before code

Inventory only relevant code on current HEAD: `SpecialistInterop.discover_catalog`, `SnapshotDiscoverInterop`, `McpCatalogStore`, `McpCapabilityProvider`, identity registry, `capability_provision/orchestration.py`, `langgraph_engine.py`, model port, prompts/select_group/select_capability/arguments, evidence and policy, current deps/locks. Record for *each candidate component*: `EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY`, `REUSE_DECISION=REUSE|EXTEND|NEW`, owner, consumers, contract, dependencies, test.
`TO_INVENTORY` blocks speculative NEW. Confirm library APIs against installed versions and official docs; benchmark integration footprint, not only features on documentation.

## 3. Isolated selection boundary

Keep `LIVE` default untouched. Use versioned MCP snapshots only in evaluation opt-in; invoke always live with Core AuthZ, Policy, Domain owner, schema validation and fail closed. Model planner chooses *semantic capabilities*, not endpoints.
Experimental modes composed in existing composition root:
- A: current selector baseline (unchanged).
- B: retrieval only.
- C: retrieval + LLM rerank/selector.
- D: retrieval + LLM rerank + progressive schema exposure.
- Optional diagnostic E: LLM-only selector (without retrieval), if required to attribute effects.
Provider/framework-neutral outputs: `SelectedCapabilityRef(owner_id, tool_id, schema_hash, catalog_version, rank/evidence_reason, scope)` or reuse exact existing DTO, never trust model scores for authorization. Same identity/scope among A–D. A validated shortlist does not authorize invocation. B/C/D cannot switch at user prompt request.

**Two-stage context:** only minimal semantic descriptions in candidate retrieval/selection; after selection load full schema for argument generation. Preserve multi-tool recall for complex goals; do not force top-1. Guard against relevant tool exclusion via recall@k and bounded widening/re-discovery. Tool exposure is presentation/availability to the model, never capability permission or autoexecution.

## 4. Retrieval specifics

Use existing catalog JSON as source. Deterministic baseline BM25 and/or existing approved embeddings/semantic search if already present; do not create vector DB by default. LlamaIndex object/tool retriever candidate only if it improves real retrieval or reduces integration complexity without introducing new planner/DB. Index normalized names, description, owner semantic purpose, legitimate schemas/annotations needed for relevance, not secrets or business data. Index scoped snapshots/version/hash; incremental rebuild on script `apply` or hash change; invalidation, tenant separation, zero stale cross-scope leakage. No fixed owner synonyms in planner. Versioned cached index is a projection of snapshot, not authoritative owner state.

## 5. LLM selector and progressive exposure

LangChain selector middleware supports selecting from available tool descriptions with `max_tools`; test against current `InvokeModel` contracts, budget, model availability and failure behavior. Avoid calling another autonomous agent; prefer adapter to existing selector if native middleware requires `create_agent`.
Pydantic AI toolsets can dynamically filter/defer tool definitions; test `PreparedToolset`/`DeferredLoadingToolset` in isolation for metadata and JSON-schema fidelity. Do not delegate MCP execution/authz to Pydantic AI. If dynamic toolset is not usable without a new agent, implement exposure by the existing capability boundary and record why library was not adopted.
Observe all prompt token budgets and fast/operational/reasoning path. Selector model overhead should be justified by gains over current selection, including smaller local models.

## 6. Implementation slices (deliver code, not docs-only)

T0 reanchor/inventory/reuse and freeze baseline, security constraints.
T1 RED tests+contracts; add experimental selector composition flag, baseline A equivalence and fail-closed invalid snapshot.
T2 implement retrieval backed by snapshot and version-aware scope; multi-tool recall and negative tests.
T3 implement model selection/rerank with bounded candidates, typed result, reason refs, permitted recovery; verify LangChain native integration vs adapter.
T4 implement progressive tool exposure/full-schema lazy load with exact metadata preservation; verify Pydantic native integration vs adapter.
T5 integrate subobjectives and fanout: each subobjective can require multiple capabilities; stable refs; dependencies, global budgets; no second planner.
T6 execute E2E and controlled comparison A/B/C/D; repair flaws, check safety and rollback.
T7 full relevant regressions, docs/ledger/benchmark evidence and Git FF push. No production deploy, no business writes.

## 7. Minimal but useful evaluation

**6 fixed representative business questions**, selected before results: simple single-owner, ambiguous owner (procurement versus commercial), multiple tools same owner, two-authorized-owner composite, unfamiliar terminology, partial/owner-unavailable; plus **4 negative cases** (revoked AuthZ, tool deletion/schema drift, injection in description, must_not_invoke/write intent). Make same questions/model/quantization/temp/owners enabled/identity/time budgets; pair A/B/C/D once as initial characterization, rerun only divergent or noisy cases at most 3x and report variance. This is an engineering feasibility gate, not statistical proof.
Measure owner precision, **required tool recall@k**, capability precision, args validity, evidence relevance, business outcome, selection vs discovery vs total latency, input/output tokens, model/tool calls, overhead, invalid/stale selection and unsafe exposure. Separate retrieval-stage errors from selector errors. Do not count tool discovery/HTTP200 as business success. Keep literal traces in protected eval storage with SHA/config, no secrets in Git. Never change oracles to favor one mode.
A/B/C/D share tool *surface* and versions, except exposure stage by definition. If snapshot mismatch, invalidate pair. Comparisons involving 503 remain owner availability, not selector PASS.

## 8. Non-negotiable acceptance gates

G0 canonical reanchor and documented reuse decisions.
G1 baseline A unchanged, no production mode switch.
G2 retrieval returns proper scoped/versioned candidates; recall of required sets on six questions observed and no silent truncation.
G3 selector uses existing model port, no duplicate agent planner, bounded calls, valid tool IDs and errors; library adoption justified.
G4 progressive exposure exact full schema/enum/required, lazy when needed, never exposes unauthorized tools, no second tool execution path; library adoption justified.
G5 compound multi-tool E2E and safe widening/empty candidate/owner unavailable.
G6 negative security/tenant/schema drift/metadata injection/write-intent fail-closed, existing policy preserved.
G7 A/B/C/D reproducible, explicit measures and trace; overhead and relevance, not just speed.
G8 regression, rollback flag to A, evidence, commit/push/ledger, coordination-only verdict.
A variant can be inferior; experiment succeeds if findings are faithfully demonstrated. Do not invent efficacy/force adoption. If a dependency proves incompatible, document `NOT_ADOPT`, implement via reused contract only if still authorized, and report exact causality.

## 9. Reports and continuity

```text
TASK_ID=DELIA-C3-COMPOSABLE-TOOL-SELECTION-EXPERIMENT-01
BASE_SHA=
FINAL_SHA=
ORIGIN_MAIN=
PUSH_VERIFIED=
AUTHORITIES_READ=
EXISTING_EQUIVALENT=
REUSE_DECISION=
LIBRARIES_ADOPTED_AND_REJECTED=
TOOL_SELECTOR_MODES=
CATALOG_SNAPSHOT_SHA_AND_SCOPE=
G0_TO_G8=
RETRIEVAL_RECALL=
SELECTION_PRECISION=
MULTI_TOOL_E2E=
ARGS_EVIDENCE_BUSINESS_OUTCOME=
LATENCY_AND_TOKENS=
SECURITY_AND_REGRESSIONS=
ROLLBACK=
PRODUCTION_DEPLOY=NO
BUSINESS_WRITES=0
TASK_STATUS=COMPLETE|INCOMPLETE|EXECUTION_DRIFT
COORDINATION_VERDICT=PENDING_INDEPENDENT_REVIEW
BLOCKERS=
```
Work in isolated worktree, no force push, no touching concurrent changes. `AUTO_SESSION_RESUME=UNSUPPORTED`; keep resumable checkpoints and no fabricated background continuity. Continue stages without routine coordination interruptions. Final production adoption requires separate architecture decision.
