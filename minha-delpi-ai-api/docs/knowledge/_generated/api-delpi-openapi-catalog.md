# Catálogo OpenAPI — api-delpi (gerado automaticamente)

**Provider:** `api-delpi` · **Rotas:** 168 · **Gerado em:** 2026-06-15 15:15 UTC

> Não edite manualmente. Regenerado por `scripts/sync_api_delpi_openapi.py`.

> **Referência canônica até regeneração:** [`api-delpi-rotas-agente.md`](../api-delpi-rotas-agente.md) § Playbook 15 e [`13-producao-operacional.md`](../../../../api-delpi/docs/api/13-producao-operacional.md).

## Agendamento

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/scheduling/bookings` | `list_bookings_scheduling_bookings_get` | List Bookings |
| `POST` | `/scheduling/bookings` | `create_booking_scheduling_bookings_post` | Create Booking |
| `PATCH` | `/scheduling/bookings/{booking_id}/cancel` | `cancel_booking_scheduling_bookings__booking_id__cancel_patch` | Cancel Booking |
| `GET` | `/scheduling/resources` | `list_resources_scheduling_resources_get` | List Resources |
| `POST` | `/scheduling/resources` | `create_resource_scheduling_resources_post` | Create Resource |
| `PATCH` | `/scheduling/resources/{resource_id}` | `update_resource_scheduling_resources__resource_id__patch` | Update Resource |

## Comercial

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

## Compras operacionais

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/purchases/top-products` | `get_purchases_top_products` | Produtos mais comprados no período |

## Cultura DELPI

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/cultura-delpi/content` | `get_cultura_delpi_content_cultura_delpi_content_get` | Get Cultura Delpi Content |
| `PUT` | `/cultura-delpi/content` | `update_cultura_delpi_content_cultura_delpi_content_put` | Update Cultura Delpi Content |

## Engenharia

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/engineering/lmps` | `list_lmps` | Listar LMPs (ordens especiais / amostras) |
| `GET` | `/engineering/lmps/dashboard` | `list_lmps_dashboard` | Dashboard de LMPs |
| `GET` | `/engineering/lmps/dashboard/charts` | `get_lmps_dashboard_charts` | Gráficos do painel de LMPs |
| `GET` | `/engineering/lmps/dashboard/items` | `list_lmps_dashboard_items` | Itens paginados do painel de LMPs |
| `GET` | `/engineering/lmps/dashboard/summary` | `get_lmps_dashboard_summary` | KPIs resumidos do painel de LMPs |
| `GET` | `/engineering/lmps/{sale_number}` | `get_lmp_by_sale_number` | Detalhe da LMP por ordem de venda |
| `GET` | `/engineering/mini-applicators/ferramentas` | `list_mini_applicators_ferramentas` | Listar ferramentas mini-aplicadores |
| `GET` | `/engineering/mini-applicators/ferramentas/{codigo}` | `get_mini_applicators_ferramenta` | Detalhe de ferramenta mini-aplicador |
| `GET` | `/engineering/mini-applicators/ferramentas/{codigo}/componentes` | `list_mini_applicators_componentes` | Componentes do mini-aplicador |
| `GET` | `/engineering/mini-applicators/ferramentas/{codigo}/golpes` | `get_mini_applicators_golpes` | Golpes do mini-aplicador no período |
| `GET` | `/engineering/mini-applicators/ferramentas/{codigo}/pecas` | `list_mini_applicators_pecas` | Listar peças do mini-aplicador |
| `GET` | `/engineering/transforma-mais/processes` | `list_transforma_mais_processes` | Listar processos Transforma Mais |
| `GET` | `/engineering/transforma-mais/processes/summary` | `get_transforma_mais_summary` | Resumo Transforma Mais |

## Financeiro

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

## Health

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/health` | `root_health_get` | Root |

## Pedidos de Venda em Aberto

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/pedidos-venda-abertos/` | `list_pedidos_venda_abertos_route_pedidos_venda_abertos__get` | List Pedidos Venda Abertos Route |
| `GET` | `/pedidos-venda-abertos/ops-abertas` | `list_ops_abertas_route_pedidos_venda_abertos_ops_abertas_get` | List Ops Abertas Route |

