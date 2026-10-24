"""GLPI #1197: discover and execute the same canonical dashboard READs."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from app.application.external_capabilities.dynamic_information.action_index import reset_action_index_for_tests, set_actions_for_tests
from app.application.external_capabilities.dynamic_information.catalog_builder import build_technical_actions_from_baseline
from app.application.external_capabilities.dynamic_information.content_loader import load_external_read_allowlist
from app.application.external_capabilities.dynamic_information.discover_service import discover_delpi_information
from app.application.external_capabilities.dynamic_information.execute_service import execute_delpi_information
from app.application.external_capabilities.dynamic_information.argument_validator import build_argument_json_schema, validate_arguments, ArgumentValidationError
from app.application.external_capabilities.dynamic_information.errors import GovernedExecutionError
from app.domain.ports.davi_catalog_action_executor_port import CatalogActionExecutionResult

ROOT = Path(__file__).resolve().parents[1]

@pytest.fixture(autouse=True)
def catalog(monkeypatch):
    reset_action_index_for_tests()
    load_external_read_allowlist.cache_clear()
    baseline = json.loads((ROOT / 'app/content/openapi_baseline.json').read_text())
    actions = build_technical_actions_from_baseline(baseline, allowlist=load_external_read_allowlist())
    set_actions_for_tests(actions)
    for module in ('discover_service', 'execute_service'):
        monkeypatch.setattr(f'app.application.external_capabilities.dynamic_information.{module}.candidate_token_secret', lambda: 'test-inventory-validation-secret')
    yield {a.action_id: a for a in actions}
    reset_action_index_for_tests()
    load_external_read_allowlist.cache_clear()


def discover(query):
    return discover_delpi_information(query=query, top_k=5, actor_id='inventory-validator')

@pytest.mark.parametrize(('query','expected'), [
    ('Consultar acuracidade de estoque', 'get_supplies_inventory_accuracy_summary'),
    ('Resumo de acuracidade do inventário', 'get_supplies_inventory_accuracy_summary'),
    ('Detalhamento das contagens de inventário', 'get_supplies_inventory_accuracy_items'),
    ('Lista de contagens oficiais corretas e divergentes', 'get_supplies_inventory_accuracy_items'),
    ('Matérias-primas sem giro nos últimos 12 meses', 'get_supplies_non_moving_stock_summary'),
    ('Qual o valor de materiais sem consumo?', 'get_supplies_non_moving_stock_summary'),
    ('Detalhamento do estoque sem giro', 'get_supplies_non_moving_stock_items'),
    ('Listar matérias-primas sem giro', 'get_supplies_non_moving_stock_items'),
    ('Ajuste de estoque da filial 01 este ano', 'get_supplies_inventory_adjustments_summary'),
])
def test_discovery_routes_canonical_family(query, expected):
    result = discover(query)
    assert result['candidates'][0]['action_id'] == expected

@pytest.mark.parametrize('family', ['inventory_accuracy','non_moving_stock'])
def test_execute_preserves_reference_rows_partiality_and_drops_unapproved(family):
    query = 'Detalhamento das contagens' if family == 'inventory_accuracy' else 'Detalhamento do estoque sem giro'
    candidate = discover(query)['candidates'][0]
    executor = Mock()
    executor.execute.return_value = CatalogActionExecutionResult(outcome='ok', payload={
        'success': True, 'data': {
            'items': [{'product_code': '10080001', 'branch': '01', 'secret': 'drop'}],
            'page': 1, 'page_size': 20, 'total': 5002, 'total_pages': 251,
            'reference': {'period_start': '2025-05-01', 'consumption_window_start': '2025-05-01', 'valuation_reference': 'sb2_current_snapshot', 'secret': 'drop'},
            'secret': 'drop',
        },
    })
    args = {'start_date':'2025-05-01','end_date':'2026-05-31','branch':['01','02'],'page_size':20}
    result = execute_delpi_information(candidate_token=candidate['candidate_token'],arguments=args,actor_id='inventory-validator',catalog_action_executor=executor)
    assert result['action_id'] == f'get_supplies_{family}_items'
    assert result['is_complete'] is False
    assert result['data']['total'] == 5002
    assert result['data']['items'] == [{'product_code':'10080001','branch':'01'}]
    assert 'secret' not in result['data']['reference']
    executor.execute.assert_called_once()
    assert executor.execute.call_args.kwargs['validated_arguments']['branch'] == ['01','02']

@pytest.mark.parametrize('family', ['inventory_accuracy','non_moving_stock'])
def test_contract_bounds_and_forbidden_transport(catalog, family):
    action = catalog[f'get_supplies_{family}_items']
    schema = build_argument_json_schema(action)
    assert schema['properties']['branch']['items']['type'] == 'string'
    assert schema['properties']['page_size']['maximum'] == 50
    for args in ({'page_size':51}, {'sql':'SELECT 1'}, {'url':'https://example.com'}, {'start_date':'2025-01-01'}, {'search':'x'*121}, {'branch':['01','02','03']}):
        with pytest.raises(ArgumentValidationError):
            validate_arguments(action,args)

@pytest.mark.parametrize('outcome', ['forbidden','error'])
def test_owner_failure_never_becomes_empty_success(outcome):
    candidate = discover('Detalhamento das contagens')['candidates'][0]
    executor = Mock()
    executor.execute.return_value = CatalogActionExecutionResult(outcome=outcome,error_message='failed')
    with pytest.raises((PermissionError,GovernedExecutionError)):
        execute_delpi_information(candidate_token=candidate['candidate_token'],arguments={},actor_id='inventory-validator',catalog_action_executor=executor)


def test_array_item_enum_is_validated(catalog):
    from dataclasses import replace
    action = catalog['get_supplies_inventory_accuracy_items']
    params = tuple({'name':'branch','in':'query','schema':{'type':'array','items':{'type':'string','enum':['01','02']}}} if p['name']=='branch' else p for p in action.parameters)
    action = replace(action, parameters=params)
    assert validate_arguments(action, {'branch':['01']})['branch'] == ['01']
    with pytest.raises(ArgumentValidationError):
        validate_arguments(action, {'branch':['03']})

@pytest.mark.parametrize('query',['Altere o estoque sem giro'])
def test_no_write_or_sql_candidate(query):
    assert discover(query)['candidate_count'] == 0

def test_sql_intent_surfaces_only_governed_read_candidates():
    result = discover('Execute SQL para acuracidade')
    ids = {c['action_id'] for c in result['candidates']}
    assert 'execute_readonly_sql' not in ids
    assert all(i.startswith(('get_', 'list_', 'search_')) for i in ids)

@pytest.mark.parametrize(('family','detail','query'), [
    ('inventory_accuracy', False, 'Resumo de acuracidade'),
    ('inventory_accuracy', True, 'Detalhamento das contagens'),
    ('non_moving_stock', False, 'Resumo de estoque sem giro'),
    ('non_moving_stock', True, 'Detalhamento do estoque sem giro'),
])
@pytest.mark.parametrize('allowed', [True, False])
def test_broker_to_real_owner_route_preserves_end_user_authorization(family, detail, query, allowed):
    from contextlib import ExitStack
    from types import SimpleNamespace
    from unittest.mock import patch
    from fastapi.testclient import TestClient
    from app.infrastructure.davi.asgi_catalog_action_executor import AsgiCatalogActionExecutor
    from app.interface.http.routes.supplies import inventory_accuracy_router, non_moving_stock_router

    permissions = ['api-delpi.access'] if allowed else []
    actor = 'inventory-validator'
    claims = {'sub':actor, 'aud':'delpi-central', 'email':'validator@example.com'}
    async def rbac(_token):
        return {'id':actor, 'permissions':permissions, 'is_superadmin':False, 'roles':[], 'groups':[], 'rbac_unavailable':False}
    module = inventory_accuracy_router if family == 'inventory_accuracy' else non_moving_stock_router
    suffix = 'items' if detail else 'summary'
    builder = f'build_get_{family}_{suffix}_use_case'
    payload = ({'items':[{'product_code':'10080001','branch':'01','secret':'drop'}], 'page':1,'page_size':20,'total':1,'total_pages':1,'reference':{'period_start':'2025-05-01','consumption_window_start':'2025-05-01'}} if detail else {'summary':{'status':'ok','valid_count_total':5002,'no_consumption_stock_value':10,'secret':'drop'}, 'reference':{'period_start':'2025-05-01','consumption_window_start':'2025-05-01'}})
    uc = Mock()
    uc.execute.return_value = payload
    with ExitStack() as stack:
        for target in ('delpi_auth.jwt_validator.validate_token','delpi_auth.middleware.fastapi_auth.validate_token','app.middleware.auth_middleware.validate_token'):
            stack.enter_context(patch(target,return_value=claims))
        stack.enter_context(patch('delpi_auth.authorization.resolve_user_context',return_value=SimpleNamespace(is_superadmin=False, permissions=permissions)))
        stack.enter_context(patch('delpi_auth.middleware.fastapi_auth.load_user_rbac',side_effect=rbac))
        stack.enter_context(patch.object(module,builder,return_value=uc))
        from app.main import app
        client = TestClient(app)
        candidate = discover(query)['candidates'][0]
        args = {'branch':['01','02'], 'start_date':'2025-05-01','end_date':'2026-05-31'}
        executor = AsgiCatalogActionExecutor(client,authorization='Bearer test-end-user-token')
        if not allowed:
            with pytest.raises(PermissionError):
                execute_delpi_information(candidate_token=candidate['candidate_token'],arguments=args,actor_id=actor,catalog_action_executor=executor)
            uc.execute.assert_not_called()
        else:
            result = execute_delpi_information(candidate_token=candidate['candidate_token'],arguments=args,actor_id=actor,catalog_action_executor=executor)
            assert result['status'] == 'ok'
            request = uc.execute.call_args.args[0]
            assert tuple(request.branches) == ('01','02')
            assert request.start_date == '20250501'
            assert request.end_date == '20260531'
            assert 'secret' not in str(result['data'])
