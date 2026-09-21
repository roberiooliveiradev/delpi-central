from tests.conftest import auth_headers, build_client, link


def test_missing_permission_does_not_call_glpi():
    client, glpi = build_client()
    denied = client.get("/tickets", headers={"x-subject": "user-a"})
    assert denied.status_code == 403
    assert denied.json()["error"] == "forbidden"
    assert glpi.calls == 0


def test_callback_rejects_unknown_state():
    client, _glpi = build_client()
    response = client.get("/auth/glpi/callback", params={"code": "good-code", "state": "nope"})
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_oauth_state"


def test_sessions_are_isolated_by_subject():
    client, _glpi = build_client()
    link(client, "user-a")
    mine = client.get("/auth/glpi/session", headers=auth_headers("user-a"))
    other = client.get("/auth/glpi/session", headers=auth_headers("user-b"))
    assert mine.json() == {"linked": True}
    assert other.json() == {"linked": False}
    missing = client.get("/tickets", headers=auth_headers("user-b"))
    assert missing.status_code == 409
    assert missing.json()["error"] == "glpi_link_required"
    assert missing.json()["authorize_url"].endswith("/auth/glpi/start")


def test_delete_session_unlinks_only_the_subject():
    client, _glpi = build_client()
    link(client, "user-a")
    client.delete("/auth/glpi/session", headers=auth_headers("user-a"))
    assert client.get("/auth/glpi/session", headers=auth_headers("user-a")).json()["linked"] is False


def test_list_empty_is_ok_and_detail_hides_foreign_ticket():
    client, glpi = build_client()
    link(client)
    glpi.tickets = []
    listed = client.get("/tickets", headers=auth_headers())
    assert listed.status_code == 200
    assert listed.json() == {"items": [], "page": 1, "page_size": 20, "has_more": False}
    missing = client.get("/tickets/99", headers=auth_headers())
    assert missing.status_code == 404
    forbidden = client.get("/tickets/403", headers=auth_headers())
    assert forbidden.status_code == 403
    assert forbidden.json()["error"] == "glpi_forbidden"
    assert "description" not in forbidden.json()


def test_list_publishes_dates_and_forwards_filter():
    client, glpi = build_client()
    link(client)
    listed = client.get(
        "/tickets",
        params={"q": "Impressora", "status": "open", "sort": "updated_at:desc", "page": 1},
        headers=auth_headers(),
    )
    assert listed.status_code == 200
    body = listed.json()
    assert body["items"][0]["id"] == 7
    assert body["items"][0]["created_at"] == ""
    assert body["items"][0]["status_id"] == 1
    assert "assigned_display_name" in body["items"][0]
    assert body["page"] == 1
    assert glpi.last_list_query.filter.startswith("is_deleted==false")
    assert "name=like=*Impressora*" in glpi.last_list_query.filter
    assert "status.id=in=(1,10,2,3,4)" in glpi.last_list_query.filter
    assert "status_id" in body["items"][0]
    pending = client.get("/tickets", params={"status": "pending"}, headers=auth_headers())
    assert pending.status_code == 200
    assert "status.id==4" in glpi.last_list_query.filter
    approval = client.get("/tickets", params={"status": "approval"}, headers=auth_headers())
    assert approval.status_code == 200
    assert "status.id==10" in glpi.last_list_query.filter
    bad = client.get("/tickets", params={"status": "drop-table"}, headers=auth_headers())
    assert bad.status_code == 422
    foo = client.get("/tickets", params={"status": "foo"}, headers=auth_headers())
    assert foo.status_code == 422


def test_create_ticket_and_followup_are_idempotent():
    client, glpi = build_client()
    link(client)
    payload = {
        "title": "Impressora",
        "description": "Não imprime",
        "category_id": 3,
        "urgency_id": 3,
    }
    headers = {**auth_headers(), "Idempotency-Key": "intent-1"}
    first = client.post("/tickets", json=payload, headers=headers)
    second = client.post("/tickets", json=payload, headers=headers)
    assert first.status_code == 201
    assert first.json() == {"id": 42}
    assert second.json() == {"id": 42}
    assert len(glpi.created) == 1
    assert glpi.created[0][4] == "access-a"

    follow_headers = {**auth_headers(), "Idempotency-Key": "intent-2"}
    follow = client.post(
        "/tickets/42/followups",
        json={"content": "Testei o cabo"},
        headers=follow_headers,
    )
    again = client.post(
        "/tickets/42/followups",
        json={"content": "Testei o cabo"},
        headers=follow_headers,
    )
    assert follow.status_code == 201
    assert follow.json()["id"] == again.json()["id"]
    assert len(glpi.followups) == 1


def test_create_rejects_requester_field_and_missing_key():
    client, glpi = build_client()
    link(client)
    extra = client.post(
        "/tickets",
        json={
            "title": "Impressora",
            "description": "Não imprime",
            "category_id": 3,
            "urgency_id": 3,
            "requester_id": 9,
        },
        headers={**auth_headers(), "Idempotency-Key": "intent-3"},
    )
    assert extra.status_code == 422
    missing_key = client.post(
        "/tickets",
        json={
            "title": "Impressora",
            "description": "Não imprime",
            "category_id": 3,
            "urgency_id": 3,
        },
        headers=auth_headers(),
    )
    assert missing_key.status_code == 400
    assert missing_key.json()["error"] == "idempotency_key_required"
    alien = client.post(
        "/tickets/99/followups",
        json={"content": "oi"},
        headers={**auth_headers(), "Idempotency-Key": "intent-4"},
    )
    assert alien.status_code == 404
    assert glpi.followups == []


def test_attachment_download_uses_only_files_on_the_ticket():
    client, glpi = build_client()
    link(client)
    detail = client.get("/tickets/7", headers=auth_headers())
    assert detail.status_code == 200
    body = detail.json()
    assert body["created_at"] == "2026-09-21T11:00:00Z"
    assert body["status_id"] == 1
    assert body["requester_display_name"] == "Robério Teixeira"
    assert body["requester_mine"] is False
    assert body["timeline"][0]["mine"] is False
    assert body["attachments"] == [
        {"document_id": 2, "filename": "logo.png", "mime": "image/png"},
        {"document_id": 4, "filename": "foto.jpg", "mime": "image/jpeg"},
    ]
    downloaded = client.get("/tickets/7/attachments/2", headers=auth_headers())
    assert downloaded.status_code == 200
    assert downloaded.content == b"png-bytes"
    assert downloaded.headers["content-type"].startswith("image/png")
    sibling = client.get("/tickets/7/attachments/4", headers=auth_headers())
    assert sibling.content == b"jpg-bytes"
    foreign = client.get("/tickets/7/attachments/99", headers=auth_headers())
    assert foreign.status_code == 404
    assert foreign.json()["error"] == "not_found"
    assert b"png-bytes" not in foreign.content
    assert 99 not in glpi.downloaded


def test_categories_come_from_glpi():
    client, _glpi = build_client()
    link(client)
    response = client.get("/ticket-categories", headers=auth_headers())
    assert response.json()["items"] == [{"id": 3, "name": "Hardware"}]
    urgencies = client.get("/urgencies", headers=auth_headers())
    assert [item["id"] for item in urgencies.json()["items"]] == [1, 2, 3, 4, 5]
