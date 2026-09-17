# DAVI Wave 1 capability freeze

> **Normative for the next implementation task.** Evidence/governance only. Does not change runtime.

- Task: `DAVI-CAPABILITY-EXPANSION-INVENTORY-001`
- Source HEAD: `306efc16ec6787972edda827a7f8517e14c7969b`
- Freeze status: `FROZEN_FOR_IMPLEMENTATION`
- Theme: Operational Product Intelligence (classified factory snapshot + MP exclusivity + shipping)
- Current eligible: **7**
- New Wave 1 capabilities: **3**
- Expected eligible after implementation: **10**
- Expected MCP tools after implementation: **3**
- Agent instructions change: **NO**

## Architecture invariants (do not reopen)

```text
DAVI capability <= authenticated user capability
DAVI_BUSINESS_AUTHZ_OWNER = NONE
CANONICAL_BACKEND_AUTHZ = REQUIRED_FINAL
DAVI_LOCAL_RBAC / BRANCH / OBJECT / ROLE AUTHZ = FORBIDDEN
FILTER != AUTHORIZATION
endpoint != capability
backend AuthZ != raw model exposure
MCP tools remain search_products + discover_delpi_information + execute_delpi_information
```

## Why this Wave 1 (not the seeded summary trio as-is)

Evidence-driven alternative to seeding product.snapshot.summary. These three expand distinct operational questions, reuse generic nested projection, keep MCP tools=3, and avoid promoting prices or redundant master/stock slices. Size 3 is enough to validate composite summaries, playbook_report lists, and sibling disambiguation.

`get_product_summary` is **DEFER**: omitting prices makes it redundant with current search+stock; including prices belongs to Wave 2. `get_product_shipping_status` is the clearer unique operational sibling.

## product.factory.status

- **CAPABILITY ID:** `product.factory.status`
- **BUSINESS NAME:** Status fabril consolidado do produto / Product factory operational status
- **BUSINESS NEED:** Entender a situação fabril de um PA: se há estrutura vigente, OP, produção iniciada e PA liberado para expedição — sem despejar as listas já cobertas por BOM, produção e expedição.
- **OWNER:** api-delpi Product bounded context (`PROVEN`)
- **SOURCE OF TRUTH:** GetProductFactoryStatusUseCase → ProductPlaybookRepository (SB1/SG1/SB2/SC2) + GetProducedQuantityUseCase (SH6/SHB)
- **CANONICAL OPERATION(S):** `get_product_factory_status`
- **CANONICAL USE CASE:** `GetProductFactoryStatusUseCase`
- **READ/PREPARE/ACT:** READ
- **IDENTITY:** END_USER_ACCOUNT
- **BACKEND AUTHZ:** PROVEN: @require_permission(API_DELPI_ACCESS) on get_factory_status
- **BUSINESS AUTHZ OWNER:** NONE
- **SEMANTIC INPUT CONTRACT:** required=['code'] optional=['branch', 'reference_date', 'start_date', 'end_date', 'max_depth']
- **APPROVED INPUT FIELDS:** ['code', 'branch', 'reference_date', 'start_date', 'end_date', 'max_depth']
- **INPUT MINIMIZATION:** Omit legacy/debug/sort internals; keep business identifiers and bounded paging/dates.
- **SEMANTIC OUTPUT CONTRACT:** Classified factory_status plus product header, dates and section summaries/indicators. Items arrays of structure/stock/production/shipping are out of this capability (sibling capabilities already cover those slices).
- **APPROVED RESPONSE FIELDS:**
  - `product.product_code`
  - `product.description`
  - `product.product_type`
  - `product.unit`
  - `product.group_code`
  - `reference_date`
  - `start_date`
  - `factory_status`
  - `indicators.total_intermediates`
  - `indicators.total_raw_materials`
  - `indicators.total_exclusive_raw_materials`
  - `indicators.total_raw_materials_without_stock_for_one_pa`
  - `indicators.max_pa_producible_from_stock`
  - `indicators.limiting_raw_material_code`
  - `indicators.total_pa_orders`
  - `indicators.total_pi_orders`
  - `indicators.total_pa_reported_quantity`
  - `indicators.total_pi_reported_quantity`
  - `indicators.total_pa_shipped_quantity`
  - `indicators.total_inspection_loss_quantity`
  - `structure.summary.total_components`
  - `structure.summary.total_intermediates`
  - `structure.summary.total_raw_materials`
  - `structure.summary.total_exclusive_raw_materials`
  - `raw_material_stock.summary.total_raw_materials`
  - `raw_material_stock.summary.total_without_stock_for_one_pa`
  - `raw_material_stock.summary.max_pa_producible_from_stock`
  - `raw_material_stock.summary.limiting_raw_material_code`
  - `production.summary.total_pa_orders`
  - `production.summary.total_pi_orders`
  - `production.summary.pa_production_started`
  - `production.summary.pi_production_started`
  - `shipping.summary.total_shipped_quantity`
  - `shipping.summary.total_inspection_loss_quantity`
  - `shipping.summary.total_reports`
