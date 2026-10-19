# 40 — R2 · Provider-neutral capability selection quality

**DATA:** 2026-10-19  
**TASK_ID:** `DELIA-C3-R2-PROVIDER-NEUTRAL-CAPABILITY-SELECTION-QUALITY-01`  
**AUTHORITIES:** doc 35 (R2 gated); docs 38–39 R1/R3; docs 27–32 I03; ledger §§6.279–6.280  
**EXISTING_EQUIVALENT:** `YES`  
**REUSE_DECISION:** `EXTEND`  
**I03_ACCEPTED:** `YES_WITH_RESIDUAL` (unchanged)  
**I04_ACCEPTED:** `NO`  
**C3_EXECUTED:** `NO`  
**Q01_AUTHORIZED:** `NO`

## 1. Root cause (PROVEN)

```text
USER coverage inquiry
 → select_group = mcp:davi (OK)
 → select_capability model → applicable=false / invalid remote_name
 → _select_target = None
 → CLARIFICATION_REQUIRED (R1)   # never invokes DISCOVERY
 → I03 zero-candidate terminal NEVER RUNS
 → USER_TASK_OUTCOME = NOT_SATISFIED
```

Owner direct discovery still returns `eligible_action_count>0` with `candidate_count=0` — surface exists; orchestrator failed **before** owner READ/DISCOVERY.

Classification: `MODEL_SEMANTIC_MISS` on stage-2 applicability for coverage inquiry, with a **contract-proven** recovery path available (sole `DISCOVERY` on the already-selected group).

## 2. Implementation (minimal EXTEND)

| Change | Detail |
|---|---|
| Selection instructions v12 | Coverage inquiry → select listed `operation_class=DISCOVERY` when present; never answer catalog from model knowledge |
| `_capability_payload` | `role=owner_vocabulary_discovery` derived only from `DISCOVERY` class |
| `_is_information_coverage_inquiry` | Bounded PT/EN detector; excludes methodology checklist follow-ups |
| `_select_target` recovery | When capability proposal fails **and** coverage inquiry **and** `_discovery_capability(group)` is unique → select that DISCOVERY (not arbitrary singleton) |

Not created: second planner, registry, DAVI hardcode, auto-select of any singleton, new public DTO, ACT path.

## 3. Tests

`test_r2_provider_neutral_capability_selection_quality.py` R2-T01–T17 + R1/R3 holdouts.  
Regressions: I01/I02/R3B/ACR/I03/I03-nonreg/I04/specialist + **full `delia-api` pytest PASS**.

## 4. Live (MESSAGE-only)

**SOURCE_SHA = DEPLOYED_SHA = `19843e5cf9f5684f52124f0df25ae8d131b6bb35`**  
**MODEL:** `openai_compatible` / `moonshotai/kimi-k3`  
**BUDGET/STAGE:** 30 / 30 · **ACT:** 0

| Case | HTTP | ms | Result |
|---|---|---|---|
| **K4-A** broad | 200 | 16118 | **PASS** — `davi.discover_delpi_information` GROUNDED; I03 `eligible=95` search-miss honesty; corr `d4ddc761-…`; **not** generic R1 |
| **K4-B** thematic products | 200 | 26163 | PASS_WITH_LIMITATION — selected `openapi:delpi.search_products` then bounded ask-back for location fields (no invented facts) |
| **K4-C** no-match | 200 | 30019 | PASS_WITH_LIMITATION — budget edge + source unverified (honest); not false catalog absence |
| **L02** | 200 | 3560 | **PASS** R1 clarification; no 504 |
| **L03** | 200 | 16734 | **PASS** GROUNDED `teo.get_methodology_guide` corr `50b7657c-…` |
| **L04** | 200 | 15420 | **PASS** R3 `Recuperei 8 itens da orientação anterior` |
| **L05** | 200 | 21969 | **PASS** safe VISTA clarification |
| **L01** | 200 | 10432 | **PASS** routing + `glpi_link_required` precondition preserved |

## 5. Residuals

| Item | State |
|---|---|
| R2 thematic model quality without recovery | OPEN (instruction-aided) |
| I04 global | `NO` / REWORK |
| Helpdesk GLPI | SEPARATE |
| Q01 | NOT AUTHORIZED |

## 6. Rollback

```text
git revert <this-sha>
```

## 7. Next

```text
NEXT=COORDINATION_INDEPENDENT_REVIEW
I04_ACCEPTED=NO
C3_EXECUTED=NO
Q01_AUTHORIZED=NO
```
