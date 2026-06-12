# Catálogo OpenAPI — api-delpi (gerado automaticamente)

**Provider:** `api-delpi` · **Rotas:** 83 · **Gerado em:** 2026-05-29 16:45 UTC

> **⚠ Snapshot desatualizado (pré-Playbook 15).** Não inclui rotas operacionais `/production/consumption/*`, `/production/losses/*`, `/purchases/top-products`, etc.  
> **Regenerar:** `PYTHONPATH=/app python scripts/sync_api_delpi_openapi.py` (container `minha-delpi-ai-api`) após deploy api-delpi.  
> **Referência canônica até regeneração:** [`api-delpi-rotas-agente.md`](../api-delpi-rotas-agente.md) § Playbook 15 e [`13-producao-operacional.md`](../../../../api-delpi/docs/api/13-producao-operacional.md).

> Corpo abaixo: não editar manualmente — regenerado por `scripts/sync_api_delpi_openapi.py`.

## Comercial (9)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/commercial/branch_rol_target_pct` | `get_branch_rol_target_pct_commercial_branch_rol_target_pct_get` | Get Branch Rol Target Pct |
| `GET` | `/commercial/closing-rate` | `get_sales_conversion_rate_commercial_closing_rate_get` | Get Sales Conversion Rate |
| `GET` | `/commercial/head_office_rol_target_pct` | `get_head_office_rol_target_pct_commercial_head_office_rol_target_pct_get` | Get Head Office Rol Target Pct |
| `GET` | `/commercial/new-business-rol-pct` | `get_new_business_rol_pct_commercial_new_business_rol_pct_get` | Get New Business Rol Pct |
| `GET` | `/commercial/new-clients-average` | `get_new_clients_average_commercial_new_clients_average_get` | Get New Clients Average |
| `GET` | `/commercial/new-clients-rol-pct` | `get_new_clients_rol_pct_commercial_new_clients_rol_pct_get` | Get New Clients Rol Pct |
| `GET` | `/commercial/proposals` | `list_commercial_proposals_commercial_proposals_get` | List Commercial Proposals |
| `GET` | `/commercial/rol/series` | `get_commercial_rol_series_commercial_rol_series_get` | Get Commercial Rol Series |
| `GET` | `/commercial/sales-order-otd` | `get_sales_order_otd_commercial_sales_order_otd_get` | Get Sales Order Otd |

## Engenharia (8)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/engineering/lmps` | `list_lmps` | Listar LMPs (ordens especiais / amostras) |
| `GET` | `/engineering/lmps/dashboard` | `list_lmps_dashboard` | Dashboard de LMPs |
| `GET` | `/engineering/lmps/dashboard/charts` | `lmps_dashboard_charts_route_engineering_lmps_dashboard_charts_get` | Lmps Dashboard Charts Route |
| `GET` | `/engineering/lmps/dashboard/items` | `lmps_dashboard_items_route_engineering_lmps_dashboard_items_get` | Lmps Dashboard Items Route |
| `GET` | `/engineering/lmps/dashboard/summary` | `lmps_dashboard_summary_route_engineering_lmps_dashboard_summary_get` | Lmps Dashboard Summary Route |
| `GET` | `/engineering/lmps/{sale_number}` | `get_lmp_by_sale_number` | Detalhe da LMP por ordem de venda |
| `GET` | `/engineering/transforma-mais/processes` | `list_processes_engineering_transforma_mais_processes_get` | List Processes |
| `GET` | `/engineering/transforma-mais/processes/summary` | `get_process_summary_engineering_transforma_mais_processes_summary_get` | Get Process Summary |

## Financeiro (8)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/finacial/ebitda_pct` | `get_ebitda_pct_finacial_ebitda_pct_get` | Get Ebitda Pct |
| `GET` | `/finacial/fixed_cost_pct` | `get_fixed_cost_pct_finacial_fixed_cost_pct_get` | Get Fixed Cost Pct |
| `GET` | `/finacial/pmr` | `get_pmr_finacial_pmr_get` | Get Pmr |
| `GET` | `/finacial/rol` | `get_rol_finacial_rol_get` | Get Rol |
| `GET` | `/financial/ebitda_pct` | `get_ebitda_pct_financial_ebitda_pct_get` | Get Ebitda Pct |
| `GET` | `/financial/fixed_cost_pct` | `get_fixed_cost_pct_financial_fixed_cost_pct_get` | Get Fixed Cost Pct |
| `GET` | `/financial/pmr` | `get_pmr_financial_pmr_get` | Get Pmr |
| `GET` | `/financial/rol` | `get_rol_financial_rol_get` | Get Rol |

## Health (1)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/health` | `root_health_get` | Root |

