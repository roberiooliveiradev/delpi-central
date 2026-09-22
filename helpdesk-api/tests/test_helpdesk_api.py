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


def test_create_attaches_observers_without_requester_or_entity():
    client, glpi = build_client()
    link(client)
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

        def search_users(self, *, q="", limit=20, browse=False):
            assert browse is False
            assert "ana" in (q or "").lower()
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

        def search_users(self, *, q="", limit=20, browse=False):
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
    assert f"attachments/{document_id}" in glpi.followups[0][1]


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
    assert glpi.uploads == [(7, "placa.png", b"png-new", "image/png")]
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
    assert "attachments/100" in glpi.followups[0][1]
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

