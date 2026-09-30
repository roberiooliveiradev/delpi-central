# Generated evidence artifact for the API DELPI `value` field inventory pass.
import json

tv = json.load(open('tv-dashboard-api/tv_app/content/tv_data_routes.json', encoding='utf-8'))['routes']
val = [r for r in tv if 'value' in (r.get('valueFields') or [])]
base = {o['operationId']: o for o in json.load(open('api-delpi/app/content/openapi_baseline.json', encoding='utf-8'))['operations']}

TV_COMMON = [
    'tv-dashboard-api: tv_data_routes.json catalog entry (valueFields/projectableFields)',
    'tv-dashboard-api: TvDataRouteCatalogService (route resolution, overlays, SI goal fields)',
    'tv-dashboard-api: DelpiOperationalGateway.fetch_by_operation_id (route call, envelope unwrap, meta.fields)',
    'tv-dashboard-api: ProjectionFieldsContract (projectable-field validation, INVALID_PROJECTION_FIELD)',
    'tv-dashboard-api: ComunicadoDataEnrichmentService (kpi/kpiMetrics materialization, value fallback)',
    'tv-dashboard-api: DisplayFormatService._kpi_scalar_for_field (kpiMetrics -> kpi.value fallback)',
    'plugins/tv-dashboard MFE: slide binding editor + projection readers (valueField/selectedValueFields/dataRef.field)',
    'PERSISTED: tv_dashboard.slides.native_config / playlists.master_config / data_defaults JSONB (dataBinding.operationId + field refs) - cannot enumerate from repo',
]
CHAT = [
    'minha-delpi-ai-api: operational_route_registry_autotierc.ci.json (tierC action)',
    'minha-delpi-ai-api: openapi_operation_contracts.json (entity/shape)',
    'minha-delpi-ai-api: universal OpenAPI tool executor + scalar commentary (reads data fields generically)',
]
DAVI = ['davi: api-delpi/app/content/davi_external_read_allowlist.json (approvedResponseFields = semantic fields only, no value)']

TV_COMMON_FILES = [
    'tv-dashboard-api/tv_app/content/tv_data_routes.json',
    'tv-dashboard-api/tv_app/content/tv_data_route_overlays.json',
    'tv-dashboard-api/tv_app/content/tv_operation_id_aliases.json',
    'tv-dashboard-api/tv_app/application/services/tv_data_route_catalog_service.py',
    'tv-dashboard-api/tv_app/infrastructure/gateways/delpi_operational_gateway.py',
    'tv-dashboard-api/tv_app/application/services/data/projection_fields_contract.py',
    'tv-dashboard-api/tv_app/application/services/comunicado_data_enrichment_service.py',
    'tv-dashboard-api/tv_app/application/services/data/display_format_service.py',
    'tv-dashboard-api/tv_app/application/services/data/tv_commercial_composite_binding_migration_service.py',
]
CHAT_FILES = [
    'minha-delpi-ai-api/app/content/pt-BR/assistant/operational_route_registry_autotierc.ci.json',
    'minha-delpi-ai-api/app/content/pt-BR/assistant/openapi_operation_contracts.json',
]

DAVI_OPS = {'get_new_business_rol_pct', 'get_new_business_rol_target_pct', 'get_new_clients_rol_pct',
            'get_on_time_delivery_pct', 'get_overall_equipment_effectiveness_pct', 'get_sales_conversion_rate',
            'get_supplies_stock_value', 'get_weg_rol_target_pct'}

