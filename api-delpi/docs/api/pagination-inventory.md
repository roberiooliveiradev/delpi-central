# Inventário de paginação api-delpi

Gerado: 2026-09-04

- Inbound Query sites: **117**
- Tiers distintos: **29**
- Outbound pagination emitters: **46**

## Tiers (resumo)

| Tier | param | default | le | n |
|------|-------|--------:|---:|--:|
| `page_50_200` | page_size | 50 | 200 | 22 |
| `page_50_500` | page_size | 50 | 500 | 15 |
| `limit_optional_200` | limit | None | 200 | 14 |
| `page_20_100` | page_size | 20 | 100 | 10 |
| `page_optional_open` | page_size | None | None | 5 |
| `page_20_1000` | page_size | 20 | 1000 | 4 |
| `limit_10_50` | limit | 10 | 50 | 4 |
| `page_50_100` | page_size | 50 | 100 | 4 |
| `limit_20_50` | limit | 20 | 50 | 4 |
| `limit_25_100` | limit | 25 | 100 | 4 |
| `limit_50_200` | limit | 50 | 200 | 3 |
| `page_optional_500` | page_size | None | 500 | 3 |
| `limit_100_500` | limit | 100 | 500 | 3 |
| `limit_100_200` | limit | 100 | 200 | 2 |
| `limit_optional_500` | limit | None | 500 | 2 |
| `history_limit_optional_200` | history_limit | None | 200 | 2 |
| `limit_ranking_10_50` | limit | 10 | 50 | 2 |
| `top_limit_5_20` | top_limit | 5 | 20 | 2 |
| `limit_20_200` | limit | 20 | 200 | 2 |
| `limit_20_500` | limit | 20 | 500 | 1 |
| `limit_500_500` | limit | 500 | 500 | 1 |
| `limit_rol_8000` | limit | 8000 | 8000 | 1 |
| `limit_freight_20000` | limit | 20000 | 20000 | 1 |
| `page_25_50` | page_size | 25 | 50 | 1 |
| `page_100_200` | page_size | 100 | 200 | 1 |
| `page_10_100` | page_size | 10 | 100 | 1 |
| `limit_20_20` | limit | 20 | 20 | 1 |
| `limit_8_20` | limit | 8 | 20 | 1 |
| `top_limit_10_50` | top_limit | 10 | 50 | 1 |

## Outbound por classificação

### inline_dict (26)
- `app/application/dto/audit_5s/audit_5s_dashboard_response.py`
- `app/application/dto/eficiencia_fabril/eficiencia_fabril_dashboard_response.py`
- `app/application/dto/financeiro_despesas_centro_custo/despesas_centro_custo_lancamentos_response.py`
- `app/application/dto/financeiro_inadimplencia/clientes_response.py`
- `app/application/dto/financeiro_inadimplencia/titulos_response.py`
- `app/application/dto/inspecoes_entrada/inspecoes_entrada_historico_response.py`
- `app/application/dto/inspecoes_entrada/inspecoes_entrada_pendentes_response.py`
- `app/application/use_cases/commercial/get_sales_order_otd_by_customer_use_case.py`
- `app/application/use_cases/commercial/get_sales_order_otd_series_by_customer_use_case.py`
- `app/application/use_cases/financial/get_purchase_freight_links_use_case.py`
- `app/application/use_cases/financial/get_rol_invoices_use_case.py`
- `app/application/use_cases/planejamento_orcamentario/budget_responsibility_use_cases.py`
- `app/application/use_cases/planejamento_orcamentario/capex_consolidation_use_cases.py`
- `app/application/use_cases/planejamento_orcamentario/capex_investment_use_cases.py`
- `app/application/use_cases/planejamento_orcamentario/capex_plan_use_cases.py`
- `app/application/use_cases/planejamento_orcamentario/personnel_plan_use_cases.py`
- `app/application/use_cases/product/list_exclusive_raw_materials_catalog_use_case.py`
- `app/application/use_cases/production_appointments/production_appointments_use_cases.py`
- `app/application/use_cases/quality_labels/quality_labels_service.py`
- `app/domain/entities/pedidos_venda_abertos/customer_outbound_invoice.py`
- `app/infrastructure/persistence/plugins/repositories/audit_5s/postgres_audit_5s_repository.py`
- `app/infrastructure/persistence/plugins/repositories/kaizen/postgres_kaizen_repository.py`
- `app/infrastructure/persistence/plugins/repositories/quality_action_plans/postgres_quality_action_plan_read_repository.py`
- `app/infrastructure/persistence/plugins/repositories/quality_action_plans/postgres_quality_intelligence_repository.py`
- `app/infrastructure/persistence/plugins/repositories/quality_action_plans/quality_action_plan_revision_mixin.py`
- `app/interface/http/schemas/openapi_examples.py`

### build_operational_pagination (15)
- `app/application/use_cases/production/get_production_allocation_gaps_use_case.py`
- `app/application/use_cases/production/get_production_consumption_by_item_use_case.py`
- `app/application/use_cases/production/get_production_consumption_top_items_by_work_center_use_case.py`
- `app/application/use_cases/production/get_production_consumption_top_items_use_case.py`
- `app/application/use_cases/production/get_production_consumption_top_items_validated_use_case.py`
- `app/application/use_cases/production/get_production_losses_records_use_case.py`
- `app/application/use_cases/production/get_production_losses_top_materials_use_case.py`
- `app/application/use_cases/production/get_production_orders_finished_use_case.py`
- `app/application/use_cases/production/get_production_orders_finished_without_consumption_use_case.py`
- `app/application/use_cases/production/get_production_orders_open_use_case.py`
- `app/application/use_cases/production/get_production_planned_vs_real_time_use_case.py`
- `app/application/use_cases/production/get_production_schedule_today_use_case.py`
- `app/application/use_cases/production/get_production_work_center_average_planned_time_use_case.py`
- `app/application/use_cases/production/get_production_work_center_order_summary_use_case.py`
- `app/application/use_cases/purchases/get_purchases_top_products_use_case.py`

### build_has_next_pagination (4)
- `app/application/dto/inspecoes_processo/inspecoes_processo_auditoria_apontamentos_response.py`
- `app/application/dto/inspecoes_processo/inspecoes_processo_historico_detalhe_response.py`
- `app/application/dto/inspecoes_processo/inspecoes_processo_historico_response.py`
- `app/application/services/paged_list_envelope_service.py`

### build_pagination (1)
- `app/application/dto/process_inspection_plans/process_inspection_plans_list_responses.py`