## Produção

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/production/depreciation_pct` | `get_depreciation_pct_production_depreciation_pct_get` | Get Depreciation Pct |
| `GET` | `/production/direct_labor_cost_pct` | `get_direct_labor_cost_pct_production_direct_labor_cost_pct_get` | Get Direct Labor Cost Pct |
| `GET` | `/production/eficiencia-fabril/appointments` | `list_eficiencia_fabril_appointments` | Eficiência fabril — apontamentos (carga bulk) |
| `GET` | `/production/eficiencia-fabril/dashboard` | `get_eficiencia_fabril_dashboard` | Eficiência fabril — dashboard MOD e gráficos |
| `GET` | `/production/oee` | `get_production_oee` | OEE produção — resumo e apontamentos (view fabril) |
| `GET` | `/production/oee/appointments/{appointment_id}` | `get_production_oee_appointment_by_id` | Detalhe do apontamento OEE (roteiro, estrutura e tempos) |
| `GET` | `/production/oee/series` | `get_production_oee_series_production_oee_series_get` | Get Production Oee Series |
| `GET` | `/production/on_time_delivery_pct` | `get_on_time_delivery_pct_production_on_time_delivery_pct_get` | Get On Time Delivery Pct |
| `GET` | `/production/otd` | `get_production_otd` | OTD produção — resumo e ordens (SC2010) |
| `GET` | `/production/otd/series` | `get_production_otd_series_production_otd_series_get` | Get Production Otd Series |
| `GET` | `/production/overall_equipment_effectiveness_pct` | `get_overall_equipment_effectiveness_pct_production_overall_equipment_effectiveness_pct_get` | Get Overall Equipment Effectiveness Pct |
| `GET` | `/production/production_cost_pct` | `get_production_cost_pct_production_production_cost_pct_get` | Get Production Cost Pct |

## Produção operacional

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/production/allocation-gaps` | `get_production_allocation_gaps` | Componentes sem empenho (travamento) |
| `GET` | `/production/consumption/by-item/{code}` | `get_production_consumption_by_item` | Consumo real de item por produto |
| `GET` | `/production/consumption/top-items` | `get_production_consumption_top_items` | Itens mais consumidos na produção |
| `GET` | `/production/consumption/top-items-by-work-center` | `get_production_consumption_top_items_by_work_center` | Consumo por centro de trabalho |
| `GET` | `/production/consumption/top-items-validated` | `get_production_consumption_top_items_validated` | Consumo validado por apontamento real |
| `GET` | `/production/losses/records` | `get_production_losses_records` | Registros detalhados de refugo/scrap |
| `GET` | `/production/losses/top-materials` | `get_production_losses_top_materials` | Matérias-primas com mais refugo/scrap no período |
| `GET` | `/production/orders/by-op/{production_order}` | `get_production_order_by_op` | Detalhe da OP por C2_OP |
| `GET` | `/production/orders/finished` | `get_production_orders_finished` | OPs finalizadas na data |
| `GET` | `/production/orders/finished-without-consumption` | `get_production_orders_finished_without_consumption` | OPs finalizadas sem consumo de componentes |
| `GET` | `/production/orders/open` | `get_production_orders_open` | OPs em aberto na data |
| `GET` | `/production/planned-vs-real-time` | `get_production_planned_vs_real_time` | Tempo planejado × tempo real por OP |
| `GET` | `/production/schedule/today` | `get_production_schedule_today` | Produtos programados para produzir na data |
| `GET` | `/production/work-centers/average-planned-time` | `get_production_work_center_average_planned_time` | Tempo médio planejado por centro de trabalho |
| `GET` | `/production/work-centers/order-summary` | `get_production_work_center_order_summary` | Resumo de OPs por centro de trabalho |

