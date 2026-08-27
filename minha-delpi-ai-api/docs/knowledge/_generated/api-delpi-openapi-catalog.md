# Catálogo OpenAPI — api-delpi (gerado automaticamente)

**Provider:** `api-delpi` · **Rotas:** 691 · **Gerado em:** 2026-08-27 10:31 UTC

> Não edite manualmente. Regenerado por `scripts/sync_api_delpi_openapi.py`.

## Agendamento (10)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/scheduling/bookings` | `list_scheduling_bookings` | List Bookings |
| `POST` | `/scheduling/bookings` | `create_scheduling_booking` | Create scheduling booking |
| `GET` | `/scheduling/bookings/mine` | `list_my_scheduling_bookings` | List My Bookings |
| `GET` | `/scheduling/bookings/pending` | `list_pending_scheduling_bookings` | List Pending Bookings |
| `POST` | `/scheduling/bookings/{booking_id}/approve` | `approve_scheduling_booking` | Approve Booking |
| `PATCH` | `/scheduling/bookings/{booking_id}/cancel` | `cancel_scheduling_booking` | Cancel scheduling booking |
| `POST` | `/scheduling/bookings/{booking_id}/reject` | `reject_scheduling_booking` | Reject Booking |
| `GET` | `/scheduling/resources` | `list_scheduling_resources` | List Resources |
| `POST` | `/scheduling/resources` | `create_scheduling_resource` | Create scheduling resource |
| `PATCH` | `/scheduling/resources/{resource_id}` | `update_scheduling_resource` | Update scheduling resource |

## Agendamento — público (3)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/public/scheduling/resources/{public_token}` | `get_public_scheduling_resource` | Get Public Scheduling Resource |
| `GET` | `/public/scheduling/resources/{public_token}/availability` | `get_public_scheduling_availability` | Get Public Scheduling Availability |
| `POST` | `/public/scheduling/resources/{public_token}/bookings` | `create_public_scheduling_booking` | Create Public Scheduling Booking |

## Canal de Denúncia (1)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `POST` | `/canal-denuncia/denuncias` | `create_canal_denuncia` | Create Anonymous Denuncia |

## Canal de Denúncia — público (1)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `POST` | `/public/canal-denuncia/denuncias` | `create_public_canal_denuncia` | Submit public whistleblowing report |

## Clientes (1)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/customers/search` | `search_customers` | Search Customers Route |

## Comercial (22)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/commercial/branch_new_business_rol_target_pct` | `get_branch_new_business_rol_target_pct` | Indicator — Commercial rol new business target |
| `GET` | `/commercial/branch_rol_target_pct` | `get_branch_rol_target_pct` | Indicator — Meta percentage rol comercial |
| `GET` | `/commercial/branch_weg_rol_target_pct` | `get_branch_weg_rol_target_pct` | Indicator — Commercial rol weg target |
| `GET` | `/commercial/closing-rate` | `get_sales_conversion_rate` | Sales conversion rate |
| `GET` | `/commercial/closing-rate/series` | `get_sales_conversion_rate_series` | Sales conversion rate series |
| `GET` | `/commercial/head_office_new_business_rol_target_pct` | `get_head_office_new_business_rol_target_pct` | Indicator — Commercial rol new business target |
| `GET` | `/commercial/head_office_rol_target_pct` | `get_head_office_rol_target_pct` | Indicator — Meta percentage rol comercial |
| `GET` | `/commercial/head_office_weg_rol_target_pct` | `get_head_office_weg_rol_target_pct` | Indicator — Commercial rol weg target |
| `GET` | `/commercial/new-business-rol-pct` | `get_new_business_rol_pct` | New business rol pct |
| `GET` | `/commercial/new-clients-average` | `get_new_clients_average` | New clients average |
| `GET` | `/commercial/new-clients-rol-pct` | `get_new_clients_rol_pct` | Indicator — percentage rol de clientes novos |
| `GET` | `/commercial/proposals` | `list_commercial_proposals` | Commercial proposals |
| `GET` | `/commercial/proposals/{proposal_number}` | `get_commercial_proposal` | Commercial proposal detail (sales order) |
| `GET` | `/commercial/proposals/{proposal_number}/history/events` | `get_commercial_proposal_history_events` | Commercial proposal stage history |
| `GET` | `/commercial/rol` | `get_commercial_rol` | Commercial ROL consolidated analysis |
| `GET` | `/commercial/rol/by-customer` | `get_commercial_rol_by_customer` | Commercial ROL ranking by customer |
| `GET` | `/commercial/rol/series` | `get_commercial_rol_series` | Commercial rol series |
| `GET` | `/commercial/sales-order-otd` | `get_sales_order_otd` | Sales order otd |
| `GET` | `/commercial/sales-order-otd/analysis` | `get_commercial_sales_order_otd_analysis` | Sales order OTD consolidated analysis |
| `GET` | `/commercial/sales-order-otd/lines/{branch}/{order_number}/{line_item}` | `get_sales_order_otd_line_detail` | Sales order otd line detail |
| `GET` | `/commercial/sales-order-otd/panel` | `get_sales_order_otd_panel` | Sales order otd panel |
| `GET` | `/commercial/sales-order-otd/series` | `get_sales_order_otd_series` | Sales order otd series |

## Compras operacionais (1)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/purchases/top-products` | `get_purchases_top_products` | product mais comprados no period |

## Cultura DELPI (2)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/cultura-delpi/content` | `get_cultura_delpi_content` | Get Cultura Delpi Content |
| `PUT` | `/cultura-delpi/content` | `update_cultura_delpi_content` | Update culture Delpi content |

## Dashboard (75)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/dashboard/department-idd` | `get_dashboard_department_idd` | Department IDD score |
| `GET` | `/dashboard/department-indicators` | `get_dashboard_department_indicators` | Department IDD with indicators (goals and realized) |
| `GET` | `/dashboard/departments-indicators` | `get_dashboard_departments_indicators` | All departments with IDD, goals and realized per indicator |
| `GET` | `/dashboard/indicators/commercial-closing-rate/meta` | `get_si_indicator_commercial_closing_rate_meta` | Taxa de Fechamento de Negócios — goal |
| `GET` | `/dashboard/indicators/commercial-closing-rate/realized` | `get_si_indicator_commercial_closing_rate_realized` | Taxa de Fechamento de Negócios — actual |
| `GET` | `/dashboard/indicators/commercial-new-business-rol/meta` | `get_si_indicator_commercial_new_business_rol_meta` | % ROL de Novos Negócios — goal |
| `GET` | `/dashboard/indicators/commercial-new-business-rol/realized` | `get_si_indicator_commercial_new_business_rol_realized` | % ROL de Novos Negócios — actual |
| `GET` | `/dashboard/indicators/commercial-rol/meta` | `get_si_indicator_commercial_rol_meta` | ROL — goal |
| `GET` | `/dashboard/indicators/commercial-rol/realized` | `get_si_indicator_commercial_rol_realized` | ROL — actual |
| `GET` | `/dashboard/indicators/commercial-sales-order-otd/meta` | `get_si_indicator_commercial_sales_order_otd_meta` | OTD de Pedidos de Venda — goal |
| `GET` | `/dashboard/indicators/commercial-sales-order-otd/realized` | `get_si_indicator_commercial_sales_order_otd_realized` | OTD de Pedidos de Venda — actual |
| `GET` | `/dashboard/indicators/engineering-projects-on-time/meta` | `get_si_indicator_engineering_projects_on_time_meta` | % de Projetos Concluídos no Prazo — goal |
| `GET` | `/dashboard/indicators/engineering-projects-on-time/realized` | `get_si_indicator_engineering_projects_on_time_realized` | % de Projetos Concluídos no Prazo — actual |
| `GET` | `/dashboard/indicators/engineering-transforma-plus/meta` | `get_si_indicator_engineering_transforma_plus_meta` | Ganhos Financeiros do TRANSFORMA+ DELPI — goal |
| `GET` | `/dashboard/indicators/engineering-transforma-plus/realized` | `get_si_indicator_engineering_transforma_plus_realized` | Ganhos Financeiros do TRANSFORMA+ DELPI — actual |
| `GET` | `/dashboard/indicators/financial-ebitda/meta` | `get_si_indicator_financial_ebitda_meta` | EBITDA / Receita Operacional — goal |
| `GET` | `/dashboard/indicators/financial-ebitda/realized` | `get_si_indicator_financial_ebitda_realized` | EBITDA / Receita Operacional — actual |
| `GET` | `/dashboard/indicators/financial-fixed-cost/meta` | `get_si_indicator_financial_fixed_cost_meta` | % Custos Fixos / Receita Operacional — goal |
| `GET` | `/dashboard/indicators/financial-fixed-cost/realized` | `get_si_indicator_financial_fixed_cost_realized` | % Custos Fixos / Receita Operacional — actual |
| `GET` | `/dashboard/indicators/financial-pmr/meta` | `get_si_indicator_financial_pmr_meta` | Prazo Médio de Recebimento (PMR) — goal |
| `GET` | `/dashboard/indicators/financial-pmr/realized` | `get_si_indicator_financial_pmr_realized` | Prazo Médio de Recebimento (PMR) — actual |
| `GET` | `/dashboard/indicators/hr-absenteeism/meta` | `get_si_indicator_hr_absenteeism_meta` | Absenteísmo — goal |
| `GET` | `/dashboard/indicators/hr-absenteeism/realized` | `get_si_indicator_hr_absenteeism_realized` | Absenteísmo — actual |
| `GET` | `/dashboard/indicators/hr-pdi/meta` | `get_si_indicator_hr_pdi_meta` | Número de PDI's Ativos — goal |
| `GET` | `/dashboard/indicators/hr-pdi/realized` | `get_si_indicator_hr_pdi_realized` | Número de PDI's Ativos — actual |
| `GET` | `/dashboard/indicators/hr-performance-reviews/meta` | `get_si_indicator_hr_performance_reviews_meta` | % de Avaliações de Desempenho Concluídas — goal |
| `GET` | `/dashboard/indicators/hr-performance-reviews/realized` | `get_si_indicator_hr_performance_reviews_realized` | % de Avaliações de Desempenho Concluídas — actual |
| `GET` | `/dashboard/indicators/hr-satisfaction/meta` | `get_si_indicator_hr_satisfaction_meta` | Satisfação Interna (Clima/Engajamento) — goal |
| `GET` | `/dashboard/indicators/hr-satisfaction/realized` | `get_si_indicator_hr_satisfaction_realized` | Satisfação Interna (Clima/Engajamento) — actual |
| `GET` | `/dashboard/indicators/hr-training-hours/meta` | `get_si_indicator_hr_training_hours_meta` | Horas de Treinamento / Colaborador / mês — goal |
| `GET` | `/dashboard/indicators/hr-training-hours/realized` | `get_si_indicator_hr_training_hours_realized` | Horas de Treinamento / Colaborador / mês — actual |
| `GET` | `/dashboard/indicators/hr-turnover/meta` | `get_si_indicator_hr_turnover_meta` | Turnover (Rotatividade) — goal |
| `GET` | `/dashboard/indicators/hr-turnover/realized` | `get_si_indicator_hr_turnover_realized` | Turnover (Rotatividade) — actual |
| `GET` | `/dashboard/indicators/production-costs/meta` | `get_si_indicator_production_costs_meta` | Custos de Produção / ROL — goal |
| `GET` | `/dashboard/indicators/production-costs/realized` | `get_si_indicator_production_costs_realized` | Custos de Produção / ROL — actual |
| `GET` | `/dashboard/indicators/production-depreciation/meta` | `get_si_indicator_production_depreciation_meta` | Depreciação / ROL — goal |
| `GET` | `/dashboard/indicators/production-depreciation/realized` | `get_si_indicator_production_depreciation_realized` | Depreciação / ROL — actual |
| `GET` | `/dashboard/indicators/production-direct-labor/meta` | `get_si_indicator_production_direct_labor_meta` | Custo Mão de Obra Direta / ROL — goal |
| `GET` | `/dashboard/indicators/production-direct-labor/realized` | `get_si_indicator_production_direct_labor_realized` | Custo Mão de Obra Direta / ROL — actual |
| `GET` | `/dashboard/indicators/production-oee/meta` | `get_si_indicator_production_oee_meta` | OEE (Eficiência Global dos Equip.) — goal |
| `GET` | `/dashboard/indicators/production-oee/realized` | `get_si_indicator_production_oee_realized` | OEE (Eficiência Global dos Equip.) — actual |
| `GET` | `/dashboard/indicators/production-otd/meta` | `get_si_indicator_production_otd_meta` | OTD (Entrega no Prazo) — goal |
| `GET` | `/dashboard/indicators/production-otd/realized` | `get_si_indicator_production_otd_realized` | OTD (Entrega no Prazo) — actual |
| `GET` | `/dashboard/indicators/quality-audit-5s/meta` | `get_si_indicator_quality_audit_5s_meta` | Nota Auditoria 5S — goal |
| `GET` | `/dashboard/indicators/quality-audit-5s/realized` | `get_si_indicator_quality_audit_5s_realized` | Nota Auditoria 5S — actual |
| `GET` | `/dashboard/indicators/quality-kaizen-financial/meta` | `get_si_indicator_quality_kaizen_financial_meta` | Ganhos Financeiros Kaizen/mês — goal |
| `GET` | `/dashboard/indicators/quality-kaizen-financial/realized` | `get_si_indicator_quality_kaizen_financial_realized` | Ganhos Financeiros Kaizen/mês — actual |
| `GET` | `/dashboard/indicators/quality-kaizen-ideas/meta` | `get_si_indicator_quality_kaizen_ideas_meta` | Ideias Aprovadas para Kaizen/mês — goal |
| `GET` | `/dashboard/indicators/quality-kaizen-ideas/realized` | `get_si_indicator_quality_kaizen_ideas_realized` | Ideias Aprovadas para Kaizen/mês — actual |
| `GET` | `/dashboard/indicators/quality-ppm-external-components/meta` | `get_si_indicator_quality_ppm_external_components_meta` | PPM Externo Chicotes — goal |
| `GET` | `/dashboard/indicators/quality-ppm-external-components/realized` | `get_si_indicator_quality_ppm_external_components_realized` | PPM Externo Chicotes — actual |
| `GET` | `/dashboard/indicators/quality-ppm-external-plugs/meta` | `get_si_indicator_quality_ppm_external_plugs_meta` | PPM Externo Plugues — goal |
| `GET` | `/dashboard/indicators/quality-ppm-external-plugs/realized` | `get_si_indicator_quality_ppm_external_plugs_realized` | PPM Externo Plugues — actual |
| `GET` | `/dashboard/indicators/quality-ppm-external/meta` | `get_si_indicator_quality_ppm_external_meta` | PPM Externo — goal |
| `GET` | `/dashboard/indicators/quality-ppm-external/realized` | `get_si_indicator_quality_ppm_external_realized` | PPM Externo — actual |
| `GET` | `/dashboard/indicators/quality-ppm-internal-components/meta` | `get_si_indicator_quality_ppm_internal_components_meta` | PPM Interno Chicotes — goal |
| `GET` | `/dashboard/indicators/quality-ppm-internal-components/realized` | `get_si_indicator_quality_ppm_internal_components_realized` | PPM Interno Chicotes — actual |
| `GET` | `/dashboard/indicators/quality-ppm-internal-plugs/meta` | `get_si_indicator_quality_ppm_internal_plugs_meta` | PPM Interno Plugues — goal |
| `GET` | `/dashboard/indicators/quality-ppm-internal-plugs/realized` | `get_si_indicator_quality_ppm_internal_plugs_realized` | PPM Interno Plugues — actual |
| `GET` | `/dashboard/indicators/quality-ppm-internal/meta` | `get_si_indicator_quality_ppm_internal_meta` | PPM Interno — goal |
| `GET` | `/dashboard/indicators/quality-ppm-internal/realized` | `get_si_indicator_quality_ppm_internal_realized` | PPM Interno — actual |
| `GET` | `/dashboard/indicators/quality-rework-cost-pct/meta` | `get_si_indicator_quality_rework_cost_pct_meta` | Custo de Retrabalho / ROL — goal |
| `GET` | `/dashboard/indicators/quality-rework-cost-pct/realized` | `get_si_indicator_quality_rework_cost_pct_realized` | Custo de Retrabalho / ROL — actual |
| `GET` | `/dashboard/indicators/quality-scrap-cost-pct/meta` | `get_si_indicator_quality_scrap_cost_pct_meta` | Custo de Refugo / ROL — goal |
| `GET` | `/dashboard/indicators/quality-scrap-cost-pct/realized` | `get_si_indicator_quality_scrap_cost_pct_realized` | Custo de Refugo / ROL — actual |
| `GET` | `/dashboard/indicators/supplies-cpv/meta` | `get_si_indicator_supplies_cpv_meta` | CPV Consolidado (matriz e filial) — goal |
| `GET` | `/dashboard/indicators/supplies-cpv/realized` | `get_si_indicator_supplies_cpv_realized` | CPV Consolidado (matriz e filial) — actual |
| `GET` | `/dashboard/indicators/supplies-negotiation-savings/meta` | `get_si_indicator_supplies_negotiation_savings_meta` | Economia em Negociações de Compras — goal |
| `GET` | `/dashboard/indicators/supplies-negotiation-savings/realized` | `get_si_indicator_supplies_negotiation_savings_realized` | Economia em Negociações de Compras — actual |
| `GET` | `/dashboard/indicators/supplies-otd/meta` | `get_si_indicator_supplies_otd_meta` | OTD Consolidado de Compras — goal |
| `GET` | `/dashboard/indicators/supplies-otd/realized` | `get_si_indicator_supplies_otd_realized` | OTD Consolidado de Compras — actual |
| `GET` | `/dashboard/indicators/supplies-stock-turnover/meta` | `get_si_indicator_supplies_stock_turnover_meta` | Giro de Estoque — goal |
| `GET` | `/dashboard/indicators/supplies-stock-turnover/realized` | `get_si_indicator_supplies_stock_turnover_realized` | Giro de Estoque — actual |
| `GET` | `/dashboard/indicators/supplies-stock-value/meta` | `get_si_indicator_supplies_stock_value_meta` | Valor Total do Estoque Consolidado — goal |
| `GET` | `/dashboard/indicators/supplies-stock-value/realized` | `get_si_indicator_supplies_stock_value_realized` | Valor Total do Estoque Consolidado — actual |

