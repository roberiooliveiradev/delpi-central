# 43 — Independent R4/R5 review and pagination correctness gate

**DATE:** 2026-10-19. **REVIEWED CODE SHA:** `31a10b866956d3ac3ee3d80b5376f6430ca27095`. **SOURCE:** [42](./42-r4-r5-personal-ticket-count-and-pagination-remediation.md), ledger §6.284, `paginated_result_semantics.py` and R4/R5 orchestration diff. **VERDICT:** `REWORK` for R5 exact-count correctness; `ACCEPT_WITH_RESIDUAL` for R4 protective personal-scope gates. Independent runtime re-execution `TEST_NOT_RUN`.

## Evidence

- Existing Helpdesk BFF / TÉO owner preserved; no parallel Helpdesk. Ambiguous assigned/requested scope clarifies; unproven assignee/requester filter produces limitation. Page slice with `has_more=True` no longer claimed as total. Executor reports full backend PASS and 28 container tests PASS. Live SHA matches evaluated code, but model selection timed out before Helpdesk owner READ in all sampled L01 requests, with `linked=false`; linked-personal count `TEST_NOT_RUN` and business outcome `INCONCLUSIVE`.

## Code-level gaps requiring RED/GREEN

1. **Unsignaled pagination as complete aggregate.** `aggregate_paginated_pages()` marks `complete=True` when last page `has_more=None` with no duplicates, while `extract_pagination_envelope()` also accepts bare `items` without metadata. A partial first page may become a fabricated count. Require explicit last-page evidence or trusted owner total; unknown remains unknown.
2. **Non-first isolated page counted as a total.** `resolve_count_semantics()` returns `COMPLETE_AGGREGATE=len(items)` whenever `has_more=False`, even with `page>1`. A final page is not the whole query. Verify first-page continuity and same filters or return unknown.
3. **Pagination completeness and consistency.** Verify page sequence, stable unique IDs, owner total consistency, failed page handling, cap and snapshot changes. No merging of partial pages into authoritative total. Test `page_size` and `has_more` anomalies and a last-page result after incomplete traversal.
4. **Scope of new pure module.** Functions are in DÉLIA orchestration boundary and exposed to generic result envelopes; confirm they never interpret unrelated list/query data as Helpdesk personal identity. No model-generated `assignee_id` may count as proven identity; exact identity binding requires owner contract.
5. **Live latency:** all reported L01 cases ended at ~30s pre-owner. The issue is independent of R5 count logic; reanchor against I04 budget/selection rework. HTTP200/SOURCE_UNAVAILABLE is not successful task outcome.

## Bounded decision

- `R4_SAFE_PERSONAL_PROJECTION=ACCEPT_WITH_RESIDUAL` for the bounded protection only.
- `R5_EXACT_COUNT=REWORK` until unsafe un-signaled/last-page totals are corrected and independently evaluated. Synthetic 20-item aggregation is not sufficient on its own.
- `PERSONAL_COUNT_LIVE=INCONCLUSIVE`; linked account `TEST_NOT_RUN`; GLPI owner session ID/requester filter and projected total gaps are owned by Helpdesk BFF and require contract decision, not parallel logic.
- Retest R1/R2/R3/I03/I04, no material ACT, full backend, real model and SHA alignment. Avoid whole-project refactor and no new planner.

```text
REVIEW=REWORK_R5 / ACCEPT_WITH_RESIDUAL_R4
I03_ACCEPTED=YES_WITH_RESIDUAL
I04_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=R45_BOUNDED_PAGINATION_INTEGRITY_REWORK
```
