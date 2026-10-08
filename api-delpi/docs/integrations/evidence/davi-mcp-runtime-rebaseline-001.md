# DAVI MCP Runtime Rebaseline — 001

```text
TASK_ID      = DAVI-MCP-RUNTIME-REBASELINE-001
EVALUATED_SHA = 7f2bfab647fdedd1fdca3298f750b712cb3f5c13
SCOPE        = current-state documentation/evidence rebaseline (no runtime change)
```

This artifact reanchors CURRENT claims on source-recomputed state and on
Architecture-provided provider runtime observations dated 2026-10-08.
Provider observations are classified `PROVIDER_CHAT_RUNTIME_OBSERVATION`
(executed by Architecture through the connected ChatGPT remote MCP; not
independently reproduced by Cursor).

## Current source state (recomputed from source at evaluated SHA)

```text
allowlist        = app/content/davi_external_read_allowlist.json
  version        = 19
  governed ops   = 89 (1 approved_external_capability + 88 catalog_action)
agent_intelligence = app/content/davi_agent_intelligence.json
  version        = 2026.10.07.2
MCP tools        = exactly 2
  discover_delpi_information
  execute_delpi_information
posture          = READ-only (write intent -> 0 candidates)
generic SQL      = FORBIDDEN (arbitrary SELECT intent -> 0 candidates)
candidate_token  = actor-bound HMAC (DAVI_CANDIDATE_HMAC_SECRET preferred)
backend AuthZ    = final authority (DAVI_LOCAL_RBAC / DAVI_BRANCH_AUTHZ = FORBIDDEN)
```

## Governed operation families (allowlist v19, 89 ops)

| Family | Count | Representative operations | AuthZ / projection |
|---|---|---|---|
| Product Master & item context | 27 | search_products, get_product_stock, get_product_pricing, get_product_structure, get_product_drawing, get_product_internal_movements | backend AuthZ; approved field projection |
| Commercial / Sales | 18 | get_sales_order_otd*, get_commercial_rol_*, get_sales_conversion_rate* | KPI_COMMERCIAL_ACCESS et al. |
| Supplies / Purchasing / Inventory | 22 | get_supplies_stock_balances_*, list_supplies_inventory_adjustments, get_supplies_purchase_order_otd | KPI_SUPPLIES_ACCESS et al. |
| Production | 17 | get_production_oee*, get_production_machine_load_*, get_production_losses_* | PRODUCTION_* permissions |
| System Metadata | 5 | get_protheus_table, search_tables_by_description, list_protheus_table_columns | metadata describe/search only — never row dumps |

`BUSINESS_OWNER` for unratified families = `TO_INVENTORY`.

## Provider runtime observations (2026-10-08, PROVIDER_CHAT_RUNTIME_OBSERVATION)

| Surface | Observation | Status |
|---|---|---|
| MCP tool surface | exactly 2 tools exposed | PROVEN |
| live discover | eligible_action_count = 89; agent_directives.version = 2026.10.07.2; read_only = true | PROVEN |
| Product Master | «description do produto 10080034» → search_products → execute ok, approved projection | PROVEN |
| Stock | «estoque atual do produto 10080034» → get_product_stock executed ok | PROVEN |
| Inventory adjustments | day + month queries → list/summary executed ok | PROVEN |
| Pricing | «qual o preço do produto 10080034» → get_product_pricing executed ok; `prices=[]` for that product | PROVEN |
| Write guard | «altere o produto 10080034» → candidate_count = 0 | PROVEN |
| Generic SQL guard | arbitrary `SELECT * FROM SB1010` → candidate_count = 0 | PROVEN |
| Pagination bound | inventory adjustments page_size=51 → rejected, maximum 50 | PROVEN |

## Live coverage classification

```text
SOURCE GOVERNANCE FOR 89        = PROVEN
LIVE MCP REPRESENTATIVE COVERAGE = PROVEN (families above)
FULL 89-OPERATION LIVE COVERAGE  = PARTIAL (not all 89 live-tested)
DISCOVERY_TOP_K_RECALL          = PASS
DISCOVERY_TOP1_PRECISION        = RESIDUAL (get_product_stock not top-1
                                  for the stock query; unrelated/redundant
                                  candidates ranked above)
```

## Pricing semantics (persisted distinction)

`get_product_pricing` = registered commercial DA1 price-table rows —
**not** "the current effective price". Approved fields:
`product.code/description/unit`, `prices[].table_code, table_description,
sale_price, currency, lot_quantity, valid_from, active`.
`prices=[]` is a canonical zero-row result — NOT capability absence.

## Current residual ledger (MCP-core only)

```text
P0 SECOND_USER_IDENTITY_PROOF   = PENDING
P0 NEGATIVE_BUSINESS_AUTHZ      = PENDING (needs real less-privileged user;
                                  no service-account substitute)
P1 DISCOVERY_TOP1_QUALITY       = RESIDUAL_FOUND
P1 FULL_89_OPERATION_LIVE_ACCEPTANCE = PARTIAL
P1 MCP_RATE_POLICY              = PENDING_OWNER_DECISION
  (no proven MCP-specific gateway limit_req on /apps/api-delpi/;
   policy owner = gateway owner — DAVI-MCP-RATE-POLICY-001)
```

Non-core / separate workstreams (not MCP defects): Agent Files, citation
rendering, RAG/vector, third MCP tool, PDF model visibility, provider
publication UX, dedicated DAVI backend.

## Stale claims corrected by this rebaseline

| Location | Was | Now |
|---|---|---|
| openai-plugin-mcp.md current block | allowlist v15 / 63, AI 2026.09.24.3, live TEST_NOT_RUN | v19 / 89, AI 2026.10.07.2, representative live PROVEN |
| openai-plugin-mcp.md status table | 2-tool rediscovery PENDING | PROVEN (provider observation) |
| openai-plugin-mcp.md V1 boundary | implied stock/pricing excluded from current surface | V1 boundary marked historical; families now governed |
| davi README §16 ledger | stock/pricing/BOM/production listed as TO_INVENTORY | marked SUPERSEDED by v19 expansion |
| workspace-agent scenario H | pricing → "sem candidate elegível" | get_product_pricing governed; prices=[] valid |

Historical wave values (v5→v18, 3-tool periods, TEST_NOT_RUN at wave dates)
remain preserved where scoped to their wave.

## Next tasks (recommended only — not executed)

```text
DAVI-MCP-DISCOVERY-QUALITY-001   benchmark top-1/top-3/zero-candidate for 89
DAVI-MCP-LIVE-ACCEPTANCE-001     E2E matrix by semantic family
DAVI-MCP-SECOND-USER-AUTHZ-001   second-user identity + negative AuthZ
DAVI-MCP-RATE-POLICY-001         policy owner decision
```
