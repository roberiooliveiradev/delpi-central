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
    assert mine.json()["linked"] is True
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


def test_refresh_failure_asks_relink_not_validation_error():
    """GLPI 400 on refresh_token must surface as glpi_link_required (409), not 422."""
    from datetime import datetime, timezone

    from helpdesk_app.domain.errors import GlpiValidation
    from helpdesk_app.domain.models import OAuthSession

    client, glpi = build_client()
    link(client)
    glpi.refresh_error = GlpiValidation("O GLPI recusou os dados enviados.")
    oauth = client.app.state.oauth
    session = oauth._sessions.get("user-a")
    assert session is not None
    oauth._sessions.save(
        OAuthSession(
            subject=session.subject,
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            access_expires_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
        )
    )
    response = client.get("/tickets", headers=auth_headers())
    assert response.status_code == 409
    assert response.json()["error"] == "glpi_link_required"
    assert response.json()["authorize_url"].endswith("/auth/glpi/start")
    assert oauth._sessions.get("user-a") is None


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
        params={
            "q": "Impressora",
            "status": "open",
            "sort": "updated_at:desc",
            "page": 1,
            "page_size": 10,
            "created_from": "2026-01-01",
            "created_to": "2026-01-31",
        },
        headers=auth_headers(),
    )
    assert listed.status_code == 200
    body = listed.json()
    assert body["items"][0]["id"] == 7
    assert body["items"][0]["created_at"] == ""
    assert body["items"][0]["status_id"] == 1
    assert "assigned_display_name" in body["items"][0]
    assert body["items"][0].get("assigned_user_id") == 15
    assert body["items"][0]["requester_display_name"] == "Robério Teixeira"
    assert body["page"] == 1
    assert body["page_size"] == 10
    assert glpi.last_list_query.filter.startswith("is_deleted==false")
    assert "(name=like=*Impressora*,content=like=*Impressora*)" in glpi.last_list_query.filter
    assert "solved_at" in body["items"][0]
    assert "closed_at" in body["items"][0]
    assert "status.id=in=(1,10,2,3,4)" in glpi.last_list_query.filter
    assert "date_creation=ge=2026-01-01T00:00:00" in glpi.last_list_query.filter
    assert "date_creation=le=2026-01-31T23:59:59" in glpi.last_list_query.filter
    assert glpi.last_list_query.page_size == 10
    assert glpi.last_list_query.limit == 11
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
    bad_date = client.get("/tickets", params={"created_from": "21/01/2026"}, headers=auth_headers())
    assert bad_date.status_code == 422


def test_list_filters_by_assignee_id():
    client, glpi = build_client()
    link(client)
    hit = client.get("/tickets", params={"assignee_id": 15}, headers=auth_headers())
    assert hit.status_code == 200
    assert [row["id"] for row in hit.json()["items"]] == [7]
    assert glpi.last_list_query.assignee_id == 15
    miss = client.get("/tickets", params={"assignee_id": 99}, headers=auth_headers())
    assert miss.status_code == 200
    assert miss.json()["items"] == []
    sorted_assigned = client.get(
        "/tickets", params={"sort": "assigned:asc"}, headers=auth_headers()
    )
    assert sorted_assigned.status_code == 200
    assert glpi.last_list_query.client_sort == "assigned:asc"


def test_create_ticket_and_followup_are_idempotent():
    client, glpi = build_client()
    link(client)
    glpi.session_uid = 12
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


def test_create_attaches_observers_without_requester_or_entity():
    client, glpi = build_client()
    link(client)
    glpi.session_uid = 12
    created = client.post(
        "/tickets",
        json={
            "title": "Com watcher",
            "description": "Preciso de cópia",
            "category_id": 3,
            "urgency_id": 3,
            "observer_ids": [15, 15, 22],
        },
        headers={**auth_headers(), "Idempotency-Key": "intent-obs-1"},
    )
    assert created.status_code == 201
    assert glpi.observers == [(42, 15, "access-a"), (42, 22, "access-a")]
    forbidden = client.post(
        "/tickets",
        json={
            "title": "X",
            "description": "Y",
            "category_id": 3,
            "urgency_id": 3,
            "requester_id": 9,
            "observer_ids": [1],
        },
        headers={**auth_headers(), "Idempotency-Key": "intent-obs-2"},
    )
    assert forbidden.status_code == 422


def test_create_attaches_assignee_hd011_safe():
    client, glpi = build_client()
    link(client)
    glpi.session_uid = 12
    created = client.post(
        "/tickets",
        json={
            "title": "Com técnico",
            "description": "Preciso de atendimento",
            "category_id": 3,
            "urgency_id": 3,
            "assignee_id": 15,
        },
        headers={**auth_headers(), "Idempotency-Key": "intent-assign-create"},
    )
    assert created.status_code == 201
    assert glpi.assignees == [(42, 15, "access-a")]


def test_set_assignee_positive_and_reassign_sibling():
    client, glpi = build_client()
    link(client)
    first = client.put(
        "/tickets/7/assignee",
        json={"user_id": 15},
        headers={**auth_headers(), "Idempotency-Key": "intent-assign-1"},
    )
    assert first.status_code == 200
    assert first.json()["user_id"] == 15
    assert glpi.assignees[-1][:2] == (7, 15)

    second = client.put(
        "/tickets/7/assignee",
        json={"user_id": 22},
        headers={**auth_headers(), "Idempotency-Key": "intent-assign-2"},
    )
    assert second.status_code == 200
    assert second.json()["user_id"] == 22
    assert glpi.removed_assignees[-1][:2] == (7, 15)
    assert glpi.assignees[-1][:2] == (7, 22)


def test_set_assignee_negative_forbidden_and_invalid():
    client, glpi = build_client()
    link(client)
    glpi.can_assign = False
    forbidden_users = client.get("/users", headers=auth_headers())
    assert forbidden_users.status_code == 403
    assert forbidden_users.json()["error"] == "glpi_forbidden"

    glpi.can_assign = True
    caps = client.get("/session/capabilities", headers=auth_headers())
    assert caps.status_code == 200
    assert caps.json() == {"can_assign": True}

    detail = client.get("/tickets/7", headers=auth_headers())
    assert detail.status_code == 200
    assert detail.json()["can_assign"] is True

    bad = client.put(
        "/tickets/7/assignee",
        json={"user_id": 0},
        headers={**auth_headers(), "Idempotency-Key": "intent-assign-bad"},
    )
    assert bad.status_code == 422


def test_list_users_returns_id_and_display_name():
    client, glpi = build_client()
    link(client)
    listed = client.get("/users?q=Ana", headers=auth_headers())
    assert listed.status_code == 200
    assert listed.json()["items"] == [
        {
            "id": 15,
            "display_name": "Ana Silva",
            "email": "ana.silva@delpi.com.br",
            "directory_user_id": "",
            "has_photo": False,
        }
    ]


