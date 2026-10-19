# 36 — I04 · Contextual Provider-Neutral Generalization · Implementation Evidence

**DATA:** 2026-10-19  
**TASK_ID:** `DELIA-C3-I04-CONTEXTUAL-PROVIDER-NEUTRAL-GENERALIZATION-01`  
**BASE_HEAD:** `2b00c576b940c3dc13b1aeb3396a38e13fd343e5`  
**DOC_NUMBER:** `36` (33–35 reserved for live L01–L06 / routing review / reliability decision)  
**AUTHORITIES:** [32](./32-i03-independent-nonregression-review-and-acceptance.md), README I04, ledger §6.273–§6.276  
**EXISTING_EQUIVALENT:** `YES` — `OperationalCapabilityOrchestrator` + `select_decision_path`  
**REUSE_DECISION:** `EXTEND` (one proven arguments-budget defect; no second planner)  
**I04_ACCEPTED:** `NO`  
**VERDICT:** `IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW`

## 1. Reuse gate

| Mechanism | Status |
|---|---|
| Orchestrator / typed goal / discovery / index / continuity | REUSE |
| Decision-path FAST/OPERATIONAL/REASONING | REUSE (telemetry + rule tests) |
| Foreign evidence / corroboration | REUSE (existing LOOP-02 + I04 holdout) |
| Specialist-name branches in planner | ABSENT (source hygiene test) |
| Parallel planner / registry / MCP catalog copy | NOT INTRODUCED |

## 2. Inventário contratual utilizado

- Typed capability + goal selection (existing).
- Owner discovery terminal classes (`CAPABILITY_NOT_MATCHED` / unavailable / not enumerable).
- `_prior_continuation_attempt` + `recover_invalid_index`.
- `_build_arguments` + `TurnDeadline` (`turn_budget_exhausted` vs `model_timeout`).
- Policy/Decision gates; MESSAGE-only live (`max_execution_stage=prepare`).
- MCP/A2A as interoperability surfaces only.

## 3. Generalization matrix (synthetic)

Suite: `delia-api/tests/test_i04_provider_neutral_generalization.py` — **17 PASS**.

| Scenario | Result |
|---|---|
| Renamed / non-MCP methodology READ | PASS |
| Capability order independence | PASS |
| Equivalent descriptions without specialist tokens | PASS |
| Discovery search-miss vs absence (HTTP provider) | PASS |
| Index no-match clarification | PASS |
| Continuity invalid-index recovery | PASS |
| Forged history never ACT | PASS |
| Multi-owner comparison | PASS |
| Owner unavailable truthful | PASS |
| Missing inputs clarify | PASS |
| Ambiguous write clarify | PASS |
| FAST / OPERATIONAL / REASONING rules | PASS |
| Singleton opaque schema ≠ auto FAST | PASS |
| Arguments budget → query projection | PASS (new) |

Full `delia-api` pytest: **PASS** (R1 concurrent suite parked outside tree).

## 4. Defect found in live characterization (pre-fix)

**K4 sample (runtime without args projection):** DAVI `discover_delpi_information` selected; `arguments` hit `budget_too_small` (remaining_ms≈52) → `turn_budget_exhausted` → `delpi_source_unverified` without owner invoke.

| Field | Value |
|---|---|
| session_id | `7ff45da3-6a27-40e9-a8ae-5e289946386e` |
| total_ms | 29959 |
| grounding | NON_GROUNDED / `delpi_source_unverified` |

**ROOT_CAUSE:** `_StageDeadlineExceeded(turn_budget_exhausted)` on arguments after correct selection propagated as SOURCE_UNAVAILABLE.

**FIX (minimal EXTEND):** `_single_free_text_argument_from_input` + catch only `reason == "turn_budget_exhausted"` in `_build_arguments` → project sole unconstrained string field from user text when schema-valid; else clarify. `model_timeout` remains terminal (LOOP-03R2A).

**NOT CHANGED:** no specialist-name `if`, no second planner, no experimental args-headroom production ON, no stage-cap 10, no ACT path.