- **SHAPE:** composite_analysis
- **PROJECTION MODE:** nested
- **LIMITS:** Use global execute_max_response_bytes=65536 and execute_max_items=50.; max_items=50; max_depth=8
- **BRANCH:** optional_consolidated: all | 01 | 02
- **PAGINATION:** none — summaries only
- **TIME SEMANTICS:** reference_date default today; start_date/end_date default same day; implementation must bound interval (recommended max 31 days). Do not approve unbounded history.
- **COMPLETENESS:** Summaries are complete relative to backend query; items are intentionally omitted, so the capability is a classified snapshot, not a full dump. truncated=false unless global byte budget truncates.
- **PROVENANCE:** Preserve canonical operationId/use case, reference/start dates, branch filter scope, truncated/is_complete. Do not expose SQL, hosts, or internals.
- **RETRIEVAL ALIASES PT-BR:** ['status fabril', 'situação fabril', 'status na fábrica', 'visão fabril do produto', 'situação do produto na fábrica']
- **RETRIEVAL ALIASES EN:** ['factory status', 'factory situation', 'product factory status', 'shop-floor status']
- **PRIVACY:** low
- **RISK:** volume=LOW runtime=MEDIUM
- **OBSERVABILITY:** Log action_id, actor id when allowed, status, latency, page/page_size, result_count, correlation id. No payload dump.
- **TEST PLAN:** unit projection paths; discover aliases positive+collision; execute bounded payload; sibling non-match (produção vs fabril vs expedição vs exclusividade); negative AuthZ 403 with unauthorized identity when available.
- **LIVE ACCEPTANCE:** Agent Preview discover→candidate→execute for a real product code; verify allowlisted fields only; verify sibling questions still hit current seven plus new three without new MCP tools.
- **NEGATIVE AUTHZ PLAN:** `YES` — authenticated user without `API_DELPI_ACCESS` must receive backend 403. SECOND_USER_NEGATIVE_AUTHZ remains TEST_NOT_RUN for broad publication.
- **QUARANTINE CHANGE REQUIRED:** [{"token": "factory", "action": "KEEP_GLOBAL_AND_OWN_VIA_ALIASES", "rationale": "Do not remove global factory quarantine. Implementation must add aliases so the eligible action owns the token and retrieval no longer treats it as foreign."}]
- **IMPLEMENTATION NOTES:** Add allowlist `operations[]` entry only. Do not add MCP tools, Agent prompt enumeration, DAVI RBAC, per-operation executor, or generic HTTP/SQL. Reuse generic nested projection. Bound max_depth≤8 and date interval. Omit `legacy` input.
- **OPEN GAPS:** ['SECOND_USER_NEGATIVE_AUTHZ = TEST_NOT_RUN (rollout, not freeze blocker)', 'Date-interval hard cap is an implementation argument-validator decision (recommended 31 days)']
- **FREEZE STATUS:** `FROZEN_FOR_IMPLEMENTATION`

## product.structure.exclusivity