def test_list_users_assignee_purpose_filters_non_technicians():
    client, glpi = build_client()
    link(client)
    all_users = client.get("/users?q=a", headers=auth_headers())
    assert all_users.status_code == 200
    mention_ids = {item["id"] for item in all_users.json()["items"]}
    assert 40 in mention_ids  # RH aparece em menções

    assignees = client.get("/users?q=a&purpose=assignee", headers=auth_headers())
    assert assignees.status_code == 200
    assignee_ids = {item["id"] for item in assignees.json()["items"]}
    assert 15 in assignee_ids
    assert 22 in assignee_ids
    assert 40 not in assignee_ids
    assert 2 not in assignee_ids


def test_assignee_picker_works_when_user_cannot_read_user_catalog():
    """Requester profile: Administration/User read is denied (entity/profile
    scoped), but the bounded technician catalog must still resolve and
    can_assign stays true — assignment is a BFF-bounded write."""
    client, glpi = build_client()
    link(client)
    glpi.user_catalog_denied = True

    caps = client.get("/session/capabilities", headers=auth_headers())
    assert caps.status_code == 200
    assert caps.json() == {"can_assign": True}

    assignees = client.get("/users?q=a&purpose=assignee", headers=auth_headers())
    assert assignees.status_code == 200
    assignee_ids = {item["id"] for item in assignees.json()["items"]}
    assert 15 in assignee_ids
    assert 22 in assignee_ids
    assert 40 not in assignee_ids


def test_list_users_filters_system_and_noise_labels():
    client, glpi = build_client()
    link(client)
    listed = client.get("/users", headers=auth_headers())
    assert listed.status_code == 200
    names = {item["display_name"] for item in listed.json()["items"]}
    assert "Ana Silva" in names
    assert "Bruno Costa" in names
    assert "glpi" not in names
    assert "0" not in names


def test_list_users_enriches_from_minha_delpi_directory():
    class FakeDirectory:
        def configured(self):
            return True

        def search_users(self, *, q="", limit=20, browse=False, permission=None):
            assert browse is False
            assert "ana" in (q or "").lower()
            _ = permission
            return [
                {
                    "id": "delpi-ana",
                    "name": "Ana Silva Delpi",
                    "email": "ana.silva@delpi.com.br",
                },
                {
                    "id": "delpi-ghost",
                    "name": "Sem GLPI",
                    "email": "ghost@delpi.com.br",
                },
            ]

    client, glpi = build_client(directory=FakeDirectory())
    link(client)
    listed = client.get("/users?q=ana", headers=auth_headers())
    assert listed.status_code == 200
    items = listed.json()["items"]
    assert any(
        item["id"] == 15
        and item["display_name"] == "Ana Silva Delpi"
        and item["email"] == "ana.silva@delpi.com.br"
        and item.get("directory_user_id") == "delpi-ana"
        for item in items
    )


def test_list_users_keeps_glpi_results_when_delpi_email_does_not_map():
    class FakeDirectory:
        def configured(self):
            return True

        def search_users(self, *, q="", limit=20, browse=False, permission=None):
            _ = permission
            return [
                {
                    "id": "delpi-shared",
                    "name": "Ana Silva",
                    "email": "shared-mailbox@delpi.com.br",
                }
            ]

    client, glpi = build_client(directory=FakeDirectory())
    link(client)
    listed = client.get("/users?q=Ana", headers=auth_headers())
    assert listed.status_code == 200
    items = listed.json()["items"]
    assert any(item["id"] == 15 for item in items)
    ana = next(item for item in items if item["id"] == 15)
    assert ana["display_name"] == "Ana Silva"
    assert "shared-mailbox" not in (ana.get("email") or "") or ana["email"] in {
        "ana.silva@delpi.com.br",
        "shared-mailbox@delpi.com.br",
    }


def test_create_and_followup_sanitize_html_and_keep_plain_text():
    client, glpi = build_client()
    link(client)
    glpi.session_uid = 12
    rich = client.post(
        "/tickets",
        json={
            "title": "Rede",
            "description": '<p>Cabo <strong>solto</strong> <script>alert(1)</script></p>',
            "category_id": 3,
            "urgency_id": 3,
        },
        headers={**auth_headers(), "Idempotency-Key": "intent-html-1"},
    )
    assert rich.status_code == 201
    assert glpi.created[-1][1] == "<p>Cabo <strong>solto</strong> </p>"
    assert "<script" not in glpi.created[-1][1].lower()

    plain = client.post(
        "/tickets",
        json={
            "title": "Teclado",

            "description": "Só texto puro",
            "category_id": 3,
            "urgency_id": 3,
        },
        headers={**auth_headers(), "Idempotency-Key": "intent-plain-1"},
    )
    assert plain.status_code == 201
    assert glpi.created[-1][1] == "Só texto puro"

    dirty_follow = client.post(
        "/tickets/42/followups",
        json={"content": '<p>ok</p><img src="https://evil.example/x.png" onerror="x">'},
        headers={**auth_headers(), "Idempotency-Key": "intent-html-2"},
    )
    assert dirty_follow.status_code == 201
    assert glpi.followups[-1][1] == "<p>ok</p>"
    assert "<img" not in glpi.followups[-1][1].lower()

    script_only = client.post(
        "/tickets/42/followups",
        json={"content": "<script>alert(1)</script>"},
        headers={**auth_headers(), "Idempotency-Key": "intent-html-3"},
    )
    assert script_only.status_code == 422
    assert script_only.json()["error"] == "validation_error"

    too_long = client.post(
        "/tickets/42/followups",
        json={"content": "x" * 50_001},
        headers={**auth_headers(), "Idempotency-Key": "intent-html-4"},
    )
    assert too_long.status_code == 422
    assert too_long.json()["error"] == "validation_error"


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
    assert body["can_followup"] is True
    assert body["observers_display_name"] == ""
    assert "solved_at" in body
    assert "closed_at" in body
    assert body["requester_display_name"] == "Robério Teixeira"
    assert body["requester_mine"] is False
    assert body["timeline"][0]["mine"] is False
    assert "description_html" in body
    assert "content_html" in body["timeline"][0]
    assert [
        {"document_id": item["document_id"], "filename": item["filename"], "mime": item["mime"]}
        for item in body["attachments"]
    ] == [
        {"document_id": 2, "filename": "logo.png", "mime": "image/png"},
        {"document_id": 4, "filename": "foto.jpg", "mime": "image/jpeg"},
    ]
    assert all("itemtype" in item and "items_id" in item for item in body["attachments"])
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


def test_attachment_download_allows_linked_doc_missing_from_timeline():
    """H12: upload cria Document_Item; Timeline pode omitir — GET ainda libera."""
    client, glpi = build_client()
    link(client)
    glpi.attach_uploads_to_timeline = False
    uploaded = client.post(
        "/tickets/7/attachments",
        files={"file": ("print.png", b"img", "image/png")},
        headers={**auth_headers(), "Idempotency-Key": "up-lag"},
    )
    assert uploaded.status_code == 201
    document_id = uploaded.json()["document_id"]
    assert document_id not in {item.document_id for item in glpi.detail.attachments}
    downloaded = client.get(f"/tickets/7/attachments/{document_id}", headers=auth_headers())
    assert downloaded.status_code == 200
    assert downloaded.content == b"img"
    alien = client.get("/tickets/7/attachments/99", headers=auth_headers())
    assert alien.status_code == 404


