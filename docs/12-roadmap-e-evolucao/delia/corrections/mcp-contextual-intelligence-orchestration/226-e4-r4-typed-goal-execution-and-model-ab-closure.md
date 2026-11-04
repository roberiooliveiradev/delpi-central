# 226 — DÉLIA · E4 R4 — Typed-goal execution and bounded model A/B closure

**Date:** 2026-11-03. **TASK_ID:** `DELIA-C3-E4-R4-TYPED-GOAL-EXECUTION-AND-MODEL-AB-CLOSURE-01`. **INPUT_SHA:** `d1188aafef` (verified main at coordination review). **STATUS:** `REWORK` — previous R3 commit changed only execution-ledger documentation; no runtime corrective diff since doc225. **PRODUCTION_DEPLOY=NOT_AUTHORIZED**.

## 1. Review verdict / claim precision

- Real local runs show Qwen3 4B outputs variable typed decomposition and sometimes returns empty/unbound candidates; some runs achieved two-tree composition and HTTP 200. This establishes VARIABLE_OUTCOME, not by itself a clean causal exclusion of prompt/schema/context/provider/concurrency or strong attribution of dominant model-size inadequacy.
- `H2=DOMINANT_CAUSE` in executor report is downgraded by coordination to `INCONCLUSIVE_EXACT_CAUSE` until same-stage, same-schema, same-context, same-seed/settings/provider-resource controlled samples with proposal/validation distinctions and stage-specific statistics are available.
- Redundant `so_compare`/foreign VISTA/TEO work is reported: a typed validated comparison objective with two authorized targets does not require another LLM to reinvent tasks already implied by its validated semantics. This is **not** permission to skip legitimate owner-specific analytics when the user asks for them.
- R3 commit verified: compare `a0d83ffce412` → `d1188aafef` shows only ledger modification. No runtime implementation or reliable real-model acceptance occurred in R3.
- G04/G05/G07/G12 remain NOT PASS. Existing SEC01 has revocation limitation; client latency varies and 117.8s is unacceptably close to 120s gateway. No production deploy.

## 2. Architecture decision — use semantic decisions once; execute validated tasks deterministically

`ARCHITECTURE_DECISION=APPROVED_BOUNDED_REUSE` within ADR 58, 221–225 and existing contracts only.

**Owner:** DÉLIA Application / existing governed orchestration, Domain APIs factual owner, Core AuthZ owner. **Frameworks:** Pydantic AI typed semantic goal and provider-neutral model invocation; LangGraph existing sequencing/fan-in/checkpoint, after ownership/concurrency test.

1. Interpret user intent semantically via existing typed goal (comparison_requested, business_subject, target refs where proven). A valid typed goal is a model HYPOTHESIS that must be checked against actual admissible context and owner catalog.
2. Once the **distinct target references are validated** against legitimate user input or authorized reference resolution, the application can derive the minimal required READ evidence obligations using existing capability contracts and subobjective tracker. This is deterministic plan realization of an approved semantic goal, NOT an additional lexical intent parser, product-specific branch or new planner. If targets are not known/validated, ask clarification or perform legitimate discovery; never pretend text history is FACT.
3. Only request additional LLM decomposition if the objective actually contains unknown or complex dependencies that cannot be represented by existing typed goals and constraints. No unconditional re-decomposition of already-known READ requirements or extra `so_compare` delegated to analytics without independent owner-specific need.
4. Execute authorized source READs through existing live catalogue/discover→candidate→execute path, with policy/Core/Domain validation, deadlines and bounded retries; provide typed source refs and exact target-set coverage to existing deterministic evidence comparator. Do not treat `sources>=2` as proof of matching target-set.
5. Model can propose candidate relationships; deterministic verifier must cover full evidence and all user-requested targets, including known false common `10030012` and omitted common `10030015`. No model-authored factual prose, new authority, or shadow VISTA/TÉO analytics.
6. Before changing execution, map `EXISTING_EQUIVALENT=YES/PARTIAL` and `REUSE_DECISION=REUSE/EXTEND/REMOVE_REDUNDANT` for existing `_decompose_objective`, `_investigate_subobjectives`, LangGraph and `ModelInvocationPort`. Remove truly duplicate control flow rather than introducing an extra semantic coordinator. No SDK imports into Domain/Application.

## 3. A/B of model capability — conditional, local and finite

