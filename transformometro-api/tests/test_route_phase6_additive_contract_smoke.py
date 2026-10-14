"""HTTP operation inventory regression for additive TÉO routes.

Product guide GETs exercise the HTTP smoke runner. Other routes have their
operationId, method and canonical path asserted against the TestApp OpenAPI;
those contract assertions are not substitutes for domain/AuthZ E2E.
"""

from __future__ import annotations

import pytest

from tests.support.route_smoke_runner import run_route_smoke


EXPECTED_ADDITIONS = (
    ("delete_transformometro_interaction_room", "DELETE", "/transformometro/interaction-rooms/{room_id}"),
    ("remove_process_bpmn_reference", "DELETE", "/transformometro/processos/{processo_id}/bpmn-reference"),
    ("list_process_bpmn_model_revisions", "GET", "/transformometro/processos/{processo_id}/bpmn-reference/candidates/{model_id}/revisions"),
    ("list_process_bpmn_model_candidates", "GET", "/transformometro/processos/{processo_id}/bpmn-reference/candidates"),
    ("get_process_bpmn_reference", "GET", "/transformometro/processos/{processo_id}/bpmn-reference"),
    ("gpt_prepare_helpdesk_change", "POST", "/transformometro/gpt-actions/v1/helpdesk/prepare"),
    ("set_process_bpmn_reference", "PUT", "/transformometro/processos/{processo_id}/bpmn-reference"),
)


@pytest.mark.parametrize("operation_id,method,path", EXPECTED_ADDITIONS)
def test_additive_route_contract_is_available(operation_id, method, path, openapi_ops):
    operation = openapi_ops[operation_id]
    assert operation["operationId"] == operation_id
    assert operation["path"] == path
    assert operation["method"] == method


@pytest.mark.parametrize(
    "operation_id",
    ("list_product_guide_topics", "get_product_guide_topic"),
)
def test_guidance_routes_http_smoke(operation_id, tm_client, openapi_ops):
    operation = openapi_ops[operation_id]
    assert operation["method"] == "GET"
    run_route_smoke(tm_client, operation)