## Delpi Reports (19)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/reports/definitions` | `list_report_definitions` | List Report Definitions |
| `POST` | `/reports/definitions` | `create_report_definition` | Create Report Definition |
| `GET` | `/reports/definitions/{definition_id}` | `get_report_definition` | Get Report Definition |
| `PATCH` | `/reports/definitions/{definition_id}` | `update_report_definition` | Update Report Definition |
| `GET` | `/reports/definitions/{definition_id}/item-notes` | `list_report_shortage_item_notes` | List Report Shortage Item Notes |
| `PUT` | `/reports/definitions/{definition_id}/item-notes/{product_code}` | `upsert_report_shortage_item_note` | Upsert Report Shortage Item Note |
| `DELETE` | `/reports/definitions/{definition_id}/item-notes/{product_code}` | `delete_report_shortage_item_note` | Delete Report Shortage Item Note |
| `GET` | `/reports/definitions/{definition_id}/recipients` | `list_report_recipients` | List Report Recipients |
| `PUT` | `/reports/definitions/{definition_id}/recipients` | `replace_report_recipients` | Replace Report Recipients |
| `POST` | `/reports/definitions/{definition_id}/run` | `run_report_definition` | Run Report Definition |
| `GET` | `/reports/definitions/{definition_id}/schedule` | `get_report_schedule` | Get Report Schedule |
| `PUT` | `/reports/definitions/{definition_id}/schedule` | `upsert_report_schedule` | Upsert Report Schedule |
| `DELETE` | `/reports/definitions/{definition_id}/schedule` | `delete_report_schedule` | Delete Report Schedule |
| `GET` | `/reports/providers` | `list_report_providers` | List Report Providers |
| `GET` | `/reports/providers/management_revenue_monthly/preview` | `preview_report_provider_management_revenue_monthly` | Preview Management Revenue Monthly |
| `GET` | `/reports/providers/safety_stock_shortage_30d/preview` | `preview_report_provider_safety_stock_shortage_30d` | Preview Safety Stock Shortage 30D |
| `GET` | `/reports/runs` | `list_report_runs` | List Report Runs |
| `GET` | `/reports/runs/{run_id}` | `get_report_run` | Get Report Run |
| `POST` | `/reports/schedules/process-pending` | `process_pending_report_schedules` | Process Pending Report Schedules |

## Engenharia (28)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/engineering/lmps` | `list_lmps` | list LMPs (ordens especiais / amostras) |
| `GET` | `/engineering/lmps/dashboard` | `list_lmps_dashboard` | LMPs dashboard |
| `GET` | `/engineering/lmps/dashboard/charts` | `get_lmps_dashboard_charts` | Lmps dashboard charts |
| `GET` | `/engineering/lmps/dashboard/items` | `list_lmps_dashboard_items` | Lmps dashboard items |
| `GET` | `/engineering/lmps/dashboard/summary` | `get_lmps_dashboard_summary` | LMPs dashboard summary |
| `GET` | `/engineering/lmps/nonconformities` | `list_lmp_nonconformities` | List LMP nonconformities |
| `POST` | `/engineering/lmps/nonconformities` | `create_lmp_nonconformity` | Create LMP nonconformity |
| `GET` | `/engineering/lmps/nonconformities/export` | `export_lmp_nonconformities` | Export LMP nonconformities as JSON |
| `POST` | `/engineering/lmps/nonconformities/import` | `import_lmp_nonconformities` | Import LMP nonconformities from JSON |
| `GET` | `/engineering/lmps/nonconformities/problem-tags` | `list_lmp_problem_tags` | List LMP problem tags |
| `GET` | `/engineering/lmps/nonconformities/streak` | `get_lmp_nonconformity_streak` | LMP nonconformity days-without streak |
| `GET` | `/engineering/lmps/nonconformities/{record_id}` | `get_lmp_nonconformity` | Get LMP nonconformity by id |
| `PUT` | `/engineering/lmps/nonconformities/{record_id}` | `update_lmp_nonconformity` | Update LMP nonconformity |
| `DELETE` | `/engineering/lmps/nonconformities/{record_id}` | `delete_lmp_nonconformity` | Delete LMP nonconformity |
| `GET` | `/engineering/lmps/nonconformities/{record_id}/history` | `list_lmp_nonconformity_history` | List LMP nonconformity change history |
| `GET` | `/engineering/lmps/{sale_number}` | `get_lmp_by_sale_number` | Lmp by sale number |
| `GET` | `/engineering/lmps/{sale_number}/history/events` | `get_lmp_history_events` | Lmp history events |
| `GET` | `/engineering/lmps/{sale_number}/history/flow` | `get_lmp_history_flow` | Lmp history flow |
| `GET` | `/engineering/mini-applicators/ferramentas` | `list_mini_applicators_ferramentas` | list ferramentas mini-aplicadores |
| `POST` | `/engineering/mini-applicators/ferramentas/golpes/batch` | `post_mini_applicators_golpes_batch` | Golpes batch for mini-applicator tools |
| `GET` | `/engineering/mini-applicators/ferramentas/{codigo}` | `get_mini_applicators_ferramenta` | Mini applicators tool |
| `GET` | `/engineering/mini-applicators/ferramentas/{codigo}/componentes` | `list_mini_applicators_componentes` | Mini applicators components |
| `GET` | `/engineering/mini-applicators/ferramentas/{codigo}/golpes` | `get_mini_applicators_golpes` | Golpes do mini-aplicador no period |
| `GET` | `/engineering/mini-applicators/ferramentas/{codigo}/pecas` | `list_mini_applicators_pecas` | Mini applicators pecas |
| `GET` | `/engineering/mini-applicators/pecas-reposicao` | `list_mini_applicators_pecas_reposicao` | Mini applicators pecas reposicao |
| `GET` | `/engineering/transforma-mais/processes` | `list_transforma_mais_processes` | list processos Transforma Mais |
| `GET` | `/engineering/transforma-mais/processes/summary` | `get_transforma_mais_summary` | Transforma mais summary |
| `GET` | `/engineering/transformometro/savings-investment/series` | `get_transformometro_savings_investment_series` | Economia bruta vs Investimento do TRANSFORMA+ DELPI |