## Produção (8)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/production/depreciation_pct` | `get_depreciation_pct_production_depreciation_pct_get` | Get Depreciation Pct |
| `GET` | `/production/direct_labor_cost_pct` | `get_direct_labor_cost_pct_production_direct_labor_cost_pct_get` | Get Direct Labor Cost Pct |
| `GET` | `/production/eficiencia-fabril/appointments` | `get_eficiencia_fabril_appointments_production_eficiencia_fabril_appointments_get` | Get Eficiencia Fabril Appointments |
| `GET` | `/production/eficiencia-fabril/dashboard` | `get_eficiencia_fabril_dashboard_production_eficiencia_fabril_dashboard_get` | Get Eficiencia Fabril Dashboard |
| `GET` | `/production/oee/series` | `get_production_oee_series_production_oee_series_get` | Get Production Oee Series |
| `GET` | `/production/on_time_delivery_pct` | `get_on_time_delivery_pct_production_on_time_delivery_pct_get` | Get On Time Delivery Pct |
| `GET` | `/production/overall_equipment_effectiveness_pct` | `get_overall_equipment_effectiveness_pct_production_overall_equipment_effectiveness_pct_get` | Get Overall Equipment Effectiveness Pct |
| `GET` | `/production/production_cost_pct` | `get_production_cost_pct_production_production_cost_pct_get` | Get Production Cost Pct |

## Qualidade (11)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/quality/audit-5s/summary` | `get_audit_5s_summary_quality_audit_5s_summary_get` | Get Audit 5S Summary |
| `GET` | `/quality/branches` | `list_quality_branches_quality_branches_get` | List Quality Branches |
| `GET` | `/quality/kaizens/summary` | `get_kaizen_summary_quality_kaizens_summary_get` | Get Kaizen Summary |
| `GET` | `/quality/nonconformities` | `list_nonconformity_route_quality_nonconformities_get` | List Nonconformity Route |
| `GET` | `/quality/nonconformities/series` | `get_nonconformity_series_quality_nonconformities_series_get` | Get Nonconformity Series |
| `GET` | `/quality/ppm/external` | `list_external_ppm_quality_ppm_external_get` | List External Ppm |
| `GET` | `/quality/ppm/external/series` | `get_external_ppm_series_quality_ppm_external_series_get` | Get External Ppm Series |
| `GET` | `/quality/ppm/external/summary` | `get_external_ppm_summary_quality_ppm_external_summary_get` | Get External Ppm Summary |
| `GET` | `/quality/ppm/internal` | `list_internal_ppm_quality_ppm_internal_get` | List Internal Ppm |
| `GET` | `/quality/ppm/internal/series` | `get_internal_ppm_series_quality_ppm_internal_series_get` | Get Internal Ppm Series |
| `GET` | `/quality/ppm/internal/summary` | `get_internal_ppm_summary_quality_ppm_internal_summary_get` | Get Internal Ppm Summary |

## Recursos Humanos (4)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/hr/active-pdi-count` | `get_hr_active_pdi_count_hr_active_pdi_count_get` | Get Hr Active Pdi Count |
| `GET` | `/hr/branches` | `list_hr_branches_hr_branches_get` | List Hr Branches |
| `GET` | `/hr/performance-reviews-completion` | `get_hr_performance_reviews_completion_hr_performance_reviews_completion_get` | Get Hr Performance Reviews Completion |
| `GET` | `/hr/snapshot` | `get_hr_snapshot_hr_snapshot_get` | Get Hr Snapshot |

## Suprimentos (4)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/supplies/cpv` | `get_supplies_cpv` | CPV — custo de produto vendido (Kardex / suprimentos) |
| `GET` | `/supplies/inventory-turnover` | `get_supplies_inventory_turnover` | Giro de estoque / IDD (suprimentos) |
| `GET` | `/supplies/otd` | `get_supplies_otd` | OTD — entrega no prazo (suprimentos) |
| `GET` | `/supplies/stock-value` | `get_supplies_stock_value` | Valor total de estoque (suprimentos) |

## data (1)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `POST` | `/data/sql` | `execute_readonly_sql` | Executar consulta SQL somente leitura |

