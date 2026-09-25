# VISTA DISPLAY FORMAT BRIDGE EXECUTION REPORT

## BASELINE

BASE_HEAD: `9c09df606dbb738131404054c8b380381273f70f`
BRANCH: `main`
WORKING_TREE: unrelated Davi, Helpdesk, generated API catalog and `tsbuildinfo` changes were present and preserved.
FINAL_HEAD: recorded after the isolated task commit.

## ROOT CAUSE REVALIDATION

The GPT `upsert_block` contract exposed legacy `format` on text bindings but omitted the canonical `DisplayFormatSpec` properties. The compact `blockIndex` identified blocks without exposing each binding's persisted format. The backend renderer already consumed `dataRef.displayFormat` and `textProjection.displayFormat`, so this was a write/read contract gap, not a React formatter defect.

## OWNER CHAIN

| Layer | Authority |
|---|---|
| Editor | `NumberFormatSection` and `displayFormatSelection` author canonical specs |
| PresentationMutation | `set_display_format` resolves a semantic text binding and changes only its format |
| DisplayFormatService | validates presets and materializes `display*` |
| VISTA | reads/copies a spec and sends typed PREPARE/ACT intent |
| MFE | paints backend materialized display |

## DISPLAY FORMAT SPEC

The product type is `{category, presetId?, decimalPlaces?, useThousandsSeparator?, currency?, pattern?, locale?}`. `locale` is `pt-BR`; `currency` is `BRL`. The backend's existing `_PRESETS` and `format_catalog_entries()` provide presets. GPT `displayFormatCatalog` is a projection of those entries, not a second preset list. New writes reject unknown category/preset, mismatched category/preset, unsupported locale/currency and empty custom pattern.

## FORMAT OWNER INVENTORY

| Target | Persisted location | Read projection | Write path | Status |
|---|---|---|---|---|
| Text, heading, shape run | `contentRuns[].dataRef.displayFormat` | `formatBindings` | `set_display_format` | Integrated |
| Text, heading, shape projection | `textProjection.displayFormat` | `formatBindings` | `set_display_format` | Unit tested |
| KPI default | `kpiOptions.displayValueFormat` | unavailable | editor | Typed VISTA target pending |
| KPI metric | `kpiProjection.metrics[].displayFormat` | unavailable | editor | Typed VISTA target pending |
| Chart value/category | `chartOptions.displayValueFormat` / `displayCategoryFormat` | unavailable | editor | Typed VISTA target pending |
| Table default/column | `tableOptions.displayValueFormat` / `tableProjection.columns[].displayFormat` | unavailable | editor | Typed VISTA target pending |
| Canvas cell/dataRef | `cells[][].displayFormat` / `cells[][].dataRef.displayFormat` | unavailable | editor | Typed VISTA target pending |
| Native screen | native screen display contract, no confirmed canonical `DisplayFormatSpec` slot | unavailable | none | Not established as a spec owner |

Legacy `dataRef.format`, `textProjection.format`, and `valueFormat` remain compatibility inputs. They are not a full `DisplayFormatSpec`.

## BEFORE CONTRACT

`upsert_block` advertised legacy format fields but not the full canonical text binding spec. `blockIndex` omitted binding formats. VISTA could change bindings and revision without proving a format change.

## AFTER CONTRACT

`set_display_format` targets `{blockId, target:{owner, field, occurrence?}, displayFormat}`. `owner` is `contentRunDataRef` or `textProjection`; `occurrence` is zero based and required only for repeated matching fields. `upsert_block` now documents `displayFormat` on text binding structures. `blockIndex.items[].formatBindings[]` exposes persisted owner/field/occurrence/spec, including in `objectMatches`. `gpt_get_catalog.displayFormatCatalog` lists backend owned presets.

## TYPED OP

`set_display_format` goes through catalog validation, plan compiler, PresentationPatchService, HTTP command planner, GPT preview, and GPT commit. Missing and ambiguous bindings fail closed with `DISPLAY_FORMAT_TARGET_NOT_FOUND` and `DISPLAY_FORMAT_TARGET_AMBIGUOUS`; unsupported owners and invalid specs use `DISPLAY_FORMAT_UNSUPPORTED_TARGET` and `DISPLAY_FORMAT_INVALID`. It never creates a block. It clears stale `resolved` and preserves unrelated content, styles, geometry and bindings.

