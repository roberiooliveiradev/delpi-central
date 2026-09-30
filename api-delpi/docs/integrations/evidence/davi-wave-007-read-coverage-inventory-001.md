# DAVI structured READ coverage inventory (Wave 007) — reconciled

> Evidence artifact. **Not** runtime authority. **Not** the operational allowlist.

- Task: `DAVI-WAVE-007-READ-COVERAGE-INVENTORY-CORRECTION-001`
- Reviewed HEAD: `8b6042b1a3bcbe1d51b428edf7c66af9429fb5b8`
- origin/main at generation: `8b6042b1a3bcbe1d51b428edf7c66af9429fb5b8`
- Inventory source: source-generated OpenAPI (`app.main.openapi()` → 726 operations / 651 paths), `openapi_baseline.json` (726 ops after canonical sync), `davi_external_read_allowlist.json` v15 (63 ops), `route_test_coverage.json`, AST extraction of route handlers + AuthZ decorators under `app/interface/http/` (726/726 operations resolved).

## Correction note

The previous execution of this inventory (`DAVI-WAVE-007-READ-COVERAGE-INVENTORY-001`) produced valid **global** classification totals, but the family-level table contained reconciliation defects:

- `structured_business_read` was computed by an independent heuristic (excluding `system` category / `data` module rows and similar), which could disagree with the row's final classification;
- the family `READ` column counted GET-only rows, while the global `READ` figure included the six proven read-semantics POST operations;
- as a result, family columns did not reconcile (e.g. Strategic Indicators reported SBR=72 while its classification was ELIGIBLE_GAP=75; global READ 530 vs family sum 496).

Correction applied: `structured_business_read` is now derived from the final row classification (`COVERED|ELIGIBLE_GAP|REDUNDANT|DEFERRED|TO_INVENTORY`), `READ` is `GET` or proven read-semantics POST regardless of classification, and every aggregate is generated from the matrix by the build script with fail-loud assertions (no negative counts, one family per row, one classification per row, global and family sums reconcile, SBR identity holds).

This pass also revalidated against a newer `origin/main` that added the MES S2S contract `get_production_operation_standard_time` (source now 726 operations).

Disposition closure (`DAVI-OPENAPI-GOVERNANCE-HYGIENE-001`): Architecture resolved the four remaining TO_INVENTORY rows as `EXCLUDED` with rationale `EXCLUDED_CURRENT_ROUTE` — the three public/token-surface routes do not prove end-user authorization parity, and the MES `standard-time` route uses an internal S2S service credential, not end-user business authorization. These current route contracts are not eligible DAVI execution paths; future exposure requires canonical authenticated end-user READ contracts. No capability was added.

## Executive summary

- Total API DELPI operations: **726**
- READ-shaped operations (GET + read-semantics POST batch queries): **531**
- Structured business READ: **459**
- COVERED (allowlist v15): **63**
- ELIGIBLE_GAP: **374**
- REDUNDANT: **2**
- DEFERRED (existing governance dispositions): **20**
- TO_INVENTORY: **0**
- EXCLUDED (writes/destructive/binary/admin/SQL/legacy/prohibition + 4 current-route dispositions): **267**
- Allowlist orphans: **0** (all 63 operationIds resolve to current routes)
- Baseline resync: 721 → **726** operations (+ `get_billing_portfolio_*` ×4, `list_product_inventory_blocks`; all five already had route tests — `route_test_coverage.json` regenerated, statuses `covered`).

## Coverage by family

| Family | Total ops | READ | Structured business READ | COVERED | ELIGIBLE_GAP | REDUNDANT | EXCLUDED | DEFERRED | TO_INVENTORY |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Commercial & Sales | 63 | 52 | 51 | 18 | 27 | 0 | 12 | 6 | 0 |
| Compliance Channel | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| Data/SQL | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| Engineering | 28 | 23 | 22 | 0 | 22 | 0 | 6 | 0 | 0 |
| Finance & Budgeting | 119 | 62 | 50 | 0 | 50 | 0 | 69 | 0 | 0 |
| Gpt Actions | 2 | 2 | 0 | 0 | 0 | 0 | 2 | 0 | 0 |
| HR | 4 | 4 | 4 | 0 | 4 | 0 | 0 | 0 | 0 |
| Procedures & Guides | 29 | 13 | 4 | 0 | 4 | 0 | 25 | 0 | 0 |
| Product Master | 38 | 38 | 35 | 17 | 13 | 2 | 3 | 3 | 0 |
| Production | 55 | 55 | 54 | 10 | 44 | 0 | 1 | 0 | 0 |
| Public/Token Surface | 9 | 6 | 0 | 0 | 0 | 0 | 9 | 0 | 0 |
| Quality & Inspection | 185 | 119 | 105 | 0 | 105 | 0 | 80 | 0 | 0 |
| Reports & Scheduling | 21 | 11 | 10 | 0 | 10 | 0 | 11 | 0 | 0 |
| Scheduling | 10 | 4 | 4 | 0 | 4 | 0 | 6 | 0 | 0 |
| Strategic Indicators / Dashboards | 75 | 75 | 75 | 0 | 75 | 0 | 0 | 0 | 0 |
| Supplies & Purchasing | 49 | 42 | 39 | 18 | 10 | 0 | 10 | 11 | 0 |
| System | 1 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| Technical | 20 | 18 | 0 | 0 | 0 | 0 | 20 | 0 | 0 |
| UI/Reference | 16 | 6 | 6 | 0 | 6 | 0 | 10 | 0 | 0 |
| **TOTAL** | **726** | **531** | **459** | **63** | **374** | **2** | **267** | **20** | **0** |

Identity check: SBR = COVERED + ELIGIBLE_GAP + REDUNDANT + DEFERRED + TO_INVENTORY = 459 = 459.

## ELIGIBLE_GAP by wave candidate

### WAVE_CANDIDATE_A — Strategic Indicators / Dashboards (75 routes)