## Financeiro (4)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/financial/ebitda_pct` | `get_financial_ebitda_pct` | Financial EBITDA percentage |
| `GET` | `/financial/fixed_cost_pct` | `get_financial_fixed_cost_pct` | Financial fixed cost percentage |
| `GET` | `/financial/pmr` | `get_financial_pmr` | Financial pmr |
| `GET` | `/financial/rol` | `get_financial_rol` | Financial ROL (net operating revenue) |

## Financeiro — Despesas por Centro de Custo (6)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/financeiro/despesas-centro-custo/filtros` | `get_financeiro_despesas_centro_custo_filtros` | Indicator — financial expenses cost center filtros |
| `GET` | `/financeiro/despesas-centro-custo/lancamentos` | `get_financeiro_despesas_centro_custo_lancamentos` | Cost-center expenses — ledger entries |
| `GET` | `/financeiro/despesas-centro-custo/ranking-centros` | `get_financeiro_despesas_centro_custo_ranking_centros` | Financial expenses cost center ranking centers |
| `GET` | `/financeiro/despesas-centro-custo/ranking-fornecedores` | `get_financeiro_despesas_centro_custo_ranking_fornecedores` | Financial expenses cost center ranking suppliers |
| `GET` | `/financeiro/despesas-centro-custo/resumo` | `get_financeiro_despesas_centro_custo_resumo` | Cost-center expenses — summary KPIs |
| `GET` | `/financeiro/despesas-centro-custo/serie` | `get_financeiro_despesas_centro_custo_serie` | Financial expenses cost center series |

## Financeiro — Inadimplência (5)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/financeiro/inadimplencia/clientes` | `get_financeiro_inadimplencia_clientes` | Delinquency — customers ranking |
| `GET` | `/financeiro/inadimplencia/faixas-atraso` | `get_financeiro_inadimplencia_faixas_atraso` | List — financial inadimplencia faixas atraso |
| `GET` | `/financeiro/inadimplencia/mensal` | `get_financeiro_inadimplencia_mensal` | List — financial inadimplencia mensal |
| `GET` | `/financeiro/inadimplencia/resumo` | `get_financeiro_inadimplencia_resumo` | Delinquency — summary KPIs |
| `GET` | `/financeiro/inadimplencia/titulos` | `get_financeiro_inadimplencia_titulos` | Delinquency — titles list |

## Guias e Procedimentos (3)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/guias-procedimentos/departments` | `list_guias_procedimentos_departments` | List Guias Departments |
| `GET` | `/guias-procedimentos/departments/{slug}` | `get_guias_procedimentos_department` | Get Guias Department |
| `GET` | `/guias-procedimentos/procedures/{slug}` | `get_guias_procedimentos_procedure` | Get Guias Procedure |

## Guias e Procedimentos — Admin (12)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/guias-procedimentos/admin/departments` | `list_guias_procedimentos_admin_departments` | List Admin Departments |
| `POST` | `/guias-procedimentos/admin/departments` | `create_guias_procedimentos_admin_department` | Create Admin Department |
| `GET` | `/guias-procedimentos/admin/departments/{department_id}` | `get_guias_procedimentos_admin_department` | Get Admin Department |
| `PUT` | `/guias-procedimentos/admin/departments/{department_id}` | `update_guias_procedimentos_admin_department` | Update Admin Department |
| `GET` | `/guias-procedimentos/admin/procedures` | `list_guias_procedimentos_admin_procedures` | List Admin Procedures |
| `POST` | `/guias-procedimentos/admin/procedures` | `create_guias_procedimentos_admin_procedure` | Create Admin Procedure |
| `GET` | `/guias-procedimentos/admin/procedures/{procedure_id}` | `get_guias_procedimentos_admin_procedure` | Get Admin Procedure |
| `PUT` | `/guias-procedimentos/admin/procedures/{procedure_id}` | `update_guias_procedimentos_admin_procedure` | Update Admin Procedure |
| `POST` | `/guias-procedimentos/admin/procedures/{procedure_id}/archive` | `archive_guias_procedimentos_admin_procedure` | Archive Admin Procedure |
| `POST` | `/guias-procedimentos/admin/procedures/{procedure_id}/publish` | `publish_guias_procedimentos_admin_procedure` | Publish Admin Procedure |
| `POST` | `/guias-procedimentos/admin/procedures/{procedure_id}/restore` | `restore_guias_procedimentos_admin_procedure` | Restore Admin Procedure |
| `POST` | `/guias-procedimentos/admin/procedures/{procedure_id}/unpublish` | `unpublish_guias_procedimentos_admin_procedure` | Unpublish Admin Procedure |

## Guias e Procedimentos — Admin Media (10)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `PUT` | `/guias-procedimentos/admin/attachments/{attachment_id}` | `update_guias_procedimentos_admin_attachment` | Update attachment metadata |
| `POST` | `/guias-procedimentos/admin/attachments/{attachment_id}/archive` | `archive_guias_procedimentos_admin_attachment` | Archive procedure attachment |
| `PUT` | `/guias-procedimentos/admin/media/{media_id}` | `update_guias_procedimentos_admin_media` | Update procedure media metadata |
| `POST` | `/guias-procedimentos/admin/media/{media_id}/archive` | `archive_guias_procedimentos_admin_media` | Archive procedure media |
| `GET` | `/guias-procedimentos/admin/procedures/{procedure_id}/attachments` | `list_guias_procedimentos_admin_procedure_attachments` | List admin procedure attachments |
| `POST` | `/guias-procedimentos/admin/procedures/{procedure_id}/attachments` | `upload_guias_procedimentos_admin_procedure_attachment` | Upload procedure attachment |
| `GET` | `/guias-procedimentos/admin/procedures/{procedure_id}/media` | `list_guias_procedimentos_admin_procedure_media` | List admin procedure media |
| `POST` | `/guias-procedimentos/admin/procedures/{procedure_id}/media/external-videos` | `create_guias_procedimentos_admin_external_video` | Create external procedure video |
| `POST` | `/guias-procedimentos/admin/procedures/{procedure_id}/media/images` | `upload_guias_procedimentos_admin_procedure_image` | Upload procedure image |
| `POST` | `/guias-procedimentos/admin/procedures/{procedure_id}/media/videos` | `upload_guias_procedimentos_admin_procedure_video` | Upload procedure video |

## Guias e Procedimentos — Media (4)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/guias-procedimentos/attachments/{attachment_id}/file` | `download_guias_procedimentos_attachment_file` | Download procedure attachment file |
| `GET` | `/guias-procedimentos/media/{media_id}/file` | `download_guias_procedimentos_media_file` | Download procedure media file |
| `GET` | `/guias-procedimentos/procedures/{procedure_id}/attachments` | `list_guias_procedimentos_procedure_attachments` | List procedure attachments |
| `GET` | `/guias-procedimentos/procedures/{procedure_id}/media` | `list_guias_procedimentos_procedure_media` | List procedure media |

## Health (1)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/health` | `get_health` | Root |

## Inspeções de Entrada (7)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/inspecoes-entrada/historico` | `get_inspecoes_entrada_historico` | Incoming inspections — history |
| `GET` | `/inspecoes-entrada/historico/detalhe` | `get_inspecoes_entrada_historico_detalhe` | Incoming inspection — history detail |
| `GET` | `/inspecoes-entrada/pendentes` | `get_inspecoes_entrada_pendentes` | Incoming inspections — pending |
| `GET` | `/inspecoes-entrada/pendentes-fornecedor` | `get_inspecoes_entrada_pendentes_fornecedor` | Incoming inspections — pending by supplier |
| `GET` | `/inspecoes-entrada/rejeitadas-ensaiador` | `get_inspecoes_entrada_rejeitadas_ensaiador` | Incoming inspections — rejected by tester |
| `GET` | `/inspecoes-entrada/rejeitadas-produto` | `get_inspecoes_entrada_rejeitadas_produto` | Incoming inspections — rejected by product |
| `GET` | `/inspecoes-entrada/resumo` | `get_inspecoes_entrada_resumo` | Incoming inspections — summary KPIs |

## Inspeções de Processo (8)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/inspecoes-processo/auditoria-apontamentos` | `get_inspecoes_processo_auditoria_apontamentos` | Inspections processo auditoria apontamentos |
| `GET` | `/inspecoes-processo/historico` | `get_inspecoes_processo_historico` | In-process inspections — history |
| `GET` | `/inspecoes-processo/historico/detalhe` | `get_inspecoes_processo_historico_detalhe` | Inspections processo history detail |
| `GET` | `/inspecoes-processo/por-ensaiador` | `get_inspecoes_processo_por_ensaiador` | Inspections processo por tester |
| `GET` | `/inspecoes-processo/por-operacao` | `get_inspecoes_processo_por_operacao` | Inspections processo por operacao |
| `GET` | `/inspecoes-processo/por-produto` | `get_inspecoes_processo_por_produto` | Inspections processo por product |
| `GET` | `/inspecoes-processo/ranking-ensaio` | `get_inspecoes_processo_ranking_ensaio` | Inspections processo ranking ensaio |
| `GET` | `/inspecoes-processo/resumo` | `get_inspecoes_processo_resumo` | In-process inspections — summary KPIs |

## Invoice issuance (14)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/invoice-issuance/carriers` | `search_invoice_issuance_carriers` | Search invoice issuance carriers |
| `GET` | `/invoice-issuance/open-sales-orders` | `list_invoice_issuance_open_sales_orders` | List open sales orders for issuance |
| `GET` | `/invoice-issuance/parties` | `search_invoice_issuance_parties` | Search invoice issuance parties |
| `GET` | `/invoice-issuance/products` | `search_invoice_issuance_products` | Search invoice issuance products |
| `GET` | `/invoice-issuance/products/{code}/warehouse-01-balance` | `get_invoice_issuance_warehouse_01_balance` | Warehouse 01 stock hint for issuance |
| `GET` | `/invoice-issuance/requests` | `list_invoice_issuance_requests` | List invoice issuance requests |
| `POST` | `/invoice-issuance/requests` | `create_invoice_issuance_request` | Create invoice issuance request |
| `GET` | `/invoice-issuance/requests/{request_id}` | `get_invoice_issuance_request` | Get invoice issuance request |
| `PATCH` | `/invoice-issuance/requests/{request_id}` | `update_invoice_issuance_request` | Update returned issuance request |
| `POST` | `/invoice-issuance/requests/{request_id}/cancel` | `cancel_invoice_issuance_request` | Cancel invoice issuance request |
| `POST` | `/invoice-issuance/requests/{request_id}/issue` | `issue_invoice_issuance_request` | Mark invoice issuance as issued |
| `POST` | `/invoice-issuance/requests/{request_id}/resubmit` | `resubmit_invoice_issuance_request` | Resubmit invoice issuance request |
| `POST` | `/invoice-issuance/requests/{request_id}/return` | `return_invoice_issuance_request` | Return invoice issuance request |
| `POST` | `/invoice-issuance/requests/{request_id}/start` | `start_invoice_issuance_request` | Start invoice issuance attendance |

## Kaizen — público (1)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `POST` | `/public/kaizen/suggestions` | `create_public_kaizen_suggestion` | Create Public Kaizen Suggestion |

## Lançamento de Notas Fiscais (15)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `POST` | `/lancamento-notas-fiscais/reconciliation/refresh` | `refresh_lancamento_notas_fiscais_reconciliation` | Refresh Reconciliation |
| `POST` | `/lancamento-notas-fiscais/reconciliation/run` | `run_lancamento_notas_fiscais_reconciliation` | Run Reconciliation |
| `GET` | `/lancamento-notas-fiscais/requests` | `list_lancamento_notas_fiscais_requests` | List Requests |
| `POST` | `/lancamento-notas-fiscais/requests` | `create_lancamento_notas_fiscais_request` | Create Request |
| `GET` | `/lancamento-notas-fiscais/requests/{request_id}` | `get_lancamento_notas_fiscais_request` | Get Request |
| `PATCH` | `/lancamento-notas-fiscais/requests/{request_id}` | `update_lancamento_notas_fiscais_request` | Update Request |
| `POST` | `/lancamento-notas-fiscais/requests/{request_id}/block` | `block_lancamento_notas_fiscais_request` | Block Request |
| `POST` | `/lancamento-notas-fiscais/requests/{request_id}/cancel` | `cancel_lancamento_notas_fiscais_request` | Cancel Request |
| `POST` | `/lancamento-notas-fiscais/requests/{request_id}/comments` | `add_lancamento_notas_fiscais_comment` | Add Comment |
| `POST` | `/lancamento-notas-fiscais/requests/{request_id}/post-manual` | `post_manual_lancamento_notas_fiscais_request` | Post Manual Request |
| `GET` | `/lancamento-notas-fiscais/requests/{request_id}/purchase-orders` | `list_lancamento_notas_fiscais_request_purchase_orders` | List Request Purchase Orders |
| `POST` | `/lancamento-notas-fiscais/requests/{request_id}/purchase-orders/link` | `link_lancamento_notas_fiscais_request_purchase_order` | Link Request Purchase Order |
| `POST` | `/lancamento-notas-fiscais/requests/{request_id}/resume` | `resume_lancamento_notas_fiscais_request` | Resume Request |
| `POST` | `/lancamento-notas-fiscais/requests/{request_id}/start` | `start_lancamento_notas_fiscais_request` | Start Request |
| `GET` | `/lancamento-notas-fiscais/suppliers` | `search_lancamento_notas_fiscais_suppliers` | Search Suppliers |