## COMPACT READ

`formatBindings` is built from persisted block config only. No `resolved` or full runs are returned. An editorFocus payload with 70 formatted blocks returned all 70 items and measured 23,588 bytes in the one-binding fixture, below 102,400. A two-binding 70-block fixture also passed the budget test. Existing pagination remains available.

## REAL WEG REGRESSION

A server-side WEG SC → WEG ES fixture copied the SC canonical spec through `gpt_preview_change` and `gpt_commit_change`, reread ES through `gpt_get_playlist_context(scope=editorFocus)`, and enriched display. The WEG date fixture covers year, numeric month/year and abbreviated month/year. A sibling numeric-field fixture covers number, currency and percent through the same GPT Actions chain. A separate 16-label mutation on a 70-block fixture preserved exactly 70 block IDs. No authenticated deployed WEG dashboard was exercised.

## MATERIALIZATION PROOF

`filter.end_date=2026-09-24` with `date-year` produced `2026`; `date-month-year` produced `09/2026`; `date-month-abbrev-year` produced `set./2026`. The backend also produced number, currency and percent displays in GPT Actions integration tests. Null/invalid runtime values fail convertibility and cannot satisfy the targeted VERIFIED check.

## PROPERTY PRESERVATION

The mutation changes only the selected `displayFormat` and drops stale `resolved`. Tests compare the full block before/after, including other runs, `dataRef.field`, legacy `format`, frame and style. Ambiguous repeated fields cause no write until `occurrence` is supplied.

## GPT ACTIONS E2E

`gpt_get_catalog` preset projection and `blockIndex` READ → `gpt_preview_change` → opaque proposal handle → `gpt_commit_change` → persisted slide → `gpt_get_playlist_context(editorFocus)` READ → `DisplayFormatService` enrich → exact display comparison passed in a server-side persisted-state mock for six format variants. The commit postcondition checks both persisted spec and materialized target display; an ISO display under `date-year` fails `OUTCOME_NOT_VERIFIED`.

## FILES CHANGED

`display_format_service.py`, `presentation_mutation/patch_service.py`, `presentation_http_command_planner_service.py`, `gpt_actions/dispatch_service.py`, `gpt_actions/commit_service.py`, `gpt_actions/response_compact.py`, `presentation_ops_content.json`, `vista_agent_intelligence.json`, generated GPT OpenAPI, ADR, capability matrix and bridge tests.

## CONTRACT IMPACT

PresentationMutation adds one typed op. OpenAPI still has 8 GPT Actions. Product editor and paint code were unchanged. Agent directives now instruct sibling-spec copying, typed mutation, readback and materialization verification.

## TESTS

- `python3 scripts/sync_gpt_actions_openapi.py`: 8 operations.
- `.venv/bin/python -m pytest -q tests/test_gpt_actions_facade.py -k 'not idempotency_replay_and_conflict' tests/test_vista_display_format_bridge.py tests/test_gpt_actions_response_compact.py tests/test_presentation_mutation_merge.py tests/test_display_format_service.py tests/test_vista_agent_intelligence.py tests/test_vista_builder_instructions_budget.py tests/test_tv_openapi_catalog_sync.py`: 136 passed, 1 deselected.
- The same suite without exclusion produced 136 passed and 1 failed. The idempotency replay test fails because the original response carries full `visualVerification` while replay carries its compact projection. This is outside the format change and remains unresolved.
- `git diff --check`: clean.

## OPENAPI

Action count: 8. Operation IDs: `gpt_get_catalog`, `gpt_list_playlists`, `gpt_get_playlist_context`, `gpt_search_data_routes`, `gpt_preview_data_block`, `gpt_suggest_change`, `gpt_preview_change`, `gpt_commit_change`. Maximum operation description: 250 characters. Generated artifact synchronized from the canonical script.

## RQ COVERAGE

