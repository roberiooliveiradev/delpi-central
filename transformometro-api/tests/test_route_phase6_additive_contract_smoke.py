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
    ("remove_transformometro_interaction_room_link", "DELETE", "/transformometro/interaction-rooms/{room_id}/links/{link_id}"),
    ("remove_transformometro_interaction_room_participant", "DELETE", "/transformometro/interaction-rooms/{room_id}/participants/{user_id}"),
    ("get_transformometro_interaction_room_delete_impact", "GET", "/transformometro/interaction-rooms/{room_id}/impact"),
    ("list_transformometro_interaction_room_links", "GET", "/transformometro/interaction-rooms/{room_id}/links"),
    ("list_transformometro_interaction_room_participants", "GET", "/transformometro/interaction-rooms/{room_id}/participants"),
    ("create_transformometro_standalone_interaction_room", "POST", "/transformometro/interaction-rooms/standalone"),
    ("open_transformometro_interaction_room_for_ticket", "POST", "/transformometro/interaction-rooms/ticket"),
    ("add_transformometro_interaction_room_link", "POST", "/transformometro/interaction-rooms/{room_id}/links"),
    ("add_transformometro_interaction_room_participant", "POST", "/transformometro/interaction-rooms/{room_id}/participants"),
    ("restore_transformometro_interaction_room", "POST", "/transformometro/interaction-rooms/{room_id}/restore"),
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
    if operation_id == "get_product_guide_topic":
        # The generic smoke path filler uses a UUID. This route requires an
        # existing catalog topic slug, not an entity identifier.
        response = tm_client.get("/transformometro/product-guides/process")
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["success"] is True
        assert payload["data"]
        missing = tm_client.get("/transformometro/product-guides/unknown-slug")
        assert missing.status_code == 404
        assert missing.json()["success"] is False
    else:
        run_route_smoke(tm_client, operation)