## Mural de Acessos (14)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/mural-acessos/hubs` | `list_mural_acessos_hubs` | List Hubs |
| `POST` | `/mural-acessos/hubs` | `create_mural_acessos_hub` | Create Hub |
| `GET` | `/mural-acessos/hubs/{hub_id}` | `get_mural_acessos_hub` | Get Hub |
| `PUT` | `/mural-acessos/hubs/{hub_id}` | `update_mural_acessos_hub` | Update Hub |
| `DELETE` | `/mural-acessos/hubs/{hub_id}` | `delete_mural_acessos_hub` | Delete Hub |
| `GET` | `/mural-acessos/hubs/{hub_id}/links` | `list_mural_acessos_links` | List Links |
| `POST` | `/mural-acessos/hubs/{hub_id}/links` | `create_mural_acessos_link` | Create Link |
| `PUT` | `/mural-acessos/hubs/{hub_id}/links/reorder` | `reorder_mural_acessos_links` | Reorder Links |
| `GET` | `/mural-acessos/hubs/{hub_id}/qr.png` | `get_mural_acessos_hub_qr` | Get Hub Qr |
| `PUT` | `/mural-acessos/links/{link_id}` | `update_mural_acessos_link` | Update Link |
| `DELETE` | `/mural-acessos/links/{link_id}` | `delete_mural_acessos_link` | Delete Link |
| `GET` | `/mural-acessos/links/{link_id}/image` | `get_mural_acessos_link_image` | Get Link Image |
| `POST` | `/mural-acessos/links/{link_id}/image` | `upload_mural_acessos_link_image` | Upload Link Image |
| `DELETE` | `/mural-acessos/links/{link_id}/image` | `delete_mural_acessos_link_image` | Delete Link Image |

## Mural de Acessos — público (3)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/public/mural-acessos/links/{link_id}/image` | `get_public_mural_acessos_link_image` | Get Public Link Image |
| `GET` | `/public/mural-acessos/menu` | `list_public_mural_acessos_menu` | List Public Menu |
| `GET` | `/public/mural-acessos/menu/{public_token}` | `list_public_mural_acessos_menu_by_token` | List Public Menu By Token |

## Pedidos de Venda em Aberto (25)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/pedidos-venda-abertos/` | `list_pedidos_venda_abertos` | Orders sales abertos |
| `GET` | `/pedidos-venda-abertos/clientes/{codigo}/{loja}/notas-fiscais` | `list_cliente_notas_fiscais_saida` | Customer outbound invoices by code and store |
| `POST` | `/pedidos-venda-abertos/customers/billing-series` | `list_customer_billing_series` | Customer billing series |
| `POST` | `/pedidos-venda-abertos/customers/enrichment` | `enrich_portfolio_customers` | Enrich portfolio customers |
| `POST` | `/pedidos-venda-abertos/customers/open-order-metrics` | `list_customer_open_order_metrics` | Lista paginada — Customer open order metrics |
| `GET` | `/pedidos-venda-abertos/customers/search` | `search_active_customers_for_portfolio` | Search active TOTVS customers for portfolio |
| `GET` | `/pedidos-venda-abertos/customers/{codigo}/{loja}/avatar` | `get_customer_avatar` | Get customer avatar |
| `PUT` | `/pedidos-venda-abertos/customers/{codigo}/{loja}/avatar` | `upsert_customer_avatar` | Upload customer avatar |
| `DELETE` | `/pedidos-venda-abertos/customers/{codigo}/{loja}/avatar` | `delete_customer_avatar` | Delete customer avatar |
| `GET` | `/pedidos-venda-abertos/ops-abertas` | `list_ops_abertas_pedidos_venda` | Production orders open orders sales |
| `GET` | `/pedidos-venda-abertos/sellers` | `list_seller_portfolios` | List seller portfolios |
| `POST` | `/pedidos-venda-abertos/sellers` | `create_seller_portfolio` | Create seller portfolio |
| `GET` | `/pedidos-venda-abertos/sellers/me` | `get_my_seller_portfolio` | My seller portfolio |
| `GET` | `/pedidos-venda-abertos/sellers/{seller_id}` | `get_seller_portfolio` | Get seller portfolio |
| `PATCH` | `/pedidos-venda-abertos/sellers/{seller_id}` | `update_seller_portfolio` | Update seller portfolio |
| `DELETE` | `/pedidos-venda-abertos/sellers/{seller_id}` | `deactivate_seller_portfolio` | Deactivate seller portfolio |
| `PUT` | `/pedidos-venda-abertos/sellers/{seller_id}/customers` | `replace_seller_customers` | Replace seller customers |
| `POST` | `/pedidos-venda-abertos/sellers/{seller_id}/customers` | `add_seller_customer` | Add seller customer |
| `DELETE` | `/pedidos-venda-abertos/sellers/{seller_id}/customers` | `remove_seller_customer` | Remove seller customer |
| `POST` | `/pedidos-venda-abertos/sellers/{seller_id}/customers/transfer` | `transfer_seller_customers` | Transfer seller customers |
| `GET` | `/pedidos-venda-abertos/totvs-open-orders` | `list_totvs_open_orders` | TOTVS open sales orders (no portfolio membership) |
| `GET` | `/pedidos-venda-abertos/totvs-open-orders/{customer_code}/{customer_store}` | `list_totvs_open_orders_by_customer` | TOTVS open sales orders by customer |
| `GET` | `/pedidos-venda-abertos/totvs-outbound-invoices/{branch}/{invoice_number}/{invoice_series}` | `get_totvs_outbound_invoice` | TOTVS outbound invoice by key |
| `GET` | `/pedidos-venda-abertos/totvs-outbound-invoices/{customer_code}/{customer_store}` | `list_totvs_outbound_invoices` | TOTVS outbound invoices (no portfolio membership) |
| `GET` | `/pedidos-venda-abertos/totvs-recently-closed-orders` | `list_totvs_recently_closed_orders` | Lista paginada — Pedidos de venda em aberto |