## 5. Live (MESSAGE-only)

| Field | Value |
|---|---|
| MODEL | `moonshotai/kimi-k3` / `openai_compatible` |
| BUDGET / STAGE | 30 / 30 |
| K1 prompt sha256-8 | `2a8147e1` |

### Pre-fix sample (characterization)

| Case | ms | Result |
|---|---|---|
| K1 | 12995 | PASS GROUNDED (TÉO methodology) |
| K2 | 28857 | PASS continuity 5 bullets / no invented ACT |
| K3 | 22388 | PASS clarification |
| K4 | 29959 | FAIL arguments budget → source_unverified |

### Post-fix sample (deployed `37f4e21229`)

| Case | ms | session_id | Result |
|---|---|---|---|
| K1 | 18277 | `df0864c9-…` | **PASS** GROUNDED TÉO `get_methodology_guide` (corr. `d047be58-…`) |
| K2 | 10818 | `192df3bc-…` | **PASS** continuity 6 bullets / `prior_turn_evidence_only` / no owner reinvoke |
| K3 | 30028 | `30dd4afb-…` | **PASS_WITH_LIMITATION** VISTA INDEX→`no_match`→clarification `budget_fallback` (corr. `58244a59-…`) |
| K4 | 8768 | `9411ac97-…` | **FAIL** `select_capability decision=none` after `group=mcp:davi` (corr. `6afa51fe-…`) — **not** the args-budget path; same family as doc34 L06 / §6.276 R1 residual |

```text
SOURCE_SHA=37f4e21229ca9de80be3aa08f7261a1a081424aa
DEPLOYED_SHA=37f4e21229ca9de80be3aa08f7261a1a081424aa
MODEL_ID=moonshotai/kimi-k3
MODEL_PROVIDER=openai_compatible
CONFIG_FINGERPRINT=7042edd2bc100442
GLOBAL_TURN_BUDGET_SECONDS=30
MATERIAL_ACT_COUNT=0
ARGS_BUDGET_PROJECTION_LIVE_EXERCISED=NO (K4 failed earlier at select_capability none)
ARGS_BUDGET_PROJECTION_SYNTHETIC=PASS
```

### 5.1 Runtime config fingerprint

Computed inside `delpi-delia-api` over non-secret `DELIA_*`/`LLM_*`/`KEYCLOAK_*` env keys → sha256-16 `7042edd2bc100442`. Markers in image: `_single_free_text_argument_from_input`, `budget_input_projection`, `recover_invalid_index` = present.

## 6. Direct MCP comparison

`DIRECT_OWNER_TEST_NOT_RUN` from this executor for TÉO/VISTA/DAVI in the I04 window. DAVI owner contract remains as documented in [29](./29-i03-independent-davi-crosscheck-review.md) (generic discovery 0/95 miss vs catalog). Orchestrated live remains authoritative for I04 outcome.

## 7. Security / authority gates

Preserved:

```text
Keycloak = Identity
Core = Live AuthZ
Domain APIs = Final Business Authority
DÉLIA = Intelligence + Governance
MCP/A2A = Interoperability
```

Invariants exercised in suite: forged history ≠ ACT; ambiguous WRITE clarify; prompt-injection holdouts; discovery ≠ approval; MODEL_OUTPUT ≠ FACT; GUIDANCE ≠ DOMAIN_FACT.

## 8. Residuals (not closed by I04)

- §6.271 helpdesk personal ticket count / GLPI link — **separate**.
- Doc 34/35 R1 none-selection → 504 and R3 projection wording — **NEXT_RELATED**, not mixed into this diff.
- `ALGORITHM_COMPLETION` remains `PARTIAL` (telemetry ≠ completion proof).
- Independent review / live replay by coordination still required for `I04_ACCEPTED`.

## 9. Rollback

```text
git revert <IMPLEMENTATION_SHA>
```

## 10. State

```text
I04_IMPLEMENTATION=EVIDENCE_READY_FOR_REVIEW
I04_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=COORDINATION_INDEPENDENT_REVIEW
Q01_AUTHORIZED=NO
```