## Propostas Comerciais

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/propostas-comerciais/` | `list_propostas_comerciais_route_propostas_comerciais__get` | List Propostas Comerciais Route |
| `GET` | `/propostas-comerciais/{proposta_interna}` | `get_proposta_comercial_route_propostas_comerciais__proposta_interna__get` | Get Proposta Comercial Route |
| `GET` | `/propostas-comerciais/{proposta_interna}/pdf` | `export_proposta_comercial_pdf_route_propostas_comerciais__proposta_interna__pdf_get` | Export Proposta Comercial Pdf Route |
| `POST` | `/propostas-comerciais/{proposta_interna}/pdf` | `export_proposta_comercial_pdf_with_overrides_route_propostas_comerciais__proposta_interna__pdf_post` | Export Proposta Comercial Pdf With Overrides Route |

## Qualidade

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/quality/audit-5s/analytics/dashboard` | `get_audit_5s_dashboard_quality_audit_5s_analytics_dashboard_get` | Get Audit 5S Dashboard |
| `GET` | `/quality/audit-5s/areas` | `list_areas_quality_audit_5s_areas_get` | List Areas |
| `POST` | `/quality/audit-5s/areas` | `create_area_quality_audit_5s_areas_post` | Create Area |
| `GET` | `/quality/audit-5s/audits` | `list_audits_quality_audit_5s_audits_get` | List Audits |
| `POST` | `/quality/audit-5s/audits` | `create_audit_quality_audit_5s_audits_post` | Create Audit |
| `GET` | `/quality/audit-5s/audits/{audit_id}` | `get_audit_quality_audit_5s_audits__audit_id__get` | Get Audit |
| `POST` | `/quality/audit-5s/audits/{audit_id}/close` | `close_audit_quality_audit_5s_audits__audit_id__close_post` | Close Audit |
| `POST` | `/quality/audit-5s/audits/{audit_id}/complete-evaluation` | `complete_evaluation_quality_audit_5s_audits__audit_id__complete_evaluation_post` | Complete Evaluation |
| `POST` | `/quality/audit-5s/audits/{audit_id}/delete` | `delete_audit_quality_audit_5s_audits__audit_id__delete_post` | Delete Audit |
| `POST` | `/quality/audit-5s/audits/{audit_id}/join` | `join_audit_quality_audit_5s_audits__audit_id__join_post` | Join Audit |
| `GET` | `/quality/audit-5s/audits/{audit_id}/nc-attachments` | `list_audit_nc_attachments_quality_audit_5s_audits__audit_id__nc_attachments_get` | List Audit Nc Attachments |
| `GET` | `/quality/audit-5s/audits/{audit_id}/nc-candidates` | `list_nc_candidates_quality_audit_5s_audits__audit_id__nc_candidates_get` | List Nc Candidates |
| `GET` | `/quality/audit-5s/audits/{audit_id}/nonconformities` | `list_audit_nonconformities_quality_audit_5s_audits__audit_id__nonconformities_get` | List Audit Nonconformities |
| `POST` | `/quality/audit-5s/audits/{audit_id}/nonconformities` | `create_nonconformity_quality_audit_5s_audits__audit_id__nonconformities_post` | Create Nonconformity |
| `PUT` | `/quality/audit-5s/audits/{audit_id}/responses/{criterion_id}` | `upsert_response_quality_audit_5s_audits__audit_id__responses__criterion_id__put` | Upsert Response |
| `GET` | `/quality/audit-5s/criteria` | `list_criteria_quality_audit_5s_criteria_get` | List Criteria |
| `PATCH` | `/quality/audit-5s/nonconformities/{nc_id}` | `update_nonconformity_quality_audit_5s_nonconformities__nc_id__patch` | Update Nonconformity |
| `GET` | `/quality/audit-5s/nonconformities/{nc_id}/actions` | `list_nc_actions_quality_audit_5s_nonconformities__nc_id__actions_get` | List Nc Actions |
| `POST` | `/quality/audit-5s/nonconformities/{nc_id}/actions` | `add_nc_action_quality_audit_5s_nonconformities__nc_id__actions_post` | Add Nc Action |
| `GET` | `/quality/audit-5s/nonconformities/{nc_id}/attachments` | `list_nc_attachments_quality_audit_5s_nonconformities__nc_id__attachments_get` | List Nc Attachments |
| `POST` | `/quality/audit-5s/nonconformities/{nc_id}/attachments` | `upload_nc_attachment_quality_audit_5s_nonconformities__nc_id__attachments_post` | Upload Nc Attachment |
| `GET` | `/quality/audit-5s/nonconformities/{nc_id}/attachments/{attachment_id}/file` | `download_nc_attachment_quality_audit_5s_nonconformities__nc_id__attachments__attachment_id__file_get` | Download Nc Attachment |
| `POST` | `/quality/audit-5s/nonconformities/{nc_id}/complete-action` | `complete_nc_action_quality_audit_5s_nonconformities__nc_id__complete_action_post` | Complete Nc Action |
| `GET` | `/quality/audit-5s/summary` | `get_audit_5s_summary_quality_audit_5s_summary_get` | Get Audit 5S Summary |
| `GET` | `/quality/branches` | `list_quality_branches_quality_branches_get` | List Quality Branches |
| `GET` | `/quality/kaizens/summary` | `get_kaizen_summary` | Kaizens — resumo e listagem (Google Sheets) |
| `GET` | `/quality/kaizens/{kaizen_id}` | `get_kaizen_by_id` | Detalhe do kaizen (Google Sheets) |
| `GET` | `/quality/nonconformities` | `list_nonconformity_route_quality_nonconformities_get` | List Nonconformity Route |
| `GET` | `/quality/nonconformities/series` | `get_nonconformity_series_quality_nonconformities_series_get` | Get Nonconformity Series |
| `GET` | `/quality/ppm/external` | `list_ppm_external` | List External Ppm |
| `GET` | `/quality/ppm/external/series` | `get_ppm_external_series` | Get External Ppm Series |
| `GET` | `/quality/ppm/external/summary` | `get_ppm_external_summary` | Get External Ppm Summary |
| `GET` | `/quality/ppm/internal` | `list_ppm_internal` | List Internal Ppm |
| `GET` | `/quality/ppm/internal/series` | `get_ppm_internal_series` | Get Internal Ppm Series |
| `GET` | `/quality/ppm/internal/summary` | `get_ppm_internal_summary` | Get Internal Ppm Summary |
| `GET` | `/quality/produced-quantity` | `get_produced_quantity` | Get Produced Quantity |