| RQ | Status | Evidence |
|---|---|---|
| RQ-01 | ATENDIDO | Product DisplayFormatSpec |
| RQ-02 | ATENDIDO | No second formatter/preset list |
| RQ-03 | ATENDIDO | set_display_format |
| RQ-04 | ATENDIDO | Existing 8 Actions |
| RQ-05 | ATENDIDO | contentRuns.dataRef |
| RQ-06 | ATENDIDO | textProjection |
| RQ-07 | PARCIAL — non-text typed targets pending | See corresponding sections above |
| RQ-08 | ATENDIDO | Binding preserved |
| RQ-09 | ATENDIDO | Typography preserved |
| RQ-10 | ATENDIDO | Multiple runs |
| RQ-11 | ATENDIDO | Fail-closed ambiguity |
| RQ-12 | ATENDIDO | formatBindings |
| RQ-13 | ATENDIDO | 70-block editorFocus budget |
| RQ-14 | ATENDIDO | Copy sibling spec |
| RQ-15 | ATENDIDO | date-year |
| RQ-16 | ATENDIDO | date-month-year |
| RQ-17 | ATENDIDO | date-month-abbrev-year |
| RQ-18 | ATENDIDO | number-2 |
| RQ-19 | ATENDIDO | currency-brl |
| RQ-20 | ATENDIDO | percent |
| RQ-21 | ATENDIDO | Persisted and materialized postcondition |
| RQ-22 | ATENDIDO | Revision alone insufficient |
| RQ-23 | ATENDIDO_EM_TESTE — persisted-state reload mock | See corresponding sections above |
| RQ-24 | HERDADO — shared backend enrich; no new four-surface run | See corresponding sections above |
| RQ-25 | ATENDIDO | Builder schema guardrail |
| RQ-26 | ATENDIDO | 8 Actions |
| RQ-27 | ATENDIDO | Agent directives published |
| RQ-28 | ATENDIDO | Capability matrix corrected |
| RQ-29 | ATENDIDO | No FE production change |
| RQ-30 | ATENDIDO_EM_TESTE — server-side GPT Actions integration; live smoke pending | See corresponding sections above |

## RESIDUAL SEARCH

`DisplayFormatService` owns canonical formatting. Legacy `format`/`valueFormat` consumers remain for saved dashboards. MFE paths inspected are authoring/paint. No VISTA-only formatter or ninth Action was introduced. Non-text canonical spec slots listed above remain a capability gap.

## EXECUTION_DRIFT

Before: a PROVEN claim was not supported by a typed read/write/verify chain. After: that chain is evidenced for text binding owners, including WEG-style date labels. Generic display-format capability remains PARTIAL until non-text owners have typed selectors and integration coverage.

## FINAL GATES

CANONICAL_DISPLAY_FORMAT_SPEC_REUSED: YES
TYPED_DISPLAY_FORMAT_MUTATION_AVAILABLE: YES
NEW_GPT_ACTION_CREATED: NO
CONTENT_RUN_FORMAT_WRITABLE: YES
TEXT_PROJECTION_FORMAT_WRITABLE: YES
COMPACT_READ_EXPOSES_FORMAT: YES
VISTA_CAN_COPY_EXISTING_FORMAT: YES
YEAR_FORMAT_END_TO_END: YES
MONTH_YEAR_FORMAT_END_TO_END: YES
MONTH_ABBREV_YEAR_END_TO_END: YES
NUMBER_FORMAT_END_TO_END: YES
CURRENCY_FORMAT_END_TO_END: YES
PERCENT_FORMAT_END_TO_END: YES
BINDING_PRESERVED: YES
TYPOGRAPHY_PRESERVED: YES
AMBIGUOUS_TARGET_FAILS_CLOSED: YES
POSTCONDITION_VERIFIES_DISPLAY_FORMAT: YES
REVISION_ALONE_COUNTS_AS_VERIFIED: NO
70_BLOCK_BUDGET_PASS: YES
BLOCK_COUNT_UNCHANGED: YES
ACTION_COUNT_UNCHANGED: YES
OPENAPI_BUILDER_COMPATIBLE: YES
ANY_CLIENT_CANONICAL_FORMATTER_ADDED: NO
EXECUTION_DRIFT_RESOLVED: NO

## LIVE SMOKE

PENDING_EXTERNAL_VALIDATION.

## FINAL VERDICT

IMPLEMENTATION_INCONCLUSIVE. Text binding formats are implemented and integration tested. Non-text canonical format owners and authenticated deployed runtime validation remain open; one unrelated idempotency replay test also fails in the broader suite.