**Authorized:** bounded local EVAL of a larger **already available/approved** model against pinned Qwen3 4B; not a production model switch or new provider. If not available, report TEST_NOT_RUN with inventory and implement the approved typed-goal reuse path; never require hardware procurement as a prerequisite.

- Same stage instruction, schema, context projection, model settings, provider transport and evidence. Repeat >=5 each; prefer >=10. Capture validated proposal rates, invalid schema vs empty-decomposition vs mis-bound target, latency p50/p95, input/output tokens where supplied, compute fit, safety and verified business outcome.
- A/B orthogonally tests (a) current Qwen3 with redundant decompose vs (b) Qwen3 with validated typed-goal direct obligations; only if still unreliable, (c) identical stages with a larger approved local model. Do not change prompt/schema/model/budget simultaneously.
- Model size upgrade only with evidence of materially better repeated exact target binding and grounded client delivery within resource constraints. Don't claim `seed` deterministic if Ollama runtime does not guarantee it; log available settings. No arbitrary extra retries.
- If 4B suffices under corrected graph, keep it. If 4B fails where larger model succeeds with acceptable latency, submit separate model routing/compute choice through existing doc42 and owner; no unapproved cutover.

## 4. Implementation contract for Devin

**TASK_ID:** `DELIA-C3-E4-R4-TYPED-GOAL-EXECUTION-AND-MODEL-AB-CLOSURE-01`.

Reanchor HEAD/status, Project Instructions/.cursor, 16→50→17→49→51→52→21→20→25, docs 02/24/42, ADR58, 103, 219–225, this doc 226 and ledger. Verify phase/CP/RQ. Inspect existing contract consumers before changing implementation. Tests RED first.

**W1** Prove producer/consumer and trust boundaries for typed goal target refs; inspect actual authority-backed source identification, avoid root-code positional collision and all untyped text-derived IDs. If no legitimate target ref available, STOP precise contract gate, do not fabricate.

**W2** Implement minimal typed-goal reuse for simple multi-source compare, not a new planner: two distinct valid target READ obligations through existing capability discovery and execution; no gratuitous decomposition or foreign analytics. Preserve complex decomposition when genuinely needed.

**W3** Verify actual full source coverage and deterministic outcome on two complete real trees, with duplicate rows, hierarchy, units, different/same owner, partial/unavailable/denied, unknown and cross-user/injected context negatives; prove that correct target set, not raw `sources=3`, drives success.

**W4** Audit current ThreadPoolExecutor + LangGraph parity, ContextVars, provider/model shared access and deadline/call ledger under concurrency. Use existing graph fan-out when it proves equivalent and safer; otherwise retain proven bounded mechanics, no parallel scheduler competing with graph ownership. Preserve cancellation/authorization semantics.

**W5** Run bounded paired stage repeats on identical questions; only if necessary benchmark larger approved local model using the same source evidence/configuration. Collect per-stage logs, latency/tokens, actual success rates and failures. No blind timeout escalation/heartbeat as false remedy.

**W6** Run real authenticated Keycloak/Core/DAVI/Domain + Ollama Qwen3 E2E on final SHA: direct single-turn comparison, same-session `90260147`→`90260148`→compare, correction/clarification and unrelated sibling cases; >=5 repeated original & sibling if environment allows; full deterministic oracle, negative AuthZ and outcome. Client must receive grounded correct answer *before* effective gateway boundary with useful margin. Record all failures, not just successful run.

**W7** Full regressions, cleanup of duplicate local branches with symbolic deletion proof, docs/ledger, safe commit/push main. No production deploy, no permission changes, no frozen synthesis override.

## 5. Acceptance and abort conditions

PASS only if valid current-goal intent and typed verified target binding are reliable, required authorized READs genuinely execute, both requested sources match authoritative refs, deterministic comparison equals oracle, response is delivered to client under gateway/turn budget consistently and G04/G05/G07/G12 are all PASS on final SHA/config. Tests and negative AuthZ evidence must be independently reviewable. If a true frozen contract conflict is found, classify `ARCHITECTURE_DECISION_REQUIRED` and complete independent safe work. If unrecoverable model/hardware constraint remains after bounded A/B, classify `BLOCKED_WITH_EVIDENCE`, not acceptance.

**Expected terminal:** `FUNCTIONAL_ACCEPTANCE_CANDIDATE` only with mandatory outcomes; else precise `REWORK/INCONCLUSIVE`, exact failed stage, evidence, next owner decision. Production deployment prohibited.