## Recursos Humanos

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/hr/active-pdi-count` | `get_hr_active_pdi_count_hr_active_pdi_count_get` | Get Hr Active Pdi Count |
| `GET` | `/hr/branches` | `list_hr_branches_hr_branches_get` | List Hr Branches |
| `GET` | `/hr/performance-reviews-completion` | `get_hr_performance_reviews_completion_hr_performance_reviews_completion_get` | Get Hr Performance Reviews Completion |
| `GET` | `/hr/snapshot` | `get_hr_snapshot_hr_snapshot_get` | Get Hr Snapshot |

## Suprimentos

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/supplies/cpv` | `get_supplies_cpv` | CPV — custo de produto vendido (Kardex / suprimentos) |
| `GET` | `/supplies/inventory-turnover` | `get_supplies_inventory_turnover` | Giro de estoque / IDD (suprimentos) |
| `GET` | `/supplies/negotiation-savings/summary` | `get_supplies_negotiation_savings_summary` | Economia em negociações de compras (planilha IDD Suprimentos) |
| `GET` | `/supplies/otd` | `get_supplies_otd` | OTD — entrega no prazo (suprimentos) |
| `GET` | `/supplies/stock-value` | `get_supplies_stock_value` | Valor total de estoque (suprimentos) |

## data

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `POST` | `/data/sql` | `execute_readonly_sql` | Executar consulta SQL somente leitura |

## products

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/products/exclusive-raw-materials/catalog` | `list_exclusive_raw_materials_catalog` | Catálogo global de matérias-primas exclusivas |
| `GET` | `/products/search` | `search_products` | Buscar produtos no Protheus |
| `GET` | `/products/{code}` | `get_product_detail` | Dados cadastrais do produto |
| `GET` | `/products/{code}/analyser` | `get_product_analyser` | Analisador completo do produto |
| `GET` | `/products/{code}/cost-impact-simulation` | `get_product_cost_impact_simulation` | Simulador de impacto de custos do PA |
| `GET` | `/products/{code}/customers` | `get_product_customers` | Clientes do produto |
| `GET` | `/products/{code}/factory-status` | `get_product_factory_status` | Status fabril completo do produto |
| `GET` | `/products/{code}/guide` | `get_product_guide` | Roteiro de produção do produto |
| `GET` | `/products/{code}/inbound-invoice-items` | `get_product_inbound_invoice_items` | Itens de nota fiscal de entrada do produto |
| `GET` | `/products/{code}/inspection` | `get_product_inspection` | Inspeção de qualidade do produto (QP6/QP7/QP8) |
| `GET` | `/products/{code}/internal-movements` | `get_product_internal_movements` | Movimentações internas do produto |
| `GET` | `/products/{code}/last-purchase` | `get_product_last_purchase` | Última compra válida da matéria-prima |
| `GET` | `/products/{code}/outbound-invoice-items` | `get_product_outbound_invoice_items` | Itens de nota fiscal de saída do produto |
| `GET` | `/products/{code}/parents` | `get_product_parents` | Onde o produto é usado (produtos pai / BOM reversa) |
| `GET` | `/products/{code}/pricing` | `get_product_pricing` | Preços e tabelas comerciais do produto |
| `GET` | `/products/{code}/production-status` | `get_product_production_status` | Situação produtiva do produto (PA, PI, OP e apontamentos) |
| `GET` | `/products/{code}/purchase-budget-history` | `get_product_purchase_budget_history` | Histórico de orçamento de compra (SC + PC) |
| `GET` | `/products/{code}/purchase-price-history` | `get_product_purchase_price_history` | Histórico de preço de compra da matéria-prima |
| `GET` | `/products/{code}/purchases` | `get_product_purchases` | Histórico de compras do produto |
| `GET` | `/products/{code}/raw-material-price-intelligence` | `get_product_raw_material_price_intelligence` | Análise inteligente de preço de matéria-prima |
| `GET` | `/products/{code}/sales` | `get_product_sales_summary` | Resumo de vendas do produto |
| `GET` | `/products/{code}/sales/billing` | `get_product_sales_billing` | Faturamento do produto |
| `GET` | `/products/{code}/sales/open-orders` | `get_product_sales_open_orders` | Carteira de pedidos de venda em aberto do produto |
| `GET` | `/products/{code}/shipping-status` | `get_product_shipping_status` | Expedição do PA via inspeção final |
| `GET` | `/products/{code}/stock` | `get_product_stock` | Estoque do produto por filial e local |
| `GET` | `/products/{code}/structure` | `get_product_structure` | Estrutura (BOM) do produto |
| `GET` | `/products/{code}/structure/excel` | `structure_excel_public_products__code__structure_excel_get` | Structure Excel Public |
| `GET` | `/products/{code}/structure/exclusivity` | `get_product_structure_exclusivity` | Estrutura do produto com exclusividade de matérias-primas |
| `GET` | `/products/{code}/summary` | `get_product_summary` | Resumo do produto (cadastro + estoque + preços) |
| `GET` | `/products/{code}/suppliers` | `get_product_suppliers` | Fornecedores do produto |

## sales

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/sales/` | `list_sale_orders` | Listar ordens de venda |