- **CAPABILITY ID:** `product.structure.exclusivity`
- **BUSINESS NAME:** Exclusividade de matérias-primas na estrutura / BOM raw-material exclusivity
- **BUSINESS NEED:** Saber quais MPs da BOM vigente de um PA são exclusivas (presentes em apenas um PA válido).
- **OWNER:** api-delpi Product bounded context (`PROVEN`)
- **SOURCE OF TRUTH:** GetProductStructureExclusivityUseCase → ProductPlaybookRepository.fetch_structure_with_exclusivity (SG1/SB1)
- **CANONICAL OPERATION(S):** `get_product_structure_exclusivity`
- **CANONICAL USE CASE:** `GetProductStructureExclusivityUseCase`
- **READ/PREPARE/ACT:** READ
- **IDENTITY:** END_USER_ACCOUNT
- **BACKEND AUTHZ:** PROVEN: @require_permission(API_DELPI_ACCESS) on get_structure_exclusivity
- **BUSINESS AUTHZ OWNER:** NONE
- **SEMANTIC INPUT CONTRACT:** required=['code'] optional=['max_depth']
- **APPROVED INPUT FIELDS:** ['code', 'max_depth']
- **INPUT MINIMIZATION:** Do not expose legacy boolean SIM/NAO toggle.
- **SEMANTIC OUTPUT CONTRACT:** Flat leveled BOM rows with exclusive_raw_material flag and summary counts. Not a recursive tree dump; not a substitute for product.structure.bom.
- **APPROVED RESPONSE FIELDS:**
  - `product.product_code`
  - `product.description`
  - `product.product_type`
  - `product.unit`
  - `items[].level`
  - `items[].parent_code`
  - `items[].parent_description`
  - `items[].component_code`
  - `items[].component_description`
  - `items[].component_type`
  - `items[].component_unit`
  - `items[].quantity_per`
  - `items[].accumulated_quantity`
  - `items[].exclusive_raw_material`
  - `items[].total_valid_finished_products_using_mp`
  - `summary.total_components`
  - `summary.total_intermediates`
  - `summary.total_raw_materials`
  - `summary.total_exclusive_raw_materials`
- **SHAPE:** playbook_report
- **PROJECTION MODE:** nested
- **LIMITS:** Use global execute_max_response_bytes=65536 and execute_max_items=50.; max_items=50; max_depth=8
- **BRANCH:** not_applicable
- **PAGINATION:** max_items=50; max_depth default 8 cap 8
- **TIME SEMANTICS:** None
- **COMPLETENESS:** If items truncated by max_items/max_depth, is_complete=false and truncated=true. summary totals remain backend-computed for the requested depth.
- **PROVENANCE:** Preserve canonical operationId/use case, reference/start dates, branch filter scope, truncated/is_complete. Do not expose SQL, hosts, or internals.
- **RETRIEVAL ALIASES PT-BR:** ['exclusividade', 'matéria-prima exclusiva', 'mp exclusiva', 'componentes exclusivos', 'exclusividade de mp']
- **RETRIEVAL ALIASES EN:** ['exclusive raw material', 'bom exclusivity', 'exclusive components']
- **PRIVACY:** low
- **RISK:** volume=MEDIUM runtime=MEDIUM
- **OBSERVABILITY:** Log action_id, actor id when allowed, status, latency, page/page_size, result_count, correlation id. No payload dump.
- **TEST PLAN:** unit projection paths; discover aliases positive+collision; execute bounded payload; sibling non-match (produção vs fabril vs expedição vs exclusividade); negative AuthZ 403 with unauthorized identity when available.
- **LIVE ACCEPTANCE:** Agent Preview discover→candidate→execute for a real product code; verify allowlisted fields only; verify sibling questions still hit current seven plus new three without new MCP tools.
- **NEGATIVE AUTHZ PLAN:** `YES` — authenticated user without `API_DELPI_ACCESS` must receive backend 403. SECOND_USER_NEGATIVE_AUTHZ remains TEST_NOT_RUN for broad publication.
- **QUARANTINE CHANGE REQUIRED:** []
- **IMPLEMENTATION NOTES:** Add allowlist `operations[]` entry only. Do not add MCP tools, Agent prompt enumeration, DAVI RBAC, per-operation executor, or generic HTTP/SQL. Reuse generic nested projection. Bound max_depth≤8 and date interval. Omit `legacy` input.
- **OPEN GAPS:** ['SECOND_USER_NEGATIVE_AUTHZ = TEST_NOT_RUN', 'Global exclusive-MP catalog is a separate capability (not Wave 1)']
- **FREEZE STATUS:** `FROZEN_FOR_IMPLEMENTATION`

## product.shipping.status

