# 08 — Revisão arquitetural independente da Etapa 02 — REWORK

**Task:** DELIA-C3-CONVERSATIONAL-INTELLIGENCE-GAP-CLOSURE-01-STAGE-02-INDEPENDENT-REVIEW
**Data:** 2026-10-16
**Reviewed implementation SHA:** `4a9f05e5b9bd2b40332638d5bec49678de050bdd`
**Review remote HEAD:** `b7a1e4b6db8f2362a673c68f2db751e17400ccce` (contém commit Stage02 e depois commit helpdesk sem mudança delia-api; working tree local NÃO verificada)
**VERDICT:** `REWORK` — implementação parcialmente correta, com dois bloqueios de fidelidade à intenção e governança de escrita. **No production tests executed by this independent review; pytest 1078/1078 is executor-REPORTED.**
**MODE:** static contract/code/test review of published GitHub SHA; no production diff, no writes, no deployment.

## 1. Authorities / invariants

Read/revalidated applicable parts of Project Instructions/.cursor, 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → 02 → 24 → 60 + personality/02 + ledger §§6.126/6.130/6.133/6.140/6.141/6.145/6.171/6.172/6.173, and correction-plan files 02/03/05/06/07.
Preserve DÉLIA standalone and its sole provider-neutral OperationalCapabilityOrchestrator; MCP tools/list owner-owned, resolver bounded, PREPARE != ACT, structural owner-sealed confirmation requirement, live Core/AuthZ/Domain and Policy/Decision; model proposals HYPOTHESIS; MODEL_AUTHORED_FACTUAL_PROSE=NONE. No second planner, local MCP catalog, per-provider logic, user-claim-based authority or universal confirmation.

## 2. What the reviewed implementation genuinely accomplished

- `orchestration.py`: selection instruction v7→v8; goal instruction clarifies information-seeking vs action-seeking; `goal.declared`; deterministic gate after `_understand_goal` for **declared non-action** + selected write class; one bounded reselection on same-owner non-write surface, or `CLARIFICATION_REQUIRED` for declared ambiguity. Reuses existing components; no new engine/catalog.
- Goal selection still occurs after initial target selection, and the new gate sits before PREPARE; this is a legitimate incremental correction **for the validated and correctly classified goal case**.
- Nine new fakes/scripted S2 tests and write-fixture updates. Full `delia-api` suite 1078/1078 PASS **reported by executor; independent reviewer did not rerun**. Positive/negative, rename and multi-turn test intentions reviewed in diff.

## 3. Blocking findings

### B1 — Unknown/uninterpreted intent still reaches write path (PROVEN in code + committed test)

`_attempt`: compatibility gate is conditional on `descriptor.operation_class in _WRITE_OPERATION_CLASSES and goal.declared and goal.goal_class != 'create_or_modify'`. `_TurnGoal` defaults `declared=False` when a model goal proposal is absent. For this case the write target is not reconciled, despite no positive evidence of requested action.
Committed test `test_s2_uninterpreted_goal_preserves_governed_write_path` intentionally asserts a PREPARE owner invocation for user input **'Você consegue criar?'** with absent GOAL proposal. This is an ability/information question, not sufficient evidence of a change request. A PREPARE potentially continues to ACT under owner-declared `explicit_user_confirmation=false` if the applicable request ceiling does not prevent it.
**Classification:** confirmed structural counterexample; real-model occurrence frequency / real ACT outcome = TEST_NOT_RUN. Availability fallback cannot silently grant progression to a write class. Need an intent-compatibility rule that handles uninterpreted/invalid goal safely through the existing boundary (clarify or another demonstrably safe path), while allowing legitimate writes when evidence is adequate. Do not simply require confirmation for every owner.

### B2 — The user-provided 'prepare but do not apply' ceiling is not proven (PROVEN coverage gap + conditional runtime path)