def test_attachment_upload_forwards_optional_title():
    client, glpi = build_client()
    link(client)
    uploaded = client.post(
        "/tickets/7/attachments",
        files={"file": ("print.png", b"img", "image/png")},
        data={"title": "Evidência do erro"},
        headers={**auth_headers(), "Idempotency-Key": "up-title"},
    )
    assert uploaded.status_code == 201
    assert glpi.uploads[-1][4] == "Evidência do erro"


def test_followup_keeps_inline_image_when_doc_only_on_document_item():
    client, glpi = build_client()
    link(client)
    glpi.attach_uploads_to_timeline = False
    uploaded = client.post(
        "/tickets/7/attachments",
        files={"file": ("placa.png", b"png-new", "image/png")},
        headers={**auth_headers(), "Idempotency-Key": "up-follow-lag"},
    )
    document_id = uploaded.json()["document_id"]
    follow = client.post(
        "/tickets/7/followups",
        json={
            "content": (
                f'<p>foto</p><p><img src="/apps/helpdesk-api/tickets/7/attachments/{document_id}" '
                'alt="placa" /></p>'
            )
        },
        headers={**auth_headers(), "Idempotency-Key": "follow-lag"},
    )
    assert follow.status_code == 201
    assert f"docid={document_id}" in glpi.followups[0][1]


def test_attachment_upload_via_legacy_path():
    client, glpi = build_client()
    link(client)
    first = client.post(
        "/tickets/7/attachments",
        files={"file": ("placa.png", b"png-new", "image/png")},
        headers={**auth_headers(), "Idempotency-Key": "up-1"},
    )
    assert first.status_code == 201
    body = first.json()
    assert body["document_id"] == 100
    assert body["filename"] == "placa.png"
    assert body["mime"] == "image/png"
    assert glpi.uploads == [(7, "placa.png", b"png-new", "image/png", None)]
    replay = client.post(
        "/tickets/7/attachments",
        files={"file": ("placa.png", b"png-new", "image/png")},
        headers={**auth_headers(), "Idempotency-Key": "up-1"},
    )
    assert replay.status_code == 201
    assert replay.json() == body
    assert len(glpi.uploads) == 1
    follow = client.post(
        "/tickets/7/followups",
        json={
            "content": (
                '<p>foto</p><p><img src="/apps/helpdesk-api/tickets/7/attachments/100" alt="placa" /></p>'
            )
        },
        headers={**auth_headers(), "Idempotency-Key": "up-follow"},
    )
    assert follow.status_code == 201
    # Outbound stores the GLPI-native doc.send URL — renders inline in GLPI
    # and is rewritten back to the authenticated BFF path on read.
    assert "document.send.php?docid=100" in glpi.followups[0][1]
    foreign_img = client.post(
        "/tickets/7/followups",
        json={
            "content": (
                '<p>x</p><p><img src="/apps/helpdesk-api/tickets/99/attachments/100" alt="x" /></p>'
            )
        },
        headers={**auth_headers(), "Idempotency-Key": "up-foreign"},
    )
    assert foreign_img.status_code == 201
    assert "attachments/100" not in glpi.followups[1][1]
    assert "img" not in glpi.followups[1][1].lower()


def test_update_description_preserves_inline_images():
    """Opening description PATCH keeps inline images in position — stored
    in GLPI as the canonical document.send.php reference (docid-verified)."""
    from dataclasses import replace

    client, glpi = build_client()
    link(client)
    glpi.detail = replace(glpi.detail, requester_mine=True)
    response = client.patch(
        "/tickets/7/description",
        json={
            "content": (
                '<p>antes</p><p><img src="/apps/helpdesk-api/tickets/7/attachments/2" '
                'alt="logo" /></p><p>depois</p>'
            )
        },
        headers={**auth_headers(), "Idempotency-Key": "desc-1"},
    )
    assert response.status_code == 200
    ticket_id, stored_html = glpi.description_writes[0]
    assert ticket_id == 7
    assert "document.send.php?docid=2" in stored_html
    assert "antes" in stored_html and "depois" in stored_html
    # image stays between the paragraphs — not moved to a separate entry
    assert stored_html.index("antes") < stored_html.index("docid=2") < stored_html.index("depois")
    replay = client.patch(
        "/tickets/7/description",
        json={
            "content": (
                '<p>antes</p><p><img src="/apps/helpdesk-api/tickets/7/attachments/2" /></p><p>depois</p>'
            )
        },
        headers={**auth_headers(), "Idempotency-Key": "desc-1"},
    )
    assert replay.status_code == 200
    assert len(glpi.description_writes) == 1


def test_update_description_strips_unowned_document_reference():
    from dataclasses import replace

    client, glpi = build_client()
    link(client)
    glpi.detail = replace(glpi.detail, requester_mine=True)
    response = client.patch(
        "/tickets/7/description",
        json={
            "content": (
                '<p>ok</p><p><img src="/apps/helpdesk-api/tickets/7/attachments/77" '
                'alt="alien" /></p>'
            )
        },
        headers={**auth_headers(), "Idempotency-Key": "desc-alien"},
    )
    assert response.status_code == 200
    assert "docid=77" not in glpi.description_writes[0][1]
    assert "attachments/77" not in glpi.description_writes[0][1]
    assert "ok" in glpi.description_writes[0][1]


def test_update_description_forbidden_for_non_requester():
    client, _glpi = build_client()
    link(client)
    # default detail is not requester_mine
    response = client.patch(
        "/tickets/7/description",
        json={"content": "<p>edit</p>"},
        headers={**auth_headers(), "Idempotency-Key": "desc-denied"},
    )
    assert response.status_code == 403


def test_update_description_fails_when_readback_diverges():
    from dataclasses import replace

    client, glpi = build_client()
    link(client)
    glpi.detail = replace(glpi.detail, requester_mine=True)
    glpi.description_applies = False
    response = client.patch(
        "/tickets/7/description",
        json={"content": "<p>edit</p>"},
        headers={**auth_headers(), "Idempotency-Key": "desc-stale"},
    )
    assert response.status_code == 422


def test_attachment_upload_reports_author_state():
    client, glpi = build_client()
    link(client)
    glpi.session_uid = 15
    uploaded = client.post(
        "/tickets/7/attachments",
        files={"file": ("placa.png", b"png-new", "image/png")},
        headers={**auth_headers(), "Idempotency-Key": "up-auth"},
    )
    assert uploaded.status_code == 201
    body = uploaded.json()
    assert body["author_state"] == "verified"
    assert body["author_verified"] is True


def test_categories_come_from_glpi():
    client, _glpi = build_client()
    link(client)
    response = client.get("/ticket-categories", headers=auth_headers())
    assert response.json()["items"] == [{"id": 3, "name": "Hardware"}]
    urgencies = client.get("/urgencies", headers=auth_headers())
    assert [item["id"] for item in urgencies.json()["items"]] == [1, 2, 3, 4, 5]