MFE = {
    'get_sales_conversion_rate': ['plugins/commercial', 'commercial-api BFF: bff_get_closing_rate / bff_get_sales_conversion_rate_series (separate contract, semantic fields)'],
    'get_new_business_rol_pct': ['plugins/commercial'],
    'get_new_business_rol_target_pct': ['plugins/commercial', 'tv migration target: legacy ops head_office/branch_new_business_rol_target_pct'],
    'get_new_clients_rol_pct': ['plugins/commercial'],
    'get_weg_rol_target_pct': ['plugins/commercial', 'tv migration target: legacy ops head_office/branch_weg_rol_target_pct'],
    'get_dashboard_department_idd': ['plugins/plugin-ui goalDisplay (indicators[].score)', 'dashboard MFE idd consumers read item.score'],
    'get_financial_ebitda_pct': ['plugins/dashboard-financial (reads ebitda_over_rol_pct)'],
    'get_financial_fixed_cost_pct': ['plugins/dashboard-financial (reads fixed_cost_over_rol_pct)'],
    'get_depreciation_pct': ['plugins/dashboard-production'],
    'get_direct_labor_cost_pct': ['plugins/dashboard-production'],
    'get_on_time_delivery_pct': ['plugins/dashboard-production (otdPct)'],
    'get_overall_equipment_effectiveness_pct': ['plugins/dashboard-production (oeePct)'],
    'get_production_cost_pct': ['plugins/dashboard-production'],
    'get_audit_5s_summary': ['plugins/dashboard-quality (average_score)'],
    'get_kaizen_summary': ['plugins/dashboard-quality (total_savings,total_kaizens)'],
    'get_nonconformity_streak': ['plugins/dashboard-quality (current_days_without_nc)'],
    'get_ppm_external_summary': ['plugins/dashboard-quality (ppm)'],
    'get_ppm_internal_summary': ['plugins/dashboard-quality (ppm)'],
    'get_quality_rework_cost_pct': ['plugins/dashboard-quality (rework_cost_pct)'],
    'get_quality_rework_cost_pct_series': ['plugins/dashboard-quality (points[].metrics.rework_cost_pct)'],
    'get_quality_scrap_cost_pct': ['plugins/dashboard-quality (scrap_cost_pct)'],
    'get_quality_scrap_cost_pct_series': ['plugins/dashboard-quality (points[].metrics.scrap_cost_pct)'],
    'get_refugos_rankings': ['refugos dashboard consumers (items[].value, sharePct)'],
    'get_refugos_scrap_cost_pct': ['refugos dashboard consumers (scrap_cost_pct)'],
    'get_retrabalhos_rework_cost_pct': ['retrabalhos dashboard consumers (rework_cost_pct)'],
    'get_supplies_stock_value': ['plugins/dashboard-supplies (total_stock_value via summary)'],
}