## system

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/system/caller-stats` | `get_caller_stats_system_caller_stats_get` | Breakdown de requests por X-Delpi-Caller-App |
| `GET` | `/system/columns/search` | `search_columns_global_system_columns_search_get` | Busca colunas por descrição (SX3010 + ranking semântico) |
| `GET` | `/system/console-alerts` | `get_console_alerts_system_console_alerts_get` | Histórico recente de alertas do console |
| `POST` | `/system/console-alerts/evaluate` | `post_console_alerts_evaluate_system_console_alerts_evaluate_post` | Avalia alertas (p95, SQL) e opcionalmente dispara webhook |
| `POST` | `/system/console-alerts/smoke` | `post_console_alerts_smoke_system_console_alerts_smoke_post` | Registra resultado de smoke e dispara alertas |
| `GET` | `/system/console-health` | `get_console_health_system_console_health_get` | Saúde agregada do console para Admin Stats |
| `GET` | `/system/envelope-contracts` | `get_envelope_contracts_system_envelope_contracts_get` | Golden files de contrato de envelope (smoke) |
| `GET` | `/system/observability-snapshot` | `get_observability_snapshot_system_observability_snapshot_get` | Snapshot unificado para comparador de deploy |
| `GET` | `/system/openapi-diff` | `get_openapi_diff_system_openapi_diff_get` | Diff do OpenAPI atual vs baseline versionado |
| `GET` | `/system/query-cache/stats` | `get_query_cache_stats_system_query_cache_stats_get` | Hits e misses do cache compartilhado (LMP, estoque) |
| `GET` | `/system/smoke-definitions` | `get_smoke_definitions_system_smoke_definitions_get` | Definições das smoke suites do console |
| `GET` | `/system/sql-health` | `get_sql_health_system_sql_health_get` | Telemetria SQL recente (ring buffer memória ou Redis) |
| `GET` | `/system/tables/search` | `search_tables_system_tables_search_get` | Busca tabelas por descrição (SX2) |
| `GET` | `/system/tables/{tableName}` | `table_system_tables__tableName__get` | Consulta informações de tabela |
| `GET` | `/system/tables/{tableName}/columns` | `table_columns_system_tables__tableName__columns_get` | Consulta colunas de tabela com paginação |
| `GET` | `/system/tables/{tableName}/columns/search` | `search_columns_system_tables__tableName__columns_search_get` | Buscar colunas por texto |
| `GET` | `/system/tables/{tableName}/indexes` | `table_indexes_system_tables__tableName__indexes_get` | Consulta índices (SIX010) |
| `GET` | `/system/tables/{tableName}/relations` | `table_relations_system_tables__tableName__relations_get` | Consulta relacionamentos (SX9010) |
| `GET` | `/system/tables/{tableName}/schema` | `table_schema_system_tables__tableName__schema_get` | Schema completo da tabela (SX2, SX3, SIX, SX9) |