## products (20)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/products/search` | `search_products` | Buscar produtos no Protheus |
| `GET` | `/products/{code}` | `get_product_detail_products__code__get` | Descrição e dados cadastrais do produto |
| `GET` | `/products/{code}/analyser` | `get_product_analyser` | Analisador completo do produto |
| `GET` | `/products/{code}/customers` | `customers_products__code__customers_get` | Customers |
| `GET` | `/products/{code}/guide` | `guide_products__code__guide_get` | Guide |
| `GET` | `/products/{code}/inbound-invoice-items` | `inbound_invoice_items_products__code__inbound_invoice_items_get` | Inbound Invoice Items |
| `GET` | `/products/{code}/inspection` | `inspection_products__code__inspection_get` | Inspection |
| `GET` | `/products/{code}/internal-movements` | `internal_movements_products__code__internal_movements_get` | Internal Movements |
| `GET` | `/products/{code}/outbound-invoice-items` | `outbound_invoice_items_products__code__outbound_invoice_items_get` | Outbound Invoice Items |
| `GET` | `/products/{code}/parents` | `parents_products__code__parents_get` | Parents |
| `GET` | `/products/{code}/pricing` | `product_pricing_products__code__pricing_get` | Product commercial pricing |
| `GET` | `/products/{code}/purchases` | `get_product_purchases` | Histórico de compras do produto |
| `GET` | `/products/{code}/sales` | `get_product_sales_summary` | Resumo de vendas do produto |
| `GET` | `/products/{code}/sales/billing` | `product_sales_billing_products__code__sales_billing_get` | Product billing summary |
| `GET` | `/products/{code}/sales/open-orders` | `get_product_sales_open_orders` | Carteira de pedidos de venda em aberto do produto |
| `GET` | `/products/{code}/stock` | `get_product_stock` | Estoque do produto por filial e local |
| `GET` | `/products/{code}/structure` | `get_product_structure` | Estrutura (BOM) do produto |
| `GET` | `/products/{code}/structure/excel` | `structure_excel_public_products__code__structure_excel_get` | Structure Excel Public |
| `GET` | `/products/{code}/summary` | `get_product_summary_products__code__summary_get` | Resumo consolidado do produto |
| `GET` | `/products/{code}/suppliers` | `suppliers_products__code__suppliers_get` | Suppliers |

## sales (1)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/sales/` | `list_sale_orders` | Listar ordens de venda |

## system (8)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/system/columns/search` | `search_columns_global_system_columns_search_get` | Busca colunas por descrição (SX3010 + ranking semântico) |
| `GET` | `/system/tables/search` | `search_tables_system_tables_search_get` | Busca tabelas por descrição (SX2) |
| `GET` | `/system/tables/{tableName}` | `table_system_tables__tableName__get` | Consulta informações de tabela |
| `GET` | `/system/tables/{tableName}/columns` | `table_columns_system_tables__tableName__columns_get` | Consulta colunas de tabela com paginação |
| `GET` | `/system/tables/{tableName}/columns/search` | `search_columns_system_tables__tableName__columns_search_get` | Buscar colunas por texto |
| `GET` | `/system/tables/{tableName}/indexes` | `table_indexes_system_tables__tableName__indexes_get` | Consulta índices (SIX010) |
| `GET` | `/system/tables/{tableName}/relations` | `table_relations_system_tables__tableName__relations_get` | Consulta relacionamentos (SX9010) |
| `GET` | `/system/tables/{tableName}/schema` | `table_schema_system_tables__tableName__schema_get` | Schema completo da tabela (SX2, SX3, SIX, SX9) |

---

## Apêndice manual — Playbook 15 (jun/2026, pós-deploy)

Rotas implementadas no código mas **ausentes** no snapshot de 29/05/2026 acima. Remover este apêndice após regenerar o catálogo.

### Produção operacional (14)

| Método | Path | operationId |
|--------|------|-------------|
| `GET` | `/production/consumption/top-items` | `get_production_consumption_top_items` |
| `GET` | `/production/consumption/top-items-by-work-center` | `get_production_consumption_top_items_by_work_center` |
| `GET` | `/production/consumption/top-items-validated` | `get_production_consumption_top_items_validated` |
| `GET` | `/production/consumption/by-item/{code}` | `get_production_consumption_by_item` |
| `GET` | `/production/losses/top-materials` | `get_production_losses_top_materials` |
| `GET` | `/production/losses/records` | `get_production_losses_records` |
| `GET` | `/production/schedule/today` | `get_production_schedule_today` |
| `GET` | `/production/orders/open` | `get_production_orders_open` |
| `GET` | `/production/orders/finished` | `get_production_orders_finished` |
| `GET` | `/production/orders/finished-without-consumption` | `get_production_orders_finished_without_consumption` |
| `GET` | `/production/work-centers/order-summary` | `get_production_work_center_order_summary` |
| `GET` | `/production/work-centers/average-planned-time` | `get_production_work_center_average_planned_time` |
| `GET` | `/production/allocation-gaps` | `get_production_allocation_gaps` |
| `GET` | `/production/planned-vs-real-time` | `get_production_planned_vs_real_time` |

### Compras operacionais (1)

| Método | Path | operationId |
|--------|------|-------------|
| `GET` | `/purchases/top-products` | `get_purchases_top_products` |
