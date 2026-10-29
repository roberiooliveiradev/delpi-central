"""Etapa 1 — governed create classification, session context, ticket items
and related tickets. Behavior + contract tests (not structural greps)."""

from tests.conftest import FakeGlpi, auth_headers, build_client, link


def _linked_client():
    client, glpi = build_client()
    link(client)
    glpi.session_uid = 12
    return client, glpi


def _create_payload(**extra):
    payload = {
        "title": "Impressora",
        "description": "Não imprime",
        "category_id": 3,
        "urgency_id": 3,
    }
    payload.update(extra)
    return payload


def test_create_with_classification_fields_forwards_to_glpi():
    client, glpi = _linked_client()
    response = client.post(
        "/tickets",
        json=_create_payload(type_id=2, impact_id=4, request_type_id=4),
        headers={**auth_headers(), "Idempotency-Key": "e1-class"},
    )
    assert response.status_code == 201
    assert response.json() == {"id": 42}
    assert glpi.created[0][5] == {"type_id": 2, "impact_id": 4, "request_type_id": 4}


def test_create_without_optional_fields_stays_backward_compatible():
    client, glpi = _linked_client()
    response = client.post(
        "/tickets",
        json=_create_payload(),
        headers={**auth_headers(), "Idempotency-Key": "e1-compat"},
    )
    assert response.status_code == 201
    assert glpi.created[0][5] == {"type_id": None, "impact_id": None, "request_type_id": None}


def test_create_rejects_invalid_type_id():
    client, glpi = _linked_client()
    response = client.post(
        "/tickets",
        json=_create_payload(type_id=99),
        headers={**auth_headers(), "Idempotency-Key": "e1-badtype"},
    )
    assert response.status_code == 422
    assert glpi.created == []


def test_create_rejects_invalid_impact_id():
    client, glpi = _linked_client()
    response = client.post(
        "/tickets",
        json=_create_payload(impact_id=42),
        headers={**auth_headers(), "Idempotency-Key": "e1-badimpact"},
    )
    assert response.status_code == 422
    assert glpi.created == []