## Planejamento Orçamentário (87)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/planejamento-orcamentario/admin/budget-responsibilities` | `list_planejamento_orcamentario_admin_budget_responsibilities` | Admin List Budget Responsibilities |
| `POST` | `/planejamento-orcamentario/admin/budget-responsibilities` | `create_planejamento_orcamentario_admin_budget_responsibility` | Admin Create Budget Responsibility |
| `GET` | `/planejamento-orcamentario/admin/budget-responsibilities/{responsibility_id}` | `get_planejamento_orcamentario_admin_budget_responsibility` | Admin Get Budget Responsibility |
| `PUT` | `/planejamento-orcamentario/admin/budget-responsibilities/{responsibility_id}` | `update_planejamento_orcamentario_admin_budget_responsibility` | Admin Update Budget Responsibility |
| `POST` | `/planejamento-orcamentario/admin/budget-responsibilities/{responsibility_id}/deactivate` | `deactivate_planejamento_orcamentario_admin_budget_responsibility` | Admin Deactivate Budget Responsibility |
| `POST` | `/planejamento-orcamentario/admin/budget-responsibilities/{responsibility_id}/reactivate` | `reactivate_planejamento_orcamentario_admin_budget_responsibility` | Admin Reactivate Budget Responsibility |
| `GET` | `/planejamento-orcamentario/admin/capex/categories` | `list_planejamento_orcamentario_admin_capex_categories` | Admin List Capex Categories |
| `POST` | `/planejamento-orcamentario/admin/capex/categories` | `create_planejamento_orcamentario_admin_capex_category` | Admin Create Capex Category |
| `PUT` | `/planejamento-orcamentario/admin/capex/categories/{category_id}` | `update_planejamento_orcamentario_admin_capex_category` | Admin Update Capex Category |
| `POST` | `/planejamento-orcamentario/admin/capex/categories/{category_id}/deactivate` | `deactivate_planejamento_orcamentario_admin_capex_category` | Admin Deactivate Capex Category |
| `POST` | `/planejamento-orcamentario/admin/capex/categories/{category_id}/icon-image` | `upload_planejamento_orcamentario_admin_capex_category_icon_image` | Admin Upload Capex Category Icon Image |
| `DELETE` | `/planejamento-orcamentario/admin/capex/categories/{category_id}/icon-image` | `clear_planejamento_orcamentario_admin_capex_category_icon_image` | Admin Clear Capex Category Icon Image |
| `POST` | `/planejamento-orcamentario/admin/capex/categories/{category_id}/reactivate` | `reactivate_planejamento_orcamentario_admin_capex_category` | Admin Reactivate Capex Category |
| `PUT` | `/planejamento-orcamentario/admin/documents/{document_id}` | `update_planejamento_orcamentario_admin_document` | Admin Update Document |
| `POST` | `/planejamento-orcamentario/admin/documents/{document_id}/archive` | `archive_planejamento_orcamentario_admin_document` | Admin Archive Document |
| `GET` | `/planejamento-orcamentario/admin/exercises` | `list_planejamento_orcamentario_admin_exercises` | Admin List Exercises |
| `POST` | `/planejamento-orcamentario/admin/exercises` | `create_planejamento_orcamentario_admin_exercise` | Admin Create Exercise |
| `GET` | `/planejamento-orcamentario/admin/exercises/{exercise_id}` | `get_planejamento_orcamentario_admin_exercise` | Admin Get Exercise |
| `PUT` | `/planejamento-orcamentario/admin/exercises/{exercise_id}` | `update_planejamento_orcamentario_admin_exercise` | Admin Update Exercise |
| `GET` | `/planejamento-orcamentario/admin/exercises/{exercise_id}/guidance` | `get_planejamento_orcamentario_admin_guidance` | Admin Get Guidance |
| `POST` | `/planejamento-orcamentario/admin/exercises/{exercise_id}/guidance` | `create_planejamento_orcamentario_admin_guidance_draft` | Admin Create Guidance |
| `POST` | `/planejamento-orcamentario/admin/exercises/{exercise_id}/transitions` | `transition_planejamento_orcamentario_admin_exercise` | Admin Transition Exercise |
| `PUT` | `/planejamento-orcamentario/admin/guidance/{guidance_id}` | `update_planejamento_orcamentario_admin_guidance` | Admin Update Guidance |
| `GET` | `/planejamento-orcamentario/admin/guidance/{guidance_id}/documents` | `list_planejamento_orcamentario_admin_documents` | Admin List Documents |
| `POST` | `/planejamento-orcamentario/admin/guidance/{guidance_id}/documents` | `upload_planejamento_orcamentario_admin_document` | Admin Upload Document |
| `POST` | `/planejamento-orcamentario/admin/guidance/{guidance_id}/publish` | `publish_planejamento_orcamentario_admin_guidance` | Admin Publish Guidance |
| `POST` | `/planejamento-orcamentario/admin/org/cost-centers` | `upsert_planejamento_orcamentario_admin_cost_center` | Admin Upsert Cost Center |
| `POST` | `/planejamento-orcamentario/admin/org/cost-centers/from-erp` | `create_planejamento_orcamentario_admin_cost_center_from_erp` | Admin Create Cost Center From Erp |
| `PATCH` | `/planejamento-orcamentario/admin/org/cost-centers/icon` | `update_planejamento_orcamentario_admin_cost_center_icon` | Admin Update Cost Center Icon |
| `GET` | `/planejamento-orcamentario/admin/scopes` | `list_planejamento_orcamentario_admin_scopes` | Admin List Scopes |
| `POST` | `/planejamento-orcamentario/admin/scopes` | `create_planejamento_orcamentario_admin_scope` | Admin Create Scope |
| `PUT` | `/planejamento-orcamentario/admin/scopes/{scope_id}` | `update_planejamento_orcamentario_admin_scope` | Admin Update Scope |
| `POST` | `/planejamento-orcamentario/admin/scopes/{scope_id}/deactivate` | `deactivate_planejamento_orcamentario_admin_scope` | Admin Deactivate Scope |
| `POST` | `/planejamento-orcamentario/capex/attachments/{attachment_id}/archive` | `archive_planejamento_orcamentario_capex_attachment` | Archive Capex Attachment |
| `GET` | `/planejamento-orcamentario/capex/attachments/{attachment_id}/download` | `download_planejamento_orcamentario_capex_attachment` | Download Capex Attachment |
| `GET` | `/planejamento-orcamentario/capex/categories` | `list_planejamento_orcamentario_capex_categories` | List Capex Categories |
| `GET` | `/planejamento-orcamentario/capex/categories/{category_id}/icon-image` | `get_planejamento_orcamentario_capex_category_icon_image` | Get Capex Category Icon Image |
| `GET` | `/planejamento-orcamentario/capex/consolidation/by-area` | `list_planejamento_orcamentario_capex_consolidation_by_area` | List Capex Consolidation By Area |
| `GET` | `/planejamento-orcamentario/capex/consolidation/by-category` | `list_planejamento_orcamentario_capex_consolidation_by_category` | List Capex Consolidation By Category |
| `GET` | `/planejamento-orcamentario/capex/consolidation/by-cost-center` | `list_planejamento_orcamentario_capex_consolidation_by_cost_center` | List Capex Consolidation By Cost Center |
| `GET` | `/planejamento-orcamentario/capex/consolidation/by-month` | `list_planejamento_orcamentario_capex_consolidation_by_month` | List Capex Consolidation By Month |
| `GET` | `/planejamento-orcamentario/capex/consolidation/by-origin` | `list_planejamento_orcamentario_capex_consolidation_by_origin` | List Capex Consolidation By Origin |
| `GET` | `/planejamento-orcamentario/capex/consolidation/by-plan-status` | `list_planejamento_orcamentario_capex_consolidation_by_plan_status` | List Capex Consolidation By Plan Status |
| `GET` | `/planejamento-orcamentario/capex/consolidation/by-priority` | `list_planejamento_orcamentario_capex_consolidation_by_priority` | List Capex Consolidation By Priority |
| `GET` | `/planejamento-orcamentario/capex/consolidation/by-unit` | `list_planejamento_orcamentario_capex_consolidation_by_unit` | List Capex Consolidation By Unit |
| `GET` | `/planejamento-orcamentario/capex/consolidation/details` | `list_planejamento_orcamentario_capex_consolidation_details` | List Capex Consolidation Details |
| `GET` | `/planejamento-orcamentario/capex/consolidation/export.xlsx` | `export_planejamento_orcamentario_capex_consolidation_xlsx` | Export Capex Consolidation Xlsx |
| `GET` | `/planejamento-orcamentario/capex/consolidation/summary` | `get_planejamento_orcamentario_capex_consolidation_summary` | Get Capex Consolidation Summary |
| `GET` | `/planejamento-orcamentario/capex/investments` | `list_planejamento_orcamentario_capex_investments` | List Capex Investments |
| `POST` | `/planejamento-orcamentario/capex/investments` | `create_planejamento_orcamentario_capex_investment` | Create Capex Investment |
| `GET` | `/planejamento-orcamentario/capex/investments/{investment_id}` | `get_planejamento_orcamentario_capex_investment` | Get Capex Investment |
| `PUT` | `/planejamento-orcamentario/capex/investments/{investment_id}` | `update_planejamento_orcamentario_capex_investment` | Update Capex Investment |
| `POST` | `/planejamento-orcamentario/capex/investments/{investment_id}/archive` | `archive_planejamento_orcamentario_capex_investment` | Archive Capex Investment |
| `GET` | `/planejamento-orcamentario/capex/investments/{investment_id}/attachments` | `list_planejamento_orcamentario_capex_investment_attachments` | List Capex Investment Attachments |
| `POST` | `/planejamento-orcamentario/capex/investments/{investment_id}/attachments` | `upload_planejamento_orcamentario_capex_investment_attachment` | Upload Capex Investment Attachment |
| `GET` | `/planejamento-orcamentario/capex/my-responsibilities` | `list_planejamento_orcamentario_capex_my_responsibilities` | List Capex My Responsibilities |
| `GET` | `/planejamento-orcamentario/capex/plans` | `list_planejamento_orcamentario_capex_plans` | List Capex Plans |
| `POST` | `/planejamento-orcamentario/capex/plans/resolve` | `resolve_planejamento_orcamentario_capex_plan` | Resolve Capex Plan |
| `GET` | `/planejamento-orcamentario/capex/plans/{plan_id}` | `get_planejamento_orcamentario_capex_plan` | Get Capex Plan |
| `GET` | `/planejamento-orcamentario/capex/plans/{plan_id}/history` | `list_planejamento_orcamentario_capex_plan_history` | List Capex Plan History |
| `POST` | `/planejamento-orcamentario/capex/plans/{plan_id}/submit` | `submit_planejamento_orcamentario_capex_plan` | Submit Capex Plan |
| `GET` | `/planejamento-orcamentario/capex/review-queue` | `list_planejamento_orcamentario_capex_review_queue` | List Capex Review Queue |
| `GET` | `/planejamento-orcamentario/capex/review/{plan_id}` | `get_planejamento_orcamentario_capex_review` | Get Capex Review |
| `POST` | `/planejamento-orcamentario/capex/review/{plan_id}/approve` | `approve_planejamento_orcamentario_capex_plan` | Approve Capex Plan |
| `POST` | `/planejamento-orcamentario/capex/review/{plan_id}/investments/{investment_id}/approve` | `approve_planejamento_orcamentario_capex_investment` | Approve Capex Investment |
| `POST` | `/planejamento-orcamentario/capex/review/{plan_id}/investments/{investment_id}/reject` | `reject_planejamento_orcamentario_capex_investment` | Reject Capex Investment |
| `POST` | `/planejamento-orcamentario/capex/review/{plan_id}/reject` | `reject_planejamento_orcamentario_capex_plan` | Reject Capex Plan |
| `POST` | `/planejamento-orcamentario/capex/review/{plan_id}/request-changes` | `request_changes_planejamento_orcamentario_capex_plan` | Request Changes Capex Plan |
| `GET` | `/planejamento-orcamentario/context` | `get_planejamento_orcamentario_context` | Get Context |
| `GET` | `/planejamento-orcamentario/documents/{document_id}/download` | `download_planejamento_orcamentario_document` | Download Document |
| `GET` | `/planejamento-orcamentario/guidance/current` | `get_planejamento_orcamentario_guidance_current` | Get Guidance Current |
| `POST` | `/planejamento-orcamentario/guidance/current/acknowledge` | `acknowledge_planejamento_orcamentario_guidance` | Acknowledge Guidance |
| `GET` | `/planejamento-orcamentario/guidance/current/documents` | `list_planejamento_orcamentario_guidance_documents` | List Guidance Documents |
| `GET` | `/planejamento-orcamentario/org/erp-cost-centers` | `list_planejamento_orcamentario_org_erp_cost_centers` | List Erp Cost Centers |
| `PUT` | `/planejamento-orcamentario/personnel/lines/{line_id}` | `update_planejamento_orcamentario_personnel_plan_line` | Update Personnel Plan Line |
| `POST` | `/planejamento-orcamentario/personnel/lines/{line_id}/archive` | `archive_planejamento_orcamentario_personnel_plan_line` | Archive Personnel Plan Line |
| `GET` | `/planejamento-orcamentario/personnel/plans` | `list_planejamento_orcamentario_personnel_plans` | List Personnel Plans |
| `POST` | `/planejamento-orcamentario/personnel/plans/resolve` | `resolve_planejamento_orcamentario_personnel_plan` | Resolve Personnel Plan |
| `GET` | `/planejamento-orcamentario/personnel/plans/{plan_id}` | `get_planejamento_orcamentario_personnel_plan` | Get Personnel Plan |
| `GET` | `/planejamento-orcamentario/personnel/plans/{plan_id}/history` | `list_planejamento_orcamentario_personnel_plan_history` | List Personnel Plan History |
| `POST` | `/planejamento-orcamentario/personnel/plans/{plan_id}/lines` | `create_planejamento_orcamentario_personnel_plan_line` | Create Personnel Plan Line |
| `POST` | `/planejamento-orcamentario/personnel/plans/{plan_id}/submit` | `submit_planejamento_orcamentario_personnel_plan` | Submit Personnel Plan |
| `GET` | `/planejamento-orcamentario/personnel/review-queue` | `list_planejamento_orcamentario_personnel_review_queue` | List Personnel Review Queue |
| `GET` | `/planejamento-orcamentario/personnel/review/{plan_id}` | `get_planejamento_orcamentario_personnel_review` | Get Personnel Review |
| `POST` | `/planejamento-orcamentario/personnel/review/{plan_id}/approve` | `approve_planejamento_orcamentario_personnel_plan` | Approve Personnel Plan |
| `POST` | `/planejamento-orcamentario/personnel/review/{plan_id}/reject` | `reject_planejamento_orcamentario_personnel_plan` | Reject Personnel Plan |
| `POST` | `/planejamento-orcamentario/personnel/review/{plan_id}/request-changes` | `request_changes_planejamento_orcamentario_personnel_plan` | Request Changes Personnel Plan |

## Planos de inspeção de processo (5)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/process-inspection-plans/orders-without-plan` | `get_process_inspection_plans_orders_without_plan` | Open production orders without inspection plan |
| `GET` | `/process-inspection-plans/products` | `get_process_inspection_plans_products` | Products with process inspection plan |
| `GET` | `/process-inspection-plans/products-without-plan` | `get_process_inspection_plans_products_without_plan` | Products without inspection plan (open OPs) |
| `GET` | `/process-inspection-plans/products/{code}` | `get_process_inspection_plans_product` | Process inspection plan detail by product |
| `GET` | `/process-inspection-plans/summary` | `get_process_inspection_plans_summary` | Process inspection plans — summary KPIs |

## Produção (13)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/production/depreciation_pct` | `get_depreciation_pct` | Depreciation pct |
| `GET` | `/production/direct_labor_cost_pct` | `get_direct_labor_cost_pct` | Direct labor cost pct |
| `GET` | `/production/eficiencia-fabril/appointments` | `list_eficiencia_fabril_appointments` | Eficiencia fabril appointments |
| `GET` | `/production/eficiencia-fabril/dashboard` | `get_eficiencia_fabril_dashboard` | Eficiencia fabril dashboard |
| `GET` | `/production/eficiencia-fabril/efficiency-by-work-center` | `get_eficiencia_fabril_efficiency_by_work_center` | Factory efficiency average % by work center |
| `GET` | `/production/oee` | `get_production_oee` | Production OEE — summary and appointments |
| `GET` | `/production/oee/appointments/{appointment_id}` | `get_production_oee_appointment_by_id` | Production oee appointment by id |
| `GET` | `/production/oee/series` | `get_production_oee_series` | Production OEE series |
| `GET` | `/production/on_time_delivery_pct` | `get_on_time_delivery_pct` | On-time delivery % |
| `GET` | `/production/otd` | `get_production_otd` | Production otd |
| `GET` | `/production/otd/series` | `get_production_otd_series` | Production OTD series |
| `GET` | `/production/overall_equipment_effectiveness_pct` | `get_overall_equipment_effectiveness_pct` | Overall equipment effectiveness % |
| `GET` | `/production/production_cost_pct` | `get_production_cost_pct` | Production cost pct |

