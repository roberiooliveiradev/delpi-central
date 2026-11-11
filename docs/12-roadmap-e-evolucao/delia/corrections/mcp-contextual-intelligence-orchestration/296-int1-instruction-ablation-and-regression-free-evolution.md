# 296 — INT-1 instruction ablation and regression-free evolution

**TASK_ID:** `DELIA-C3-T2-INT1-INSTRUCTION-ABLATION-AND-REGRESSION-FREE-EVOLUTION-01`  
**PO_BOUNDED_AUTHORIZATION:** YES (2º ciclo delimitado)  
**DEFAULT_VERSION:** `generalist-semantic-v2` (unchanged)  
**FINAL_CANDIDATE:** NONE (not composed)  
**PROMOTION_RECOMMENDATION:** DO_NOT_PROMOTE  
**INT1_STAGE_ACCEPTANCE:** BLOCKED  

## 1. Diff groups (v2 → v3)

| GROUP_ID | Cognitive responsibility | Expected benefit | Possible regression |
|---|---|---|---|
| G-OBJ | Objective + evidence-kind framing; compare description↔schema↔shape; expanded mismatch (incl. structure vs catalog) | Better capability match (P3/G1/H4) | Steer “estrutura/árvore” to wrong hierarchy owner; over-filter P2 |
| G-PROG | “New info ≠ progress”; continue only if legitimate path | Recover from related-insufficient (G1) | Extra calls; wrong-owner chase; GROUNDED with wrong evidence |
| G-DISC | Discovery before incompatible call; published error-kind recovery | Avoid 422 loops (P3) | Premature clarification; discovery-only dead-ends |
| G-EFF | Avoid redundant discovery/spend (v3-only) | Efficiency | **NOT_EVALUATED** (budget) |

Reformulations of existing v2 bullets (examine contracts carefully; shorter validation hint) were **not** ablated separately.

## 2. Ablation variants

| Variant | Fingerprint | Group |
|---|---|---|
| `generalist-semantic-v2` | `7dbc94c5035b0f19` | baseline |
| `generalist-semantic-ablation-obj-v1` | `d455ef41408ccdea` | G-OBJ |
| `generalist-semantic-ablation-prog-v1` | `7d38c1237ea79909` | G-PROG |
| `generalist-semantic-ablation-disc-v1` | `30d80637559e6ec8` | G-DISC |

Prior full candidate `generalist-semantic-v3-objective-progress` / `658d3da51783e23d` retained as historical artifact (not default).

## 3. Cost ceiling (pre-declared)

```text
max_arms=4
max_scenarios_per_arm=5 (P1,P2,P3,G1,H4)
max_repetitions=1
max_scenario_runs=20
max_wall_seconds=2700
tokens/cost=UNAVAILABLE (meter null; not presumed zero)
```

Executed 20/20 scenario runs. `PROD_UNTOUCHED=YES`. Egress allowlist OpenRouter. Credential residual unchanged (shared infra key scope).

**EVALUATED_SHA (host):** `5220eef522b4ca250dae2db78741beeb586a24da`  
**MODEL:** `qwen/qwen3-14b` / `openrouter_qwen` / pydantic-ai `2.50.0` / config fp `b42a0da3f3be8154`

Local evidence: `delia-api/.battery/int1-instruction-ablation/ablation-comparison.json` (gitignored).

## 4. Diagnostic matrix (this run)

| Scenario | v2 | OBJ | PROG | DISC |
|---|---|---|---|---|
| P1 | G / davi:get_context / BOM | G / davi:read / BOM | G / davi / BOM (more calls) | G / davi / BOM |
| P2 | G / teo:read | **N** | G | G |
| P3 | G / vista:read (weak playlist-shaped head) | **N** / limit | G but **wrong evidence** (dashboard metrics) | **N** / clarification |
| G1 | G / teo:read → BOM | G / **davi:get_context** → BOM | G / **davi:get_context** → BOM | G / teo:read → BOM |
| H4 | G / teo:analyze | G / teo:analyze | G / teo:analyze | G / teo:analyze |

**Stochasticity note:** In this diagnostic run, baseline already GROUNDED P3/G1/H4. Therefore prior doc-295 claims that “v3 improved P3/G1/H4 vs v2” are **not stable causal proofs** across runs; treat as historical observation only.

## 5. Classification

| Group | Class | Evidence |
|---|---|---|
| G-OBJ | **REGRESSION_ASSOCIATED** | P2 NON_GROUNDED; P3 NON_GROUNDED + tool-limit |
| G-OBJ / G1 first-tool | **PROMISING_BUT_INCONCLUSIVE** | davi-first on G1 (1 rep; baseline also obtained BOM) |
| G-PROG | **REGRESSION_ASSOCIATED** | P3 GROUNDED with TEO dashboard metrics (objective fail) |
| G-PROG / G1 first-tool | **PROMISING_BUT_INCONCLUSIVE** | davi-first (same caveat) |
| G-DISC | **NO_DEMONSTRATED_BENEFIT** / P3 **REGRESSION_ASSOCIATED** | P3 clarification; no unique gain vs v2 |
| G-EFF | **NOT_EVALUATED** | Outside 3-group budget |

**SUPPORTED_IMPROVEMENT:** none at promotion strength.

Preserved as versioned experimental artifacts (not activated): all ablation variants + prior v3 remain in `investigation_instructions.delpi.json` for future review.

## 6. Final composed candidate

**Not built.** No sustained, regression-free gain package justified composition under task criteria.

Default remains `generalist-semantic-v2`.

No final A/B of a composite vs v2 (would be speculative). New independent cases deferred with the composite.

## 7. Revision of doc 295

Doc 295’s candidate `v3-objective-progress` remains **DO_NOT_PROMOTE**. Ablation shows its gains were not isolable as safe additive groups; several themes correlate with P2/P3 failures. Do not silently discard the experiment — keep fingerprints and traces references.

## 8. Architecture bound

No Agent/AuthZ/MCP/Evidence/Outcome code changes. Remaining hard defects (stable objective obligations, wrong-evidence GROUNDED) may need INT-2/INT-3 — **not authorized**.

## 9. Status

```text
INT1_STAGE_ACCEPTANCE=BLOCKED
INT1_CLOSED=NO
INT2_AUTHORIZED=NO
T3_AUTHORIZED=NO
PRODUCTION_DEPLOY=NOT_AUTHORIZED
NEXT=COORDINATION_INT1_INCREMENTAL_EVOLUTION_INDEPENDENT_REVIEW
```