`test_s2_prepare_only_request_stops_at_confirmation` uses `confirmation_requirement.explicit_user_confirmation=True`. This proves ACT does not occur when the **owner itself** requires additional confirmation; it does NOT prove the user-text restriction 'Prepare ... mas não aplique' survives an owner proposal with `explicit_user_confirmation=False`.
`OperationalCapabilityOrchestrator._attempt` calculates `prepare_only = (max_execution_stage == 'prepare')`, supplied by `InteractiveTurnRequest.max_execution_stage`. Neither the goal_class `create_or_modify` nor goal.scope_constraints currently enforces a reduction-only 'prepare' ceiling from the text of the current request. With request ceiling None and owner confirmation=false, `_attempt_prepare` has a direct governed continuation to ACT. Therefore user explicit 'não aplique' has no demonstrated operational enforcement.
**Classification:** test coverage gap proven, possibility of ACT by code path conditional; actual unwanted ACT with real provider = TEST_NOT_RUN. The rework must test this combination, prove an invariant that preserves user-requested PREPARE!=ACT using existing ceilings/gates, or flag ARCHITECTURE_DECISION_REQUIRED if current contracts cannot carry that bound. Never change the owner confirmation policy to patch this.

## 4. Additional residuals (not separate blockers)

- Wrong positive `goal_class=create_or_modify` on a guidance question can still reach PREPARE (existing test `test_ci01_hazard_guidance_question_can_reach_prepare` intentionally preserves the counterexample); instruction wording alone does not enforce truthful semantic intent. Add holdout/misclassification tests and classify real-model risk accurately.
- Selection instruction states ACT only after explicit confirmation, but the frozen §6.140 permits direct governed ACT when the owner seals no additional confirmation. Align the instruction with existing policy; do not modify policy or promise universal confirmation.
- No dedicated real-model, tokens/latency or OpenAPI provider eval in this review; +0/+1 LLM call reported, not independently measured. 1078/1078 code PASS cannot imply task outcome PASS.
- An unknown `goal_class` within a proposal is coerced to `read` and `declared=True`; an absent proposal becomes `declared=False`. Review semantic consistency and availability/safety tradeoff instead of treating these as equivalent confidence states.

## 5. Required bounded rework and tests

R2-01: reproduce RED for **'Você consegue criar?'** plus no validated goal and selected PREPARE; assert zero PREPARE/ACT and bounded, understandable clarification; prove a positive explicit action request still follows the existing owner governance, with no new planner/engine or per-provider hardcode.
R2-02: reproduce RED for **'Prepare um cadastro, mas não aplique'** with a valid `create_or_modify` proposal, selected PREPARE, `max_execution_stage=None`, owner READY with `explicit_user_confirmation=false`, a fake ACT tool and write continuation. Assert zero ACT; compare with the explicit request-scoped `max_execution_stage='prepare'` case and normal unqualified explicit action case. Correct through an existing reduction-only boundary; no universal confirmation / no Domain or owner policy duplicate.
R2-03: preserve provider/tool-rename, read/guidance, negative/ambiguous, multi-turn, UNKNOWN, reclassification and candidate security tests; do not weaken prior assertions or adjust fixture to hide a counterexample. Same pattern existing FakeProposalModel; verify no masking `_generic`/`_last`.
R2-04: execute targeted and full tests, security evals, and real-model eval only in approved read/controlled environment; classify actual results with SHA/config/model/provider/policy/dataset. No material ACT test against real owner; fakes only.

## 6. Reuse Gate, scope and decision

EXISTING_EQUIVALENT=YES: same OperationalCapabilityOrchestrator, `_understand_goal`, `_select_capability`, structured goal, CLARIFICATION_REQUIRED, reduction-only `max_execution_stage`, Policy/Decision and owner confirmation gates, test harness. REUSE_DECISION=EXTEND for minimal contract-aligned correction, conditional on proving the two blockers. If a semantic or contract change is material or exceeds bounded Stage 02: STOP/ARCHITECTURE_DECISION_REQUIRED instead of redesigning.

**Formal verdict:** `REWORK`. `STAGE_02_ACCEPTED=NO`. Stage 03 remains PLANNED / NOT_AUTHORIZED; do not advance C3, C4 or C5. Runtime/code not changed in this review. All references are to the published GitHub artifacts; no local test or git status evidence was obtained by reviewer.

**NEXT:** RETURN_TO_ARCHITECTURE_COORDINATION → approve specific Stage-02R1 task → independent retest/review. Preserve original report `07` as execution evidence, do not rewrite it.