## Produção operacional (16)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/production/allocation-gaps` | `get_production_allocation_gaps` | Production allocation gaps |
| `GET` | `/production/consumption/by-item/{code}` | `get_production_consumption_by_item` | Production consumption by item |
| `GET` | `/production/consumption/top-items` | `get_production_consumption_top_items` | Itens mais consumidos na production |
| `GET` | `/production/consumption/top-items-by-work-center` | `get_production_consumption_top_items_by_work_center` | Production consumption top items by work center |
| `GET` | `/production/consumption/top-items-validated` | `get_production_consumption_top_items_validated` | Production consumption top items validated |
| `GET` | `/production/losses/records` | `get_production_losses_records` | Production losses records |
| `GET` | `/production/losses/top-materials` | `get_production_losses_top_materials` | Production losses top materials |
| `GET` | `/production/machine-programs/top-intermediates` | `list_production_machine_program_top_intermediates` | Paged list — top intermediate products for machine programs |
| `GET` | `/production/orders/by-op/{production_order}` | `get_production_order_by_op` | Production order by op |
| `GET` | `/production/orders/finished` | `get_production_orders_finished` | Production orders finished |
| `GET` | `/production/orders/finished-without-consumption` | `get_production_orders_finished_without_consumption` | Production orders finished without consumption |
| `GET` | `/production/orders/open` | `get_production_orders_open` | Production orders open |
| `GET` | `/production/planned-vs-real-time` | `get_production_planned_vs_real_time` | Production planned vs real time |
| `GET` | `/production/schedule/today` | `get_production_schedule_today` | product programados para produzir na data |
| `GET` | `/production/work-centers/average-planned-time` | `get_production_work_center_average_planned_time` | Production work center average planned time |
| `GET` | `/production/work-centers/order-summary` | `get_production_work_center_order_summary` | Production work center order summary |

## Produção — Acompanhamento de Refugos (7)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/refugos/filtros` | `get_refugos_filtros` | Indicator — Refugos filtros |
| `GET` | `/refugos/health` | `get_refugos_health` | Indicator — Refugos health |
| `GET` | `/refugos/rankings` | `get_refugos_rankings` | Scrap rankings |
| `GET` | `/refugos/registros` | `get_refugos_registros` | Scrap loss records |
| `GET` | `/refugos/resumo` | `get_refugos_resumo` | Scrap losses summary |
| `GET` | `/refugos/scrap_cost_pct` | `get_refugos_scrap_cost_pct` | Scrap cost / ROL |
| `GET` | `/refugos/serie` | `get_refugos_serie` | Refugos series |

## Produção — Apontamento de Produção (8)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/production/appointments` | `list_production_appointments` | Paged list of production appointments |
| `GET` | `/production/appointments/by-op` | `list_production_appointments_by_op` | Production appointments aggregated by OP |
| `GET` | `/production/appointments/child-ops` | `list_production_appointments_child_ops` | Child production orders of the same family |
| `GET` | `/production/appointments/finished-ops/series` | `get_production_appointments_finished_ops_series` | Finished production orders count by period |
| `GET` | `/production/appointments/produced-totals` | `get_production_appointments_produced_totals` | Produced quantity totals (final inspection + mother OP) |
| `GET` | `/production/appointments/series` | `get_production_appointments_series` | Production appointments time series |
| `GET` | `/production/appointments/summary` | `get_production_appointments_summary` | Production appointments summary |
| `GET` | `/production/appointments/work-centers` | `list_production_appointment_work_centers` | Work centers catalog for production appointments |

## Produção — Carga máquina (3)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `POST` | `/production/machine-load/appointment-status` | `get_production_machine_load_appointment_status` | Lista — Status de apontamento hza das operações da carga máquina |
| `GET` | `/production/machine-load/operations` | `get_production_machine_load_operations` | Machine load operations |
| `GET` | `/production/machine-load/work-centers` | `get_production_machine_load_work_centers` | Machine load work centers |

## Produção — Conjuntos de OP (1)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/production/production-order-sets/incomplete` | `get_production_order_sets_incomplete` | Incomplete production order sets |

## Produção — Horas improdutivas (3)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/production/unproductive-hours/items` | `get_production_unproductive_hours_items` | Unproductive hours items |
| `GET` | `/production/unproductive-hours/ranking` | `get_production_unproductive_hours_ranking` | Unproductive hours ranking |
| `GET` | `/production/unproductive-hours/summary` | `get_production_unproductive_hours_summary` | Unproductive hours summary |

## Produção — Ordens de produção (3)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/production/pcp-orders/items` | `get_production_pcp_orders_items` | Production orders items |
| `GET` | `/production/pcp-orders/ranking` | `get_production_pcp_orders_ranking` | Production orders ranking |
| `GET` | `/production/pcp-orders/summary` | `get_production_pcp_orders_summary` | Production orders summary |

## Propostas Comerciais (4)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/propostas-comerciais/` | `list_propostas_comerciais` | Paged list — Proposta comercial interna (pdf/totvs) |
| `GET` | `/propostas-comerciais/{proposta_interna}` | `get_proposta_comercial` | Proposta comercial |
| `GET` | `/propostas-comerciais/{proposta_interna}/pdf` | `export_proposta_comercial_pdf` | Export Proposta Comercial Pdf Route |
| `POST` | `/propostas-comerciais/{proposta_interna}/pdf` | `export_proposta_comercial_pdf_with_overrides` | Export proposal commercial PDF with overrides |