def test_solicitante_accept_reject_satisfaction_cycle():
    from dataclasses import replace

    from helpdesk_app.domain.models import TimelineEntry

    client, glpi = build_client()
    link(client)
    glpi.detail = replace(
        glpi.detail,
        status_id=5,
        status="Solucionado",
        requester_mine=True,
        timeline=(TimelineEntry(9, "solution", "Pronto", "2026-09-22T10:00:00Z", "Ana"),),
    )
    detail = client.get("/tickets/7", headers=auth_headers())
    assert detail.status_code == 200
    body = detail.json()
    assert body["can_accept_solution"] is True
    assert body["can_reject_solution"] is True
    assert body["can_submit_satisfaction"] is False

    denied = client.post(
        "/tickets/7/solution/accept",
        json={},
        headers={**auth_headers(), "Idempotency-Key": "acc-denied"},
    )
    # still mine — should work
    assert denied.status_code == 200
    assert denied.json()["status_id"] == 6
    assert glpi.accepted_solutions == [(7, "Solução aceita.")]

    glpi.detail = replace(glpi.detail, status_id=5, status="Solucionado", requester_mine=False)
    foreign = client.post(
        "/tickets/7/solution/accept",
        json={"content": "ok"},
        headers={**auth_headers(), "Idempotency-Key": "acc-foreign"},
    )
    assert foreign.status_code == 403

    glpi.detail = replace(glpi.detail, status_id=5, status="Solucionado", requester_mine=True)
    rejected = client.post(
        "/tickets/7/solution/reject",
        json={"content": "ainda falha"},
        headers={**auth_headers(), "Idempotency-Key": "rej-1"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["status_id"] == 1
    assert glpi.rejected_solutions[-1] == (7, "ainda falha")

    glpi.detail = replace(glpi.detail, status_id=6, status="Fechado", requester_mine=True, can_followup=False)
    closed = client.get("/tickets/7", headers=auth_headers())
    assert closed.json()["can_submit_satisfaction"] is True
    sat = client.put(
        "/tickets/7/satisfaction",
        json={"satisfaction": 5, "comment": "ótimo"},
        headers={**auth_headers(), "Idempotency-Key": "sat-1"},
    )
    assert sat.status_code == 201
    assert sat.json() == {"satisfaction": 5, "comment": "ótimo"}
    again = client.put(
        "/tickets/7/satisfaction",
        json={"satisfaction": 1},
        headers={**auth_headers(), "Idempotency-Key": "sat-2"},
    )
    assert again.status_code == 422
    got = client.get("/tickets/7/satisfaction", headers=auth_headers())
    assert got.json() == {"satisfaction": 5, "comment": "ótimo"}
    detail_after = client.get("/tickets/7", headers=auth_headers())
    assert detail_after.json()["can_submit_satisfaction"] is False
    assert detail_after.json()["satisfaction"] == 5


def test_validation_accept_reject_for_designated_approver():
    from dataclasses import replace

    from helpdesk_app.domain.models import TicketValidation

    client, glpi = build_client()
    link(client)
    glpi.detail = replace(
        glpi.detail,
        validations=(
            TicketValidation(
                id=9,
                status=2,
                submission_comment="pode?",
                requested_approver_id=1,
                mine_to_decide=True,
            ),
        ),
        can_decide_validation=True,
    )
    detail = client.get("/tickets/7", headers=auth_headers())
    assert detail.json()["can_decide_validation"] is True
    assert detail.json()["validations"][0]["mine_to_decide"] is True

    accepted = client.post(
        "/tickets/7/validations/9/accept",
        json={"content": "sim"},
        headers={**auth_headers(), "Idempotency-Key": "val-acc"},
    )
    assert accepted.status_code == 200
    assert accepted.json()["status"] == 3
    assert glpi.validation_decisions[-1][:3] == (7, 9, True)

    glpi.detail = replace(
        glpi.detail,
        validations=(
            TicketValidation(
                id=10,
                status=2,
                submission_comment="ainda?",
                requested_approver_id=1,
                mine_to_decide=True,
            ),
        ),
        can_decide_validation=True,
    )
    refused = client.post(
        "/tickets/7/validations/10/reject",
        json={"content": "nao"},
        headers={**auth_headers(), "Idempotency-Key": "val-rej"},
    )
    assert refused.status_code == 200
    assert refused.json()["status"] == 4

    glpi.detail = replace(
        glpi.detail,
        validations=(
            TicketValidation(
                id=11,
                status=2,
                submission_comment="outro",
                requested_approver_id=99,
                mine_to_decide=False,
            ),
        ),
        can_decide_validation=False,
    )
    foreign = client.post(
        "/tickets/7/validations/11/accept",
        json={},
        headers={**auth_headers(), "Idempotency-Key": "val-foreign"},
    )
    assert foreign.status_code == 403



def test_create_solution_task_approval_for_technician_only():
    from dataclasses import replace

    client, glpi = build_client()
    link(client)
    tech = {**auth_headers(), "x-email": "ana.silva@delpi.com.br"}
    non_tech = {**auth_headers(), "x-email": "rh_ues@delpi.com.br"}

    detail = client.get("/tickets/7", headers=tech)
    assert detail.status_code == 200
    body = detail.json()
    assert body["can_create_solution"] is True
    assert body["can_create_task"] is True
    assert body["can_request_approval"] is True

    denied_detail = client.get("/tickets/7", headers=non_tech)
    assert denied_detail.json()["can_create_solution"] is False
    assert denied_detail.json()["can_create_task"] is False
    assert denied_detail.json()["can_request_approval"] is False

    forbidden = client.post(
        "/tickets/7/solutions",
        json={"content": "<p>solucao</p>"},
        headers={**non_tech, "Idempotency-Key": "sol-deny"},
    )
    assert forbidden.status_code == 403

    created = client.post(
        "/tickets/7/solutions",
        json={"content": "<p>solucao tecnica</p>"},
        headers={**tech, "Idempotency-Key": "sol-ok"},
    )
    assert created.status_code == 201
    assert created.json()["id"] >= 50
    assert glpi.solutions[-1][0] == 7
    assert any(entry["kind"] == "solution" for entry in client.get("/tickets/7", headers=tech).json()["timeline"])

    task = client.post(
        "/tickets/7/tasks",
        json={"content": "<p>tarefa</p>"},
        headers={**tech, "Idempotency-Key": "task-ok"},
    )
    assert task.status_code == 201
    assert any(entry["kind"] == "task" for entry in client.get("/tickets/7", headers=tech).json()["timeline"])

    approval = client.post(
        "/tickets/7/validations",
        json={"approver_user_id": 22, "content": "<p>preciso aprovar</p>"},
        headers={**tech, "Idempotency-Key": "apr-ok"},
    )
    assert approval.status_code == 201
    assert approval.json()["requested_approver_id"] == 22
    assert glpi.created_validations[-1][0] == 7
    assert glpi.created_validations[-1][1] == "User"
    assert glpi.created_validations[-1][2] == 22

    group_approval = client.post(
        "/tickets/7/validations",
        json={"approver_type": "group", "approver_id": 9, "content": "<p>grupo</p>"},
        headers={**tech, "Idempotency-Key": "apr-group-ok"},
    )
    assert group_approval.status_code == 201
    assert group_approval.json()["requested_approver_type"] == "Group"
    assert glpi.created_validations[-1][1:3] == ("Group", 9)

    bad_approver = client.post(
        "/tickets/7/validations",
        json={"approver_user_id": 404},
        headers={**tech, "Idempotency-Key": "apr-bad"},
    )
    assert bad_approver.status_code == 422

    glpi.detail = replace(glpi.detail, status_id=6, status="Fechado", can_followup=False)
    closed = client.post(
        "/tickets/7/solutions",
        json={"content": "<p>depois de fechado</p>"},
        headers={**tech, "Idempotency-Key": "sol-closed"},
    )
    assert closed.status_code == 422


def test_create_solution_requires_idempotency_and_auth():
    client, _glpi = build_client()
    # Middleware test harness rejects empty subject as forbidden (not 401).
    assert client.post("/tickets/7/solutions", json={"content": "x"}).status_code == 403
    link(client)
    tech = {**auth_headers(), "x-email": "ana.silva@delpi.com.br"}
    missing = client.post(
        "/tickets/7/solutions",
        json={"content": "<p>sem chave</p>"},
        headers=tech,
    )
    assert missing.status_code == 400


def test_technician_ops_via_glpi_session_user_id_without_email_match():
    """OAuth session user_id ∈ technician profiles unlocks can_create_* (email optional)."""
    client, glpi = build_client()
    link(client)
    glpi.session_uid = 15  # Ana — technician profile
    # JWT email does not match any GLPI catalog email — session path must still work.
    headers = {**auth_headers(), "x-email": "roberio.portal@example.invalid"}
    detail = client.get("/tickets/7", headers=headers)
    assert detail.status_code == 200
    body = detail.json()
    assert body["can_assign"] is True
    assert body["can_create_solution"] is True
    assert body["can_create_task"] is True
    assert body["can_request_approval"] is True


def test_session_user_id_outside_technician_profiles_stays_denied():
    client, glpi = build_client()
    link(client)
    glpi.session_uid = 40  # Sônia RH — not in technician_ids
    headers = {**auth_headers(), "x-email": "rh_ues@delpi.com.br"}
    detail = client.get("/tickets/7", headers=headers)
    assert detail.json()["can_create_solution"] is False


def test_ops004_catalogs_and_enriched_task_write():
    client, glpi = build_client()
    link(client)
    tech = {**auth_headers(), "x-email": "ana.silva@delpi.com.br"}

    assert client.get("/task-statuses", headers=tech).json()["items"][1]["name"] == "A fazer"
    assert client.get("/task-categories", headers=tech).json()["items"][0]["id"] == 4
    assert client.get("/task-templates", headers=tech).json()["items"][0]["duration_seconds"] == 3600
    assert client.get("/solution-types", headers=tech).json()["items"][0]["id"] == 2
    assert client.get("/request-types", headers=tech).json()["items"][0]["id"] == 1
    assert client.get("/groups", headers=tech).json()["items"][0]["id"] == 9

    task = client.post(
        "/tickets/7/tasks",
        json={
            "content": "<p>planejada</p>",
            "state": 1,
            "duration_seconds": 1800,
            "category_id": 4,
            "user_tech_id": 15,
            "group_tech_id": 9,
            "planned_begin": "2026-09-25T10:00:00",
            "planned_end": "2026-09-25T10:30:00",
        },
        headers={**tech, "Idempotency-Key": "task-rich-ok"},
    )
    assert task.status_code == 201
    body = task.json()
    assert body["id"] >= 60
    assert body["state"] == 1
    assert body["duration_seconds"] == 1800
    assert body["planned_begin"] == "2026-09-25T10:00:00"
    assert glpi.tasks[-1][2:7] == (1, 1800, 4, 15, 9)

    sol = client.post(
        "/tickets/7/solutions",
        json={"content": "<p>com tipo</p>", "solution_type_id": 2},
        headers={**tech, "Idempotency-Key": "sol-type-ok"},
    )
    assert sol.status_code == 201
    assert glpi.solutions[-1][2] == 2

    fu = client.post(
        "/tickets/7/followups",
        json={"content": "<p>origem</p>", "request_type_id": 1},
        headers={**tech, "Idempotency-Key": "fu-type-ok"},
    )
    assert fu.status_code == 201
    assert glpi.followups[-1][2] == 1


def test_delete_ticket_moves_to_trash_idempotent_and_verified():
    client, glpi = build_client()
    link(client)
    headers = {**auth_headers(), "Idempotency-Key": "del-1"}
    first = client.delete("/tickets/7", headers=headers)
    assert first.status_code == 200
    body = first.json()
    assert body["id"] == 7
    assert body["deleted"] is True
    assert body["delete_semantics"] == "trash"
    assert glpi.delete_calls == 1
    # post-delete same-user read is canonical not_found (trash semantics)
    gone = client.get("/tickets/7", headers=auth_headers())
    assert gone.status_code == 404

    # same proposal key replays the stored response — no second GLPI delete
    replay = client.delete("/tickets/7", headers=headers)
    assert replay.status_code == 200
    assert replay.json() == body
    assert glpi.delete_calls == 1


def test_delete_ticket_requires_idempotency_key_and_auth():
    client, glpi = build_client()
    link(client)
    missing_key = client.delete("/tickets/7", headers=auth_headers())
    assert missing_key.status_code == 400
    assert missing_key.json()["error"] == "idempotency_key_required"
    no_perm = client.delete(
        "/tickets/7",
        headers={"x-subject": "user-a", "Idempotency-Key": "k"},
    )
    assert no_perm.status_code == 403
    assert glpi.delete_calls == 0


def test_delete_ticket_not_found_is_typed_not_silent_success():
    """An initial not_found must never be masked as a successful retry."""
    client, glpi = build_client()
    link(client)
    headers = {**auth_headers(), "Idempotency-Key": "del-404"}
    resp = client.delete("/tickets/99", headers=headers)
    assert resp.status_code == 404
    assert resp.json()["error"] == "not_found"
    assert glpi.delete_calls == 0


def test_delete_ticket_forbidden_fails_closed():
    client, glpi = build_client()
    link(client)
    # FakeGlpi: get_ticket(403) → GlpiForbidden — the same-user pre-read
    # fails closed before any GLPI delete is attempted.
    headers = {**auth_headers(), "Idempotency-Key": "del-403"}
    resp = client.delete("/tickets/403", headers=headers)
    assert resp.status_code == 403
    assert resp.json()["error"] == "glpi_forbidden"
    assert glpi.delete_calls == 0


def test_delete_ticket_unlinked_session_is_typed():
    client, glpi = build_client()
    # never linked → _token() raises LinkRequired → typed 409
    resp = client.delete(
        "/tickets/7",
        headers={**auth_headers(), "Idempotency-Key": "del-nolink"},
    )
    assert resp.status_code == 409
    assert resp.json()["error"] == "glpi_link_required"
    assert glpi.delete_calls == 0


def test_delete_ticket_2xx_without_readback_fails_loudly():
    """2xx alone is never success — if the ticket is still readable the
    owner surfaces a typed failure instead of claiming deletion."""
    client, glpi = build_client()
    glpi.delete_actually_removes = False
    link(client)
    headers = {**auth_headers(), "Idempotency-Key": "del-mismatch"}
    resp = client.delete("/tickets/7", headers=headers)
    assert resp.status_code == 502
    assert resp.json()["error"] == "glpi_unavailable"
    assert glpi.delete_calls == 1

def test_ticket_detail_projects_attachment_refs_including_inline():
    """R4.2: attachment_refs = attachments[] + inline img refs, deduped."""
    from dataclasses import replace

    client, glpi = build_client()
    link(client)
    img_9 = "/apps/helpdesk-api/tickets/7/attachments/9"
    img_2 = "/apps/helpdesk-api/tickets/7/attachments/2"
    glpi.detail = replace(
        glpi.detail,
        description_html=(
            "<p>Erro</p>"
            "<img src=\"" + img_9 + "\">"
            "<img src=\"" + img_2 + "\">"
        ),
    )
    detail = client.get("/tickets/7", headers=auth_headers())
    assert detail.status_code == 200
    refs = {item["document_id"] for item in detail.json()["attachment_refs"]}
    assert refs == {2, 4, 9}


# --------------------------------------------------------------------------
# Requester corrective — authenticated session user becomes GLPI requester
# --------------------------------------------------------------------------


def test_create_registers_session_user_as_requester():
    client, glpi = build_client()
    link(client)
    glpi.session_uid = 12
    created = client.post(
        "/tickets",
        json={
            "title": "Sem impressão",
            "description": "Não imprime",
            "category_id": 3,
            "urgency_id": 3,
        },
        headers={**auth_headers(), "Idempotency-Key": "intent-req-1"},
    )
    assert created.status_code == 201
    assert glpi.requesters == [(42, 12, "access-a")]


def test_create_without_session_identity_never_creates():
    client, glpi = build_client()
    link(client)
    glpi.session_uid = None
    created = client.post(
        "/tickets",
        json={
            "title": "X",
            "description": "Y",
            "category_id": 3,
            "urgency_id": 3,
        },
        headers={**auth_headers(), "Idempotency-Key": "intent-req-no-session"},
    )
    assert created.status_code == 409
    assert created.json()["error"] == "glpi_link_required"
    assert glpi.created == []
    assert glpi.requesters == []


def test_create_requester_tracks_distinct_sessions():
    client, glpi = build_client()
    link(client)
    glpi.session_uid = 44
    created = client.post(
        "/tickets",
        json={
            "title": "T",
            "description": "D",
            "category_id": 3,
            "urgency_id": 3,
        },
        headers={**auth_headers(), "Idempotency-Key": "intent-req-44"},
    )
    assert created.status_code == 201
    assert glpi.requesters == [(42, 44, "access-a")]


def test_create_requester_distinct_from_assignee_and_observers():
    client, glpi = build_client()
    link(client)
    glpi.session_uid = 12
    created = client.post(
        "/tickets",
        json={
            "title": "T",
            "description": "D",
            "category_id": 3,
            "urgency_id": 3,
            "assignee_id": 15,
            "observer_ids": [22],
        },
        headers={**auth_headers(), "Idempotency-Key": "intent-req-roles"},
    )
    assert created.status_code == 201
    assert glpi.requesters == [(42, 12, "access-a")]
    assert glpi.assignees == [(42, 15, "access-a")]
    assert glpi.observers == [(42, 22, "access-a")]


def test_create_requester_association_failure_trashes_orphan():
    """Requester write fails → no success reported; the created ticket is
    best-effort trashed (GLPI trash semantics) instead of orphaned."""
    from helpdesk_app.domain.errors import GlpiForbidden

    client, glpi = build_client()
    link(client)
    glpi.session_uid = 12
    glpi.requester_error = GlpiForbidden("negado")
    created = client.post(
        "/tickets",
        json={
            "title": "T",
            "description": "D",
            "category_id": 3,
            "urgency_id": 3,
        },
        headers={**auth_headers(), "Idempotency-Key": "intent-req-fail"},
    )
    assert created.status_code != 201
    assert len(glpi.created) == 1
    assert glpi.delete_calls == 1
    assert 42 in glpi.deleted_tickets


def test_create_requester_readback_mismatch_trashes_orphan():
    """2xx TeamMember write but read-back shows a different/absent requester
    → typed failure + orphan compensation, never silent success."""
    client, glpi = build_client()
    link(client)
    glpi.session_uid = 12
    glpi.requester_readback = 99
    created = client.post(
        "/tickets",
        json={
            "title": "T",
            "description": "D",
            "category_id": 3,
            "urgency_id": 3,
        },
        headers={**auth_headers(), "Idempotency-Key": "intent-req-mismatch"},
    )
    assert created.status_code != 201
    assert glpi.requesters == [(42, 12, "access-a")]
    assert glpi.delete_calls == 1


def test_requester_id_still_rejected_in_create_body():
    """Security invariant: caller-supplied requester stays forbidden."""
    client, glpi = build_client()
    link(client)
    glpi.session_uid = 12
    resp = client.post(
        "/tickets",
        json={
            "title": "T",
            "description": "D",
            "category_id": 3,
            "urgency_id": 3,
            "requester_id": 9,
        },
        headers={**auth_headers(), "Idempotency-Key": "intent-req-forbid"},
    )
    assert resp.status_code == 422
    assert glpi.created == []
    assert glpi.requesters == []


def test_cycle_comments_rich_text_contract():
    """UNIFIED-RICH-TEXT-COMPOSER-V1 — cycle comments accept sanitized HTML
    for HTML destinations and are converted to plain text where GLPI
    stores TEXT (validation decision, satisfaction)."""
    from dataclasses import replace

    from helpdesk_app.domain.models import TicketValidation

    client, glpi = build_client()
    link(client)
    glpi.detail = replace(
        glpi.detail,
        status_id=5,
        status="Solucionado",
        requester_mine=True,
        validations=(
            TicketValidation(
                id=9,
                status=2,
                submission_comment="pode?",
                requested_approver_id=1,
                mine_to_decide=True,
            ),
        ),
        can_decide_validation=True,
    )
    headers = auth_headers()

    # Accept with rich HTML → ITILFollowup receives sanitized HTML.
    accepted = client.post(
        "/tickets/7/solution/accept",
        json={"content": "<p>Aprovado <strong>com ressalva</strong></p><script>x</script>"},
        headers={**headers, "Idempotency-Key": "cycle-acc-html"},
    )
    assert accepted.status_code == 200
    sent = glpi.accepted_solutions[-1]
    assert sent[0] == 7
    assert "<strong>com ressalva</strong>" in sent[1]
    assert "script" not in sent[1].lower()

    # Empty markup → default message (no <p></p> leak).
    glpi.detail = replace(glpi.detail, status_id=5, status="Solucionado", requester_mine=True)
    empty = client.post(
        "/tickets/7/solution/accept",
        json={"content": "<p></p><br>"},
        headers={**headers, "Idempotency-Key": "cycle-acc-empty"},
    )
    assert empty.status_code == 200
    assert glpi.accepted_solutions[-1] == (7, "Solução aceita.")

    # Reject with paragraphs/list keeps structure in the followup.
    glpi.detail = replace(glpi.detail, status_id=5, status="Solucionado", requester_mine=True)
    rejected = client.post(
        "/tickets/7/solution/reject",
        json={"content": "<p>Falta item A</p><ul><li>critério 1</li></ul>"},
        headers={**headers, "Idempotency-Key": "cycle-rej-html"},
    )
    assert rejected.status_code == 200
    assert "<li>critério 1</li>" in glpi.rejected_solutions[-1][1]

    # Validation decision → approval_comment is TEXT in GLPI: HTML → text.
    decided = client.post(
        "/tickets/7/validations/9/accept",
        json={"content": "<p>Ok pela <em>regra</em></p><p>segunda linha</p>"},
        headers={**headers, "Idempotency-Key": "cycle-val-html"},
    )
    assert decided.status_code == 200
    decision_comment = glpi.validation_decisions[-1][3]
    assert "<" not in decision_comment
    assert "Ok pela regra" in decision_comment
    assert "segunda linha" in decision_comment

    # Satisfaction → comment is TEXT: also receives plain text.
    glpi.detail = replace(glpi.detail, status_id=6, status="Fechado", requester_mine=True, can_followup=False)
    sat = client.put(
        "/tickets/7/satisfaction",
        json={"satisfaction": 4, "comment": "<p>muito <b>bom</b></p>"},
        headers={**headers, "Idempotency-Key": "cycle-sat-html"},
    )
    assert sat.status_code == 201
    assert sat.json()["comment"] == "muito bom"

    # Comment above 2000 visible chars → rejected.
    glpi.detail = replace(
        glpi.detail,
        status_id=5,
        status="Solucionado",
        requester_mine=True,
        can_followup=True,
    )
    too_long = client.post(
        "/tickets/7/solution/accept",
        json={"content": "<p>" + "x" * 2100 + "</p>"},
        headers={**headers, "Idempotency-Key": "cycle-acc-long"},
    )
    assert too_long.status_code == 422


def test_cycle_write_governed_outcome_author_mismatch():
    """POST persists with technical author and the restore PUT is denied →
    governed result (executed, author NOT verified), never a bare success;
    the stored idempotent response replays the same governed outcome and a
    same-key retry never re-executes the write."""
    from dataclasses import replace

    from helpdesk_app.domain.models import CycleWriteOutcome

    client, glpi = build_client()
    link(client)
    glpi.detail = replace(
        glpi.detail, status_id=5, status="Solucionado", requester_mine=True
    )
    glpi.cycle_outcome = CycleWriteOutcome(
        followup_id=77, users_id=68, author_state="mismatch"
    )

    headers = {**auth_headers(), "Idempotency-Key": "acc-mismatch"}
    resp = client.post(
        "/tickets/7/solution/accept", json={"content": "ok"}, headers=headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["outcome"] == "author_mismatch"
    assert body["author_verified"] is False
    assert body["status_verified"] is True
    assert body["followup_id"] == 77

    replay = client.post(
        "/tickets/7/solution/accept", json={"content": "ok"}, headers=headers
    )
    assert replay.json() == body
    assert len(glpi.accepted_solutions) == 1


def test_cycle_write_governed_outcome_author_unverified():
    """Author read-back unavailable → author_unverified (executed, integrity
    not confirmed), also stored idempotently."""
    from dataclasses import replace

    from helpdesk_app.domain.models import CycleWriteOutcome

    client, glpi = build_client()
    link(client)
    glpi.detail = replace(
        glpi.detail, status_id=5, status="Solucionado", requester_mine=True
    )
    glpi.cycle_outcome = CycleWriteOutcome(
        followup_id=78, users_id=68, author_state="unverified"
    )

    resp = client.post(
        "/tickets/7/solution/reject",
        json={"content": "reabrir"},
        headers={**auth_headers(), "Idempotency-Key": "rej-unverified"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["outcome"] == "author_unverified"
    assert body["author_verified"] is False
    assert body["followup_id"] == 78


def test_cycle_write_retry_with_new_key_blocked_by_transition():
    """After accept closes the ticket, a new Idempotency-Key must not
    duplicate the write — the state check rejects it (Cenário F)."""
    from dataclasses import replace

    client, glpi = build_client()
    link(client)
    glpi.detail = replace(
        glpi.detail, status_id=5, status="Solucionado", requester_mine=True
    )
    first = client.post(
        "/tickets/7/solution/accept",
        json={},
        headers={**auth_headers(), "Idempotency-Key": "acc-k1"},
    )
    assert first.status_code == 200
    assert first.json()["outcome"] == "verified"

    second = client.post(
        "/tickets/7/solution/accept",
        json={},
        headers={**auth_headers(), "Idempotency-Key": "acc-k2"},
    )
    assert second.status_code == 422
    assert len(glpi.accepted_solutions) == 1


def test_cycle_write_stored_response_status_unverified():
    """Author verified but ticket status outside the expected set →
    status_unverified, not full success."""
    from helpdesk_app.application.ticket_service import _cycle_write_stored_response
    from helpdesk_app.domain.models import CycleWriteOutcome, TicketDetail

    detail = TicketDetail(
        id=7,
        title="t",
        status="Solucionado",
        category="c",
        urgency="Media",
        updated_at="",
        description="",
        timeline=(),
        status_id=5,
    )
    stored = _cycle_write_stored_response(
        detail,
        CycleWriteOutcome(followup_id=77, users_id=68, author_state="verified"),
        expected_status_ids={6},
    )
    assert stored.body["outcome"] == "status_unverified"
    assert stored.body["author_verified"] is True
    assert stored.body["status_verified"] is False


def test_update_followup_edits_existing_entry():
    client, glpi = build_client()
    link(client)
    response = client.put(
        "/tickets/7/followups/1",
        json={"content": "texto corrigido"},
        headers={**auth_headers(), "Idempotency-Key": "upd-1"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == 1
    assert "texto corrigido" in (body["content"] or body["content_html"])
    assert glpi.updated_followups == [(7, 1, "texto corrigido")]


def test_update_followup_not_found_on_this_ticket():
    client, glpi = build_client()
    link(client)
    response = client.put(
        "/tickets/7/followups/999",
        json={"content": "x"},
        headers={**auth_headers(), "Idempotency-Key": "upd-2"},
    )
    assert response.status_code == 404
    assert glpi.updated_followups == []


def test_update_followup_requires_idempotency_key():
    client, _glpi = build_client()
    link(client)
    response = client.put(
        "/tickets/7/followups/1",
        json={"content": "x"},
        headers=auth_headers(),
    )
    assert response.status_code == 400
    assert response.json()["error"] == "idempotency_key_required"


def test_update_followup_rejects_empty_and_oversized_content():
    client, glpi = build_client()
    link(client)
    empty = client.put(
        "/tickets/7/followups/1",
        json={"content": ""},
        headers={**auth_headers(), "Idempotency-Key": "upd-3"},
    )
    assert empty.status_code == 422
    too_long = client.put(
        "/tickets/7/followups/1",
        json={"content": "x" * 50_001},
        headers={**auth_headers(), "Idempotency-Key": "upd-4"},
    )
    assert too_long.status_code == 422
    assert glpi.updated_followups == []


def test_update_followup_glpi_forbidden_propagates():
    from helpdesk_app.domain.errors import GlpiForbidden

    client, glpi = build_client()
    link(client)

    def _deny(access_token, ticket_id, followup_id, content):
        raise GlpiForbidden("sem permissão")

    glpi.update_followup = _deny  # type: ignore[method-assign]
    response = client.put(
        "/tickets/7/followups/1",
        json={"content": "x"},
        headers={**auth_headers(), "Idempotency-Key": "upd-5"},
    )
    assert response.status_code == 403


def test_update_followup_readback_mismatch_fails():
    client, glpi = build_client()
    link(client)
    glpi.update_followup_applies = False
    response = client.put(
        "/tickets/7/followups/1",
        json={"content": "texto novo"},
        headers={**auth_headers(), "Idempotency-Key": "upd-6"},
    )
    assert response.status_code == 422


def test_update_followup_idempotent_replay():
    client, glpi = build_client()
    link(client)
    first = client.put(
        "/tickets/7/followups/1",
        json={"content": "v2"},
        headers={**auth_headers(), "Idempotency-Key": "upd-7"},
    )
    second = client.put(
        "/tickets/7/followups/1",
        json={"content": "v2"},
        headers={**auth_headers(), "Idempotency-Key": "upd-7"},
    )
    assert first.status_code == 200
    assert second.status_code == 200
    # Replay hits the idempotency store — GLPI sees a single write.
    assert len(glpi.updated_followups) == 1


def test_update_classification_urgency_only():
    client, glpi = build_client()
    link(client)
    response = client.patch(
        "/tickets/7/classification",
        json={"urgency_id": 5},
        headers={**auth_headers(), "Idempotency-Key": "cls-1"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["urgency_id"] == 5
    assert body["urgency"] == "Muito alta"
    assert body["priority_id"] == 3  # untouched field keeps current value
    assert body["updated_fields"] == ["urgency_id"]
    assert glpi.classification_writes == [(7, 5, None, None, None, None, None)]


def test_update_classification_multiple_fields():
    client, glpi = build_client()
    link(client)
    response = client.patch(
        "/tickets/7/classification",
        json={"urgency_id": 4, "category_id": 3, "type_id": 2, "impact_id": 5},
        headers={**auth_headers(), "Idempotency-Key": "cls-2"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["category_id"] == 3
    assert body["type_id"] == 2
    assert body["type_name"] == "Requisição"
    assert body["impact_id"] == 5


def test_update_classification_requires_at_least_one_field():
    client, glpi = build_client()
    link(client)
    response = client.patch(
        "/tickets/7/classification",
        json={},
        headers={**auth_headers(), "Idempotency-Key": "cls-3"},
    )
    assert response.status_code == 422
    assert glpi.classification_writes == []


def test_update_classification_rejects_invalid_ids():
    client, glpi = build_client()
    link(client)
    for body in (
        {"urgency_id": 9},
        {"urgency_id": 0},
        {"impact_id": 6},
        {"type_id": 7},
        {"priority_id": 9},
        {"category_id": 999},  # not in the GLPI catalog
    ):
        response = client.patch(
            "/tickets/7/classification",
            json=body,
            headers={**auth_headers(), "Idempotency-Key": "cls-4"},
        )
        assert response.status_code in {422}, (body, response.status_code)
    assert glpi.classification_writes == []


def test_update_classification_rejects_unknown_field():
    client, glpi = build_client()
    link(client)
    response = client.patch(
        "/tickets/7/classification",
        json={"urgency_id": 5, "hack": 1},
        headers={**auth_headers(), "Idempotency-Key": "cls-5"},
    )
    assert response.status_code == 422
    assert glpi.classification_writes == []


def test_update_classification_requires_idempotency_key():
    client, _glpi = build_client()
    link(client)
    response = client.patch(
        "/tickets/7/classification",
        json={"urgency_id": 5},
        headers=auth_headers(),
    )
    assert response.status_code == 400
    assert response.json()["error"] == "idempotency_key_required"


def test_update_classification_missing_ticket():
    client, glpi = build_client()
    link(client)
    response = client.patch(
        "/tickets/99/classification",
        json={"urgency_id": 5},
        headers={**auth_headers(), "Idempotency-Key": "cls-6"},
    )
    assert response.status_code == 404


def test_update_classification_readback_divergence_fails():
    client, glpi = build_client()
    link(client)
    glpi.classification_applies = False
    response = client.patch(
        "/tickets/7/classification",
        json={"urgency_id": 5},
        headers={**auth_headers(), "Idempotency-Key": "cls-7"},
    )
    assert response.status_code == 422


def test_update_classification_glpi_forbidden_propagates():
    from helpdesk_app.domain.errors import GlpiForbidden

    client, glpi = build_client()
    link(client)

    def _deny(access_token, ticket_id, **kwargs):
        raise GlpiForbidden("sem permissão")

    glpi.update_ticket_classification = _deny  # type: ignore[method-assign]
    response = client.patch(
        "/tickets/7/classification",
        json={"urgency_id": 5},
        headers={**auth_headers(), "Idempotency-Key": "cls-8"},
    )
    assert response.status_code == 403


def test_update_classification_idempotent_replay():
    client, glpi = build_client()
    link(client)
    first = client.patch(
        "/tickets/7/classification",
        json={"urgency_id": 4},
        headers={**auth_headers(), "Idempotency-Key": "cls-9"},
    )
    second = client.patch(
        "/tickets/7/classification",
        json={"urgency_id": 4},
        headers={**auth_headers(), "Idempotency-Key": "cls-9"},
    )
    assert first.status_code == 200
    assert second.status_code == 200
    assert len(glpi.classification_writes) == 1


def test_classification_catalogs():
    client, _glpi = build_client()
    link(client)
    for path, expected_len in (
        ("/impacts", 5),
        ("/priorities", 6),
        ("/ticket-types", 2),
    ):
        response = client.get(path, headers=auth_headers())
        assert response.status_code == 200
        assert len(response.json()["items"]) == expected_len


def test_ticket_detail_exposes_classification_projection():
    client, _glpi = build_client()
    link(client)
    detail = client.get("/tickets/7", headers=auth_headers())
    assert detail.status_code == 200
    body = detail.json()
    assert body["urgency_id"] == 3
    assert body["impact_id"] == 3
    assert body["priority_id"] == 3
    assert body["type_id"] == 1
    assert body["type_name"] == "Incidente"
    assert body["category_id"] == 10
    assert "can_update_classification" in body
