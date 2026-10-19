# 51 — Independent review of SEMARG rework

**DATE:** 2026-10-19. **REVIEWED CODE SHA:** `43b577bd4b`. **EXECUTOR FINAL DOCS SHA:** `aa13257ab489e99c39c163d4c3629a11765b7a00`. **MAIN AT REVIEW:** `d7d262db8211db4d2eff5778432d1de3db4f24dd`. **SOURCES:** [50](./50-semantic-argument-and-task-outcome-rework.md), GitHub implementation diff, ledger §6.292. **VERDICT:** `ACCEPT_WITH_RESIDUAL` for removing heuristic argument parsing and fabricated clarification; `REWORK` for operational catalog task outcome, latency, and untested continuity. Independent live replay `TEST_NOT_RUN`.

## Code-level observations

- Confirmed deletion of `_recover_stated_arguments_from_input`, `_STATED_QUANTITY_RE`, `_STATED_SEARCH_FIELD_HINTS`, `_STATED_LIMIT_FIELD_HINTS`. The existing LLM argument proposal and schema validation remain. This removes one artificial linguistic interpretation path.
- `_clarification_content` no longer quotes the request with invented 'código/filtro/escopo' wording. Under the known budget skip, the orchestration now returns `SOURCE_UNAVAILABLE` with `turn_budget_exhausted`. That is honest taxonomy, **not** a completed user task.
- `interaction_admission` instruction steers illustrative examples toward `hypothetical`. Current patch includes examples of wording in instruction, but no new regex for the P01 case; semantic generalization still needs holdouts.
- Test `SEMARG-T01` and `SEMARG-T03` assert absence of code strings/functions, not successful semantic interpretation. Combined with executor live P01/P02, this supports the narrow correction but does not prove a general argument solution.

## Executor-reported live results

| Case | Result | Review |
|---|---|---|
| P01/P02 illustrative terminal pino | 11.8s/14.9s results | `PASS_EXECUTOR_REPORTED` for illustrative goal only |
| P03/P05 real registered products | `SOURCE_UNAVAILABLE` | `FAIL_TASK` |
| P06/P07 contextual number/year | `SOURCE_UNAVAILABLE` at 30014ms | `FAIL_TASK_AND_BUDGET` |
| P08 terminal olhal list | `SOURCE_UNAVAILABLE` | `FAIL_TASK` |
| P09/P10 illustrations/concept | response | `PASS_EXECUTOR_REPORTED` |
| Cold greeting | 5.3s | `PASS_EXECUTOR_REPORTED` |
| Multiturn continuity | not run | `TEST_NOT_RUN` |

Full backend pytest PASS and ACT=0 reported, not independently rerun. Recorded live code SHA `43b577bd4b`; docs final SHA differs and is not the evaluated runtime. User-facing exact product records remain unproven.

## Next gate

Do **not** add regex or another planner. Prioritize a bounded end-to-end **real product owner-read** investigation: use already accepted capabilities, capture LLM stages and budgets, compare direct owner contract/response to DÉLIA selection/arguments, then correct only proven latency/context/projection failure. Require source-authenticated product query PASS, strict 30s, holdouts with multiple numbers, renamed/non-MCP provider, continuity D01–D04, security 0 ACT, and exact deployed SHA/config. If legitimate owner search contract is missing, `ARCHITECTURE_DECISION_REQUIRED`; no DELIA shadow product catalog.

```text
SEMARG_HEURISTIC_REMOVAL=ACCEPT_WITH_RESIDUAL
SEMARG_FALSE_CLARIFICATION=ACCEPT_WITH_RESIDUAL
REAL_PRODUCT_TASK_OUTCOME=REWORK
GENERAL_SEMANTIC_INTELLIGENCE=INCONCLUSIVE
MULTITURN_CONTINUITY=TEST_NOT_RUN
INDEPENDENT_LIVE_REPLAY=TEST_NOT_RUN
I04_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=BOUNDED_LIVE_PRODUCT_OWNER_READ_AND_BUDGET_REWORK
```