## Qualidade (146)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/quality/action-plans` | `list_quality_action_plans` | Paged list — Quality action plan |
| `POST` | `/quality/action-plans` | `create_quality_action_plan` | Indicator — Quality action plan |
| `GET` | `/quality/action-plans/assignable-users` | `list_quality_action_plan_assignable_users` | Paged list — Directory user |
| `GET` | `/quality/action-plans/dashboard` | `get_quality_action_plans_dashboard` | Indicator — Quality action plan dashboard |
| `GET` | `/quality/action-plans/effectiveness-review/pending` | `list_quality_action_plan_pending_effectiveness_reviews` | Paged list — Quality action plan |
| `GET` | `/quality/action-plans/evidences/search` | `search_quality_action_plan_evidences` | Paged list — Quality action plan evidence |
| `GET` | `/quality/action-plans/export-templates` | `list_quality_action_plan_export_templates` | Paged list — Quality action plan export template |
| `GET` | `/quality/action-plans/intelligence/knowledge-graph` | `get_quality_action_plan_knowledge_graph` | Quality action plan knowledge graph |
| `POST` | `/quality/action-plans/intelligence/recurrence-opening-assessment` | `assess_quality_action_plan_recurrence_on_opening` | Assess quality action plan recurrence on opening |
| `POST` | `/quality/action-plans/intelligence/suggest-evidence-tags` | `suggest_quality_action_plan_evidence_tags` | Suggest quality action plan evidence tags |
| `POST` | `/quality/action-plans/intelligence/suggest-evidence-tags/from-image` | `suggest_quality_action_plan_evidence_tags_from_image` | Suggest quality action plan evidence tags from image |
| `GET` | `/quality/action-plans/my-queue` | `list_quality_action_plan_my_queue` | Paged list — Quality action plan action |
| `POST` | `/quality/action-plans/notifications/dispatch` | `dispatch_quality_action_plan_notifications` | Indicator — Quality action plan notifications |
| `GET` | `/quality/action-plans/overdue` | `list_quality_action_plans_overdue` | Paged list — Quality action plan |
| `GET` | `/quality/action-plans/recurrence` | `list_quality_action_plans_recurrence` | Paged list — Quality action plan recurrence |
| `GET` | `/quality/action-plans/{plan_id}` | `get_quality_action_plan_detail` | Quality action plan detail |
| `PATCH` | `/quality/action-plans/{plan_id}` | `update_quality_action_plan` | Indicator — Quality action plan |
| `DELETE` | `/quality/action-plans/{plan_id}` | `delete_quality_action_plan` | Indicator — Quality action plan |
| `POST` | `/quality/action-plans/{plan_id}/actions` | `create_quality_action_plan_actions` | Paged list — Quality action plan action |
| `PATCH` | `/quality/action-plans/{plan_id}/actions/{action_id}` | `update_quality_action_plan_action` | Indicator — Quality action plan action |
| `DELETE` | `/quality/action-plans/{plan_id}/actions/{action_id}` | `delete_quality_action_plan_action` | Indicator — Quality action plan action |
| `GET` | `/quality/action-plans/{plan_id}/audit-log` | `list_quality_action_plan_audit_log` | Paged list — Quality action plan audit log |
| `POST` | `/quality/action-plans/{plan_id}/effectiveness-review` | `record_quality_action_plan_effectiveness` | Indicator — Quality action plan |
| `POST` | `/quality/action-plans/{plan_id}/effectiveness-review/approve` | `approve_quality_action_plan_effectiveness_review` | Indicator — Quality action plan |
| `POST` | `/quality/action-plans/{plan_id}/effectiveness-review/reject` | `reject_quality_action_plan_effectiveness_review` | Indicator — Quality action plan |
| `POST` | `/quality/action-plans/{plan_id}/effectiveness-review/submit` | `submit_quality_action_plan_effectiveness_review` | Indicator — Quality action plan |
| `GET` | `/quality/action-plans/{plan_id}/evidences` | `list_quality_action_plan_evidences` | Paged list — Quality action plan evidence |
| `POST` | `/quality/action-plans/{plan_id}/evidences` | `attach_quality_action_plan_evidence` | Indicator — Quality action plan evidence |
| `PATCH` | `/quality/action-plans/{plan_id}/evidences/{evidence_id}` | `update_quality_action_plan_evidence` | Indicator — Quality action plan evidence |
| `DELETE` | `/quality/action-plans/{plan_id}/evidences/{evidence_id}` | `delete_quality_action_plan_evidence` | Indicator — Quality action plan evidence |
| `GET` | `/quality/action-plans/{plan_id}/evidences/{evidence_id}/content` | `get_quality_action_plan_evidence_content` | Quality action plan evidence content |
| `GET` | `/quality/action-plans/{plan_id}/evidences/{evidence_id}/file` | `download_quality_action_plan_evidence` | Quality action plan evidence |
| `GET` | `/quality/action-plans/{plan_id}/export/pdf` | `export_quality_action_plan_pdf` | Quality action plan export |
| `GET` | `/quality/action-plans/{plan_id}/export/rnc-8d` | `export_quality_action_plan_rnc_8d` | Indicator — Quality action plan export |
| `GET` | `/quality/action-plans/{plan_id}/export/rnc-8d/pdf` | `export_quality_action_plan_rnc_8d_pdf` | Quality action plan export |
| `PUT` | `/quality/action-plans/{plan_id}/five-whys` | `upsert_quality_action_plan_five_whys` | Indicator — Quality action plan five whys |
| `PUT` | `/quality/action-plans/{plan_id}/ishikawa` | `upsert_quality_action_plan_ishikawa` | Indicator — Quality action plan ishikawa |
| `POST` | `/quality/action-plans/{plan_id}/promote-solution-pattern` | `promote_quality_action_plan_solution_pattern` | Indicator — Quality solution pattern |
| `POST` | `/quality/action-plans/{plan_id}/reopen` | `reopen_quality_action_plan` | Indicator — Quality action plan |
| `GET` | `/quality/action-plans/{plan_id}/revisions` | `list_quality_action_plan_revisions` | Paged list — Quality action plan revision |
| `GET` | `/quality/action-plans/{plan_id}/revisions/{revision_number}` | `get_quality_action_plan_revision` | Quality action plan revision |
| `POST` | `/quality/action-plans/{plan_id}/revisions/{revision_number}/restore` | `restore_quality_action_plan_revision` | Restore quality action plan revision |
| `PUT` | `/quality/action-plans/{plan_id}/rnc-8d` | `upsert_quality_action_plan_rnc_8d` | Upsert quality action plan rnc 8d |
| `GET` | `/quality/action-plans/{plan_id}/similar-cases` | `get_quality_action_plan_similar_cases` | Quality action plan similar cases |
| `PATCH` | `/quality/action-plans/{plan_id}/status` | `update_quality_action_plan_status` | Indicator — Quality action plan |
| `GET` | `/quality/audit-5s/analytics/dashboard` | `get_audit_5s_analytics_dashboard` | Get Audit 5S Dashboard |
| `GET` | `/quality/audit-5s/areas` | `list_audit_5s_areas` | List Areas |
| `POST` | `/quality/audit-5s/areas` | `create_audit_5s_area` | Create audit 5S area |
| `GET` | `/quality/audit-5s/audits` | `list_audit_5s_audits` | List Audits |
| `POST` | `/quality/audit-5s/audits` | `create_audit_5s_audit` | Create audit 5S audit |
| `GET` | `/quality/audit-5s/audits/{audit_id}` | `get_audit_5s_audit` | Get Audit |
| `PATCH` | `/quality/audit-5s/audits/{audit_id}` | `update_audit_5s_audit` | Update audit 5S audit |
| `POST` | `/quality/audit-5s/audits/{audit_id}/close` | `close_audit_5s_audit` | Close audit 5S audit |
| `POST` | `/quality/audit-5s/audits/{audit_id}/close-without-nc-treatment` | `close_audit_5s_audit_without_nc_treatment` | Close Audit Without Nc Treatment |
| `POST` | `/quality/audit-5s/audits/{audit_id}/complete-evaluation` | `complete_audit_5s_evaluation` | Complete audit 5S evaluation |
| `POST` | `/quality/audit-5s/audits/{audit_id}/delete` | `delete_audit_5s_audit` | Delete audit 5S audit |
| `POST` | `/quality/audit-5s/audits/{audit_id}/force-delete` | `force_delete_audit_5s_audit` | Force delete audit 5S audit |
| `POST` | `/quality/audit-5s/audits/{audit_id}/join` | `join_audit_5s_audit` | Join audit 5S audit |
| `GET` | `/quality/audit-5s/audits/{audit_id}/nc-attachments` | `list_audit_5s_audit_nc_attachments` | List Audit Nc Attachments |
| `GET` | `/quality/audit-5s/audits/{audit_id}/nc-candidates` | `list_audit_5s_nc_candidates` | List Nc Candidates |
| `GET` | `/quality/audit-5s/audits/{audit_id}/nonconformities` | `list_audit_5s_nonconformities` | List Audit Nonconformities |
| `POST` | `/quality/audit-5s/audits/{audit_id}/nonconformities` | `create_audit_5s_nonconformity` | Create audit 5S nonconformity |
| `POST` | `/quality/audit-5s/audits/{audit_id}/reopen-evaluation` | `reopen_audit_5s_evaluation` | Reopen audit 5S evaluation |
| `PUT` | `/quality/audit-5s/audits/{audit_id}/responses/{criterion_id}` | `upsert_audit_5s_response` | Upsert Response |
| `GET` | `/quality/audit-5s/audits/{audit_id}/responses/{criterion_id}/attachments` | `list_audit_5s_response_attachments` | List Response Attachments |
| `POST` | `/quality/audit-5s/audits/{audit_id}/responses/{criterion_id}/attachments` | `attach_audit_5s_response_photo` | Upload Response Attachment |
| `DELETE` | `/quality/audit-5s/audits/{audit_id}/responses/{criterion_id}/attachments/{attachment_id}` | `delete_audit_5s_response_photo` | Delete audit 5S response photo |
| `GET` | `/quality/audit-5s/audits/{audit_id}/responses/{criterion_id}/attachments/{attachment_id}/file` | `download_audit_5s_response_attachment` | Audit 5s response attachment |
| `GET` | `/quality/audit-5s/catalog` | `get_audit_5s_catalog` | Get Catalog |
| `GET` | `/quality/audit-5s/catalog/publications` | `list_audit_5s_catalog_publications` | List Catalog Publications |
| `PUT` | `/quality/audit-5s/catalog/publish` | `publish_audit_5s_catalog` | Publish audit 5S catalog |
| `GET` | `/quality/audit-5s/criteria` | `list_audit_5s_criteria` | List Criteria |
| `GET` | `/quality/audit-5s/nonconformities` | `list_audit_5s_nonconformities_board` | List Audit 5S Nonconformities Board |
| `PATCH` | `/quality/audit-5s/nonconformities/{nc_id}` | `update_audit_5s_nonconformity` | Update audit 5S nonconformity |
| `GET` | `/quality/audit-5s/nonconformities/{nc_id}/actions` | `list_audit_5s_nc_actions` | List Nc Actions |
| `POST` | `/quality/audit-5s/nonconformities/{nc_id}/actions` | `create_audit_5s_nc_action` | Create audit 5S NC action |
| `GET` | `/quality/audit-5s/nonconformities/{nc_id}/attachments` | `list_audit_5s_nc_attachments` | List Nc Attachments |
| `POST` | `/quality/audit-5s/nonconformities/{nc_id}/attachments` | `attach_audit_5s_evidence` | Upload Nc Attachment |
| `GET` | `/quality/audit-5s/nonconformities/{nc_id}/attachments/{attachment_id}/file` | `download_audit_5s_nc_attachment` | Audit 5s nc attachment |
| `POST` | `/quality/audit-5s/nonconformities/{nc_id}/complete-action` | `complete_audit_5s_nc_action` | Complete audit 5S NC action |
| `POST` | `/quality/audit-5s/nonconformities/{nc_id}/force-close-without-treatment` | `force_close_audit_5s_nc_without_treatment` | Force Close Nc Without Treatment |
| `POST` | `/quality/audit-5s/nonconformities/{nc_id}/reopen-action` | `reopen_audit_5s_nc_action` | Reopen Nc Action |
| `GET` | `/quality/audit-5s/summary` | `get_audit_5s_summary` | Audit 5S |
| `GET` | `/quality/audit-5s/summary/series` | `get_audit_5s_summary_series` | Audit 5S summary series |
| `GET` | `/quality/branches` | `list_quality_branches` | List Quality Branches |
| `GET` | `/quality/kaizens/records` | `list_kaizen_records` | Kaizen records |
| `POST` | `/quality/kaizens/records` | `create_kaizen_record` | Create kaizen record |
| `GET` | `/quality/kaizens/records/export` | `export_kaizen_records` | Export Kaizen Records |
| `POST` | `/quality/kaizens/records/import` | `import_kaizen_records` | Import kaizen records |
| `GET` | `/quality/kaizens/records/savings-investment/series` | `get_kaizen_savings_investment_series` | Get Kaizen savings vs investment series |
| `GET` | `/quality/kaizens/records/summary` | `get_kaizen_records_summary` | Get Kaizen Records Summary |
| `GET` | `/quality/kaizens/records/{record_id}` | `get_kaizen_record` | Kaizen record |
| `PUT` | `/quality/kaizens/records/{record_id}` | `update_kaizen_record` | Update kaizen record |
| `DELETE` | `/quality/kaizens/records/{record_id}` | `delete_kaizen_record` | Delete kaizen record |
| `GET` | `/quality/kaizens/records/{record_id}/at` | `get_kaizen_at_date` | Get Kaizen At Date |
| `GET` | `/quality/kaizens/records/{record_id}/audit-log` | `list_kaizen_audit_log` | List Kaizen Audit Log |
| `GET` | `/quality/kaizens/records/{record_id}/evidences` | `list_kaizen_evidences` | List Kaizen Evidences |
| `POST` | `/quality/kaizens/records/{record_id}/evidences` | `attach_kaizen_evidence` | Attach kaizen evidence |
| `PATCH` | `/quality/kaizens/records/{record_id}/evidences/{evidence_id}` | `update_kaizen_evidence` | Update kaizen evidence |
| `DELETE` | `/quality/kaizens/records/{record_id}/evidences/{evidence_id}` | `delete_kaizen_evidence` | Delete kaizen evidence |
| `GET` | `/quality/kaizens/records/{record_id}/evidences/{evidence_id}/file` | `download_kaizen_evidence` | Download kaizen evidence |
| `PUT` | `/quality/kaizens/records/{record_id}/evidences/{evidence_id}/file` | `replace_kaizen_evidence_file` | Replace kaizen evidence file |
| `GET` | `/quality/kaizens/records/{record_id}/history` | `list_kaizen_history` | List Kaizen History |
| `GET` | `/quality/kaizens/records/{record_id}/revisions` | `list_kaizen_revisions` | List Kaizen Revisions |
| `GET` | `/quality/kaizens/records/{record_id}/revisions/{revision_number}` | `get_kaizen_revision` | Get Kaizen Revision |
| `GET` | `/quality/kaizens/records/{record_id}/savings-timeline` | `get_kaizen_savings_timeline` | Get Kaizen Savings Timeline |
| `POST` | `/quality/kaizens/records/{record_id}/versions` | `create_kaizen_version` | Create kaizen version |
| `PUT` | `/quality/kaizens/records/{record_id}/versions/{revision_number}` | `update_kaizen_version` | Update kaizen version |
| `DELETE` | `/quality/kaizens/records/{record_id}/versions/{revision_number}` | `delete_kaizen_version` | Delete kaizen version |
| `POST` | `/quality/kaizens/records/{record_id}/versions/{revision_number}/implement` | `implement_kaizen_version` | Implement kaizen version |
| `GET` | `/quality/kaizens/summary` | `get_kaizen_summary` | Kaizen summary |
| `GET` | `/quality/kaizens/summary/series` | `get_kaizen_summary_series` | Kaizen summary series |
| `GET` | `/quality/kaizens/{kaizen_id}` | `get_kaizen_by_id` | Kaizen detail (PostgreSQL) |
| `GET` | `/quality/labels` | `list_quality_labels` | List Labels |
| `POST` | `/quality/labels` | `create_quality_label` | Create quality label |
| `GET` | `/quality/labels/audit-events` | `list_quality_label_audit_events` | List Audit Events |
| `GET` | `/quality/labels/checklist-template` | `list_quality_label_checklist_template` | List Checklist Template |
| `GET` | `/quality/labels/inspectors/me` | `get_quality_label_inspector` | Get My Inspector |
| `PUT` | `/quality/labels/inspectors/me` | `save_quality_label_inspector` | Save quality label inspector |
| `GET` | `/quality/labels/inspectors/me/signature` | `get_quality_label_inspector_signature` | Get inspector signature |
| `POST` | `/quality/labels/inspectors/me/signature` | `upload_quality_label_inspector_signature` | Upload inspector signature |
| `GET` | `/quality/labels/lookup-op/{production_order}` | `lookup_quality_label_op` | Lookup quality label op |
| `GET` | `/quality/labels/search-ops` | `search_quality_label_ops` | Search Ops |
| `GET` | `/quality/labels/{label_id}` | `get_quality_label` | Get Label |
| `DELETE` | `/quality/labels/{label_id}` | `delete_quality_label` | Delete quality label |
| `PATCH` | `/quality/labels/{label_id}/active` | `set_quality_label_active` | Set quality label active |
| `GET` | `/quality/labels/{label_id}/certificate` | `get_quality_label_certificate` | Get Certificate |
| `PUT` | `/quality/labels/{label_id}/certificate` | `save_quality_label_certificate` | Save quality label certificate |
| `GET` | `/quality/labels/{label_id}/certificate/pdf` | `get_quality_label_certificate_pdf` | Download quality label certificate PDF |
| `GET` | `/quality/labels/{label_id}/qr` | `get_quality_label_qr` | Get quality label QR |
| `GET` | `/quality/nonconformities` | `list_nonconformities` | List Nonconformity Route |
| `GET` | `/quality/nonconformities/series` | `get_nonconformity_series` | Get Nonconformity Series |
| `GET` | `/quality/nonconformities/streak` | `get_nonconformity_streak` | Days without quality nonconformity |
| `GET` | `/quality/ppm/external` | `list_ppm_external` | List External Ppm |
| `GET` | `/quality/ppm/external/series` | `get_ppm_external_series` | Get External Ppm Series |
| `GET` | `/quality/ppm/external/summary` | `get_ppm_external_summary` | External PPM |
| `GET` | `/quality/ppm/internal` | `list_ppm_internal` | List Internal Ppm |
| `GET` | `/quality/ppm/internal/series` | `get_ppm_internal_series` | Get Internal Ppm Series |
| `GET` | `/quality/ppm/internal/summary` | `get_ppm_internal_summary` | Internal PPM |
| `GET` | `/quality/produced-quantity` | `get_produced_quantity` | Get Produced Quantity |
| `GET` | `/quality/returned-totals` | `get_quality_returned_totals` | Returned quantity totals (NC QI2_QTDDEV) |
| `GET` | `/quality/rework-cost-pct` | `get_quality_rework_cost_pct` | Quality rework cost / ROL |
| `GET` | `/quality/rework-cost-pct/series` | `get_quality_rework_cost_pct_series` | Quality rework cost / ROL series |
| `GET` | `/quality/scrap-cost-pct` | `get_quality_scrap_cost_pct` | Quality scrap cost / ROL |
| `GET` | `/quality/scrap-cost-pct/series` | `get_quality_scrap_cost_pct_series` | Quality scrap cost / ROL series |
| `GET` | `/quality/solution-patterns` | `list_quality_solution_patterns` | Paged list — Quality solution pattern |