NONSI = {
    'get_sales_conversion_rate': dict(actual='sales_conversion_rate_pct', canon='sales_conversion_rate_pct',
        prod='api-delpi use_cases/commercial/get_sales_conversion_rate_use_case.py + commercial_router (enrich_dashboard_metric)',
        note='value not emitted by producer; catalog fallback candidate only'),
    'get_new_business_rol_pct': dict(actual='new_business_rol_pct', canon='new_business_rol_pct',
        prod='api-delpi use_cases/commercial/get_new_business_rol_pct_use_case.py'),
    'get_new_business_rol_target_pct': dict(actual='rol + rol_target_pct (enriched)', canon='rol_target_pct',
        prod='api-delpi use_cases/commercial/get_segment_rol_target_use_case.py (segment_kind=new_business) + enrich_dashboard_metric(recompute_target_pct_from=rol)',
        drift='catalog declares new_business_rol_target_pct + value; actual scalar field is rol_target_pct (added by enrichment) + rol'),
    'get_new_clients_rol_pct': dict(actual='new_clients_rol_pct', canon='new_clients_rol_pct',
        prod='api-delpi use_cases/commercial/get_new_clients_rol_pct_use_case.py'),
    'get_weg_rol_target_pct': dict(actual='rol + rol_target_pct (enriched)', canon='rol_target_pct',
        prod='api-delpi use_cases/commercial/get_segment_rol_target_use_case.py (segment_kind=weg) + enrich_dashboard_metric(recompute_target_pct_from=rol)',
        drift='catalog declares weg_rol_target_pct + value; actual scalar field is rol_target_pct (added by enrichment) + rol'),
    'get_dashboard_department_idd': dict(actual='score', canon='score (IDD score; idd alias absent)',
        prod='api-delpi dashboard_router -> strategic-indicators-api get_dashboard_department_score_use_case.py',
        drift='catalog declares score/value/idd; only score emitted'),
    'get_financial_ebitda_pct': dict(actual='ebitda_over_rol_pct', canon='ebitda_over_rol_pct',
        prod='api-delpi use_cases/financial/get_financial_ebitda_pct_use_case.py',
        drift='catalog declares financial_ebitda_pct + value; actual field is ebitda_over_rol_pct'),
    'get_financial_fixed_cost_pct': dict(actual='fixed_cost_over_rol_pct', canon='fixed_cost_over_rol_pct',
        prod='api-delpi use_cases/financial/get_financial_fixed_cost_pct_use_case.py',
        drift='catalog declares financial_fixed_cost_pct + value; actual field is fixed_cost_over_rol_pct'),
    'get_depreciation_pct': dict(actual='depreciation_pct', canon='depreciation_pct',
        prod='api-delpi use_cases/production/get_depreciation_pct_use_case.py'),
    'get_direct_labor_cost_pct': dict(actual='direct_labor_cost_pct', canon='direct_labor_cost_pct',
        prod='api-delpi use_cases/production/get_direct_labor_cost_pct_use_case.py'),
    'get_on_time_delivery_pct': dict(actual='on_time_delivery_pct', canon='on_time_delivery_pct',
        prod='api-delpi use_cases/production/get_on_time_delivery_pct_use_case.py'),
    'get_overall_equipment_effectiveness_pct': dict(actual='overall_equipment_effectiveness_pct', canon='overall_equipment_effectiveness_pct',
        prod='api-delpi use_cases/production/get_overall_equipment_effectiveness_pct_use_case.py'),
    'get_production_cost_pct': dict(actual='production_cost_pct', canon='production_cost_pct',
        prod='api-delpi use_cases/production/get_production_cost_pct_use_case.py'),
    'get_audit_5s_summary': dict(actual='average_score (value==average_score)', canon='average_score',
        prod='api-delpi use_cases/auditoria_5s + quality_router attach_quality_kpi_parity(primary_field=average_score)',
        emitted_value=True, note='value produced as parity alias of average_score'),
    'get_kaizen_summary': dict(actual='total_savings (value==total_savings)', canon='total_savings',
        prod='api-delpi use_cases/kaizen + quality_router attach_quality_kpi_parity(primary_field=total_savings; nested ideas_goal.value=total_kaizens)',
        emitted_value=True, note='value produced as parity alias of total_savings; ideas_goal.value==total_kaizens'),
    'get_nonconformity_streak': dict(actual='current_days_without_nc (value==same)', canon='current_days_without_nc',
        prod='api-delpi use_cases/nonconformity/get_nonconformity_streak_use_case.py',
        emitted_value=True, note='value produced as alias of current_days_without_nc'),
    'get_ppm_external_summary': dict(actual='ppm (value==ppm)', canon='ppm',
        prod='api-delpi ppm_routes attach_quality_kpi_parity(primary_field=ppm)',
        emitted_value=True, note='value produced as parity alias of ppm'),
    'get_ppm_internal_summary': dict(actual='ppm (value==ppm)', canon='ppm',
        prod='api-delpi ppm_routes attach_quality_kpi_parity(primary_field=ppm)',
        emitted_value=True, note='value produced as parity alias of ppm'),
    'get_quality_rework_cost_pct': dict(actual='rework_cost_pct', canon='rework_cost_pct',
        prod='api-delpi losses_routes -> use_cases/retrabalho/get_retrabalho_rework_cost_pct_use_case.py'),
    'get_quality_rework_cost_pct_series': dict(actual='points[].metrics.rework_cost_pct', canon='points[].metrics.rework_cost_pct',
        prod='api-delpi losses_routes -> GetQualityScalarSeriesUseCase(metric=rework_cost_pct)',
        drift='catalog declares quality_rework_cost_pct_series + value; points carry metrics.rework_cost_pct only'),
    'get_quality_scrap_cost_pct': dict(actual='scrap_cost_pct', canon='scrap_cost_pct',
        prod='api-delpi losses_routes -> use_cases/refugos/get_refugos_scrap_cost_pct_use_case.py'),
    'get_quality_scrap_cost_pct_series': dict(actual='points[].metrics.scrap_cost_pct', canon='points[].metrics.scrap_cost_pct',
        prod='api-delpi losses_routes -> GetQualityScalarSeriesUseCase(metric=scrap_cost_pct)',
        drift='catalog declares quality_scrap_cost_pct_series + value; points carry metrics.scrap_cost_pct only'),
    'get_refugos_rankings': dict(actual='items[].value (per-row monetary cost)', canon='items[].value',
        prod='api-delpi use_cases/refugos/get_refugos_rankings_use_case.py',
        emitted_value=True, note='value is canonical per-item field (cost R$); NOT a scalar KPI alias'),
    'get_refugos_scrap_cost_pct': dict(actual='scrap_cost_pct', canon='scrap_cost_pct',
        prod='api-delpi use_cases/refugos/get_refugos_scrap_cost_pct_use_case.py'),
    'get_retrabalhos_rework_cost_pct': dict(actual='rework_cost_pct', canon='rework_cost_pct',
        prod='api-delpi use_cases/retrabalho/get_retrabalho_rework_cost_pct_use_case.py'),
    'get_supplies_stock_value': dict(actual='summary/total_stock_value', canon='total_stock_value',
        prod='api-delpi use_cases/supplies/get_stock_value_use_case.py',
        drift='catalog declares value/stockValue/total; payload has summary.total_stock_value, by_branch, by_location, top_products'),
}

