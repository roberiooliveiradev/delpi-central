# 49 - Independent review of semantic-intelligence full-recovery execution

Date: 2026-10-19. Main/code reviewed: bc4c91856382f050befacf628ad87e6e13c1b749. Execution document: 48; ledger 6.290. Verdict: ACCEPT_WITH_RESIDUAL for bounded cold conversational admission; REWORK for full semantic intelligence, argument handling and generalization. Independent live SSH replay TEST_NOT_RUN.

## Evidence
- Interaction admission uses existing typed LLM proposal with bounded 6s stage before provider discovery for cold turns and NOT_APPLICABLE for conversation. Executor live A01 6.5s, A02 3.7s, B01 SIPOC 12.7s; no material ACT reported.
- Source/DEPLOYED reported matching final SHA bc4c918563, but document 48 still names prior SHA 3fd1230a7b: reconcile release/eval correlation and post-commit final copy, without claiming independent deployed proof.
- Admission is skipped when prior_turns exist, so successful multi-turn continuation is not demonstrated by the admission tests alone.

## Architectural deviation requiring bounded rework
- The newly introduced _recover_stated_arguments_from_input contains _STATED_SEARCH_FIELD_HINTS, _STATED_LIMIT_FIELD_HINTS, and _STATED_QUANTITY_RE for extracting a number from free-form user language; this is heuristic interpretation in tension with user direction to rely on LLM semantic interpretation rather than phrase/regex intent extraction. Deterministic validation of typed model-proposed schema arguments remains mandatory.
- Example adversarial prompts: compare 3 items with 5 attributes, product series 2026 and give 3 examples, show issue 1350 among top 5. Do not assert actual regression without RED/live proof.
- The recovery injects the entire user text into a search-like argument and extracts first small integer as limit. It may preserve text poorly, causing semantically invalid searches even if schema-valid. Requires contract/outcome eval.
- Admission adds an LLM call for new operational turns; production sample C01 under load still ran near 30 seconds and required a clarification fallback. Cold/warm and concurrent n>1 performance must be measured and staged against the same model/config.
- Broad consumer/product outcome remains PARTIAL and linked personal count TEST_NOT_RUN; generalization evidence limited to one synonym greeting, insufficient for global acceptance.

## Decision
COLD_ADMISSION_SCOPED=ACCEPT_WITH_RESIDUAL
SEMANTIC_ARGUMENT_RECOVERY=REWORK
PRODUCTION_FULL_TASK_OUTCOME=INCONCLUSIVE
INDEPENDENT_LIVE_REPLAY=TEST_NOT_RUN
FULL_BACKEND=PASS_EXECUTOR_REPORTED
I04_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=BOUNDED_SEMANTIC_ARGUMENT_GENERALIZATION_AND_OPERATIONAL_LOAD_REWORK

No new planner or parallel classifier; reanchor superior authorities; use LLM for meaning, validate typed output deterministically, preserve owner contracts and authz.
