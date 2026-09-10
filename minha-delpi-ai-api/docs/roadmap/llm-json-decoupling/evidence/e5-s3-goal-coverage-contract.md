# E5.S3 — Goal coverage contract

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** E (plano 05)  
**Owner:** `ChatGoalCoverageService`  
**Harness:** `tests/unit/domain/services/test_e5_s3_goal_coverage_contract.py` (+ regressão `test_chat_goal_coverage_outcome.py`)

## Veredito

```text
GOAL_COVERAGE_CONTRACT = PASS
EMPTY_PAYLOAD = needs_more_data
PARTIAL_PAGINATION = partial (facts/metadata)
SIBLING_SCHEMA = fulfilled sem path authority
UNKNOWN_API = whenNotToUse/whenToUse (não path)
BLOCKED = goal.status | 401/403 | blockReason
```

## Outcomes canônicos

| Status | Quando |
|--------|--------|
| `fulfilled` | HTTP ok + payload não-vazio + sem mismatch + sem truncamento |
| `partial` | HTTP ok + dados presentes + paginação/truncamento em facts (`total>shown`, `hasMore`, `dataCoverageNotice.kind`) |
| `needs_more_data` | HTTP ok + payload vazio (`emptyPayloadNotFulfilled`) |
| `blocked` | `ActionPlanGoal.status=blocked` ou execução 401/403 / `blockReason` |
| `mismatch` / `failed` / `pending` / `planned` | preservados (capability / HTTP fail / sem evidência / pré-execute) |

`complete=true` somente se **todos** os goals estão `fulfilled` (parcial/bloqueado/needs_more_data não fecham o turno).

## Invariantes

- Decisão por **result metadata/facts** e guidance OpenAPI (`whenToUse` / `whenNotToUse`), **não** por path literal.
- Flag content: `openapi_tool_routing.goalCoverage.partialPaginationEnabled`.
- Report expõe `partialGoalIds` / `blockedGoalIds` / `needsMoreDataGoalIds`.

## Próximo

**E5.S4** — planner-driven enrichment (extra action só entre allowed; budget; sem auto-fan-out por entity list).