- **CAPABILITY ID:** `product.shipping.status`
- **BUSINESS NAME:** Status de expedição do produto / Product shipping / final-inspection status
- **BUSINESS NEED:** Saber se o PA já passou pela inspeção final e quanto está liberado para expedição.
- **OWNER:** api-delpi Product bounded context (`PROVEN`)
- **SOURCE OF TRUTH:** GetProductShippingStatusUseCase → GetProducedQuantityUseCase.list_detail (SH6 + SHB inspeção final)
- **CANONICAL OPERATION(S):** `get_product_shipping_status`
- **CANONICAL USE CASE:** `GetProductShippingStatusUseCase`
- **READ/PREPARE/ACT:** READ
- **IDENTITY:** END_USER_ACCOUNT
- **BACKEND AUTHZ:** PROVEN: @require_permission(API_DELPI_ACCESS) on get_shipping_status
- **BUSINESS AUTHZ OWNER:** NONE
- **SEMANTIC INPUT CONTRACT:** required=['code'] optional=['branch', 'reference_date', 'start_date', 'end_date']
- **APPROVED INPUT FIELDS:** ['code', 'branch', 'reference_date', 'start_date', 'end_date']
- **INPUT MINIMIZATION:** Omit legacy flag and duplicate date_start/date_end query aliases.
- **SEMANTIC OUTPUT CONTRACT:** Shipping quantities and inspection losses for a product in a bounded date window. Distinct from production-status (OPs/apontamento) and from factory classified snapshot.
- **APPROVED RESPONSE FIELDS:**
  - `product.product_code`
  - `product.description`
  - `product.product_type`
  - `product.unit`
  - `start_date`
  - `items[].branch`
  - `items[].product_code`
  - `items[].production_order`
  - `items[].work_center`
  - `items[].shipped_quantity`
  - `items[].inspection_loss_quantity`
  - `items[].total_reports`
  - `summary.total_shipped_quantity`
  - `summary.total_inspection_loss_quantity`
  - `summary.total_reports`
- **SHAPE:** playbook_report
- **PROJECTION MODE:** nested
- **LIMITS:** Use global execute_max_response_bytes=65536 and execute_max_items=50.; max_items=50; max_depth=None
- **BRANCH:** optional_consolidated: all | 01 | 02
- **PAGINATION:** max_items=50
- **TIME SEMANTICS:** Default start=today; end=today. Implementation must bound interval (recommended max 31 days). Omit legacy date_start/date_end aliases.
- **COMPLETENESS:** summary totals are over returned+truncated window; if items truncated, is_complete=false.
- **PROVENANCE:** Preserve canonical operationId/use case, reference/start dates, branch filter scope, truncated/is_complete. Do not expose SQL, hosts, or internals.
- **RETRIEVAL ALIASES PT-BR:** ['expedição', 'status de expedição', 'liberado para expedição', 'inspeção final do pa', 'quantidade expedida']
- **RETRIEVAL ALIASES EN:** ['shipping status', 'final inspection', 'released to ship', 'shipped quantity']
- **PRIVACY:** low
- **RISK:** volume=MEDIUM runtime=LOW
- **OBSERVABILITY:** Log action_id, actor id when allowed, status, latency, page/page_size, result_count, correlation id. No payload dump.
- **TEST PLAN:** unit projection paths; discover aliases positive+collision; execute bounded payload; sibling non-match (produção vs fabril vs expedição vs exclusividade); negative AuthZ 403 with unauthorized identity when available.
- **LIVE ACCEPTANCE:** Agent Preview discover→candidate→execute for a real product code; verify allowlisted fields only; verify sibling questions still hit current seven plus new three without new MCP tools.
- **NEGATIVE AUTHZ PLAN:** `YES` — authenticated user without `API_DELPI_ACCESS` must receive backend 403. SECOND_USER_NEGATIVE_AUTHZ remains TEST_NOT_RUN for broad publication.
- **QUARANTINE CHANGE REQUIRED:** []
- **IMPLEMENTATION NOTES:** Add allowlist `operations[]` entry only. Do not add MCP tools, Agent prompt enumeration, DAVI RBAC, per-operation executor, or generic HTTP/SQL. Reuse generic nested projection. Bound max_depth≤8 and date interval. Omit `legacy` input.
- **OPEN GAPS:** ['SECOND_USER_NEGATIVE_AUTHZ = TEST_NOT_RUN']
- **FREEZE STATUS:** `FROZEN_FOR_IMPLEMENTATION`

## Implementation handoff (do not execute here)

Files expected to change later:

- `api-delpi/app/content/davi_external_read_allowlist.json` (three new operations + aliases)
- `api-delpi/tests/test_davi_dynamic_read.py` (eligible count 10, discover aliases, projection)
- generated technical inventory after promotion (separate task)

Must not change: MCP server tool surface, Agent Instructions, eligibility classifier semantics, executor genericity, API routes, use cases, repositories.

Expected eligible after implementation: **10**. Expected MCP tools: **3**.