- `GET` `/dashboard/department-idd` `get_dashboard_department_idd` — Department IDD score — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/department-indicators` `get_dashboard_department_indicators` — Department IDD with indicators (goals and realized) — AuthZ: `require_any_permission_or_supplies_bff(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/departments-indicators` `get_dashboard_departments_indicators` — All departments with IDD, goals and realized per indicator — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/commercial-closing-rate/meta` `get_si_indicator_commercial_closing_rate_meta` — Taxa de Fechamento de Negócios — goal — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/commercial-closing-rate/realized` `get_si_indicator_commercial_closing_rate_realized` — Taxa de Fechamento de Negócios — actual — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/commercial-new-business-rol/meta` `get_si_indicator_commercial_new_business_rol_meta` — % ROL de Novos Negócios — goal — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/commercial-new-business-rol/realized` `get_si_indicator_commercial_new_business_rol_realized` — % ROL de Novos Negócios — actual — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/commercial-rol/meta` `get_si_indicator_commercial_rol_meta` — ROL — goal — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/commercial-rol/realized` `get_si_indicator_commercial_rol_realized` — ROL — actual — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/commercial-sales-order-otd/meta` `get_si_indicator_commercial_sales_order_otd_meta` — OTD de Pedidos de Venda — goal — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/commercial-sales-order-otd/realized` `get_si_indicator_commercial_sales_order_otd_realized` — OTD de Pedidos de Venda — actual — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/engineering-projects-on-time/meta` `get_si_indicator_engineering_projects_on_time_meta` — % de Projetos Concluídos no Prazo — goal — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/engineering-projects-on-time/realized` `get_si_indicator_engineering_projects_on_time_realized` — % de Projetos Concluídos no Prazo — actual — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/engineering-transforma-plus/meta` `get_si_indicator_engineering_transforma_plus_meta` — Ganhos Financeiros do TRANSFORMA+ DELPI — goal — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/engineering-transforma-plus/realized` `get_si_indicator_engineering_transforma_plus_realized` — Ganhos Financeiros do TRANSFORMA+ DELPI — actual — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/financial-ebitda/meta` `get_si_indicator_financial_ebitda_meta` — EBITDA / Receita Operacional — goal — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/financial-ebitda/realized` `get_si_indicator_financial_ebitda_realized` — EBITDA / Receita Operacional — actual — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/financial-fixed-cost/meta` `get_si_indicator_financial_fixed_cost_meta` — % Custos Fixos / Receita Operacional — goal — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/financial-fixed-cost/realized` `get_si_indicator_financial_fixed_cost_realized` — % Custos Fixos / Receita Operacional — actual — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/financial-pmr/meta` `get_si_indicator_financial_pmr_meta` — Prazo Médio de Recebimento (PMR) — goal — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/financial-pmr/realized` `get_si_indicator_financial_pmr_realized` — Prazo Médio de Recebimento (PMR) — actual — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/hr-absenteeism/meta` `get_si_indicator_hr_absenteeism_meta` — Absenteísmo — goal — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/hr-absenteeism/realized` `get_si_indicator_hr_absenteeism_realized` — Absenteísmo — actual — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/hr-pdi/meta` `get_si_indicator_hr_pdi_meta` — Número de PDI's Ativos — goal — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/hr-pdi/realized` `get_si_indicator_hr_pdi_realized` — Número de PDI's Ativos — actual — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/hr-performance-reviews/meta` `get_si_indicator_hr_performance_reviews_meta` — % de Avaliações de Desempenho Concluídas — goal — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/hr-performance-reviews/realized` `get_si_indicator_hr_performance_reviews_realized` — % de Avaliações de Desempenho Concluídas — actual — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/hr-satisfaction/meta` `get_si_indicator_hr_satisfaction_meta` — Satisfação Interna (Clima/Engajamento) — goal — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/hr-satisfaction/realized` `get_si_indicator_hr_satisfaction_realized` — Satisfação Interna (Clima/Engajamento) — actual — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/hr-training-hours/meta` `get_si_indicator_hr_training_hours_meta` — Horas de Treinamento / Colaborador / mês — goal — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/hr-training-hours/realized` `get_si_indicator_hr_training_hours_realized` — Horas de Treinamento / Colaborador / mês — actual — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/hr-turnover/meta` `get_si_indicator_hr_turnover_meta` — Turnover (Rotatividade) — goal — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/hr-turnover/realized` `get_si_indicator_hr_turnover_realized` — Turnover (Rotatividade) — actual — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/production-costs/meta` `get_si_indicator_production_costs_meta` — Custos de Produção / ROL — goal — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/production-costs/realized` `get_si_indicator_production_costs_realized` — Custos de Produção / ROL — actual — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/production-depreciation/meta` `get_si_indicator_production_depreciation_meta` — Depreciação / ROL — goal — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/production-depreciation/realized` `get_si_indicator_production_depreciation_realized` — Depreciação / ROL — actual — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/production-direct-labor/meta` `get_si_indicator_production_direct_labor_meta` — Custo Mão de Obra Direta / ROL — goal — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/production-direct-labor/realized` `get_si_indicator_production_direct_labor_realized` — Custo Mão de Obra Direta / ROL — actual — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/production-oee/meta` `get_si_indicator_production_oee_meta` — OEE (Eficiência Global dos Equip.) — goal — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/production-oee/realized` `get_si_indicator_production_oee_realized` — OEE (Eficiência Global dos Equip.) — actual — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/production-otd/meta` `get_si_indicator_production_otd_meta` — OTD (Entrega no Prazo) — goal — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/production-otd/realized` `get_si_indicator_production_otd_realized` — OTD (Entrega no Prazo) — actual — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/quality-audit-5s/meta` `get_si_indicator_quality_audit_5s_meta` — Nota Auditoria 5S — goal — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/quality-audit-5s/realized` `get_si_indicator_quality_audit_5s_realized` — Nota Auditoria 5S — actual — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/quality-kaizen-financial/meta` `get_si_indicator_quality_kaizen_financial_meta` — Ganhos Financeiros Kaizen/mês — goal — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/quality-kaizen-financial/realized` `get_si_indicator_quality_kaizen_financial_realized` — Ganhos Financeiros Kaizen/mês — actual — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/quality-kaizen-ideas/meta` `get_si_indicator_quality_kaizen_ideas_meta` — Ideias Aprovadas para Kaizen/mês — goal — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/quality-kaizen-ideas/realized` `get_si_indicator_quality_kaizen_ideas_realized` — Ideias Aprovadas para Kaizen/mês — actual — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/quality-ppm-external-components/meta` `get_si_indicator_quality_ppm_external_components_meta` — PPM Externo Chicotes — goal — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/quality-ppm-external-components/realized` `get_si_indicator_quality_ppm_external_components_realized` — PPM Externo Chicotes — actual — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/quality-ppm-external/meta` `get_si_indicator_quality_ppm_external_meta` — PPM Externo — goal — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/quality-ppm-external-plugs/meta` `get_si_indicator_quality_ppm_external_plugs_meta` — PPM Externo Plugues — goal — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/quality-ppm-external-plugs/realized` `get_si_indicator_quality_ppm_external_plugs_realized` — PPM Externo Plugues — actual — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/quality-ppm-external/realized` `get_si_indicator_quality_ppm_external_realized` — PPM Externo — actual — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/quality-ppm-internal-components/meta` `get_si_indicator_quality_ppm_internal_components_meta` — PPM Interno Chicotes — goal — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/quality-ppm-internal-components/realized` `get_si_indicator_quality_ppm_internal_components_realized` — PPM Interno Chicotes — actual — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/quality-ppm-internal/meta` `get_si_indicator_quality_ppm_internal_meta` — PPM Interno — goal — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/quality-ppm-internal-plugs/meta` `get_si_indicator_quality_ppm_internal_plugs_meta` — PPM Interno Plugues — goal — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/quality-ppm-internal-plugs/realized` `get_si_indicator_quality_ppm_internal_plugs_realized` — PPM Interno Plugues — actual — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/quality-ppm-internal/realized` `get_si_indicator_quality_ppm_internal_realized` — PPM Interno — actual — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/quality-rework-cost-pct/meta` `get_si_indicator_quality_rework_cost_pct_meta` — Custo de Retrabalho / ROL — goal — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/quality-rework-cost-pct/realized` `get_si_indicator_quality_rework_cost_pct_realized` — Custo de Retrabalho / ROL — actual — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/quality-scrap-cost-pct/meta` `get_si_indicator_quality_scrap_cost_pct_meta` — Custo de Refugo / ROL — goal — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/quality-scrap-cost-pct/realized` `get_si_indicator_quality_scrap_cost_pct_realized` — Custo de Refugo / ROL — actual — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/supplies-cpv/meta` `get_si_indicator_supplies_cpv_meta` — CPV Consolidado (matriz e filial) — goal — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/supplies-cpv/realized` `get_si_indicator_supplies_cpv_realized` — CPV Consolidado (matriz e filial) — actual — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/supplies-negotiation-savings/meta` `get_si_indicator_supplies_negotiation_savings_meta` — Economia em Negociações de Compras — goal — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/supplies-negotiation-savings/realized` `get_si_indicator_supplies_negotiation_savings_realized` — Economia em Negociações de Compras — actual — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/supplies-otd/meta` `get_si_indicator_supplies_otd_meta` — OTD Consolidado de Compras — goal — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/supplies-otd/realized` `get_si_indicator_supplies_otd_realized` — OTD Consolidado de Compras — actual — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/supplies-stock-turnover/meta` `get_si_indicator_supplies_stock_turnover_meta` — Giro de Estoque — goal — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/supplies-stock-turnover/realized` `get_si_indicator_supplies_stock_turnover_realized` — Giro de Estoque — actual — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/supplies-stock-value/meta` `get_si_indicator_supplies_stock_value_meta` — Valor Total do Estoque Consolidado — goal — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`
- `GET` `/dashboard/indicators/supplies-stock-value/realized` `get_si_indicator_supplies_stock_value_realized` — Valor Total do Estoque Consolidado — actual — AuthZ: `require_any_permission(DASHBOARD_IDD_ACCESS)`

### WAVE_CANDIDATE_B — Production operational detail (44 routes)

- `GET` `/production/depreciation_pct` `get_depreciation_pct` — Depreciation pct — AuthZ: `require_any_permission(KPI_PRODUCTION_ACCESS)`
- `GET` `/production/direct_labor_cost_pct` `get_direct_labor_cost_pct` — Direct labor cost pct — AuthZ: `require_any_permission(KPI_PRODUCTION_ACCESS)`
- `GET` `/production/eficiencia-fabril/dashboard` `get_eficiencia_fabril_dashboard` — Eficiencia fabril dashboard — AuthZ: `require_any_permission(EFICIENCIA_FABRIL_ACCESS)`
- `GET` `/production/eficiencia-fabril/efficiency-by-work-center` `get_eficiencia_fabril_efficiency_by_work_center` — Factory efficiency average % by work center — AuthZ: `require_any_permission(EFICIENCIA_FABRIL_ACCESS)`
- `GET` `/production/eficiencia-fabril/efficiency-series` `get_eficiencia_fabril_efficiency_series` — Factory efficiency daily series by work center — AuthZ: `require_any_permission(EFICIENCIA_FABRIL_ACCESS)`
- `GET` `/production/allocation-gaps` `get_production_allocation_gaps` — Production allocation gaps — AuthZ: `require_permission(API_DELPI_ACCESS)`
- `GET` `/production/appointments/finished-ops/series` `get_production_appointments_finished_ops_series` — Finished production orders count by period — AuthZ: `require_any_permission(PRODUCTION_APPOINTMENTS_READ_PERMISSIONS)`
- `GET` `/production/appointments/series` `get_production_appointments_series` — Production appointments time series — AuthZ: `require_any_permission(PRODUCTION_APPOINTMENTS_READ_PERMISSIONS)`
- `GET` `/production/consumption/by-item/{code}` `get_production_consumption_by_item` — Production consumption by item — AuthZ: `require_permission(API_DELPI_ACCESS)`
- `GET` `/production/consumption/top-items` `get_production_consumption_top_items` — Itens mais consumidos na production — AuthZ: `require_permission(API_DELPI_ACCESS)`
- `GET` `/production/consumption/top-items-by-work-center` `get_production_consumption_top_items_by_work_center` — Production consumption top items by work center — AuthZ: `require_permission(API_DELPI_ACCESS)`
- `GET` `/production/consumption/top-items-validated` `get_production_consumption_top_items_validated` — Production consumption top items validated — AuthZ: `require_permission(API_DELPI_ACCESS)`
- `GET` `/production/production_cost_pct` `get_production_cost_pct` — Production cost pct — AuthZ: `require_any_permission(KPI_PRODUCTION_ACCESS)`
- `GET` `/production/factory-shifts` `get_production_factory_shifts` — Factory shifts catalog — AuthZ: `require_any_permission(EFICIENCIA_FABRIL_ACCESS)`
- `GET` `/production/losses/records` `get_production_losses_records` — Production losses records — AuthZ: `require_permission(API_DELPI_ACCESS)`
- `GET` `/production/losses/top-materials` `get_production_losses_top_materials` — Production losses top materials — AuthZ: `require_permission(API_DELPI_ACCESS)`
- `POST` `/production/machine-load/appointment-status` `get_production_machine_load_appointment_status` — Lista — Status de apontamento hza das operações da carga máquina — AuthZ: `require_any_permission(KPI_PRODUCTION_ACCESS)`
- `GET` `/production/oee/appointments/{appointment_id}` `get_production_oee_appointment_by_id` — Production oee appointment by id — AuthZ: `require_any_permission(KPI_PRODUCTION_ACCESS)`
- `GET` `/production/orders/by-op/{production_order}` `get_production_order_by_op` — Production order by op — AuthZ: `require_permission(API_DELPI_ACCESS)`
- `GET` `/production/production-order-sets/incomplete` `get_production_order_sets_incomplete` — Incomplete production order sets — AuthZ: `require_any_permission(KPI_PRODUCTION_ACCESS)`
- `GET` `/production/production-order-sets/quantity-mismatches` `get_production_order_sets_quantity_mismatches` — Production order sets with intermediate quantity mismatches — AuthZ: `require_any_permission(KPI_PRODUCTION_ACCESS)`
- `GET` `/production/orders/finished` `get_production_orders_finished` — Production orders finished — AuthZ: `require_permission(API_DELPI_ACCESS)`
- `GET` `/production/orders/finished-without-consumption` `get_production_orders_finished_without_consumption` — Production orders finished without consumption — AuthZ: `require_permission(API_DELPI_ACCESS)`
- `GET` `/production/orders/open` `get_production_orders_open` — Production orders open — AuthZ: `require_permission(API_DELPI_ACCESS)`
- `GET` `/production/pcp-orders/items` `get_production_pcp_orders_items` — Production orders items — AuthZ: `require_any_permission(KPI_PRODUCTION_ACCESS)`
- `GET` `/production/pcp-orders/ranking` `get_production_pcp_orders_ranking` — Production orders ranking — AuthZ: `require_any_permission(KPI_PRODUCTION_ACCESS)`
- `GET` `/production/pcp-orders/summary` `get_production_pcp_orders_summary` — Production orders summary — AuthZ: `require_any_permission(KPI_PRODUCTION_ACCESS)`
- `GET` `/production/planned-vs-real-time` `get_production_planned_vs_real_time` — Production planned vs real time — AuthZ: `require_permission(API_DELPI_ACCESS)`
- `GET` `/production/schedule/today` `get_production_schedule_today` — product programados para produzir na data — AuthZ: `require_permission(API_DELPI_ACCESS)`
- `GET` `/production/shared-structure-intermediates` `get_production_shared_structure_intermediates` — Lista paginada — Intermediários pi/pa usados na estrutura vigente de m — AuthZ: `require_any_permission(KPI_PRODUCTION_ACCESS)`
- `GET` `/production/unproductive-hours/items` `get_production_unproductive_hours_items` — Unproductive hours items — AuthZ: `require_any_permission(UNPRODUCTIVE_HOURS_ACCESS)`
- `GET` `/production/unproductive-hours/ranking` `get_production_unproductive_hours_ranking` — Unproductive hours ranking — AuthZ: `require_any_permission(UNPRODUCTIVE_HOURS_ACCESS)`
- `GET` `/production/unproductive-hours/series` `get_production_unproductive_hours_series` — Unproductive hours daily series — AuthZ: `require_any_permission(UNPRODUCTIVE_HOURS_ACCESS)`
- `GET` `/production/unproductive-hours/summary` `get_production_unproductive_hours_summary` — Unproductive hours summary — AuthZ: `require_any_permission(UNPRODUCTIVE_HOURS_ACCESS)`
- `GET` `/production/work-centers/average-planned-time` `get_production_work_center_average_planned_time` — Production work center average planned time — AuthZ: `require_permission(API_DELPI_ACCESS)`
- `GET` `/production/work-centers/order-summary` `get_production_work_center_order_summary` — Production work center order summary — AuthZ: `require_permission(API_DELPI_ACCESS)`
- `GET` `/production/eficiencia-fabril/appointments` `list_eficiencia_fabril_appointments` — Eficiencia fabril appointments — AuthZ: `require_any_permission(EFICIENCIA_FABRIL_ACCESS)`
- `GET` `/production/appointments/work-centers` `list_production_appointment_work_centers` — Work centers catalog for production appointments — AuthZ: `require_any_permission(PRODUCTION_APPOINTMENTS_READ_PERMISSIONS)`
- `GET` `/production/appointments` `list_production_appointments` — Paged list of production appointments — AuthZ: `require_any_permission(PRODUCTION_APPOINTMENTS_READ_PERMISSIONS)`
- `GET` `/production/appointments/by-op` `list_production_appointments_by_op` — Production appointments aggregated by OP — AuthZ: `require_any_permission(PRODUCTION_APPOINTMENTS_READ_PERMISSIONS)`
- `GET` `/production/appointments/child-ops` `list_production_appointments_child_ops` — Child production orders of the same family — AuthZ: `require_any_permission(PRODUCTION_APPOINTMENTS_READ_PERMISSIONS)`
- `GET` `/production/machine-programs/top-intermediates` `list_production_machine_program_top_intermediates` — Paged list — top intermediate products for machine programs — AuthZ: `require_permission(API_DELPI_ACCESS)`
- `GET` `/production/orders/{production_order}/operations/{operation}/materials` `list_production_order_operation_materials` — Operation materials from SD4 — AuthZ: `require_permission(API_DELPI_ACCESS)`
- `POST` `/production/orders/operation-materials/batch` `list_production_order_operation_materials_batch` — Operation materials from SD4 in batch — AuthZ: `require_permission(API_DELPI_ACCESS)`

### WAVE_CANDIDATE_C — Quality & Inspection (105 routes)

- `GET` `/quality/audit-5s/analytics/dashboard` `get_audit_5s_analytics_dashboard` — Get Audit 5S Dashboard — AuthZ: `require_any_permission(AUDIT_5S_READ_PERMISSIONS)`
- `GET` `/quality/audit-5s/audits/{audit_id}` `get_audit_5s_audit` — Get Audit — AuthZ: `require_any_permission(AUDIT_5S_READ_PERMISSIONS)`
- `GET` `/quality/audit-5s/catalog` `get_audit_5s_catalog` — Get Catalog — AuthZ: `require_any_permission(AUDIT_5S_READ_PERMISSIONS)`
- `GET` `/quality/audit-5s/summary` `get_audit_5s_summary` — Audit 5S — AuthZ: `require_any_permission(KPI_QUALITY_ACCESS)`
- `GET` `/quality/audit-5s/summary/series` `get_audit_5s_summary_series` — Audit 5S summary series — AuthZ: `require_any_permission(KPI_QUALITY_ACCESS)`
- `GET` `/inspecoes-entrada/historico` `get_inspecoes_entrada_historico` — Incoming inspections — history — AuthZ: `require_any_permission(INSPECOES_ENTRADA_READ_PERMISSIONS)`
- `GET` `/inspecoes-entrada/historico/detalhe` `get_inspecoes_entrada_historico_detalhe` — Incoming inspection — history detail — AuthZ: `require_any_permission(INSPECOES_ENTRADA_READ_PERMISSIONS)`
- `GET` `/inspecoes-entrada/pendentes` `get_inspecoes_entrada_pendentes` — Incoming inspections — pending — AuthZ: `require_any_permission(INSPECOES_ENTRADA_READ_PERMISSIONS)`
- `GET` `/inspecoes-entrada/pendentes-fornecedor` `get_inspecoes_entrada_pendentes_fornecedor` — Incoming inspections — pending by supplier — AuthZ: `require_any_permission(INSPECOES_ENTRADA_READ_PERMISSIONS)`
- `GET` `/inspecoes-entrada/rejeitadas-ensaiador` `get_inspecoes_entrada_rejeitadas_ensaiador` — Incoming inspections — rejected by tester — AuthZ: `require_any_permission(INSPECOES_ENTRADA_READ_PERMISSIONS)`
- `GET` `/inspecoes-entrada/rejeitadas-produto` `get_inspecoes_entrada_rejeitadas_produto` — Incoming inspections — rejected by product — AuthZ: `require_any_permission(INSPECOES_ENTRADA_READ_PERMISSIONS)`
- `GET` `/inspecoes-entrada/resumo` `get_inspecoes_entrada_resumo` — Incoming inspections — summary KPIs — AuthZ: `require_any_permission(INSPECOES_ENTRADA_READ_PERMISSIONS)`
- `GET` `/inspecoes-processo/auditoria-apontamentos` `get_inspecoes_processo_auditoria_apontamentos` — Inspections processo auditoria apontamentos — AuthZ: `require_any_permission(INSPECOES_PROCESSO_READ_PERMISSIONS)`
- `GET` `/inspecoes-processo/historico` `get_inspecoes_processo_historico` — In-process inspections — history — AuthZ: `require_any_permission(INSPECOES_PROCESSO_READ_PERMISSIONS)`
- `GET` `/inspecoes-processo/historico/detalhe` `get_inspecoes_processo_historico_detalhe` — Inspections processo history detail — AuthZ: `require_any_permission(INSPECOES_PROCESSO_READ_PERMISSIONS)`
- `GET` `/inspecoes-processo/por-ensaiador` `get_inspecoes_processo_por_ensaiador` — Inspections processo por tester — AuthZ: `require_any_permission(INSPECOES_PROCESSO_READ_PERMISSIONS)`
- `GET` `/inspecoes-processo/por-operacao` `get_inspecoes_processo_por_operacao` — Inspections processo por operacao — AuthZ: `require_any_permission(INSPECOES_PROCESSO_READ_PERMISSIONS)`
- `GET` `/inspecoes-processo/por-produto` `get_inspecoes_processo_por_produto` — Inspections processo por product — AuthZ: `require_any_permission(INSPECOES_PROCESSO_READ_PERMISSIONS)`
- `GET` `/inspecoes-processo/ranking-ensaio` `get_inspecoes_processo_ranking_ensaio` — Inspections processo ranking ensaio — AuthZ: `require_any_permission(INSPECOES_PROCESSO_READ_PERMISSIONS)`
- `GET` `/inspecoes-processo/resumo` `get_inspecoes_processo_resumo` — In-process inspections — summary KPIs — AuthZ: `require_any_permission(INSPECOES_PROCESSO_READ_PERMISSIONS)`
- `GET` `/quality/kaizens/records/{record_id}/at` `get_kaizen_at_date` — Get Kaizen At Date — AuthZ: `require_any_permission(KAIZEN_RECORDS_READ_PERMISSIONS)`
- `GET` `/quality/kaizens/{kaizen_id}` `get_kaizen_by_id` — Kaizen detail (PostgreSQL) — AuthZ: `require_any_permission(KPI_QUALITY_ACCESS)`
- `GET` `/quality/kaizens/records/{record_id}` `get_kaizen_record` — Kaizen record — AuthZ: `require_any_permission(KAIZEN_RECORDS_READ_PERMISSIONS)`
- `GET` `/quality/kaizens/records/summary` `get_kaizen_records_summary` — Get Kaizen Records Summary — AuthZ: `require_any_permission(KAIZEN_RECORDS_READ_PERMISSIONS)`
- `GET` `/quality/kaizens/records/{record_id}/revisions/{revision_number}` `get_kaizen_revision` — Get Kaizen Revision — AuthZ: `require_any_permission(KAIZEN_RECORDS_READ_PERMISSIONS)`
- `GET` `/quality/kaizens/records/savings-investment/series` `get_kaizen_savings_investment_series` — Get Kaizen savings vs investment series — AuthZ: `require_any_permission(KAIZEN_RECORDS_READ_PERMISSIONS)`
- `GET` `/quality/kaizens/records/{record_id}/savings-timeline` `get_kaizen_savings_timeline` — Get Kaizen Savings Timeline — AuthZ: `require_any_permission(KAIZEN_RECORDS_READ_PERMISSIONS)`
- `GET` `/quality/kaizens/summary` `get_kaizen_summary` — Kaizen summary — AuthZ: `require_any_permission(KPI_QUALITY_ACCESS)`
- `GET` `/quality/kaizens/summary/series` `get_kaizen_summary_series` — Kaizen summary series — AuthZ: `require_any_permission(KPI_QUALITY_ACCESS)`
- `GET` `/quality/nonconformities/series` `get_nonconformity_series` — Get Nonconformity Series — AuthZ: `require_any_permission(KPI_QUALITY_ACCESS)`
- `GET` `/quality/nonconformities/streak` `get_nonconformity_streak` — Days without quality nonconformity — AuthZ: `require_any_permission(KPI_QUALITY_ACCESS)`
- `GET` `/quality/ppm/external/series` `get_ppm_external_series` — Get External Ppm Series — AuthZ: `require_any_permission(KPI_QUALITY_ACCESS)`
- `GET` `/quality/ppm/external/summary` `get_ppm_external_summary` — External PPM — AuthZ: `require_any_permission(KPI_QUALITY_ACCESS)`
- `GET` `/process-inspection-plans/orders-without-plan` `get_process_inspection_plans_orders_without_plan` — Open production orders without inspection plan — AuthZ: `require_any_permission(INSPECOES_PROCESSO_READ_PERMISSIONS)`
- `GET` `/process-inspection-plans/products/{code}` `get_process_inspection_plans_product` — Process inspection plan detail by product — AuthZ: `require_any_permission(INSPECOES_PROCESSO_READ_PERMISSIONS)`
- `GET` `/process-inspection-plans/products` `get_process_inspection_plans_products` — Products with process inspection plan — AuthZ: `require_any_permission(INSPECOES_PROCESSO_READ_PERMISSIONS)`
- `GET` `/process-inspection-plans/products-without-plan` `get_process_inspection_plans_products_without_plan` — Products without inspection plan (open OPs) — AuthZ: `require_any_permission(INSPECOES_PROCESSO_READ_PERMISSIONS)`
- `GET` `/process-inspection-plans/summary` `get_process_inspection_plans_summary` — Process inspection plans — summary KPIs — AuthZ: `require_any_permission(INSPECOES_PROCESSO_READ_PERMISSIONS)`
- `GET` `/quality/produced-quantity` `get_produced_quantity` — Get Produced Quantity — AuthZ: `require_any_permission(KPI_QUALITY_ACCESS)`
- `GET` `/quality/action-plans/{plan_id}` `get_quality_action_plan_detail` — Quality action plan detail — AuthZ: `require_any_permission(QUALITY_ACTION_PLANS_READ_PERMISSIONS)`
- `GET` `/quality/action-plans/{plan_id}/evidences/{evidence_id}/content` `get_quality_action_plan_evidence_content` — Quality action plan evidence content — AuthZ: `require_any_permission(QUALITY_ACTION_PLANS_READ_PERMISSIONS)`
- `GET` `/quality/action-plans/intelligence/knowledge-graph` `get_quality_action_plan_knowledge_graph` — Quality action plan knowledge graph — AuthZ: `require_any_permission(QUALITY_ACTION_PLANS_READ_PERMISSIONS)`
- `GET` `/quality/action-plans/{plan_id}/revisions/{revision_number}` `get_quality_action_plan_revision` — Quality action plan revision — AuthZ: `require_any_permission(QUALITY_ACTION_PLANS_READ_PERMISSIONS)`
- `GET` `/quality/action-plans/{plan_id}/similar-cases` `get_quality_action_plan_similar_cases` — Quality action plan similar cases — AuthZ: `require_any_permission(QUALITY_ACTION_PLANS_READ_PERMISSIONS)`
- `GET` `/quality/action-plans/dashboard` `get_quality_action_plans_dashboard` — Indicator — Quality action plan dashboard — AuthZ: `require_any_permission(QUALITY_ACTION_PLANS_READ_PERMISSIONS)`
- `GET` `/quality/labels/{label_id}` `get_quality_label` — Get Label — AuthZ: `require_any_permission(QUALITY_LABELS_READ_PERMISSIONS)`
- `GET` `/quality/labels/{label_id}/certificate` `get_quality_label_certificate` — Get Certificate — AuthZ: `require_any_permission(QUALITY_LABELS_READ_PERMISSIONS)`
- `GET` `/quality/labels/inspectors/me` `get_quality_label_inspector` — Get My Inspector — AuthZ: `require_any_permission(QUALITY_LABELS_READ_PERMISSIONS)`
- `GET` `/quality/labels/inspectors/me/signature` `get_quality_label_inspector_signature` — Get inspector signature — AuthZ: `require_any_permission(QUALITY_LABELS_READ_PERMISSIONS)`
- `GET` `/quality/labels/{label_id}/qr` `get_quality_label_qr` — Get quality label QR — AuthZ: `require_any_permission(QUALITY_LABELS_READ_PERMISSIONS)`
- `GET` `/quality/returned-totals` `get_quality_returned_totals` — Returned quantity totals (NC QI2_QTDDEV) — AuthZ: `require_any_permission(KPI_QUALITY_ACCESS)`
- `GET` `/quality/rework-cost-pct` `get_quality_rework_cost_pct` — Quality rework cost / ROL — AuthZ: `require_any_permission(KPI_QUALITY_ACCESS)`
- `GET` `/quality/rework-cost-pct/series` `get_quality_rework_cost_pct_series` — Quality rework cost / ROL series — AuthZ: `require_any_permission(KPI_QUALITY_ACCESS)`
- `GET` `/quality/scrap-cost-pct` `get_quality_scrap_cost_pct` — Quality scrap cost / ROL — AuthZ: `require_any_permission(KPI_QUALITY_ACCESS)`
- `GET` `/quality/scrap-cost-pct/series` `get_quality_scrap_cost_pct_series` — Quality scrap cost / ROL series — AuthZ: `require_any_permission(KPI_QUALITY_ACCESS)`
- `GET` `/refugos/filtros` `get_refugos_filtros` — Indicator — Refugos filtros — AuthZ: `require_any_permission(SCRAP_MONITORING_READ_PERMISSIONS)`
- `GET` `/refugos/health` `get_refugos_health` — Indicator — Refugos health — AuthZ: `require_any_permission(SCRAP_MONITORING_READ_PERMISSIONS)`
- `GET` `/refugos/rankings` `get_refugos_rankings` — Scrap rankings — AuthZ: `require_any_permission(SCRAP_MONITORING_READ_PERMISSIONS)`
- `GET` `/refugos/registros` `get_refugos_registros` — Scrap loss records — AuthZ: `require_any_permission(SCRAP_MONITORING_READ_PERMISSIONS)`
- `GET` `/refugos/resumo` `get_refugos_resumo` — Scrap losses summary — AuthZ: `require_any_permission(SCRAP_MONITORING_READ_PERMISSIONS)`
- `GET` `/refugos/scrap_cost_pct` `get_refugos_scrap_cost_pct` — Scrap cost / ROL — AuthZ: `require_any_permission(SCRAP_MONITORING_READ_PERMISSIONS)`
- `GET` `/refugos/serie` `get_refugos_serie` — Refugos series — AuthZ: `require_any_permission(SCRAP_MONITORING_READ_PERMISSIONS)`
- `GET` `/retrabalhos/colaboradores` `get_retrabalhos_colaboradores` — List — Retrabalho horas improdutivas colaboradores — AuthZ: `require_any_permission(CONTROLE_RETRABALHO_READ_PERMISSIONS)`
- `GET` `/retrabalhos/detalhes` `get_retrabalhos_detalhes` — Rework appointment details — AuthZ: `require_any_permission(CONTROLE_RETRABALHO_READ_PERMISSIONS)`
- `GET` `/retrabalhos/filtros` `get_retrabalhos_filtros` — Indicator — Retrabalho horas improdutivas filtros — AuthZ: `require_any_permission(CONTROLE_RETRABALHO_READ_PERMISSIONS)`
- `GET` `/retrabalhos/health` `get_retrabalhos_health` — Indicator — Retrabalho horas improdutivas health — AuthZ: `require_any_permission(CONTROLE_RETRABALHO_READ_PERMISSIONS)`
- `GET` `/retrabalhos/mensal` `get_retrabalhos_mensal` — List — Retrabalho horas improdutivas mensal — AuthZ: `require_any_permission(CONTROLE_RETRABALHO_READ_PERMISSIONS)`
- `GET` `/retrabalhos/recursos` `get_retrabalhos_recursos` — List — Retrabalho horas improdutivas recursos — AuthZ: `require_any_permission(CONTROLE_RETRABALHO_READ_PERMISSIONS)`
- `GET` `/retrabalhos/resumo` `get_retrabalhos_resumo` — Rework hours summary — AuthZ: `require_any_permission(CONTROLE_RETRABALHO_READ_PERMISSIONS)`
- `GET` `/retrabalhos/rework_cost_pct` `get_retrabalhos_rework_cost_pct` — Rework cost / ROL — AuthZ: `require_any_permission(CONTROLE_RETRABALHO_READ_PERMISSIONS)`
- `GET` `/quality/audit-5s/areas` `list_audit_5s_areas` — List Areas — AuthZ: `require_any_permission(AUDIT_5S_READ_PERMISSIONS)`
- `GET` `/quality/audit-5s/audits/{audit_id}/nc-attachments` `list_audit_5s_audit_nc_attachments` — List Audit Nc Attachments — AuthZ: `require_any_permission(AUDIT_5S_READ_PERMISSIONS)`
- `GET` `/quality/audit-5s/audits` `list_audit_5s_audits` — List Audits — AuthZ: `require_any_permission(AUDIT_5S_READ_PERMISSIONS)`
- `GET` `/quality/audit-5s/catalog/publications` `list_audit_5s_catalog_publications` — List Catalog Publications — AuthZ: `require_any_permission(AUDIT_5S_READ_PERMISSIONS)`
- `GET` `/quality/audit-5s/criteria` `list_audit_5s_criteria` — List Criteria — AuthZ: `require_any_permission(AUDIT_5S_READ_PERMISSIONS)`
- `GET` `/quality/audit-5s/nonconformities/{nc_id}/actions` `list_audit_5s_nc_actions` — List Nc Actions — AuthZ: `require_any_permission(AUDIT_5S_READ_PERMISSIONS)`
- `GET` `/quality/audit-5s/audits/{audit_id}/nc-candidates` `list_audit_5s_nc_candidates` — List Nc Candidates — AuthZ: `require_any_permission(AUDIT_5S_READ_PERMISSIONS)`
- `GET` `/quality/audit-5s/audits/{audit_id}/nonconformities` `list_audit_5s_nonconformities` — List Audit Nonconformities — AuthZ: `require_any_permission(AUDIT_5S_READ_PERMISSIONS)`
- `GET` `/quality/audit-5s/nonconformities` `list_audit_5s_nonconformities_board` — List Audit 5S Nonconformities Board — AuthZ: `require_any_permission(AUDIT_5S_READ_PERMISSIONS)`
- `GET` `/inspecoes-processo/operations/inspections` `list_inspecoes_processo_operation_inspections` — Process inspections for OP+operation — AuthZ: `require_any_permission(INSPECOES_PROCESSO_READ_PERMISSIONS)`
- `GET` `/quality/kaizens/records/{record_id}/audit-log` `list_kaizen_audit_log` — List Kaizen Audit Log — AuthZ: `require_any_permission(KAIZEN_RECORDS_READ_PERMISSIONS)`
- `GET` `/quality/kaizens/records/{record_id}/evidences` `list_kaizen_evidences` — List Kaizen Evidences — AuthZ: `require_any_permission(KAIZEN_RECORDS_READ_PERMISSIONS)`
- `GET` `/quality/kaizens/records/{record_id}/history` `list_kaizen_history` — List Kaizen History — AuthZ: `require_any_permission(KAIZEN_RECORDS_READ_PERMISSIONS)`
- `GET` `/quality/kaizens/records` `list_kaizen_records` — Kaizen records — AuthZ: `require_any_permission(KAIZEN_RECORDS_READ_PERMISSIONS)`
- `GET` `/quality/kaizens/records/{record_id}/revisions` `list_kaizen_revisions` — List Kaizen Revisions — AuthZ: `require_any_permission(KAIZEN_RECORDS_READ_PERMISSIONS)`
- `GET` `/quality/nonconformities` `list_nonconformities` — List Nonconformity Route — AuthZ: `require_any_permission(KPI_QUALITY_ACCESS)`
- `GET` `/quality/ppm/external` `list_ppm_external` — List External Ppm — AuthZ: `require_any_permission(KPI_QUALITY_ACCESS)`
- `GET` `/quality/ppm/internal` `list_ppm_internal` — List Internal Ppm — AuthZ: `require_any_permission(KPI_QUALITY_ACCESS)`
- `GET` `/quality/action-plans/assignable-users` `list_quality_action_plan_assignable_users` — Paged list — Directory user — AuthZ: `require_any_permission(QUALITY_ACTION_PLANS_READ_PERMISSIONS)`
- `GET` `/quality/action-plans/{plan_id}/audit-log` `list_quality_action_plan_audit_log` — Paged list — Quality action plan audit log — AuthZ: `require_any_permission(QUALITY_ACTION_PLANS_VALIDATE_EFFECTIVENESS_PERMISSIONS)`
- `GET` `/quality/action-plans/{plan_id}/evidences` `list_quality_action_plan_evidences` — Paged list — Quality action plan evidence — AuthZ: `require_any_permission(QUALITY_ACTION_PLANS_READ_PERMISSIONS)`
- `GET` `/quality/action-plans/my-queue` `list_quality_action_plan_my_queue` — Paged list — Quality action plan action — AuthZ: `require_any_permission(QUALITY_ACTION_PLANS_READ_PERMISSIONS)`
- `GET` `/quality/action-plans/effectiveness-review/pending` `list_quality_action_plan_pending_effectiveness_reviews` — Paged list — Quality action plan — AuthZ: `require_any_permission(QUALITY_ACTION_PLANS_VALIDATE_EFFECTIVENESS_PERMISSIONS)`
- `GET` `/quality/action-plans/{plan_id}/revisions` `list_quality_action_plan_revisions` — Paged list — Quality action plan revision — AuthZ: `require_any_permission(QUALITY_ACTION_PLANS_READ_PERMISSIONS)`
- `GET` `/quality/action-plans` `list_quality_action_plans` — Paged list — Quality action plan — AuthZ: `require_any_permission(QUALITY_ACTION_PLANS_READ_PERMISSIONS)`
- `GET` `/quality/action-plans/overdue` `list_quality_action_plans_overdue` — Paged list — Quality action plan — AuthZ: `require_any_permission(QUALITY_ACTION_PLANS_READ_PERMISSIONS)`
- `GET` `/quality/action-plans/recurrence` `list_quality_action_plans_recurrence` — Paged list — Quality action plan recurrence — AuthZ: `require_any_permission(QUALITY_ACTION_PLANS_READ_PERMISSIONS)`
- `GET` `/quality/branches` `list_quality_branches` — List Quality Branches — AuthZ: `require_any_permission(KPI_QUALITY_ACCESS)`
- `GET` `/quality/labels/audit-events` `list_quality_label_audit_events` — List Audit Events — AuthZ: `require_any_permission(QUALITY_LABELS_READ_PERMISSIONS)`
- `GET` `/quality/labels/checklist-template` `list_quality_label_checklist_template` — List Checklist Template — AuthZ: `require_any_permission(QUALITY_LABELS_READ_PERMISSIONS)`
- `GET` `/quality/labels` `list_quality_labels` — List Labels — AuthZ: `require_any_permission(QUALITY_LABELS_READ_PERMISSIONS)`
- `GET` `/quality/solution-patterns` `list_quality_solution_patterns` — Paged list — Quality solution pattern — AuthZ: `require_any_permission(QUALITY_ACTION_PLANS_READ_PERMISSIONS)`
- `GET` `/quality/labels/lookup-op/{production_order}` `lookup_quality_label_op` — Lookup quality label op — AuthZ: `require_any_permission(QUALITY_LABELS_WRITE_PERMISSIONS)`
- `GET` `/quality/action-plans/evidences/search` `search_quality_action_plan_evidences` — Paged list — Quality action plan evidence — AuthZ: `require_any_permission(QUALITY_ACTION_PLANS_READ_PERMISSIONS)`
- `GET` `/quality/labels/search-ops` `search_quality_label_ops` — Search Ops — AuthZ: `require_any_permission(QUALITY_LABELS_WRITE_PERMISSIONS)`

### WAVE_CANDIDATE_D — Finance & Budgeting (50 routes)

- `GET` `/financeiro/despesas-centro-custo/filtros` `get_financeiro_despesas_centro_custo_filtros` — Indicator — financial expenses cost center filtros — AuthZ: `require_any_permission(FINANCEIRO_CENTRO_CUSTO_READ_PERMISSIONS)`
- `GET` `/financeiro/despesas-centro-custo/lancamentos` `get_financeiro_despesas_centro_custo_lancamentos` — Cost-center expenses — ledger entries — AuthZ: `require_any_permission(FINANCEIRO_CENTRO_CUSTO_READ_PERMISSIONS)`
- `GET` `/financeiro/despesas-centro-custo/ranking-centros` `get_financeiro_despesas_centro_custo_ranking_centros` — Financial expenses cost center ranking centers — AuthZ: `require_any_permission(FINANCEIRO_CENTRO_CUSTO_READ_PERMISSIONS)`
- `GET` `/financeiro/despesas-centro-custo/ranking-fornecedores` `get_financeiro_despesas_centro_custo_ranking_fornecedores` — Financial expenses cost center ranking suppliers — AuthZ: `require_any_permission(FINANCEIRO_CENTRO_CUSTO_READ_PERMISSIONS)`
- `GET` `/financeiro/despesas-centro-custo/resumo` `get_financeiro_despesas_centro_custo_resumo` — Cost-center expenses — summary KPIs — AuthZ: `require_any_permission(FINANCEIRO_CENTRO_CUSTO_READ_PERMISSIONS)`
- `GET` `/financeiro/despesas-centro-custo/serie` `get_financeiro_despesas_centro_custo_serie` — Financial expenses cost center series — AuthZ: `require_any_permission(FINANCEIRO_CENTRO_CUSTO_READ_PERMISSIONS)`
- `GET` `/financeiro/inadimplencia/clientes` `get_financeiro_inadimplencia_clientes` — Delinquency — customers ranking — AuthZ: `require_any_permission(FINANCEIRO_INADIMPLENCIA_READ_PERMISSIONS)`
- `GET` `/financeiro/inadimplencia/faixas-atraso` `get_financeiro_inadimplencia_faixas_atraso` — List — financial inadimplencia faixas atraso — AuthZ: `require_any_permission(FINANCEIRO_INADIMPLENCIA_READ_PERMISSIONS)`
- `GET` `/financeiro/inadimplencia/mensal` `get_financeiro_inadimplencia_mensal` — List — financial inadimplencia mensal — AuthZ: `require_any_permission(FINANCEIRO_INADIMPLENCIA_READ_PERMISSIONS)`
- `GET` `/financeiro/inadimplencia/resumo` `get_financeiro_inadimplencia_resumo` — Delinquency — summary KPIs — AuthZ: `require_any_permission(FINANCEIRO_INADIMPLENCIA_READ_PERMISSIONS)`
- `GET` `/financeiro/inadimplencia/titulos` `get_financeiro_inadimplencia_titulos` — Delinquency — titles list — AuthZ: `require_any_permission(FINANCEIRO_INADIMPLENCIA_READ_PERMISSIONS)`
- `GET` `/financial/ebitda_pct` `get_financial_ebitda_pct` — Financial EBITDA percentage — AuthZ: `require_any_permission(KPI_FINANCIAL_ACCESS)`
- `GET` `/financial/fixed_cost_pct` `get_financial_fixed_cost_pct` — Financial fixed cost percentage — AuthZ: `require_any_permission(KPI_FINANCIAL_ACCESS)`
- `GET` `/financial/pmr` `get_financial_pmr` — Financial pmr — AuthZ: `require_any_permission(KPI_FINANCIAL_ACCESS)`
- `GET` `/financial/purchase-freight/links` `get_financial_purchase_freight_links` — Purchase invoice to freight document links — AuthZ: `require_any_permission(KPI_FINANCIAL_ACCESS)`
- `GET` `/financial/rol` `get_financial_rol` — Financial ROL consolidated KPI by branch — AuthZ: `require_any_permission(KPI_FINANCIAL_ACCESS)`
- `GET` `/financial/rol/invoices` `get_financial_rol_invoices` — ROL invoices (sales and returns) — AuthZ: `require_any_permission(KPI_FINANCIAL_ACCESS)`
- `GET` `/lancamento-notas-fiscais/requests/{request_id}` `get_lancamento_notas_fiscais_request` — Get Request — AuthZ: `require_any_permission(LANCAMENTO_NOTAS_FISCAIS_READ_PERMISSIONS)`
- `GET` `/planejamento-orcamentario/capex/categories/{category_id}/icon-image` `get_planejamento_orcamentario_capex_category_icon_image` — Get Capex Category Icon Image — AuthZ: `require_any_permission(PLANEJAMENTO_ORCAMENTARIO_ACCESS_PERMISSIONS)`
- `GET` `/planejamento-orcamentario/capex/consolidation/summary` `get_planejamento_orcamentario_capex_consolidation_summary` — Get Capex Consolidation Summary — AuthZ: `require_any_permission(PLANEJAMENTO_ORCAMENTARIO_CAPEX_CONSOLIDATION_VIEW_PERMISSIONS)`
- `GET` `/planejamento-orcamentario/capex/investments/{investment_id}` `get_planejamento_orcamentario_capex_investment` — Get Capex Investment — AuthZ: `require_any_permission(PLANEJAMENTO_ORCAMENTARIO_ACCESS_PERMISSIONS)`
- `GET` `/planejamento-orcamentario/capex/plans/{plan_id}` `get_planejamento_orcamentario_capex_plan` — Get Capex Plan — AuthZ: `require_any_permission(PLANEJAMENTO_ORCAMENTARIO_ACCESS_PERMISSIONS)`
- `GET` `/planejamento-orcamentario/capex/review/{plan_id}` `get_planejamento_orcamentario_capex_review` — Get Capex Review — AuthZ: `require_any_permission(PLANEJAMENTO_ORCAMENTARIO_CAPEX_APPROVE_PERMISSIONS)`
- `GET` `/planejamento-orcamentario/context` `get_planejamento_orcamentario_context` — Get Context — AuthZ: `require_any_permission(PLANEJAMENTO_ORCAMENTARIO_ACCESS_PERMISSIONS)`
- `GET` `/planejamento-orcamentario/guidance/current` `get_planejamento_orcamentario_guidance_current` — Get Guidance Current — AuthZ: `require_any_permission(PLANEJAMENTO_ORCAMENTARIO_GUIDANCE_VIEW_PERMISSIONS)`
- `GET` `/planejamento-orcamentario/personnel/plans/{plan_id}` `get_planejamento_orcamentario_personnel_plan` — Get Personnel Plan — AuthZ: `require_any_permission(PLANEJAMENTO_ORCAMENTARIO_PERSONNEL_VIEW_PERMISSIONS)`
- `GET` `/planejamento-orcamentario/personnel/review/{plan_id}` `get_planejamento_orcamentario_personnel_review` — Get Personnel Review — AuthZ: `require_any_permission(PLANEJAMENTO_ORCAMENTARIO_PERSONNEL_APPROVE_PERMISSIONS)`
- `GET` `/lancamento-notas-fiscais/requests/{request_id}/purchase-orders` `list_lancamento_notas_fiscais_request_purchase_orders` — List Request Purchase Orders — AuthZ: `require_any_permission(LANCAMENTO_NOTAS_FISCAIS_READ_PERMISSIONS)`
- `GET` `/lancamento-notas-fiscais/requests` `list_lancamento_notas_fiscais_requests` — List Requests — AuthZ: `require_any_permission(LANCAMENTO_NOTAS_FISCAIS_READ_PERMISSIONS)`
- `GET` `/planejamento-orcamentario/capex/categories` `list_planejamento_orcamentario_capex_categories` — List Capex Categories — AuthZ: `require_any_permission(PLANEJAMENTO_ORCAMENTARIO_ACCESS_PERMISSIONS)`
- `GET` `/planejamento-orcamentario/capex/consolidation/by-area` `list_planejamento_orcamentario_capex_consolidation_by_area` — List Capex Consolidation By Area — AuthZ: `require_any_permission(PLANEJAMENTO_ORCAMENTARIO_CAPEX_CONSOLIDATION_VIEW_PERMISSIONS)`
- `GET` `/planejamento-orcamentario/capex/consolidation/by-category` `list_planejamento_orcamentario_capex_consolidation_by_category` — List Capex Consolidation By Category — AuthZ: `require_any_permission(PLANEJAMENTO_ORCAMENTARIO_CAPEX_CONSOLIDATION_VIEW_PERMISSIONS)`
- `GET` `/planejamento-orcamentario/capex/consolidation/by-cost-center` `list_planejamento_orcamentario_capex_consolidation_by_cost_center` — List Capex Consolidation By Cost Center — AuthZ: `require_any_permission(PLANEJAMENTO_ORCAMENTARIO_CAPEX_CONSOLIDATION_VIEW_PERMISSIONS)`
- `GET` `/planejamento-orcamentario/capex/consolidation/by-month` `list_planejamento_orcamentario_capex_consolidation_by_month` — List Capex Consolidation By Month — AuthZ: `require_any_permission(PLANEJAMENTO_ORCAMENTARIO_CAPEX_CONSOLIDATION_VIEW_PERMISSIONS)`
- `GET` `/planejamento-orcamentario/capex/consolidation/by-origin` `list_planejamento_orcamentario_capex_consolidation_by_origin` — List Capex Consolidation By Origin — AuthZ: `require_any_permission(PLANEJAMENTO_ORCAMENTARIO_CAPEX_CONSOLIDATION_VIEW_PERMISSIONS)`
- `GET` `/planejamento-orcamentario/capex/consolidation/by-plan-status` `list_planejamento_orcamentario_capex_consolidation_by_plan_status` — List Capex Consolidation By Plan Status — AuthZ: `require_any_permission(PLANEJAMENTO_ORCAMENTARIO_CAPEX_CONSOLIDATION_VIEW_PERMISSIONS)`
- `GET` `/planejamento-orcamentario/capex/consolidation/by-priority` `list_planejamento_orcamentario_capex_consolidation_by_priority` — List Capex Consolidation By Priority — AuthZ: `require_any_permission(PLANEJAMENTO_ORCAMENTARIO_CAPEX_CONSOLIDATION_VIEW_PERMISSIONS)`
- `GET` `/planejamento-orcamentario/capex/consolidation/by-unit` `list_planejamento_orcamentario_capex_consolidation_by_unit` — List Capex Consolidation By Unit — AuthZ: `require_any_permission(PLANEJAMENTO_ORCAMENTARIO_CAPEX_CONSOLIDATION_VIEW_PERMISSIONS)`
- `GET` `/planejamento-orcamentario/capex/consolidation/details` `list_planejamento_orcamentario_capex_consolidation_details` — List Capex Consolidation Details — AuthZ: `require_any_permission(PLANEJAMENTO_ORCAMENTARIO_CAPEX_CONSOLIDATION_VIEW_PERMISSIONS)`
- `GET` `/planejamento-orcamentario/capex/investments` `list_planejamento_orcamentario_capex_investments` — List Capex Investments — AuthZ: `require_any_permission(PLANEJAMENTO_ORCAMENTARIO_ACCESS_PERMISSIONS)`
- `GET` `/planejamento-orcamentario/capex/my-responsibilities` `list_planejamento_orcamentario_capex_my_responsibilities` — List Capex My Responsibilities — AuthZ: `require_any_permission(PLANEJAMENTO_ORCAMENTARIO_ACCESS_PERMISSIONS)`
- `GET` `/planejamento-orcamentario/capex/plans/{plan_id}/history` `list_planejamento_orcamentario_capex_plan_history` — List Capex Plan History — AuthZ: `require_any_permission(PLANEJAMENTO_ORCAMENTARIO_ACCESS_PERMISSIONS)`
- `GET` `/planejamento-orcamentario/capex/plans` `list_planejamento_orcamentario_capex_plans` — List Capex Plans — AuthZ: `require_any_permission(PLANEJAMENTO_ORCAMENTARIO_ACCESS_PERMISSIONS)`
- `GET` `/planejamento-orcamentario/capex/review-queue` `list_planejamento_orcamentario_capex_review_queue` — List Capex Review Queue — AuthZ: `require_any_permission(PLANEJAMENTO_ORCAMENTARIO_CAPEX_APPROVE_PERMISSIONS)`
- `GET` `/planejamento-orcamentario/guidance/current/documents` `list_planejamento_orcamentario_guidance_documents` — List Guidance Documents — AuthZ: `require_any_permission(PLANEJAMENTO_ORCAMENTARIO_GUIDANCE_VIEW_PERMISSIONS)`
- `GET` `/planejamento-orcamentario/org/erp-cost-centers` `list_planejamento_orcamentario_org_erp_cost_centers` — List Erp Cost Centers — AuthZ: `require_any_permission(PLANEJAMENTO_ORCAMENTARIO_ACCESS_PERMISSIONS)`
- `GET` `/planejamento-orcamentario/personnel/plans/{plan_id}/history` `list_planejamento_orcamentario_personnel_plan_history` — List Personnel Plan History — AuthZ: `require_any_permission(PLANEJAMENTO_ORCAMENTARIO_PERSONNEL_VIEW_PERMISSIONS)`
- `GET` `/planejamento-orcamentario/personnel/plans` `list_planejamento_orcamentario_personnel_plans` — List Personnel Plans — AuthZ: `require_any_permission(PLANEJAMENTO_ORCAMENTARIO_PERSONNEL_VIEW_PERMISSIONS)`
- `GET` `/planejamento-orcamentario/personnel/review-queue` `list_planejamento_orcamentario_personnel_review_queue` — List Personnel Review Queue — AuthZ: `require_any_permission(PLANEJAMENTO_ORCAMENTARIO_PERSONNEL_APPROVE_PERMISSIONS)`
- `GET` `/lancamento-notas-fiscais/suppliers` `search_lancamento_notas_fiscais_suppliers` — Search Suppliers — AuthZ: `require_permission(LANCAMENTO_NOTAS_FISCAIS_CREATE)`

### WAVE_CANDIDATE_E — Commercial & Sales analytics (27 routes)

- `GET` `/commercial/billing-portfolio/by-branch` `get_billing_portfolio_by_branch` — Billing portfolio by branch (forecast × realized) — AuthZ: `require_any_permission(KPI_COMMERCIAL_ACCESS)`
- `GET` `/commercial/billing-portfolio/by-customer` `get_billing_portfolio_by_customer` — Billing portfolio by customer (forecast × realized) — AuthZ: `require_any_permission(KPI_COMMERCIAL_ACCESS)`
- `GET` `/commercial/billing-portfolio/series` `get_billing_portfolio_series` — Billing portfolio series (forecast × realized) — AuthZ: `require_any_permission(KPI_COMMERCIAL_ACCESS)`
- `GET` `/commercial/billing-portfolio/summary` `get_billing_portfolio_summary` — Billing portfolio summary (forecast × realized) — AuthZ: `require_any_permission(KPI_COMMERCIAL_ACCESS)`
- `GET` `/commercial/profile-by-branch` `get_commercial_profile_by_branch` — Commercial profile by branch (OTD, conversion, new business, ROL attai — AuthZ: `require_any_permission(KPI_COMMERCIAL_ACCESS)`
- `GET` `/commercial/rol/by-customer-center` `get_commercial_rol_by_customer_center` — Commercial ROL by customer center — AuthZ: `require_any_permission(KPI_COMMERCIAL_ACCESS)`
- `GET` `/pedidos-venda-abertos/customers/{codigo}/{loja}/avatar` `get_customer_avatar` — Get customer avatar — AuthZ: `require_any_permission(PEDIDOS_VENDA_ABERTOS_PERMISSIONS)`
- `GET` `/pedidos-venda-abertos/sellers/me` `get_my_seller_portfolio` — My seller portfolio — AuthZ: `require_any_permission(PEDIDOS_VENDA_ABERTOS_PERMISSIONS)`
- `GET` `/propostas-comerciais/{proposta_interna}` `get_proposta_comercial` — Proposta comercial — AuthZ: `require_any_permission(PROPOSTAS_COMERCIAIS_ACCESS)`
- `GET` `/pedidos-venda-abertos/sellers/{seller_id}` `get_seller_portfolio` — Get seller portfolio — AuthZ: `require_any_permission(PEDIDOS_VENDA_ABERTOS_ADMIN_PERMISSIONS)`
- `GET` `/pedidos-venda-abertos/totvs-outbound-invoices/{branch}/{invoice_number}/{invoice_series}` `get_totvs_outbound_invoice` — TOTVS outbound invoice by key — AuthZ: `require_any_permission(PEDIDOS_VENDA_ABERTOS_PERMISSIONS)`
- `GET` `/pedidos-venda-abertos/clientes/{codigo}/{loja}/notas-fiscais` `list_cliente_notas_fiscais_saida` — Customer outbound invoices by code and store — AuthZ: `require_any_permission(PEDIDOS_VENDA_ABERTOS_PERMISSIONS)`
- `GET` `/commercial/customer-center-assignments` `list_commercial_customer_center_assignments` — Lista — Commercial customer center assignment — AuthZ: `require_any_permission(KPI_COMMERCIAL_ACCESS)`
- `GET` `/commercial/customer-centers` `list_commercial_customer_centers` — Lista — Commercial customer center — AuthZ: `require_any_permission(KPI_COMMERCIAL_ACCESS)`
- `POST` `/pedidos-venda-abertos/customers/billing-series` `list_customer_billing_series` — Customer billing series — AuthZ: `require_any_permission(PEDIDOS_VENDA_ABERTOS_PERMISSIONS)`
- `POST` `/pedidos-venda-abertos/customers/open-order-metrics` `list_customer_open_order_metrics` — Lista paginada — Customer open order metrics — AuthZ: `require_any_permission(PEDIDOS_VENDA_ABERTOS_PERMISSIONS)`
- `GET` `/pedidos-venda-abertos/ops-abertas` `list_ops_abertas_pedidos_venda` — Production orders open orders sales — AuthZ: `require_any_permission(PEDIDOS_VENDA_ABERTOS_PERMISSIONS)`
- `GET` `/pedidos-venda-abertos/` `list_pedidos_venda_abertos` — Orders sales abertos — AuthZ: `require_any_permission(PEDIDOS_VENDA_ABERTOS_PERMISSIONS)`
- `GET` `/propostas-comerciais/` `list_propostas_comerciais` — Paged list — Proposta comercial interna (pdf/totvs) — AuthZ: `require_any_permission(PROPOSTAS_COMERCIAIS_ACCESS)`
- `GET` `/sales/` `list_sale_orders` — Sale orders — AuthZ: `require_permission(API_DELPI_ACCESS)`
- `GET` `/pedidos-venda-abertos/sellers` `list_seller_portfolios` — List seller portfolios — AuthZ: `require_any_permission(PEDIDOS_VENDA_ABERTOS_ADMIN_PERMISSIONS)`
- `GET` `/pedidos-venda-abertos/totvs-open-orders` `list_totvs_open_orders` — TOTVS open sales orders (no portfolio membership) — AuthZ: `require_any_permission(PEDIDOS_VENDA_ABERTOS_PERMISSIONS)`
- `GET` `/pedidos-venda-abertos/totvs-open-orders/{customer_code}/{customer_store}` `list_totvs_open_orders_by_customer` — TOTVS open sales orders by customer — AuthZ: `require_any_permission(PEDIDOS_VENDA_ABERTOS_PERMISSIONS)`
- `GET` `/pedidos-venda-abertos/totvs-outbound-invoices/{customer_code}/{customer_store}` `list_totvs_outbound_invoices` — TOTVS outbound invoices (no portfolio membership) — AuthZ: `require_any_permission(PEDIDOS_VENDA_ABERTOS_PERMISSIONS)`
- `GET` `/pedidos-venda-abertos/totvs-recently-closed-orders` `list_totvs_recently_closed_orders` — Lista paginada — Pedidos de venda em aberto — AuthZ: `require_any_permission(PEDIDOS_VENDA_ABERTOS_PERMISSIONS)`
- `GET` `/pedidos-venda-abertos/customers/search` `search_active_customers_for_portfolio` — Search active TOTVS customers for portfolio — AuthZ: `require_any_permission(PEDIDOS_VENDA_ABERTOS_PERMISSIONS)`
- `GET` `/customers/search` `search_customers` — Search Customers Route — AuthZ: `require_permission(API_DELPI_ACCESS)`

### WAVE_CANDIDATE_F — Product Master extensions (13 routes)

- `GET` `/products/directives/{identifier}` `get_product_directives` — Product directives — AuthZ: `require_permission(API_DELPI_ACCESS)`
- `GET` `/products/{code}/inbound-invoice-items` `get_product_inbound_invoice_items` — Product inbound invoice items — AuthZ: `require_permission(API_DELPI_ACCESS)`
- `GET` `/products/{code}/internal-movements` `get_product_internal_movements` — Product internal movements — AuthZ: `require_permission(API_DELPI_ACCESS)`
- `GET` `/products/{code}/outbound-invoice-items` `get_product_outbound_invoice_items` — Product outbound invoice items — AuthZ: `require_permission(API_DELPI_ACCESS)`
- `GET` `/products/{code}/purchase-budget-history` `get_product_purchase_budget_history` — Product purchase budget history — AuthZ: `require_permission(API_DELPI_ACCESS)`
- `GET` `/products/{code}/raw-material-set-shortages` `get_product_raw_material_set_shortages` — Raw-material shortages in the finished-product order set — AuthZ: `require_permission(API_DELPI_ACCESS)`
- `GET` `/products/{code}/sales/billing` `get_product_sales_billing` — Faturamento do product — AuthZ: `require_permission(API_DELPI_ACCESS)`
- `GET` `/products/{code}/sales/open-orders` `get_product_sales_open_orders` — Product sales open orders — AuthZ: `require_permission(API_DELPI_ACCESS)`
- `GET` `/products/{code}/sales` `get_product_sales_summary` — Product sales summary — AuthZ: `require_permission(API_DELPI_ACCESS)`
- `GET` `/products/exclusive-raw-materials/catalog` `list_exclusive_raw_materials_catalog` — Exclusive raw materials catalog — AuthZ: `require_permission(API_DELPI_ACCESS)`
- `POST` `/products/inventory-blocks` `list_product_inventory_blocks` — Lista — Bloqueio de inventário sb2 (b2_dtinv/b2_dinvfim) de vários pro — AuthZ: `require_permission(API_DELPI_ACCESS)`
- `POST` `/products/physical-locations` `list_product_physical_locations` — Physical pickup locations in batch — AuthZ: `require_permission(API_DELPI_ACCESS)`
- `GET` `/products/by-supplier-part-number` `search_products_by_supplier_part_number` — Products by supplier part number — AuthZ: `require_permission(API_DELPI_ACCESS)`

### WAVE_CANDIDATE_G — Supplies & Purchasing detail (10 routes)

- `GET` `/invoice-issuance/requests/{request_id}` `get_invoice_issuance_request` — Get invoice issuance request — AuthZ: `require_any_permission(INVOICE_ISSUANCE_READ_PERMISSIONS)`
- `GET` `/purchases/top-products` `get_purchases_top_products` — product mais comprados no period — AuthZ: `require_permission(API_DELPI_ACCESS)`
- `GET` `/request-lookups/products/{code}/warehouse-01-balance` `get_request_lookup_warehouse_01_balance` — Warehouse 01 stock hint (request lookups) — AuthZ: `require_any_permission(REQUEST_LOOKUPS_PERMISSIONS)`
- `GET` `/supplies/purchase-orders/{branch}/{order_number}` `get_supplies_purchase_order` — Open purchase order detail — AuthZ: `require_any_permission_or_supplies_bff(KPI_SUPPLIES_ACCESS)`
- `GET` `/invoice-issuance/requests` `list_invoice_issuance_requests` — List invoice issuance requests — AuthZ: `require_any_permission(INVOICE_ISSUANCE_READ_PERMISSIONS)`
- `GET` `/request-lookups/open-sales-orders` `list_request_lookup_open_sales_orders` — List open sales orders for request lookups — AuthZ: `require_any_permission(REQUEST_LOOKUPS_PERMISSIONS)`
- `GET` `/supplies/purchase-orders` `list_supplies_purchase_orders` — Lista paginada — Linhas de pedidos de compra em aberto (sc7) — AuthZ: `require_any_permission_or_supplies_bff(KPI_SUPPLIES_ACCESS)`
- `GET` `/request-lookups/carriers` `search_request_lookup_carriers` — Search request-engine carriers — AuthZ: `require_any_permission(REQUEST_LOOKUPS_PERMISSIONS)`
- `GET` `/request-lookups/parties` `search_request_lookup_parties` — Search request-engine parties — AuthZ: `require_any_permission(REQUEST_LOOKUPS_PERMISSIONS)`
- `GET` `/request-lookups/products` `search_request_lookup_products` — Search request-engine products — AuthZ: `require_any_permission(REQUEST_LOOKUPS_PERMISSIONS)`

### WAVE_CANDIDATE_H — Engineering (22 routes)

- `GET` `/engineering/lmps/{sale_number}` `get_lmp_by_sale_number` — Lmp by sale number — AuthZ: `require_any_permission(ENGINEERING_LMP_ACCESS)`
- `GET` `/engineering/lmps/{sale_number}/history/events` `get_lmp_history_events` — Lmp history events — AuthZ: `require_any_permission(ENGINEERING_LMP_ACCESS)`
- `GET` `/engineering/lmps/{sale_number}/history/flow` `get_lmp_history_flow` — Lmp history flow — AuthZ: `require_any_permission(ENGINEERING_LMP_ACCESS)`
- `GET` `/engineering/lmps/nonconformities/{record_id}` `get_lmp_nonconformity` — Get LMP nonconformity by id — AuthZ: `require_any_permission(ENGINEERING_LMP_ACCESS)`
- `GET` `/engineering/lmps/nonconformities/streak` `get_lmp_nonconformity_streak` — LMP nonconformity days-without streak — AuthZ: `require_any_permission(ENGINEERING_LMP_ACCESS)`
- `GET` `/engineering/lmps/dashboard/charts` `get_lmps_dashboard_charts` — Lmps dashboard charts — AuthZ: `require_any_permission(ENGINEERING_LMP_ACCESS)`
- `GET` `/engineering/lmps/dashboard/summary` `get_lmps_dashboard_summary` — LMPs dashboard summary — AuthZ: `require_any_permission(ENGINEERING_LMP_ACCESS)`
- `GET` `/engineering/mini-applicators/ferramentas/{codigo}` `get_mini_applicators_ferramenta` — Mini applicators tool — AuthZ: `require_any_permission(MINI_APPLICATORS_ACCESS)`
- `GET` `/engineering/mini-applicators/ferramentas/{codigo}/golpes` `get_mini_applicators_golpes` — Golpes do mini-aplicador no period — AuthZ: `require_any_permission(MINI_APPLICATORS_ACCESS)`
- `GET` `/engineering/transforma-mais/processes/summary` `get_transforma_mais_summary` — Transforma mais summary — AuthZ: `require_any_permission(ENGINEERING_LMP_ACCESS)`
- `GET` `/engineering/transformometro/savings-investment/series` `get_transformometro_savings_investment_series` — Economia bruta vs Investimento do TRANSFORMA+ DELPI — AuthZ: `require_any_permission(ENGINEERING_TRANSFORMOMETRO_ACCESS)`
- `GET` `/engineering/lmps/nonconformities` `list_lmp_nonconformities` — List LMP nonconformities — AuthZ: `require_any_permission(ENGINEERING_LMP_ACCESS)`
- `GET` `/engineering/lmps/nonconformities/{record_id}/history` `list_lmp_nonconformity_history` — List LMP nonconformity change history — AuthZ: `require_any_permission(ENGINEERING_LMP_ACCESS)`
- `GET` `/engineering/lmps/nonconformities/problem-tags` `list_lmp_problem_tags` — List LMP problem tags — AuthZ: `require_any_permission(ENGINEERING_LMP_ACCESS)`
- `GET` `/engineering/lmps` `list_lmps` — list LMPs (ordens especiais / amostras) — AuthZ: `require_any_permission(ENGINEERING_LMP_ACCESS)`
- `GET` `/engineering/lmps/dashboard` `list_lmps_dashboard` — LMPs dashboard — AuthZ: `require_any_permission(ENGINEERING_LMP_ACCESS)`
- `GET` `/engineering/lmps/dashboard/items` `list_lmps_dashboard_items` — Lmps dashboard items — AuthZ: `require_any_permission(ENGINEERING_LMP_ACCESS)`
- `GET` `/engineering/mini-applicators/ferramentas/{codigo}/componentes` `list_mini_applicators_componentes` — Mini applicators components — AuthZ: `require_any_permission(MINI_APPLICATORS_ACCESS)`
- `GET` `/engineering/mini-applicators/ferramentas` `list_mini_applicators_ferramentas` — list ferramentas mini-aplicadores — AuthZ: `require_any_permission(MINI_APPLICATORS_ACCESS)`
- `GET` `/engineering/mini-applicators/ferramentas/{codigo}/pecas` `list_mini_applicators_pecas` — Mini applicators pecas — AuthZ: `require_any_permission(MINI_APPLICATORS_ACCESS)`
- `GET` `/engineering/mini-applicators/pecas-reposicao` `list_mini_applicators_pecas_reposicao` — Mini applicators pecas reposicao — AuthZ: `require_any_permission(MINI_APPLICATORS_ACCESS)`
- `GET` `/engineering/transforma-mais/processes` `list_transforma_mais_processes` — list processos Transforma Mais — AuthZ: `require_any_permission(ENGINEERING_LMP_ACCESS)`

### WAVE_CANDIDATE_I — Long tail: HR / Reports / Scheduling / Procedures / Reference / Public surface (28 routes)

- `GET` `/cultura-delpi/content` `get_cultura_delpi_content` — Get Cultura Delpi Content — AuthZ: `require_any_permission(CULTURA_DELPI_READ_PERMISSIONS)`
- `GET` `/guias-procedimentos/departments/{slug}` `get_guias_procedimentos_department` — Get Guias Department — AuthZ: `require_any_permission(GUIAS_PROCEDIMENTOS_READ_PERMISSIONS)`
- `GET` `/guias-procedimentos/procedures/{slug}` `get_guias_procedimentos_procedure` — Get Guias Procedure — AuthZ: `require_any_permission(GUIAS_PROCEDIMENTOS_READ_PERMISSIONS)`
- `GET` `/hr/active-pdi-count` `get_hr_active_pdi_count` — Indicator — Pdis ativos — AuthZ: `require_any_permission(KPI_HR_ACCESS)`
- `GET` `/hr/performance-reviews-completion` `get_hr_performance_reviews_completion` — Hr performance reviews completion — AuthZ: `require_any_permission(KPI_HR_ACCESS)`
- `GET` `/hr/snapshot` `get_hr_snapshot` — Hr snapshot — AuthZ: `require_any_permission(KPI_HR_ACCESS)`
- `GET` `/mural-acessos/hubs/{hub_id}` `get_mural_acessos_hub` — Get Hub — AuthZ: `require_any_permission(MURAL_ACESSOS_READ_PERMISSIONS)`
- `GET` `/mural-acessos/hubs/{hub_id}/qr.png` `get_mural_acessos_hub_qr` — Get Hub Qr — AuthZ: `require_any_permission(MURAL_ACESSOS_READ_PERMISSIONS)`
- `GET` `/mural-acessos/links/{link_id}/image` `get_mural_acessos_link_image` — Get Link Image — AuthZ: `require_any_permission(MURAL_ACESSOS_READ_PERMISSIONS)`
- `GET` `/reports/definitions/{definition_id}` `get_report_definition` — Get Report Definition — AuthZ: `require_any_permission(REPORTS_FOLLOW_UP_READ_PERMISSIONS)`
- `GET` `/reports/runs/{run_id}` `get_report_run` — Get Report Run — AuthZ: `require_any_permission(REPORTS_READ_PERMISSIONS)`
- `GET` `/reports/definitions/{definition_id}/schedule` `get_report_schedule` — Get Report Schedule — AuthZ: `require_any_permission(REPORTS_READ_PERMISSIONS)`
- `GET` `/guias-procedimentos/departments` `list_guias_procedimentos_departments` — List Guias Departments — AuthZ: `require_any_permission(GUIAS_PROCEDIMENTOS_READ_PERMISSIONS)`
- `GET` `/guias-procedimentos/procedures/{procedure_id}/media` `list_guias_procedimentos_procedure_media` — List procedure media — AuthZ: `require_any_permission(GUIAS_PROCEDIMENTOS_READ_PERMISSIONS)`
- `GET` `/hr/branches` `list_hr_branches` — Indicator — branches de rh — AuthZ: `require_any_permission(KPI_HR_ACCESS)`
- `GET` `/mural-acessos/hubs` `list_mural_acessos_hubs` — List Hubs — AuthZ: `require_any_permission(MURAL_ACESSOS_READ_PERMISSIONS)`
- `GET` `/mural-acessos/hubs/{hub_id}/links` `list_mural_acessos_links` — List Links — AuthZ: `require_any_permission(MURAL_ACESSOS_READ_PERMISSIONS)`
- `GET` `/scheduling/bookings/mine` `list_my_scheduling_bookings` — List My Bookings — AuthZ: `require_any_permission(SCHEDULING_READ_PERMISSIONS)`
- `GET` `/scheduling/bookings/pending` `list_pending_scheduling_bookings` — List Pending Bookings — AuthZ: `require_any_permission(SCHEDULING_READ_PERMISSIONS)`
- `GET` `/reports/definitions` `list_report_definitions` — List Report Definitions — AuthZ: `require_any_permission(REPORTS_FOLLOW_UP_READ_PERMISSIONS)`
- `GET` `/reports/providers` `list_report_providers` — List Report Providers — AuthZ: `require_any_permission(REPORTS_READ_PERMISSIONS)`
- `GET` `/reports/definitions/{definition_id}/recipients` `list_report_recipients` — List Report Recipients — AuthZ: `require_any_permission(REPORTS_READ_PERMISSIONS)`
- `GET` `/reports/runs` `list_report_runs` — List Report Runs — AuthZ: `require_any_permission(REPORTS_READ_PERMISSIONS)`
- `GET` `/reports/definitions/{definition_id}/item-notes` `list_report_shortage_item_notes` — List Report Shortage Item Notes — AuthZ: `require_any_permission(REPORTS_FOLLOW_UP_READ_PERMISSIONS)`
- `GET` `/scheduling/bookings` `list_scheduling_bookings` — List Bookings — AuthZ: `require_any_permission(SCHEDULING_READ_PERMISSIONS)`
- `GET` `/scheduling/resources` `list_scheduling_resources` — List Resources — AuthZ: `require_any_permission(SCHEDULING_READ_PERMISSIONS)`
- `GET` `/reports/providers/management_revenue_monthly/preview` `preview_report_provider_management_revenue_monthly` — Preview Management Revenue Monthly — AuthZ: `require_any_permission(REPORTS_FOLLOW_UP_READ_PERMISSIONS)`
- `GET` `/reports/providers/safety_stock_shortage_30d/preview` `preview_report_provider_safety_stock_shortage_30d` — Preview Safety Stock Shortage 30D — AuthZ: `require_any_permission(REPORTS_FOLLOW_UP_READ_PERMISSIONS)`

## REDUNDANT

- `get_product_detail` — Same Product Master slice already served by search_products; no distinct governed fields
- `get_product_analyser` — ProductAnalyserUseCase composes product/structure/guide/inspection JSON — it does not perform visual drawing analysis. Drawing analysis must reuse AI API workfl

## DEFERRED (existing governance dispositions in allowlist v15)

- `get_supplies_purchase_order_otd_panel` — [DEFER] Analogous to commercial OTD panel — line drill-down with large page_size; defer to detailed wave.
- `get_supplies_safety_stock_filters` — [DEFER] UI filter options helper, not a primary information capability.
- `get_supplies_safety_stock_item_details` — [DEFER] composite_analysis detail needs separate nested contract review.
- `get_supplies_safety_stock_consumption_analysis_item_details` — [DEFER] Includes calculation_memory and monthly series — defer nested detail wave.
- `get_supplies_purchase_requests_open_coverage` — [DEFER] Returns all open SC coverage items/products without page/page_size; needs owner-side bound or pagination.
- `list_supplies_purchase_request_requesters` — [DEFER] Requester lookup for UI filters; PII/identity helper without clear standalone information need.
- `get_supplies_purchase_request_lines` — [DEFER] Single SC detail by branch/request_number; promote list_supplies_purchase_request_lines first.
- `list_supplies_purchase_request_recent_linked_orders` — [DEFER] after_recno polling helper for BFF sync, not primary DAVI Q&A capability.
- `list_supplies_purchase_request_recent_linked_receipts` — [DEFER] after_recno polling helper for BFF sync, not primary DAVI Q&A capability.
- `get_supplies_protheus_user_by_email` — [DEFER] Email→Protheus user identity lookup; not a Supplies information capability for DAVI.
- `get_supplies_third_party_materials_shipment` — [DEFER] Single shipment detail with returns nested — defer after list shipments proves stable.
- `list_commercial_proposals` — [NEXT_WAVE_CANDIDATE] Proposal workflow family — out of Wave 004 analytics READ scope.
- `summarize_commercial_proposals_by_collaborator` — [NEXT_WAVE_CANDIDATE] Proposal collaborator summary — out of Wave 004 analytics READ scope.
- `get_commercial_proposal` — [NEXT_WAVE_CANDIDATE] Proposal detail — out of Wave 004 analytics READ scope.
- `get_commercial_proposal_history_events` — [NEXT_WAVE_CANDIDATE] Proposal history — out of Wave 004 analytics READ scope.
- `get_sales_order_otd_panel` — [DEFER] Wave 004 candidate deferred: line-level panel with insights arrays and page_size≤1000 is a drill-down sibling to get_sales_order_otd_line_detail; needs separate
- `get_sales_order_otd_line_detail` — [NEXT_WAVE_CANDIDATE] Explicitly out of Wave 004 commercial analytics family — proposal/detail/drill-down surface.
- `get_product_summary` — [DEFER] Composite product snapshot remains deferred; not a Wave 2 READ capability
- `get_product_raw_material_price_intelligence` — [DEFER] Unbounded budget scan / composite overlap / no bounded summaries-only backend contract
- `get_product_inspection` — [DEFER] Drawing analysis inspection cross-check deferred (DRAWING_ANALYSIS_INSPECTION_CROSSCHECK=DEFERRED). Not required for JSON drawing catalog/metadata foundation.

## TO_INVENTORY

None — all four previously unresolved routes were resolved by Architecture disposition as `EXCLUDED` / `EXCLUDED_CURRENT_ROUTE`:

- `GET` `/public/quality-labels/inspection/{token}` `get_public_quality_label_inspection` — public/token surface; no canonical per-user AuthZ parity proven.
- `GET` `/public/scheduling/resources/{public_token}` `get_public_scheduling_resource` — public/token surface; no canonical per-user AuthZ parity proven.
- `GET` `/public/scheduling/resources/{public_token}/availability` `get_public_scheduling_availability` — public/token surface; no canonical per-user AuthZ parity proven.
- `GET` `/production/orders/{production_order}/operations/{operation_code}/standard-time` `get_production_operation_standard_time` — internal MES S2S service-token authorization is not end-user business authorization.

## EXCLUDED (by reason)

- **admin/system/internal/gpt-actions plumbing** (76): `archive_guias_procedimentos_admin_attachment`, `archive_guias_procedimentos_admin_media`, `archive_guias_procedimentos_admin_procedure`, `archive_planejamento_orcamentario_admin_document`, `clear_planejamento_orcamentario_admin_capex_category_icon_image`, `create_guias_procedimentos_admin_department`, `create_guias_procedimentos_admin_external_video`, `create_guias_procedimentos_admin_procedure`, `create_planejamento_orcamentario_admin_budget_responsibility`, `create_planejamento_orcamentario_admin_capex_category`, `create_planejamento_orcamentario_admin_cost_center_from_erp`, `create_planejamento_orcamentario_admin_exercise`, `create_planejamento_orcamentario_admin_guidance_draft`, `create_planejamento_orcamentario_admin_scope`, `deactivate_planejamento_orcamentario_admin_budget_responsibility`, `deactivate_planejamento_orcamentario_admin_capex_category`, `deactivate_planejamento_orcamentario_admin_scope`, `evaluate_console_alerts`, `get_caller_stats`, `get_connection_pool_stats`, `get_console_alerts`, `get_console_health`, `get_envelope_contracts`, `get_guias_procedimentos_admin_department`, `get_guias_procedimentos_admin_procedure`, `get_observability_snapshot`, `get_openapi_diff`, `get_planejamento_orcamentario_admin_budget_responsibility`, `get_planejamento_orcamentario_admin_exercise`, `get_planejamento_orcamentario_admin_guidance`, `get_ppm_internal_series`, `get_ppm_internal_summary`, `get_protheus_table`, `get_protheus_table_indexes`, `get_protheus_table_relations`, `get_protheus_table_schema`, `get_query_cache_stats`, `get_smoke_definitions`, `list_guias_procedimentos_admin_departments`, `list_guias_procedimentos_admin_procedure_attachments`, `list_guias_procedimentos_admin_procedure_media`, `list_guias_procedimentos_admin_procedures`, `list_planejamento_orcamentario_admin_budget_responsibilities`, `list_planejamento_orcamentario_admin_capex_categories`, `list_planejamento_orcamentario_admin_documents`, `list_planejamento_orcamentario_admin_exercises`, `list_planejamento_orcamentario_admin_scopes`, `list_protheus_table_columns`, `notify_console_smoke_alerts`, `publish_guias_procedimentos_admin_procedure`, `publish_planejamento_orcamentario_admin_guidance`, `reactivate_planejamento_orcamentario_admin_budget_responsibility`, `reactivate_planejamento_orcamentario_admin_capex_category`, `restore_guias_procedimentos_admin_procedure`, `search_protheus_columns_by_description`, `search_protheus_columns_in_table`, `search_tables_by_description`, `transition_planejamento_orcamentario_admin_exercise`, `unpublish_guias_procedimentos_admin_procedure`, `update_guias_procedimentos_admin_attachment`, `update_guias_procedimentos_admin_department`, `update_guias_procedimentos_admin_media`, `update_guias_procedimentos_admin_procedure`, `update_planejamento_orcamentario_admin_budget_responsibility`, `update_planejamento_orcamentario_admin_capex_category`, `update_planejamento_orcamentario_admin_cost_center_icon`, `update_planejamento_orcamentario_admin_document`, `update_planejamento_orcamentario_admin_exercise`, `update_planejamento_orcamentario_admin_guidance`, `update_planejamento_orcamentario_admin_scope`, `upload_guias_procedimentos_admin_procedure_attachment`, `upload_guias_procedimentos_admin_procedure_image`, `upload_guias_procedimentos_admin_procedure_video`, `upload_planejamento_orcamentario_admin_capex_category_icon_image`, `upload_planejamento_orcamentario_admin_document`, `upsert_planejamento_orcamentario_admin_cost_center`
- **binary/document/file transport** (33): `archive_planejamento_orcamentario_capex_attachment`, `attach_audit_5s_evidence`, `attach_audit_5s_response_photo`, `delete_audit_5s_response_photo`, `download_audit_5s_nc_attachment`, `download_audit_5s_response_attachment`, `download_guias_procedimentos_attachment_file`, `download_guias_procedimentos_media_file`, `download_kaizen_evidence`, `download_planejamento_orcamentario_capex_attachment`, `download_planejamento_orcamentario_document`, `download_quality_action_plan_evidence`, `export_kaizen_records`, `export_lmp_nonconformities`, `export_planejamento_orcamentario_capex_consolidation_xlsx`, `export_proposta_comercial_pdf`, `export_proposta_comercial_pdf_with_overrides`, `export_quality_action_plan_pdf`, `export_quality_action_plan_rnc_8d`, `export_quality_action_plan_rnc_8d_pdf`, `export_supplies_purchase_orders`, `export_supplies_purchase_request_lines`, `export_supplies_third_party_materials_returns`, `get_product_drawing_pdf`, `get_product_structure_excel`, `get_quality_label_certificate_pdf`, `list_audit_5s_nc_attachments`, `list_audit_5s_response_attachments`, `list_guias_procedimentos_procedure_attachments`, `list_planejamento_orcamentario_capex_investment_attachments`, `list_quality_action_plan_export_templates`, `replace_kaizen_evidence_file`, `upload_planejamento_orcamentario_capex_investment_attachment`
- **compute-only PREPARE, not READ (per governance record)** (1): `get_product_cost_impact_simulation`
- **delete/destructive** (17): `deactivate_seller_portfolio`, `delete_audit_5s_area`, `delete_customer_avatar`, `delete_kaizen_evidence`, `delete_kaizen_record`, `delete_kaizen_version`, `delete_lmp_nonconformity`, `delete_mural_acessos_hub`, `delete_mural_acessos_link`, `delete_mural_acessos_link_image`, `delete_quality_action_plan`, `delete_quality_action_plan_action`, `delete_quality_action_plan_evidence`, `delete_quality_label`, `delete_report_schedule`, `delete_report_shortage_item_note`, `remove_seller_customer`
- **generic SQL** (2): `execute_readonly_sql`, `get_sql_health`
- **legacy unsafe surface** (2): `gpt_get_catalog`, `gpt_search_products`
- **personal preference plumbing, not business information** (1): `get_personal_report_subscription`
- **public UI navigation/media surface** (3): `get_public_mural_acessos_link_image`, `list_public_mural_acessos_menu`, `list_public_mural_acessos_menu_by_token`
- **technical health probe** (1): `get_health`
- **write/mutation** (127): `acknowledge_planejamento_orcamentario_guidance`, `add_lancamento_notas_fiscais_comment`, `add_seller_customer`, `approve_planejamento_orcamentario_capex_investment`, `approve_planejamento_orcamentario_capex_plan`, `approve_planejamento_orcamentario_personnel_plan`, `approve_quality_action_plan_effectiveness_review`, `approve_scheduling_booking`, `archive_planejamento_orcamentario_capex_investment`, `archive_planejamento_orcamentario_personnel_plan_line`, `assess_quality_action_plan_recurrence_on_opening`, `attach_kaizen_evidence`, `attach_quality_action_plan_evidence`, `block_lancamento_notas_fiscais_request`, `cancel_invoice_issuance_request`, `cancel_lancamento_notas_fiscais_request`, `cancel_scheduling_booking`, `close_audit_5s_audit`, `close_audit_5s_audit_without_nc_treatment`, `complete_audit_5s_evaluation`, `complete_audit_5s_nc_action`, `create_audit_5s_area`, `create_audit_5s_audit`, `create_audit_5s_nc_action`, `create_audit_5s_nonconformity`, `create_canal_denuncia`, `create_invoice_issuance_request`, `create_kaizen_record`, `create_kaizen_version`, `create_lancamento_notas_fiscais_request`, `create_lmp_nonconformity`, `create_mural_acessos_hub`, `create_mural_acessos_link`, `create_planejamento_orcamentario_capex_investment`, `create_planejamento_orcamentario_personnel_plan_line`, `create_public_canal_denuncia`, `create_public_kaizen_suggestion`, `create_public_scheduling_booking`, `create_quality_action_plan`, `create_quality_action_plan_actions`, `create_quality_label`, `create_report_definition`, `create_scheduling_booking`, `create_scheduling_resource`, `create_seller_portfolio`, `delete_audit_5s_audit`, `dispatch_quality_action_plan_notifications`, `enrich_portfolio_customers`, `force_close_audit_5s_nc_without_treatment`, `force_delete_audit_5s_audit`, `implement_kaizen_version`, `import_kaizen_records`, `import_lmp_nonconformities`, `issue_invoice_issuance_request`, `join_audit_5s_audit`, `link_lancamento_notas_fiscais_request_purchase_order`, `post_manual_lancamento_notas_fiscais_request`, `post_mini_applicators_golpes_batch`, `process_pending_report_schedules`, `promote_quality_action_plan_solution_pattern`, `publish_audit_5s_catalog`, `record_quality_action_plan_effectiveness`, `refresh_lancamento_notas_fiscais_reconciliation`, `reject_planejamento_orcamentario_capex_investment`, `reject_planejamento_orcamentario_capex_plan`, `reject_planejamento_orcamentario_personnel_plan`, `reject_quality_action_plan_effectiveness_review`, `reject_scheduling_booking`, `reopen_audit_5s_evaluation`, `reopen_audit_5s_nc_action`, `reopen_quality_action_plan`, `reorder_mural_acessos_links`, `replace_report_recipients`, `replace_seller_customers`, `request_changes_planejamento_orcamentario_capex_plan`, `request_changes_planejamento_orcamentario_personnel_plan`, `resolve_planejamento_orcamentario_capex_plan`, `resolve_planejamento_orcamentario_personnel_plan`, `restore_quality_action_plan_revision`, `resubmit_invoice_issuance_request`, `resume_lancamento_notas_fiscais_request`, `return_invoice_issuance_request`, `run_lancamento_notas_fiscais_reconciliation`, `run_report_definition`, `save_quality_label_certificate`, `save_quality_label_inspector`, `set_audit_5s_area_children`, `set_quality_label_active`, `start_invoice_issuance_request`, `start_lancamento_notas_fiscais_request`, `submit_planejamento_orcamentario_capex_plan`, `submit_planejamento_orcamentario_personnel_plan`, `submit_quality_action_plan_effectiveness_review`, `suggest_quality_action_plan_evidence_tags`, `suggest_quality_action_plan_evidence_tags_from_image`, `transfer_seller_customers`, `update_audit_5s_area`, `update_audit_5s_audit`, `update_audit_5s_nonconformity`, `update_cultura_delpi_content`, `update_invoice_issuance_request`, `update_kaizen_evidence`, `update_kaizen_record`, `update_kaizen_version`, `update_lancamento_notas_fiscais_request`, `update_lmp_nonconformity`, `update_mural_acessos_hub`, `update_mural_acessos_link`, `update_planejamento_orcamentario_capex_investment`, `update_planejamento_orcamentario_personnel_plan_line`, `update_quality_action_plan`, `update_quality_action_plan_action`, `update_quality_action_plan_evidence`, `update_quality_action_plan_status`, `update_report_definition`, `update_scheduling_resource`, `update_seller_portfolio`, `upload_mural_acessos_link_image`, `upload_quality_label_inspector_signature`, `upsert_audit_5s_response`, `upsert_customer_avatar`, `upsert_personal_report_subscription`, `upsert_quality_action_plan_five_whys`, `upsert_quality_action_plan_ishikawa`, `upsert_quality_action_plan_rnc_8d`, `upsert_report_schedule`, `upsert_report_shortage_item_note`
- **public/token surface — no end-user AuthZ parity (EXCLUDED_CURRENT_ROUTE)** (3): `get_public_quality_label_inspection`, `get_public_scheduling_availability`, `get_public_scheduling_resource`
- **internal S2S service-token authorization, not end-user AuthZ (EXCLUDED_CURRENT_ROUTE)** (1): `get_production_operation_standard_time`

## Known classification rules

- `structured_business_read` := final classification in {COVERED, ELIGIBLE_GAP, REDUNDANT, DEFERRED, TO_INVENTORY}.
- READ := HTTP GET or proven read-semantics POST (batch/query body, no state mutation).
- WRITE/TECHNICAL/other shapes never count as structured business READ.
- EXCLUDED rows are boundary-respecting (writes, binary/document transport, admin/system/internal, generic SQL, legacy unsafe) and are **not** missing coverage.
- Read-semantics POSTs (proven read-only batch queries): `list_production_order_operation_materials_batch`, `get_production_machine_load_appointment_status`, `list_product_physical_locations`, `list_product_inventory_blocks`, `list_customer_open_order_metrics`, `list_customer_billing_series`.

## Coverage ratio

FACTUAL DAVI ELIGIBLE COVERAGE = COVERED / (COVERED + ELIGIBLE_GAP) = 63 / 437 = **14.4%**.
Denominator excludes REDUNDANT, DEFERRED, TO_INVENTORY and EXCLUDED rows.

Full per-route matrix: `davi-wave-007-read-coverage-inventory-001.json` (same directory).