def test_create_with_item_links_returns_linked_items():
    client, glpi = _linked_client()
    response = client.post(
        "/tickets",
        json=_create_payload(
            item_links=[
                {"itemtype": "Peripheral", "items_id": 19},
                {"itemtype": "Peripheral", "items_id": 19},  # dedup
            ]
        ),
        headers={**auth_headers(), "Idempotency-Key": "e1-items"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 42
    assert body["linked_items"] == [
        {"itemtype": "Peripheral", "items_id": 19, "relation_id": 100}
    ]
    assert len(glpi.linked_items) == 1


def test_item_type_outside_session_allowlist_fails_closed():
    client, glpi = _linked_client()
    response = client.post(
        "/tickets",
        json=_create_payload(item_links=[{"itemtype": "NetworkEquipment", "items_id": 9}]),
        headers={**auth_headers(), "Idempotency-Key": "e1-itype"},
    )
    assert response.status_code == 207
    body = response.json()
    assert body["linked_items"] == []
    assert body["failed_items"] == [
        {"itemtype": "NetworkEquipment", "items_id": 9, "reason": "type_not_allowed"}
    ]
    assert getattr(glpi, "linked_items", None) in (None, [])


def test_item_link_failure_is_partial_not_fatal():
    client, glpi = _linked_client()
    from helpdesk_app.domain.errors import GlpiForbidden

    glpi.link_item_error = GlpiForbidden("negado")
    response = client.post(
        "/tickets",
        json=_create_payload(item_links=[{"itemtype": "Peripheral", "items_id": 19}]),
        headers={**auth_headers(), "Idempotency-Key": "e1-itemerr"},
    )
    assert response.status_code == 207
    body = response.json()
    assert body["id"] == 42
    assert body["failed_items"] == [
        {"itemtype": "Peripheral", "items_id": 19, "reason": "glpi_forbidden"}
    ]


def test_partial_result_replays_identically_under_same_key():
    client, glpi = _linked_client()
    payload = _create_payload(item_links=[{"itemtype": "NetworkEquipment", "items_id": 9}])
    headers = {**auth_headers(), "Idempotency-Key": "e1-partial-replay"}
    first = client.post("/tickets", json=payload, headers=headers)
    second = client.post("/tickets", json=payload, headers=headers)
    assert first.status_code == second.status_code == 207
    assert first.json() == second.json()
    assert len(glpi.created) == 1


def test_create_replays_item_links_without_duplication():
    client, glpi = _linked_client()
    payload = _create_payload(item_links=[{"itemtype": "Peripheral", "items_id": 19}])
    headers = {**auth_headers(), "Idempotency-Key": "e1-items-replay"}
    first = client.post("/tickets", json=payload, headers=headers)
    second = client.post("/tickets", json=payload, headers=headers)
    assert first.status_code == second.status_code == 201
    assert first.json() == second.json()
    assert len(glpi.created) == 1
    assert len(glpi.linked_items) == 1


def test_create_with_related_ticket_links():
    client, glpi = _linked_client()
    response = client.post(
        "/tickets",
        json=_create_payload(related_ticket_ids=[7]),
        headers={**auth_headers(), "Idempotency-Key": "e1-rel"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["linked_tickets"] == [{"ticket_id": 7, "relation_id": 200}]


def test_foreign_related_ticket_fails_closed():
    client, glpi = _linked_client()
    response = client.post(
        "/tickets",
        json=_create_payload(related_ticket_ids=[403]),
        headers={**auth_headers(), "Idempotency-Key": "e1-rel-foreign"},
    )
    assert response.status_code == 207
    body = response.json()
    assert body["linked_tickets"] == []
    assert body["failed_tickets"] == [{"ticket_id": 403, "reason": "glpi_forbidden"}]
    assert getattr(glpi, "linked_relations", None) in (None, [])


def test_related_ticket_same_key_replay_no_duplicate():
    client, glpi = _linked_client()
    payload = _create_payload(related_ticket_ids=[7])
    headers = {**auth_headers(), "Idempotency-Key": "e1-rel-replay"}
    first = client.post("/tickets", json=payload, headers=headers)
    second = client.post("/tickets", json=payload, headers=headers)
    assert first.json() == second.json()
    assert len(glpi.linked_relations) == 1


def test_same_key_divergent_intent_is_blocked():
    client, glpi = _linked_client()
    headers = {**auth_headers(), "Idempotency-Key": "e1-diverge"}
    first = client.post("/tickets", json=_create_payload(type_id=1), headers=headers)
    divergent = client.post("/tickets", json=_create_payload(type_id=2), headers=headers)
    assert first.status_code == 201
    assert divergent.status_code == 409
    assert len(glpi.created) == 1


def test_session_context_route_returns_entity_and_hardware():
    client, _glpi = build_client()
    link(client)
    response = client.get("/session/context", headers=auth_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["entity"]["id"] == 0
    assert body["entity"]["name"] == "Delpi"
    assert body["default_request_type_id"] == 1
    assert ("Peripheral", "Periférico") in [
        tuple(pair) for pair in body["hardware"]["item_types"]
    ]


def test_ticket_items_scope_mine_requires_capability():
    client, glpi = _linked_client()
    glpi.session_context_result = {
        "entity": {"id": 0, "name": "Delpi"},
        "hardware": {"my_devices": False, "all_devices": True, "item_types": []},
        "default_request_type_id": 1,
    }
    response = client.get("/ticket-items?scope=mine", headers=auth_headers())
    assert response.status_code == 403


def test_ticket_items_scope_all_requires_capability():
    client, glpi = _linked_client()
    glpi.session_context_result = {
        "entity": {"id": 0, "name": "Delpi"},
        "hardware": {"my_devices": True, "all_devices": False, "item_types": []},
        "default_request_type_id": 1,
    }
    response = client.get("/ticket-items?scope=all&q=dell", headers=auth_headers())
    assert response.status_code == 403


def test_ticket_items_returns_authorized_rows():
    client, glpi = _linked_client()
    glpi.search_items_result = [
        {
            "itemtype": "Peripheral",
            "items_id": 19,
            "name": "E2E-PROBE-ASSET",
            "serial": "SN1",
            "inventory_number": "INV9",
            "entity": "Delpi",
            "owner": "E2E",
        }
    ]
    response = client.get("/ticket-items?scope=mine", headers=auth_headers())
    assert response.status_code == 200
    items = response.json()["items"]
    assert items[0]["items_id"] == 19
    assert items[0]["type_label"] == "Periférico"


def test_ticket_items_rejects_disallowed_itemtype():
    client, _glpi = build_client()
    link(client)
    response = client.get(
        "/ticket-items?scope=mine&itemtype=NetworkEquipment", headers=auth_headers()
    )
    assert response.status_code == 422


def test_ticket_items_rejects_bad_scope():
    client, _glpi = build_client()
    link(client)
    response = client.get("/ticket-items?scope=everything", headers=auth_headers())
    assert response.status_code == 422


def test_request_types_purpose_ticket_returns_ticket_catalog():
    client, _glpi = build_client()
    link(client)
    response = client.get("/request-types?purpose=ticket", headers=auth_headers())
    assert response.status_code == 200
    names = {row["name"] for row in response.json()["items"]}
    assert "Helpdesk" in names


def test_ticket_detail_includes_items_and_related_tickets():
    client, glpi = _linked_client()
    glpi.item_links_result = [
        {"id": 16, "itemtype": "Peripheral", "items_id": 19, "name": "E2E-PROBE-ASSET"}
    ]
    glpi.related_links_result = [
        {"id": 3, "other_id": 7, "title": "Chamado relacionado", "link": 1}
    ]
    response = client.get("/tickets/42", headers=auth_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == [
        {
            "itemtype": "Peripheral",
            "items_id": 19,
            "name": "E2E-PROBE-ASSET",
            "relation_id": 16,
        }
    ]
    assert body["related_tickets"] == [
        {"ticket_id": 7, "title": "Chamado relacionado", "link": 1, "relation_id": 3}
    ]


def test_ticket_detail_degrades_when_item_readback_fails():
    client, glpi = _linked_client()
    from helpdesk_app.domain.errors import GlpiUnavailable

    class FailingItems(FakeGlpi):
        pass

    glpi.item_links_error = GlpiUnavailable("down")
    # Fake raises via attribute only when wired — simulate by monkeypatching
    original = glpi.ticket_item_links

    def _raise(token, tid):
        raise GlpiUnavailable("down")

    glpi.ticket_item_links = _raise
    try:
        response = client.get("/tickets/42", headers=auth_headers())
    finally:
        glpi.ticket_item_links = original
    assert response.status_code == 200
    assert response.json()["items"] == []