GROUP_OF = {
    'get_audit_5s_summary': 'C', 'get_kaizen_summary': 'C', 'get_nonconformity_streak': 'C',
    'get_ppm_external_summary': 'C', 'get_ppm_internal_summary': 'C',
    'get_refugos_rankings': 'D',
    'get_quality_rework_cost_pct_series': 'E', 'get_quality_scrap_cost_pct_series': 'E',
}

# Live persisted `value` refs resolved to operationId via block.dataBinding / dataSourceId /
# dataModels.inputs (local dev DB dump, read-only).
PERSISTED_LIVE_VALUE_REFS = {
    'get_quality_rework_cost_pct': 2,
    'get_quality_scrap_cost_pct': 2,
    'get_si_indicator_quality_ppm_external_realized': 2,
    'get_si_indicator_quality_ppm_external_meta': 1,
    'get_si_indicator_quality_ppm_internal_meta': 1,
    'get_si_indicator_quality_kaizen_ideas_realized': 1,
    'get_si_indicator_quality_kaizen_ideas_meta': 1,
    'get_si_indicator_quality_kaizen_financial_realized': 1,
    'get_si_indicator_quality_kaizen_financial_meta': 1,
    'get_audit_5s_summary': 1,
}

COMPAT_POLICY = {
    'A': 'data.value stays the canonical realized scalar; no removal path',
    'B': 'value emitted and deprecated; comparable_goal/goal_value are canonical; removal only after persisted+code consumer migration',
    'C': 'value emitted as parity alias; deprecate; removal after consumer migration to primary field',
    'D': 'items[].value is domain-canonical; exempt from scalar alias policy',
    'E': 'value never emitted; catalog correction only',
    'F': 'value never emitted; catalog correction only; no producer change',
}
REMOVAL_PRECOND = {
    'A': 'n/a - canonical field, do not remove',
    'B': 'persisted binding audit clean + kpiMetrics fallback verified + chat KPI card measure_fields resolve to comparable_goal',
    'C': 'persisted binding audit clean + parity alias references remapped to primary field',
    'D': 'n/a - canonical domain field, do not remove',
    'E': 'catalog fix shipped + INVALID_PROJECTION_FIELD behaviour verified',
    'F': 'catalog fix shipped + no persisted field refs to value for the op',
}

TESTS = {
    'A': 'schema test: data.value is realized scalar; SI meta/realized pair test; TV kpi projection test; chat tierC execution smoke; negative: no comparable_goal on realized',
    'B': 'schema test: value==comparable_goal; semantic-field preservation (goal_value/reference_goal/goals); old consumer x new producer (value removed -> fallback discovery); persisted binding migration test (valueField=value -> comparable_goal); SI meta contract test',
    'C': 'schema test: value==primary_field parity; semantic-field preservation (ppm/total_savings/average_score/current_days_without_nc); nested ideas_goal.value; TV projection test both fields; migration test for persisted valueField=value',
    'D': 'row-shape test: items[].value monetary; table projection test; negative: scalar kpi on this op must not treat items[].value as KPI',
    'E': 'series test: points[].metrics.<metric> extraction; catalog field correction test; negative: value absent - binding on value must fail discovery gracefully',
    'F': 'catalog sync test: valueFields/projectableFields vs real response fields; semantic-field preservation; TV projection on canonical field; persisted binding audit for stale value refs; negative: binding on nonexistent field rejected with INVALID_PROJECTION_FIELD',
}

