# DÉLIA — Coordination review: Qwen14B goal recovery and F2 decision

Date: 2026-11-19. Scope: C3/T2, INT-1 investigation continuity. This is a coordination **review and next bounded-step decision**, not phase acceptance, deploy authorization or implementation of F2.

## Authorities and baseline

- Current authorities: Project Instructions/AGENTS.md, Doc 16 (execution master plan), Docs 50/17/49/51/52/21/20/25, relevant INT-1/INT-2 contracts, execution ledger and the GitHub evidence at the delivered SHA. On conflict follow superior authority and return EXECUTION_DRIFT/ARCHITECTURE_DECISION_REQUIRED; do not silently redesign.
- Reviewed delivery: `DELIA-C3-T2-QWEN14B-GOAL-DECLARATION-RECOVERY-AND-F2-READINESS-01`, commit `1698b2edb005eb9365fae09a11e791c95ed131f3` (published on main, inspected by Coordination).
- Prior controlled A/B: `DELIA-C3-T2-QWEN14B-VS-KIMI-MULTITURN-CAUSAL-DIAGNOSIS-01`, commit `530d3307b17f0703abcce0b9cafc48a328864eb7`; frozen scenario and source traces at `docs/12-roadmap-e-evolucao/delia/evidence/ab-causal-diagnosis/`.
- Latest Qwen run: `docs/12-roadmap-e-evolucao/delia/evidence/goal-declaration-recovery/` (frozen scenario, run and turn-2 trace).
- No local worktree state is certified by this GitHub-only review. Executor must check its own git status, origin and leases prior to any diff.

## Independent Coordination decision

**REVIEW_VERDICT: ACCEPT_WITH_RESIDUAL**, restricted to the delivered bounded recovery contract. This does **not** mean the stock inquiry succeeded with Qwen14B.

- **PROVEN code change:** one production hunk in `delia-api/app/infrastructure/orchestration/pydantic_ai_investigation.py` changes the pre-invocation `ModelRetry` feedback. It now identifies the blocked call, states that no owner was contacted, requires `declare_investigation_goal` with `goal_class`, `expected_delivery`, `evidence_needed`, and explicitly forbids reissuing the blocked call until the goal is accepted. Goal gate and authorization semantics remain fail-closed, with no new planner/engine/provider. Existing equivalent YES; decision EXTEND.
- **Reported verification:** RED→GREEN, 15 gate tests, 92 + 135 consumer tests, zero reported regression failures; independent delpi-verifier r2 `ACCEPT_WITH_RESIDUAL` bound to SHA `1698b2edb0`, zero OCs. Verifier pytest itself `TEST_NOT_RUN` (environment); Coordination has not rerun the local suite.
- **Real Qwen14B outcome:** profile `openrouter_qwen`, `qwen/qwen3-14b`, one scenario/two LLM calls, ~149s, 1265 input/304 output tokens as reported. No `declare_investigation_goal` call; no selected stock capability; no owner invocation or stock evidence. End `NON_GROUNDED` with bounded, legitimate identifier-free clarification. **USER_OUTCOME_PROVEN=NO**, **QWEN14B_STOCK_TASK=FAIL**.
- **A/B prior outcome:** Kimi arm `moonshotai/kimi-k3` reached legitimate `get_product_stock` and authoritative READ evidence for material `10020003`, while Qwen arm failed at goal-declaration. This demonstrates scenario-specific model behavior difference, N=1 per arm, not statistical model superiority. Kimi final answer retained `declared_answer_unverified_values` / `declared_status_overridden` residual; owner evidence does not automatically validate every echoed claim.
- **Costs:** real provider cost was not reported; do not claim a demonstrated financial advantage or automatic provider switch.
- **Security and scope:** READ-only; AuthZ/Core/Domain ownership preserved. No production deployment of this recovery, no phase advancement and no automatic promotion of the two-agent split.

## Explicit C3/T2 decision and ordered work

1. **Close this Qwen14B feedback correction as ACCEPT_WITH_RESIDUAL.** Do not schedule another paid prompt trial by inertia; additional model-specific behavior changes require a separate bounded hypothesis and coordination decision. Qwen14B remains a low-cost evaluation baseline, not a proven complete stock-task executor.
2. **Authorize F2 as the next bounded coordination work package to prepare and implement only within the Doc 16/ledger scope**, contingent on fresh HEAD/lease/owner/contract inventory and its own testable RQ/AC: INT-1 continuity and pagination (`R2-CONTINUITY-PAGINATION`), convergence/no-progress/budgets, semantic capability selection, feedback of sufficiency and evidence-preserving continuation. Prefer a real 40+40+29 multi-page case, legitimate read-only A/R5/E/R6mt and negative holdouts, subject to the actual contract on HEAD. This coordination decision is not blanket authorization to refactor or run expensive external evaluation batches.
3. **Required F2 delivery:** minimal proven production diff (if defect is reproduced), RED/GREEN, negatives for scope/filters/identity/ownership, bounded budget, generalization + safety + task outcome at evaluated SHA/config, independent delpi-verifier and Coordination review. If no defect is proven, deliver evidence and a bounded decision, not cosmetic runtime edits. No invented LLM FACT or shortcut across Core/Domain authority.
4. **F3/F4/F5 remain queued, not implemented by this decision:** F3 responsibility INT-3 sufficiency/obligation demonstrability (evaluate need for a physical Agent separately); F4 cross-cutting security/generalization, including authorized restricted-identity R4/R6-N6/N7 proofs; F5 synthesis responsibility INT-4 and explicit architecture decision before any physical Agent. The current split remains experimental/OFF in production.
5. **Deploy and phase gates unchanged:** `PHASE=C3/T2`, `PHASE_ADVANCEMENT=NO`, `PRODUCTION_DEPLOY=NOT_AUTHORIZED` for this new work, `TWO_AGENT_PROMOTION=NOT_AUTHORIZED`, `INT3_INT4_AGENT_IMPLEMENTATION=NOT_AUTHORIZED`.

## Next bounded step

`COORDINATION_C3_T2_F2_INT1_CONTINUITY_PAGINATION_CONVERGENCE_EXECUTION_BRIEF`

The F2 executor must reanchor current HEAD/status, Project Instructions and .cursor, Doc 16→50→17→49→51→52→21→20→25→technical/product/thematic contracts→ledger; prove owner/equivalent/reuse; identify relevant CP/RQ; do the minimum demonstrated diff; test/evaluate; run the independent verifier before its execution report and any authorized commit. Any material premise contradiction is STOP / EXECUTION_DRIFT, not silent redesign.

**Evidence classification:** code feedback `PROVEN`; deterministic tests `PASS (reported)`; independent verifier `ACCEPT_WITH_RESIDUAL (reported)`; Qwen grounded stock outcome `FAIL`; F2 implementation `PENDING`; phase advancement `NO`.