## Qualidade — Controle de Retrabalhos (8)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/retrabalhos/colaboradores` | `get_retrabalhos_colaboradores` | List — Retrabalho horas improdutivas colaboradores |
| `GET` | `/retrabalhos/detalhes` | `get_retrabalhos_detalhes` | Rework appointment details |
| `GET` | `/retrabalhos/filtros` | `get_retrabalhos_filtros` | Indicator — Retrabalho horas improdutivas filtros |
| `GET` | `/retrabalhos/health` | `get_retrabalhos_health` | Indicator — Retrabalho horas improdutivas health |
| `GET` | `/retrabalhos/mensal` | `get_retrabalhos_mensal` | List — Retrabalho horas improdutivas mensal |
| `GET` | `/retrabalhos/recursos` | `get_retrabalhos_recursos` | List — Retrabalho horas improdutivas recursos |
| `GET` | `/retrabalhos/resumo` | `get_retrabalhos_resumo` | Rework hours summary |
| `GET` | `/retrabalhos/rework_cost_pct` | `get_retrabalhos_rework_cost_pct` | Rework cost / ROL |

## Quality Labels (público) (1)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/public/quality-labels/inspection/{token}` | `get_public_quality_label_inspection` | Get Public Inspection |

## Recursos Humanos (4)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/hr/active-pdi-count` | `get_hr_active_pdi_count` | Indicator — Pdis ativos |
| `GET` | `/hr/branches` | `list_hr_branches` | Indicator — branches de rh |
| `GET` | `/hr/performance-reviews-completion` | `get_hr_performance_reviews_completion` | Hr performance reviews completion |
| `GET` | `/hr/snapshot` | `get_hr_snapshot` | Hr snapshot |

## Suprimentos (8)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/supplies/cpv` | `get_supplies_cpv` | Supplies cpv |
| `GET` | `/supplies/inventory-turnover` | `get_supplies_inventory_turnover` | Supplies inventory turnover |
| `GET` | `/supplies/negotiation-savings/summary` | `get_supplies_negotiation_savings_summary` | Supplies negotiation savings summary |
| `GET` | `/supplies/otd` | `get_supplies_otd` | Supplies otd |
| `GET` | `/supplies/purchase-order-otd` | `get_supplies_purchase_order_otd` | Purchase order OTD (raw materials) |
| `GET` | `/supplies/purchase-order-otd/panel` | `get_supplies_purchase_order_otd_panel` | Purchase order OTD panel (MP) |
| `GET` | `/supplies/purchase-order-otd/series` | `get_supplies_purchase_order_otd_series` | Purchase order OTD series (MP) |
| `GET` | `/supplies/stock-value` | `get_supplies_stock_value` | Stock value |

## Suprimentos — Estoque de segurança (9)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/supplies/safety-stock/consumption-analysis/items` | `get_supplies_safety_stock_consumption_analysis_items` | Lista paginada — Itens da análise de consumo e estoque de segurança sugerido |
| `GET` | `/supplies/safety-stock/consumption-analysis/items/{code}` | `get_supplies_safety_stock_consumption_analysis_item_details` | Análise consolidada — Detalhe da análise de consumo com série mensal e memória de cálculo |
| `GET` | `/supplies/safety-stock/consumption-analysis/summary` | `get_supplies_safety_stock_consumption_analysis_summary` | Indicador — Resumo da análise de consumo versus estoque de segurança sugerido |
| `GET` | `/supplies/safety-stock/filters` | `get_supplies_safety_stock_filters` | Supplies safety stock filters |
| `GET` | `/supplies/safety-stock/items` | `get_supplies_safety_stock_items` | Supplies safety stock items |
| `GET` | `/supplies/safety-stock/items/{code}/details` | `get_supplies_safety_stock_item_details` | Supplies safety stock item details |
| `GET` | `/supplies/safety-stock/items/{code}/suppliers` | `get_supplies_safety_stock_item_suppliers` | Supplies safety stock item suppliers |
| `GET` | `/supplies/safety-stock/items/{code}/suppliers/{supplier_code}/purchase-price-history` | `get_supplies_safety_stock_supplier_purchase_price_history` | Supplies safety stock supplier purchase price history |
| `GET` | `/supplies/safety-stock/summary` | `get_supplies_safety_stock_summary` | Supplies safety stock summary |

## Suprimentos — Materiais de terceiros (4)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/supplies/third-party-materials/returns/export` | `export_supplies_third_party_materials_returns` | Export third-party material returns |
| `GET` | `/supplies/third-party-materials/shipments` | `get_supplies_third_party_materials_shipments` | Third-party material shipments |
| `GET` | `/supplies/third-party-materials/shipments/{shipment_recno}` | `get_supplies_third_party_materials_shipment` | Third-party material shipment detail |
| `GET` | `/supplies/third-party-materials/summary` | `get_supplies_third_party_materials_summary` | Third-party materials summary |

## Suprimentos — Saldos de estoque (2)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/supplies/stock-balances/items` | `get_supplies_stock_balances_items` | Stock balance items by warehouse |
| `GET` | `/supplies/stock-balances/summary` | `get_supplies_stock_balances_summary` | Stock balances by warehouse |

## Suprimentos — Solicitações de compra (5)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/supplies/purchase-requests/lines` | `list_supplies_purchase_request_lines` | Lista paginada — Supplies purchase request line |
| `GET` | `/supplies/purchase-requests/lines/{branch}/{request_number}` | `get_supplies_purchase_request_lines` | Lista — Supplies purchase request line |
| `GET` | `/supplies/purchase-requests/open-coverage` | `get_supplies_purchase_requests_open_coverage` | Open purchase requests with stock, order and commitment coverage |
| `GET` | `/supplies/purchase-requests/recent-linked-orders` | `list_supplies_purchase_request_recent_linked_orders` | Lista — Pedidos de compra recém-vinculados a solicitações de compra |
| `GET` | `/supplies/purchase-requests/requesters` | `list_supplies_purchase_request_requesters_route_supplies_purchase_requests_requesters_get` | List Supplies Purchase Request Requesters Route |

## Suprimentos — Usuários Protheus (1)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/supplies/protheus-users/by-email` | `get_protheus_user_by_email_route_supplies_protheus_users_by_email_get` | Get Protheus User By Email Route |

## data (1)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `POST` | `/data/sql` | `execute_readonly_sql` | Execute readonly sql |

## products (36)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/products/by-supplier-part-number` | `search_products_by_supplier_part_number` | Products by supplier part number |
| `GET` | `/products/directives/{identifier}` | `get_product_directives` | Product directives |
| `GET` | `/products/drawings` | `list_product_drawings` | Product drawings |
| `GET` | `/products/exclusive-raw-materials/catalog` | `list_exclusive_raw_materials_catalog` | Exclusive raw materials catalog |
| `GET` | `/products/search` | `search_products` | Search products |
| `GET` | `/products/{code}` | `get_product_detail` | Dados cadastrais do product |
| `GET` | `/products/{code}/analyser` | `get_product_analyser` | Product analyser |
| `GET` | `/products/{code}/cost-impact-simulation` | `get_product_cost_impact_simulation` | Product cost impact simulation |
| `GET` | `/products/{code}/customers` | `get_product_customers` | Clientes do product |
| `GET` | `/products/{code}/drawing` | `get_product_drawing` | Product drawing |
| `GET` | `/products/{code}/drawing/pdf` | `get_product_drawing_pdf` | Product drawing pdf |
| `GET` | `/products/{code}/factory-status` | `get_product_factory_status` | Product factory status |
| `GET` | `/products/{code}/guide` | `get_product_guide` | Product guide |
| `GET` | `/products/{code}/inbound-invoice-items` | `get_product_inbound_invoice_items` | Product inbound invoice items |
| `GET` | `/products/{code}/inspection` | `get_product_inspection` | Product inspection |
| `GET` | `/products/{code}/internal-movements` | `get_product_internal_movements` | Product internal movements |
| `GET` | `/products/{code}/last-purchase` | `get_product_last_purchase` | Product last purchase |
| `GET` | `/products/{code}/outbound-invoice-items` | `get_product_outbound_invoice_items` | Product outbound invoice items |
| `GET` | `/products/{code}/parents` | `get_product_parents` | Product parents |
| `GET` | `/products/{code}/pricing` | `get_product_pricing` | Product pricing |
| `GET` | `/products/{code}/production-status` | `get_product_production_status` | Product production status |
| `GET` | `/products/{code}/purchase-budget-history` | `get_product_purchase_budget_history` | Product purchase budget history |
| `GET` | `/products/{code}/purchase-price-history` | `get_product_purchase_price_history` | Product purchase price history |
| `GET` | `/products/{code}/purchases` | `get_product_purchases` | Product purchases |
| `GET` | `/products/{code}/raw-material-price-intelligence` | `get_product_raw_material_price_intelligence` | Product raw material price intelligence |
| `GET` | `/products/{code}/raw-material-set-shortages` | `get_product_raw_material_set_shortages` | Raw-material shortages in the finished-product order set |
| `GET` | `/products/{code}/sales` | `get_product_sales_summary` | Product sales summary |
| `GET` | `/products/{code}/sales/billing` | `get_product_sales_billing` | Faturamento do product |
| `GET` | `/products/{code}/sales/open-orders` | `get_product_sales_open_orders` | Product sales open orders |
| `GET` | `/products/{code}/shipping-status` | `get_product_shipping_status` | Product shipping status |
| `GET` | `/products/{code}/stock` | `get_product_stock` | Product stock |
| `GET` | `/products/{code}/structure` | `get_product_structure` | Product structure |
| `GET` | `/products/{code}/structure/excel` | `get_product_structure_excel` | Product structure excel |
| `GET` | `/products/{code}/structure/exclusivity` | `get_product_structure_exclusivity` | Product structure exclusivity |
| `GET` | `/products/{code}/summary` | `get_product_summary` | Product summary |
| `GET` | `/products/{code}/suppliers` | `get_product_suppliers` | Product suppliers |

## sales (1)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/sales/` | `list_sale_orders` | Sale orders |

## system (20)

| Método | Path | operationId | Summary |
|--------|------|-------------|---------|
| `GET` | `/system/caller-stats` | `get_caller_stats` | Caller stats |
| `GET` | `/system/columns/search` | `search_protheus_columns_by_description` | Protheus columns by description |
| `GET` | `/system/connection-pools` | `get_connection_pool_stats` | Ocupação dos pools Plugins Postgres e TOTVS |
| `GET` | `/system/console-alerts` | `get_console_alerts` | Console alerts |
| `POST` | `/system/console-alerts/evaluate` | `evaluate_console_alerts` | Evaluate console alerts |
| `POST` | `/system/console-alerts/smoke` | `notify_console_smoke_alerts` | Notify console smoke alerts |
| `GET` | `/system/console-health` | `get_console_health` | Console health |
| `GET` | `/system/envelope-contracts` | `get_envelope_contracts` | Envelope contracts |
| `GET` | `/system/observability-snapshot` | `get_observability_snapshot` | Observability snapshot |
| `GET` | `/system/openapi-diff` | `get_openapi_diff` | Openapi diff |
| `GET` | `/system/query-cache/stats` | `get_query_cache_stats` | Hits e misses do cache compartilhado (LMP, stock) |
| `GET` | `/system/smoke-definitions` | `get_smoke_definitions` | Smoke definitions |
| `GET` | `/system/sql-health` | `get_sql_health` | Sql health |
| `GET` | `/system/tables/search` | `search_tables_by_description` | Tables by description |
| `GET` | `/system/tables/{tableName}` | `get_protheus_table` | Protheus table |
| `GET` | `/system/tables/{tableName}/columns` | `list_protheus_table_columns` | Protheus table columns |
| `GET` | `/system/tables/{tableName}/columns/search` | `search_protheus_columns_in_table` | search colunas por texto |
| `GET` | `/system/tables/{tableName}/indexes` | `get_protheus_table_indexes` | Protheus table indexes |
| `GET` | `/system/tables/{tableName}/relations` | `get_protheus_table_relations` | Protheus table relations |
| `GET` | `/system/tables/{tableName}/schema` | `get_protheus_table_schema` | Protheus table schema |
