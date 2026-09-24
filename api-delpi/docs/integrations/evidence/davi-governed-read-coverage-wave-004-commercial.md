# DAVI Governed READ Coverage — Wave 004 Commercial Analytics

**TASK_ID:** `DAVI-CAPABILITY-EXPANSION-WAVE-004-COMMERCIAL-READ`  
**STATUS (source):** PASS  
**STATUS (live/deploy):** `PENDING_EXTERNAL_ACTION` / `TEST_NOT_RUN`

## Product direction (frozen)

- Production MCP only: `https://minhadelpi.com.br/apps/api-delpi/mcp`
- Progressive governed coverage of API DELPI READ families
- No MCP tool per family (tools remain 3)
- No generic expose-all / proxy / SQL
- GPT Actions surface = separate future track (`DAVI-GPT-ACTIONS-BOOTSTRAP-001`)

## Baseline → after

| Field | Before | After |
|---|---|---|
| Allowlist | v9 | **v10** |
| Eligible READ | 17 | **35** |
| MCP tools | 3 | **3** |
| Agent intelligence | 2026.09.24.2 | unchanged |
| Document transport spike | OFF / historical | unchanged |
| GPT Actions legacy | 2 / LEGACY_TRANSITIONAL | unchanged |

## Disposition (19 candidates)

**PROMOTE (18):** ROL summary/series/by-branch/by-customer/by-product; new-business pct/target; new-clients average/rol-pct; conversion rate/series; OTD overall/summary/by-branch/by-customer/series/series-by-customer; WEG ROL target.

**DEFER (1):** `get_sales_order_otd_panel` — line-level drill-down + nested insights; sibling to `get_sales_order_otd_line_detail`.

**REJECT (0)**

**OUT OF WAVE / NEXT_WAVE_CANDIDATE:** proposal family + `get_sales_order_otd_line_detail`.

## AuthZ

All promoted routes: backend `@require_any_permission(KPI_COMMERCIAL_ACCESS)`.  
DAVI local RBAC / branch AuthZ / service account = ABSENT.

## Governance notes

- Model-safe `approvedResponseFields` only (no `*`).
- Customer ranking drops `cnpj` / `city` / `state`.
- Date range constraint: `maxDays=366` when both dates present (no invented calendar defaults).
- Generic nested `pagination{}` + `has_more` completeness support.
- Retrieval: contiguous-token alias match + length weighting (fixes `cliente`⊂`clientes` collision).

## Source tests

447 passed (Wave 004 + prior wave/drawing/dynamic-read/inventory regressions).

## Live / deploy

Deploy + production MCP acceptance + live commercial parity = **not executed in this source wave**. Require canonical production recreate of `api-delpi` after push.

## Future GPT Actions handoff

Inventory later under `DAVI-GPT-ACTIONS-BOOTSTRAP-001`: TÉO/VISTA Actions auth patterns, Keycloak Actions client, whether DAVI needs dedicated Actions OAuth client, OpenAPI Action surface, reuse of DAVI intelligence/catalog, user identity parity, callback URI, scopes/audiences, backend AuthZ. Do **not** implement in Wave 004.
