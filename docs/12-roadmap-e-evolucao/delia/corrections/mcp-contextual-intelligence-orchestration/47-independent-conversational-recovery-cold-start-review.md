# 47 - Independent conversational recovery and cold-start review

Date: 2026-10-19. Reviewed main: 1a95344d545719523f0995acf667f93a1d1a5fed.
Sources: document 46, ledger section 6.288, implementation/live code SHA 3564f9ba74d5acdf1fc9defc38caf8bd506e6760.
Verdict: ACCEPT_WITH_RESIDUAL for bounded conversational and activity fix; REWORK for cold-start/full conversational user outcome.

## Verified in reported evidence

- Tagged selection distinguishes not_applicable, inconclusive and selected, and permits the existing conversational fallback when operational tools are not applicable.
- The model proposal now accepts applicable=false without requiring a remote capability identifier.
- Activity result count is omitted for paginated owner result with has_more=true, avoiding the misleading first-page count.
- Executor live samples: natural greeting 6657ms, role question 13668ms, conceptual SIPOC 20057ms, hypothetical examples 11003ms; full backend PASS reported, independent re-execution TEST_NOT_RUN, no ACT.

## Blocking gaps

1. Cold greeting A01 ended HTTP 504 when model group-selection stage lasted about 29s: FAIL user outcome, even though warm greetings succeed. Inspect existing decision path/handler for least-sufficient conversational admission. Do not add greetings keyword table or new planner, disable safety gates, or increase global deadline.
2. Real product queries and same-conversation clarification D01-D04 were TEST_NOT_RUN. Linked GLPI personal count remains an owner-contract gate; testing continuity alone does not require inventing that authorization.
3. Confirm genuine model timeout versus owner/source unavailability; preserve truthful error taxonomy and no irrelevant activity counts or source information for simple conversation.
4. Pre-register multiple cold and warm real-model runs, correlate timings and failures per SHA/config, measure task outcome and 30s hard limit, without selective retries.

## Decision

CONVERSATIONAL_FALLBACK_SCOPED=ACCEPT_WITH_RESIDUAL
ACTIVITY_PAGE_COUNT_FIX_SCOPED=ACCEPT_WITH_RESIDUAL
COLD_GREETING_USER_OUTCOME=FAIL
REAL_PRODUCT_USER_OUTCOME=TEST_NOT_RUN
CLARIFICATION_CONTINUITY=TEST_NOT_RUN
FULL_BACKEND=PASS_EXECUTOR_REPORTED
INDEPENDENT_LIVE_REPLAY=TEST_NOT_RUN
I04_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT_RELATED=DELIA-C3-COLD-CONVERSATIONAL-ADMISSION-AND-CONTINUITY-REWORK-01