rows = []
for r in val:
    op = r['operationId']
    o = base[op]
    cons = list(TV_COMMON) + list(CHAT)
    files = list(TV_COMMON_FILES) + list(CHAT_FILES)
    if op in DAVI_OPS:
        cons += DAVI
        files.append('api-delpi/app/content/davi_external_read_allowlist.json')
    for m in MFE.get(op, []):
        cons.append('MFE/external: ' + m)

    if op.startswith('get_si_indicator_'):
        kind = op.rsplit('_', 1)[1]
        grp = 'A' if kind == 'realized' else 'B'
        meaning = ('realized indicator value for the selected period - CANONICAL scalar (produced as value by SI API)'
                   if kind == 'realized' else
                   'comparable goal/meta for the selected period - ALIAS of comparable_goal (also goal_value/reference_goal/goal_label/goals/has_value present)')
        canon = 'value (canonical)' if kind == 'realized' else 'comparable_goal (canonical already present)'
        cls = 'KEEP' if kind == 'realized' else 'DEPRECATE_ALIAS'
        mig = ('none for field contract; document semantics'
               if kind == 'realized' else
               'remove value alias after consumer check (TV kpiMetrics fallback + persisted valueField refs)')
        prod = 'strategic-indicators-api get_dashboard_indicator_metric_use_case.py via api-delpi DashboardSiIndicatorMetricService + dynamic dashboard_router'
        aliases = ['value'] + ([] if kind == 'realized' else ['comparable_goal', 'goal_value', 'reference_goal']) + ['kpi.value', 'kpiMetrics.value (TV presentation)']
        ev = 'confirmed in code (SI use case payload); confirmed in contract (fields=[value]); confirmed in TV runtime chain'
    else:
        d = NONSI[op]
        grp = GROUP_OF.get(op, 'F')
        meaning = d['actual'] + ' | value: ' + (d['note'] if d.get('emitted_value') else 'not emitted at runtime - catalog-declared fallback candidate only')
        canon = d['canon']
        if grp == 'D':
            cls = 'KEEP'
            mig = 'none - items[].value is the canonical per-row monetary field; keep out of scalar-KPI alias scope'
        elif d.get('drift'):
            cls = 'FIX_CATALOG'
            mig = 'catalog valueFields/projectableFields drift vs real fields - correct catalog to ' + d['actual'] + '; no producer change; persisted bindings already rely on presentation fallback'
        elif d.get('emitted_value'):
            cls = 'DEPRECATE_ALIAS'
            mig = 'keep value as alias during transition; migrate consumers/persisted bindings to ' + canon + '; then remove'
        else:
            cls = 'DEPRECATE_ALIAS'
            mig = 'drop value from catalog candidates (never emitted); verify persisted bindings do not reference it'
        prod = d['prod']
        aliases = list(r['valueFields']) + ['kpi.value', 'kpiMetrics.value (TV presentation)']
        ev = ('confirmed in code (producer returns ' + d['actual'] + '); confirmed in contract (catalog valueFields)'
              + (' | DRIFT: ' + d['drift'] if d.get('drift') else ''))

    rows.append(dict(
        operationId=op,
        route=o['method'] + ' ' + o['path'],
        current_field='value',
        producer_field=canon.split(' ')[0],
        value_runtime_emitted=True if op.startswith('get_si_indicator_') else bool(d.get('emitted_value')),
        semantic_meaning=meaning,
        proposed_canonical_field=canon,
        canonical_field=canon,
        aliases=aliases,
        producer=prod,
        consumers=cons,
        consumer_files=files,
        consumer_count_code=len(cons) - 1,  # minus the persisted entry
        consumer_count_persisted=PERSISTED_LIVE_VALUE_REFS.get(op, 0),
        consumer_locations=cons,
        change_class=cls,
        decision=cls,
        migration_required=mig,
        compatibility_policy=COMPAT_POLICY[grp],
        removal_precondition=REMOVAL_PRECOND[grp],
        tests_required=TESTS[grp],
        evidence=ev,
        sibling_group=grp,
    ))

out = dict(
    version=1,
    generated_for='API DELPI semantic contract & consumer inventory - value field',
    totals=dict(openapi_operations=720, tv_data_routes=520, value_ops=98, si_scalar=72, non_si=26),
    rows=rows,
)
with open('docs/07-api-delpi/inventory-value-field/value_field_consumer_inventory.json', 'w', encoding='utf-8') as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1)

import collections
print('rows:', len(rows))
print(collections.Counter(r['change_class'] for r in rows))
print(collections.Counter(r['sibling_group'] for r in rows))
