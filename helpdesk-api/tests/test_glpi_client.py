from urllib.parse import unquote

import json

import httpx
import pytest

from helpdesk_app.domain.errors import GlpiUnavailable
from helpdesk_app.infrastructure.glpi.http_client import HttpxGlpiClient
from helpdesk_app.domain.models import PersonIdentity
from helpdesk_app.infrastructure.glpi.mapping import (
    apply_viewer_identity,
    build_ticket_list_query,
    parse_categories,
    parse_ticket_detail,
    parse_ticket_list,
    parse_viewer_identity,
)
from helpdesk_app.domain.errors import GlpiForbidden, GlpiNotFound, GlpiValidation


def test_get_ticket_marks_mine_from_session_user_id():
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/session"):
            return httpx.Response(200, json={"user_id": 12, "name": "roberio"})
        if path.endswith("/Timeline"):
            return httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "type": "Followup",
                            "item": {
                                "id": 9,
                                "content": "olola",
                                "user": {"id": 12, "name": "Roberio"},
                            },
                        }
                    ]
                },
            )
        return httpx.Response(
            200,
            json={
                "id": 1114,
                "name": "Chamado teste",
                "content": "Texto",
                "status": {"name": "Novo"},
                "urgency": 2,
                "team": [{"role": "requester", "id": 12, "display_name": "Outro Nome"}],
            },
        )

    client = HttpxGlpiClient(
        base_url="https://glpi.example",
        client_id="id",
        client_secret="super-secret",
        redirect_uri="https://centraldelpi.com.br/apps/helpdesk-api/auth/glpi/callback",
        transport=httpx.MockTransport(handler),
    )
    detail = client.get_ticket("token", 1114, viewer_email="roberio@delpi.com.br")
    assert detail.requester_mine is True
    assert detail.timeline[0].mine is True
    assert detail.requester_display_name == "Outro Nome"


def test_post_is_not_retried_and_get_retries_transient_status():
    calls = {"get": 0, "post": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            calls["post"] += 1
            return httpx.Response(503, json={"error": "down"})
        calls["get"] += 1
        if calls["get"] < 3:
            return httpx.Response(503, json={"error": "down"})
        return httpx.Response(200, json={"results": []})

    client = HttpxGlpiClient(
        base_url="https://glpi.example",
        client_id="id",
        client_secret="super-secret",
        redirect_uri="https://centraldelpi.com.br/apps/helpdesk-api/auth/glpi/callback",
        transport=httpx.MockTransport(handler),
    )
    try:
        client.create_ticket(
            "token",
            title="A",
            description="B",
            category_id=1,
            urgency_id=3,
        )
    except GlpiUnavailable:
        pass
    assert calls["post"] == 1
    assert client.post_calls == 1
    listed = client.list_tickets("token", build_ticket_list_query())
    assert listed.items == ()
    assert calls["get"] == 3


def test_authorization_url_starts_minha_delpi_saml_and_keeps_state():
    client = HttpxGlpiClient(
        base_url="https://helpdesk.example",
        client_id="client",
        client_secret="super-secret",
        redirect_uri="https://centraldelpi.com.br/apps/helpdesk-api/auth/glpi/callback",
        saml_idp_id="1",
    )
    url = client.authorization_url(state="abc_DEF-123", code_challenge="challenge")
    assert url.startswith("https://helpdesk.example/?samlIdpId=1&redirect=")
    stored_by_saml = unquote(url.split("redirect=", 1)[1])
    assert "&" not in stored_by_saml
    authorize = unquote(stored_by_saml)
    assert authorize.startswith("https://helpdesk.example/api.php/authorize?")
    assert "state=abc_DEF-123" in authorize
    assert "code_challenge=challenge" in authorize
    assert "code_challenge_method=S256" in authorize
    assert "accept=1" in authorize


def test_authorization_url_keeps_a_sibling_state():
    client = HttpxGlpiClient(
        base_url="https://helpdesk.example",
        client_id="client",
        client_secret="super-secret",
        redirect_uri="https://centraldelpi.com.br/apps/helpdesk-api/auth/glpi/callback",
    )
    url = client.authorization_url(state="sibling_state", code_challenge="other-challenge")
    authorize = unquote(unquote(url.split("redirect=", 1)[1]))
    assert "state=sibling_state" in authorize
    assert "state=abc_DEF-123" not in authorize


def test_authorization_url_without_idp_does_not_force_saml():
    client = HttpxGlpiClient(
        base_url="https://helpdesk.example",
        client_id="client",
        client_secret="super-secret",
        redirect_uri="https://centraldelpi.com.br/apps/helpdesk-api/auth/glpi/callback",
        saml_idp_id="",
    )
    url = client.authorization_url(state="abc_DEF-123", code_challenge="challenge")
    assert "samlIdpId=" not in url
    assert url.startswith("https://helpdesk.example/?redirect=")
    authorize = unquote(url.split("redirect=", 1)[1])
    assert authorize.startswith("https://helpdesk.example/api.php/authorize?")
    assert "state=abc_DEF-123" in authorize


def test_authorization_url_rejects_non_numeric_idp():
    client = HttpxGlpiClient(
        base_url="https://helpdesk.example",
        client_id="client",
        client_secret="super-secret",
        redirect_uri="https://centraldelpi.com.br/apps/helpdesk-api/auth/glpi/callback",
        saml_idp_id="1;bypass",
    )
    with pytest.raises(ValueError):
        client.authorization_url(state="abc", code_challenge="challenge")


def test_mapping_keeps_followups_and_tasks():
    detail = parse_ticket_detail(
        {
            "id": 4,
            "name": "Rede",
            "content": "Sem internet",
            "status": {"id": 1, "name": "Novo"},
            "category": {"id": 2, "name": "Rede"},
            "urgency": 2,
            "date_mod": "2026-09-21T10:00:00Z",
        },
        {
            "results": [
                {
                    "id": 1,
                    "type": "Followup",
                    "content": "Cabo ok",
                    "date_creation": "2026-09-21T11:00:00Z",
                    "user": {"name": "Ana"},
                },
                {"id": 2, "type": "Task", "content": "interno"},
            ]
        },
    )
    assert detail.urgency == "Baixa"
    assert detail.timeline[0].content == "Cabo ok"
    assert detail.attachments == ()
    assert [entry.kind for entry in detail.timeline] == ["followup", "task"]
    categories = parse_categories({"results": [{"id": 2, "completename": "TI > Rede"}]})
    assert categories[0].name == "TI > Rede"


def test_mapping_keeps_solution_and_hides_validation():
    detail = parse_ticket_detail(
        {
            "id": 5,
            "name": "VPN",
            "content": "Sem acesso",
            "status": {"id": 5, "name": "Solucionado"},
            "category": {"id": 2, "name": "Rede"},
            "urgency": 3,
            "date_mod": "2026-09-21T12:00:00Z",
            "date_solve": "2026-09-21T12:00:00Z",
        },
        {
            "results": [
                {
                    "type": "Followup",
                    "item": {
                        "id": 10,
                        "content": "Reinicie o cliente",
                        "date_creation": "2026-09-21T11:00:00Z",
                        "user": {"firstname": "Ana", "realname": "Silva"},
                    },
                },
                {
                    "type": "Solution",
                    "item": {
                        "id": 11,
                        "content": "<p>Cliente reiniciado; VPN ok.</p>",
                        "date_creation": "2026-09-21T12:00:00Z",
                        "user": {"firstname": "Ana", "realname": "Silva"},
                    },
                },
                {"type": "Validation", "item": {"id": 12, "content": "pedido interno"}},
                {"type": "Task", "item": {"id": 13, "content": "tarefa interna"}},
            ]
        },
    )
    # Validation stays on validations[] surface; Task is now part of workspace timeline.
    assert [entry.kind for entry in detail.timeline] == ["followup", "solution", "task"]
    assert detail.timeline[1].content == "Cliente reiniciado; VPN ok."
    assert "<p>" not in detail.timeline[1].content
    assert "Cliente reiniciado" in detail.timeline[1].content_html
    assert detail.timeline[2].content == "tarefa interna"


def test_parse_categories_keeps_helpdesk_visible_and_drops_internal():
    categories = parse_categories(
        {
            "results": [
                {"id": 1, "completename": "Helpdesk", "is_helpdesk_visible": True},
                {"id": 2, "completename": "Interna", "is_helpdesk_visible": False},
                {"id": 3, "name": "Legado visível", "is_helpdeskvisible": 1},
                {"id": 4, "name": "Sem campo"},
            ]
        }
    )
    assert [item.id for item in categories] == [1, 3, 4]


def test_list_categories_filters_helpdesk_visible_and_pages():
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        start = int(request.url.params.get("start") or 0)
        if start == 0:
            return httpx.Response(
                206,
                json={
                    "results": [
                        {"id": index, "completename": f"Cat {index}", "is_helpdesk_visible": True}
                        for index in range(1, 51)
                    ]
                },
            )
        return httpx.Response(
            200,
            json={"results": [{"id": 51, "completename": "Última", "is_helpdesk_visible": True}]},
        )

    client = HttpxGlpiClient(
        base_url="https://glpi.example",
        client_id="id",
        client_secret="super-secret",
        redirect_uri="https://centraldelpi.com.br/apps/helpdesk-api/auth/glpi/callback",
        transport=httpx.MockTransport(handler),
    )
    listed = client.list_categories("token")
    assert [item.id for item in listed] == list(range(1, 52))
    assert calls[0].url.params["filter"] == "is_helpdesk_visible==true"
    assert calls[0].url.params["limit"] == "50"
    assert calls[1].url.params["start"] == "50"


def test_list_categories_maps_forbidden_without_retrying_as_success():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"error": "forbidden"})

    client = HttpxGlpiClient(
        base_url="https://glpi.example",
        client_id="id",
        client_secret="super-secret",
        redirect_uri="https://centraldelpi.com.br/apps/helpdesk-api/auth/glpi/callback",
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(GlpiForbidden):
        client.list_categories("token")


def test_mapping_repairs_legacy_text_and_strips_html():
    listed = parse_ticket_list(
        [
            {
                "id": 3,
                "name": "Email n\u251c\u00fao funcionando",
                "status": {"id": 1, "name": "Novo"},
                "urgency": 3,
            }
        ]
    )
    assert listed[0].title == "Email não funcionando"
    assert listed[0].category == ""
    detail = parse_ticket_detail(
        {
            "id": 1,
            "name": "Teste",
            "content": "<p>Rede n\u251c\u00fao quer funcionar</p>",
            "status": {"id": 1, "name": "Novo"},
            "category": {"id": 0},
            "urgency": 2,
        },
        {
            "results": [
                {
                    "id": 9,
                    "type": "Followup",
                    "content": "<p>M\u251c\u00edquina ligada</p>",
                    "date_creation": "2026-09-21T11:00:00Z",
                    "user": {"name": "Ana"},
                }
            ]
        },
    )
    assert detail.description == "Rede não quer funcionar"
    assert detail.description_html == "<p>Rede não quer funcionar</p>"
    assert detail.timeline[0].content == "Máquina ligada"
    assert detail.timeline[0].content_html == "<p>Máquina ligada</p>"
    assert detail.category == ""


def test_mapping_publishes_sanitized_html_and_rewrites_owned_documents():
    detail = parse_ticket_detail(
        {
            "id": 1108,
            "name": "Foto",
            "content": (
                '<p><strong>Rede</strong> ok</p>'
                '<p><a href="https://example.com/docs">manual</a></p>'
                '<p><a href="/front/document.send.php?docid=391&amp;itemtype=Ticket&amp;items_id=1108" target="_blank">'
                '<img src="/front/document.send.php?docid=391" alt="placa" width="100" /></a></p>'
                '<p><img src="/front/document.send.php?docid=999" alt="alheio" /></p>'
                '<script>alert(1)</script>'
                '<p><a href="javascript:alert(1)">x</a></p>'
                '<img src="x" onerror="alert(1)" />'
            ),
            "status": {"id": 1, "name": "Novo"},
            "urgency": 2,
        },
        {
            "results": [
                {
                    "type": "Document",
                    "item": {
                        "documents_id": 391,
                        "filename": "placa.png",
                        "mime": "image/png",
                    },
                },
                {
                    "type": "Followup",
                    "item": {
                        "id": 12,
                        "content": (
                            "<p>Cabo <em>ok</em></p>"
                            '<p><img src="/front/document.send.php?docid=391" alt="mesma" /></p>'
                            '<p><img src="/front/document.send.php?docid=999" alt="alheio-fu" /></p>'
                            "<script>bad()</script>"
                        ),
                        "date_creation": "2026-09-21T11:00:00Z",
                        "user": {"name": "Ana"},
                    },
                },
            ]
        },
    )
    assert detail.description == "Rede ok manual x"
    assert "<strong>Rede</strong>" in detail.description_html
    assert 'href="https://example.com/docs"' in detail.description_html
    assert "/front/document.send.php" not in detail.description_html
    assert 'src="/apps/helpdesk-api/tickets/1108/attachments/391"' in detail.description_html
    assert 'alt="placa"' in detail.description_html
    assert "docid=999" not in detail.description_html
    assert "alheio" not in detail.description_html
    assert "<script" not in detail.description_html.lower()
    assert "javascript:" not in detail.description_html.lower()
    assert "onerror" not in detail.description_html.lower()
    assert detail.timeline[0].content == "Cabo ok"
    assert "/front/document.send.php" not in detail.timeline[0].content_html
    assert 'src="/apps/helpdesk-api/tickets/1108/attachments/391"' in detail.timeline[0].content_html
    assert "alheio-fu" not in detail.timeline[0].content_html
    assert "<script" not in detail.timeline[0].content_html.lower()
    assert [item.document_id for item in detail.attachments] == [391]
    detail = parse_ticket_detail(
        {
            "id": 5,
            "name": "Não consigo encontrar o email",
            "content": "<p>Testando 123 caçador</p>",
            "status": {"name": "Solucionado"},
            "category": {"id": 4, "name": "E-mail"},
            "urgency": 2,
        },
        {"results": []},
    )
    assert detail.title == "Não consigo encontrar o email"
    assert detail.description == "Testando 123 caçador"
    assert detail.category == "E-mail"
    assert detail.status == "Solucionado"


def test_mapping_leaves_unrepairable_marker_unchanged():
    detail = parse_ticket_detail(
        {
            "id": 8,
            "name": "Sinal \u251c isolado",
            "content": "Sem tag",
            "status": {"name": "Novo"},
            "urgency": 1,
        },
        {"results": []},
    )
    assert detail.title == "Sinal \u251c isolado"
    assert detail.description == "Sem tag"


def test_mapping_keeps_followup_document_and_task():
    from helpdesk_app.domain.models import Attachment
    from helpdesk_app.infrastructure.glpi.mapping import attachment_filename

    detail = parse_ticket_detail(
        {"id": 1, "name": "Teste", "content": "Rede", "status": {"name": "Novo"}, "urgency": 2},
        [
            {
                "type": "Followup",
                "item": {
                    "id": 8,
                    "content": "Cabo ok",
                    "date_creation": "2026-09-21T11:00:00Z",
                    "user": {"name": "Ana"},
                },
            },
            {
                "type": "Document",
                "item": {"id": 1, "documents_id": 2, "filename": "logo.png", "mime": "image/png"},
            },
            {"type": "Task", "item": {"id": 3, "content": "interno"}},
            {"type": "Document", "item": {"documents_id": 4, "name": "foto.jpg", "mime": "image/jpeg"}},
        ],
    )
    assert [entry.content for entry in detail.timeline] == ["Cabo ok", "interno"]
    assert detail.attachments == (
        Attachment(2, "logo.png", "image/png"),
        Attachment(4, "foto.jpg", "image/jpeg"),
    )
    assert attachment_filename("../segredo.txt") == "segredo.txt"
    assert attachment_filename("   ") == "anexo"


def test_mapping_document_uses_own_id_when_documents_id_absent():
    detail = parse_ticket_detail(
        {"id": 1122, "name": "Teste", "content": "x", "status": {"name": "Novo"}, "urgency": 1},
        [
            {
                "type": "Document",
                "item": {"id": 1177, "name": "Captura.png", "filename": "Captura.png", "mime": "image/png"},
            },
            {
                "type": "Document_Item",
                "item": {"id": 99, "documents_id": 1178, "name": "image.png", "mime": "image/png"},
            },
        ],
    )
    assert [item.document_id for item in detail.attachments] == [1177, 1178]

def test_mapping_publishes_requester_and_hides_private_followup():
    detail = parse_ticket_detail(
        {
            "id": 1114,
            "name": "Chamado teste",
            "content": "<p>Texto da abertura</p>",
            "status": {"name": "Novo"},
            "urgency": 2,
            "date_creation": "2026-09-21T10:00:00Z",
            "date_mod": "2026-09-21T12:00:00Z",
            "team": [
                {"role": "assigned", "display_name": "Técnico"},
                {"role": "requester", "display_name": "Robério Teixeira"},
            ],
        },
        {
            "results": [
                {
                    "type": "Followup",
                    "item": {
                        "id": 3,
                        "content": "Público",
                        "date_creation": "2026-09-21T11:00:00Z",
                        "user": {"name": "Ana"},
                        "is_private": 0,
                    },
                },
                {
                    "type": "Followup",
                    "item": {
                        "id": 4,
                        "content": "Só o técnico",
                        "is_private": True,
                        "user": {"name": "Técnico"},
                    },
                },
                {
                    "type": "Followup",
                    "item": {"id": 6, "content": "Sinal textual", "is_private": "1"},
                },
                {"type": "Task", "item": {"id": 5, "content": "interno"}},
            ]
        },
    )
    assert detail.requester_display_name == "Robério Teixeira"
    assert detail.assigned_display_name == "Técnico"
    assert detail.created_at == "2026-09-21T10:00:00Z"
    assert detail.description == "Texto da abertura"
    assert [entry.content for entry in detail.timeline] == ["Público", "interno"]


def test_list_query_uses_rsql_and_rejects_injection():
    query = build_ticket_list_query(
        q="Monitor;status==1",
        status="open",
        urgency_id=3,
        category_id=8,
        updated_from="2026-02-01",
        updated_to="2026-02-28",
        created_from="2026-01-01",
        created_to="2026-01-31",
        sort="created_at:asc",
        page=2,
        page_size=20,
    )
    assert query.filter.startswith("is_deleted==false")
    assert "status==1" not in query.filter
    assert "(name=like=*Monitorstatus1*,content=like=*Monitorstatus1*)" in query.filter
    assert "status.id=in=(1,10,2,3,4)" in query.filter
    assert build_ticket_list_query(status="pending").filter.endswith("status.id==4")
    assert build_ticket_list_query(status="approval").filter.endswith("status.id==10")
    assert "urgency==3" in query.filter
    assert "category.id==8" in query.filter
    assert "date_mod=ge=2026-02-01T00:00:00" in query.filter
    assert "date_mod=le=2026-02-28T23:59:59" in query.filter
    assert "date_creation=ge=2026-01-01T00:00:00" in query.filter
    assert "date_creation=le=2026-01-31T23:59:59" in query.filter
    assert query.sort == "date_creation:asc"
    assert query.start == 20
    assert query.limit == 21
    with pytest.raises(GlpiValidation):
        build_ticket_list_query(status="admin")
    with pytest.raises(GlpiValidation):
        build_ticket_list_query(sort="entity:desc")
    with pytest.raises(GlpiValidation):
        build_ticket_list_query(created_from="21-09-2026")
    with pytest.raises(GlpiValidation):
        build_ticket_list_query(created_to="not-a-date")
    sized = build_ticket_list_query(page_size=10)
    assert sized.page_size == 10
    assert sized.limit == 11
    assert build_ticket_list_query(sort="id:desc").sort == "id:desc"
    assert build_ticket_list_query(sort="status:asc").sort == "status.id:asc"
    assert build_ticket_list_query(sort="urgency:desc").sort == "urgency:desc"
    assert build_ticket_list_query(sort="category:asc").sort == "category.name:asc"
    assert build_ticket_list_query(sort="solved_at:desc").sort == "date_solve:desc"
    assert build_ticket_list_query(sort="closed_at:desc").sort == "date_close:desc"
    assert (
        build_ticket_list_query(sort="updated_at:desc,title:asc").sort
        == "date_mod:desc,name:asc"
    )
    with pytest.raises(GlpiValidation):
        build_ticket_list_query(sort="updated_at:desc,title:asc,status:asc,id:asc")
    with pytest.raises(GlpiValidation):
        build_ticket_list_query(sort="updated_at:desc,updated_at:asc")


def test_mapping_publishes_status_id_and_keeps_glpi_label():
    listed = parse_ticket_list(
        [{"id": 1, "name": "Novo", "status": {"id": 1, "name": "Novo"}, "urgency": 2}]
    )
    assert listed[0].status_id == 1
    assert listed[0].status == "Novo"
    approval = parse_ticket_list(
        [
            {
                "id": 10,
                "name": "Aguardando",
                "status": {"id": 10, "name": "Aprovação"},
                "urgency": 3,
            }
        ]
    )
    assert approval[0].status_id == 10
    assert approval[0].status == "Aprovação"


def test_detail_can_followup_false_only_when_closed_and_lists_observers():
    from helpdesk_app.infrastructure.glpi.mapping import ticket_allows_followup

    assert ticket_allows_followup(1) is True
    assert ticket_allows_followup(5) is True
    assert ticket_allows_followup(6) is False
    assert ticket_allows_followup(None) is True

    open_ticket = parse_ticket_detail(
        {
            "id": 20,
            "name": "Aberto",
            "content": "<p>oi</p>",
            "status": {"id": 1, "name": "Novo"},
            "urgency": 2,
            "date_creation": "2026-09-21T10:00:00Z",
            "date_mod": "2026-09-21T11:00:00Z",
            "team": [
                {"role": "requester", "display_name": "Ana"},
                {"role": "observer", "firstname": "Lia", "realname": "Costa"},
                {"role": "observer", "display_name": "Bruno Vista"},
            ],
        },
        {"results": []},
    )
    assert open_ticket.can_followup is True
    assert open_ticket.observers_display_name == "Lia Costa, Bruno Vista"

    solved = parse_ticket_detail(
        {
            "id": 21,
            "name": "Solucionado",
            "content": "<p>ok</p>",
            "status": {"id": 5, "name": "Solucionado"},
            "urgency": 2,
            "date_solve": "2026-09-21T12:00:00Z",
        },
        {"results": []},
    )
    assert solved.can_followup is True
    assert solved.solved_at == "2026-09-21T12:00:00Z"
    assert solved.observers_display_name == ""

    closed = parse_ticket_detail(
        {
            "id": 22,
            "name": "Fechado",
            "content": "<p>fim</p>",
            "status": {"id": 6, "name": "Fechado"},
            "urgency": 2,
            "date_close": "2026-09-21T13:00:00Z",
        },
        {"results": []},
    )
    assert closed.can_followup is False
    assert closed.closed_at == "2026-09-21T13:00:00Z"


def test_mapping_list_publishes_created_at_and_assigned():
    listed = parse_ticket_list(
        [
            {
                "id": 2,
                "name": "Monitor falhando",
                "status": {"id": 2, "name": "Em atendimento (atribuído)"},
                "category": {"id": 0},
                "urgency": 3,
                "date_creation": "2026-02-19T10:00:00Z",
                "date_mod": "2026-02-19T12:00:00Z",
                "date_solve": None,
                "date_close": None,
                "sla_ttr": {"id": 1, "name": "TTR 8h"},
                "sla_tto": {"id": 2, "name": "TTO 1h"},
                "team": [
                    {"role": "requester", "firstname": "Robério", "realname": "Teixeira"},
                    {"role": "assigned", "firstname": "Ana", "realname": "Silva"},
                ],
            }
        ]
    )
    assert listed[0].created_at == "2026-02-19T10:00:00Z"
    assert listed[0].requester_display_name == "Robério Teixeira"
    assert listed[0].assigned_display_name == "Ana Silva"
    assert listed[0].category == ""
    assert listed[0].status_id == 2
    assert listed[0].status == "Em atendimento (atribuído)"
    assert listed[0].solved_at == ""
    assert listed[0].closed_at == ""
    assert listed[0].sla_ttr == "TTR 8h"
    assert listed[0].sla_tto == "TTO 1h"


def test_mapping_list_requester_falls_back_to_user_recipient():
    listed = parse_ticket_list(
        [
            {
                "id": 3,
                "name": "Sem team requester",
                "status": {"id": 1, "name": "Novo"},
                "urgency": 2,
                "user_recipient": {"firstname": "Lia", "realname": "Costa"},
                "team": [{"role": "assigned", "firstname": "Ana", "realname": "Silva"}],
            }
        ]
    )
    assert listed[0].requester_display_name == "Lia Costa"
    assert listed[0].assigned_display_name == "Ana Silva"


def test_team_member_observer_body_is_hd011_safe():
    from helpdesk_app.infrastructure.glpi.mapping import (
        normalize_assignee_id,
        normalize_observer_ids,
        parse_catalog_users,
        team_member_assigned_body,
        team_member_observer_body,
        build_user_email_filter,
        build_user_search_filter,
    )

    body = team_member_observer_body(15)
    assert body == {"type": "User", "role": "observer", "id": 15}
    assert "requester" not in body
    assert "entity" not in body
    assert normalize_observer_ids([15, 15, 22]) == (15, 22)
    assigned = team_member_assigned_body(22)
    assert assigned == {"type": "User", "role": "assigned", "id": 22}
    assert "requester" not in assigned
    assert normalize_assignee_id(22) == 22
    assert normalize_assignee_id(None) is None
    assert build_user_search_filter("") == "is_active==true"
    assert "id==15" in build_user_search_filter("15")
    name_filter = build_user_search_filter("micha")
    assert "username=like=*micha*" in name_filter
    assert "username=like=*Micha*" in name_filter
    assert "email=like=" not in name_filter
    assert name_filter.startswith("is_active==true;")
    accent_filter = build_user_search_filter("robério")
    assert "robério" in accent_filter
    assert "roberio" in accent_filter
    assert "email==" not in build_user_search_filter("ana@delpi.com.br")
    assert "ana" in build_user_search_filter("ana@delpi.com.br").lower()
    assert build_user_email_filter("Ana@Delpi.com.br").startswith("is_active==true;")
    assert "email==" not in build_user_email_filter("Ana@Delpi.com.br")
    michael = build_user_search_filter("michael")
    assert "Michael" in michael
    assert "email=like=" not in michael
    noise = parse_catalog_users(
        [
            {"id": 2, "username": "glpi", "firstname": "", "realname": ""},
            {"id": 3, "username": "post-only"},
            {"id": 7, "username": "minha-delpi-upload"},
            {"id": 15, "username": "ana", "firstname": "Ana", "realname": "Silva", "email": "ana@delpi.com.br"},
            {"id": 99, "username": "x", "firstname": 0, "realname": 0, "display_name": 0},
        ]
    )
    assert [(u.id, u.display_name, u.email) for u in noise] == [
        (15, "Ana Silva", "ana@delpi.com.br")
    ]
    with pytest.raises(GlpiValidation):
        team_member_observer_body(0)
    with pytest.raises(GlpiValidation):
        normalize_observer_ids([-1])
    with pytest.raises(GlpiValidation):
        team_member_assigned_body(0)


def test_mapping_list_publishes_solved_and_closed_instants():
    listed = parse_ticket_list(
        [
            {
                "id": 9,
                "name": "Resolvido",
                "status": {"id": 5, "name": "Solucionado"},
                "urgency": 2,
                "date_solve": "2026-09-20T18:00:00Z",
                "date_close": "2026-09-21T09:00:00Z",
            }
        ]
    )
    assert listed[0].solved_at == "2026-09-20T18:00:00Z"
    assert listed[0].closed_at == "2026-09-21T09:00:00Z"


def test_mapping_list_drops_deleted_and_detail_hides_them():
    listed = parse_ticket_list(
        [
            {"id": 1, "name": "Teste", "is_deleted": 1, "status": {"id": 1, "name": "Novo"}, "urgency": 2},
            {"id": 11008, "name": "Ativo", "is_deleted": False, "status": {"id": 1, "name": "Novo"}, "urgency": 3},
        ]
    )
    assert [row.id for row in listed] == [11008]
    with pytest.raises(GlpiNotFound):
        parse_ticket_detail(
            {"id": 1, "name": "Teste", "is_deleted": True, "content": "Não deve vazar"},
            {"results": []},
        )


def test_person_name_prefers_the_most_complete_label():
    detail = parse_ticket_detail(
        {
            "id": 1114,
            "name": "Chamado teste",
            "content": "Texto",
            "status": {"name": "Novo"},
            "urgency": 2,
            "team": [
                {
                    "role": "requester",
                    "display_name": "Roberio",
                    "firstname": "Robério",
                    "realname": "Oliveira",
                }
            ],
        },
        {
            "results": [
                {
                    "type": "Followup",
                    "item": {
                        "id": 9,
                        "content": "olola",
                        "user": {"display_name": "Roberio", "firstname": "Robério", "realname": "Oliveira"},
                    },
                }
            ]
        },
    )
    assert detail.requester_display_name == "Robério Oliveira"
    assert detail.timeline[0].author_display_name == "Robério Oliveira"


def test_conversation_identity_uses_id_or_email_never_name():
    detail = parse_ticket_detail(
        {
            "id": 1114,
            "name": "Chamado teste",
            "content": "Texto",
            "status": {"name": "Novo"},
            "urgency": 2,
            "team": [
                {
                    "role": "requester",
                    "id": 12,
                    "display_name": "Roberio",
                    "email": "roberio@delpi.com.br",
                }
            ],
        },
        {
            "results": [
                {
                    "type": "Followup",
                    "item": {
                        "id": 9,
                        "content": "olola",
                        "user": {"id": 12, "name": "Roberio"},
                    },
                },
                {
                    "type": "Followup",
                    "item": {
                        "id": 10,
                        "content": "outro",
                        "user": {"id": 44, "name": "Roberio"},
                    },
                },
            ]
        },
    )
    same_id = apply_viewer_identity(detail, PersonIdentity(user_id=12))
    assert same_id.requester_mine is True
    assert same_id.timeline[0].mine is True
    assert same_id.timeline[1].mine is False

    same_email = apply_viewer_identity(detail, parse_viewer_identity({}, "ROBERIO@delpi.com.br"))
    assert same_email.requester_mine is True
    assert same_email.timeline[0].mine is False

    same_name_other_id = apply_viewer_identity(detail, PersonIdentity(user_id=99))
    assert same_name_other_id.requester_mine is False
    assert same_name_other_id.timeline[0].mine is False
    assert parse_viewer_identity({"user_id": -1}, "").user_id is None
    assert parse_viewer_identity({"users_id": 44}, "").user_id == 44
    assert parse_viewer_identity({"user": {"id": 51}}, "").user_id == 51
    assert parse_viewer_identity({"user_id": 12, "users_id": 99}, "").user_id == 12


def test_add_ticket_solution_and_task_force_public():
    bodies: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            bodies.append(json.loads(request.content.decode()))
            return httpx.Response(201, json={"id": 77 + len(bodies)})
        return httpx.Response(404)

    client = HttpxGlpiClient(
        base_url="https://glpi.example",
        client_id="id",
        client_secret="super-secret",
        redirect_uri="https://centraldelpi.com.br/apps/helpdesk-api/auth/glpi/callback",
        transport=httpx.MockTransport(handler),
    )
    assert client.add_ticket_solution("token", 7, "<p>sol</p>") == 78
    assert client.add_ticket_task("token", 7, "<p>task</p>") == 79
    assert bodies[0] == {"content": "<p>sol</p>", "is_private": 0}
    assert bodies[1] == {"content": "<p>task</p>", "is_private": 0}


def test_add_ticket_task_sends_hlapi_nested_fields():
    bodies: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            bodies.append(json.loads(request.content.decode()))
            return httpx.Response(201, json={"id": 90})
        return httpx.Response(404)

    client = HttpxGlpiClient(
        base_url="https://glpi.example",
        client_id="id",
        client_secret="super-secret",
        redirect_uri="https://centraldelpi.com.br/apps/helpdesk-api/auth/glpi/callback",
        transport=httpx.MockTransport(handler),
    )
    assert (
        client.add_ticket_task(
            "token",
            7,
            "<p>task</p>",
            state=1,
            duration_seconds=1800,
            category_id=4,
            user_tech_id=11,
            group_tech_id=9,
            planned_begin="2026-09-25T10:00:00",
            planned_end="2026-09-25T10:30:00",
        )
        == 90
    )
    assert bodies[0] == {
        "content": "<p>task</p>",
        "is_private": 0,
        "state": 1,
        "duration": 1800,
        "category": {"id": 4},
        "user_tech": {"id": 11},
        "group_tech": {"id": 9},
        "planned_begin": "2026-09-25T10:00:00",
        "planned_end": "2026-09-25T10:30:00",
    }


def test_add_followup_and_solution_optional_catalog_refs():
    bodies: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            bodies.append(json.loads(request.content.decode()))
            return httpx.Response(201, json={"id": 100 + len(bodies)})
        return httpx.Response(404)

    client = HttpxGlpiClient(
        base_url="https://glpi.example",
        client_id="id",
        client_secret="super-secret",
        redirect_uri="https://centraldelpi.com.br/apps/helpdesk-api/auth/glpi/callback",
        transport=httpx.MockTransport(handler),
    )
    assert client.add_followup("token", 7, "<p>fu</p>", request_type_id=3) == 101
    assert client.add_ticket_solution("token", 7, "<p>sol</p>", solution_type_id=2) == 102
    assert bodies[0] == {"content": "<p>fu</p>", "request_type": {"id": 3}}
    assert bodies[1] == {"content": "<p>sol</p>", "is_private": 0, "type": {"id": 2}}


def test_requester_falls_back_to_user_recipient():
    detail = parse_ticket_detail(
        {
            "id": 2,
            "name": "Monitor falhando",
            "content": "Máquina",
            "status": {"name": "Novo"},
            "urgency": 3,
            "date_creation": "2026-02-19T10:00:00Z",
            "user_recipient": {"display_name": "Robério Teixeira"},
        },
        {"results": []},
    )
    assert detail.requester_display_name == "Robério Teixeira"


def test_legacy_document_upload_uses_apirest_with_app_token():
    from helpdesk_app.domain.errors import GlpiFeatureDisabled

    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(f"{request.method} {request.url.path}")
        if request.url.path.endswith("/Assistance/Ticket/7"):
            return httpx.Response(200, json={"id": 7, "name": "t"})
        if request.url.path.endswith("/apirest.php/initSession"):
            assert request.headers.get("App-Token") == "app-token-x"
            assert request.headers.get("Authorization", "").startswith("user_token ")
            return httpx.Response(200, json={"session_token": "sess-1"})
        if request.url.path.endswith("/apirest.php/Document"):
            assert request.headers.get("Session-Token") == "sess-1"
            assert request.headers.get("App-Token") == "app-token-x"
            return httpx.Response(201, json={"id": 55})
        if request.url.path.endswith("/apirest.php/Document/55/Document_Item"):
            return httpx.Response(200, json=[])
        if request.url.path.endswith("/apirest.php/Document_Item"):
            assert request.headers.get("Session-Token") == "sess-1"
            body = json.loads(request.content.decode())
            assert body["input"]["documents_id"] == 55
            assert body["input"]["items_id"] == 7
            assert body["input"]["itemtype"] == "Ticket"
            return httpx.Response(201, json={"id": 1})
        if request.url.path.endswith("/apirest.php/killSession"):
            return httpx.Response(200, json={})
        return httpx.Response(404, json={"error": "missing"})

    disabled = HttpxGlpiClient(
        base_url="https://glpi.example",
        client_id="id",
        client_secret="super-secret",
        redirect_uri="https://centraldelpi.com.br/apps/helpdesk-api/auth/glpi/callback",
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(GlpiFeatureDisabled):
        disabled.upload_ticket_document(
            "oauth",
            ticket_id=7,
            filename="a.png",
            content=b"x",
            mime="image/png",
        )

    client = HttpxGlpiClient(
        base_url="https://glpi.example",
        client_id="id",
        client_secret="super-secret",
        redirect_uri="https://centraldelpi.com.br/apps/helpdesk-api/auth/glpi/callback",
        legacy_upload_enabled=True,
        legacy_app_token="app-token-x",
        legacy_user_token="user-token-x",
        transport=httpx.MockTransport(handler),
    )
    uploaded = client.upload_ticket_document(
        "oauth-access",
        ticket_id=7,
        filename="placa.png",
        content=b"png-bytes",
        mime="image/png",
    )
    assert uploaded.document_id == 55
    assert uploaded.filename == "placa.png"
    assert any("/apirest.php/Document" in item for item in calls)
    assert any("/apirest.php/Document_Item" in item for item in calls)
    assert any("killSession" in item for item in calls)


def test_legacy_cycle_accept_reject_satisfaction():
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(f"{request.method} {request.url.path}")
        if request.url.path.endswith("/Assistance/Ticket/7"):
            return httpx.Response(200, json={"id": 7, "name": "t", "status": {"id": 5}})
        if request.url.path.endswith("/apirest.php/initSession"):
            return httpx.Response(200, json={"session_token": "sess-cycle"})
        if request.url.path.endswith("/apirest.php/ITILFollowup"):
            body = json.loads(request.content.decode())
            assert body["input"]["items_id"] == 7
            assert body["input"]["itemtype"] == "Ticket"
            assert "add_close" in body["input"] or "add_reopen" in body["input"]
            return httpx.Response(201, json={"id": 1})
        if request.url.path.endswith("/apirest.php/TicketSatisfaction"):
            body = json.loads(request.content.decode())
            assert body["input"]["tickets_id"] == 7
            assert body["input"]["satisfaction"] == 4
            return httpx.Response(201, json={"id": 7})
        if request.url.path.endswith("/apirest.php/Ticket/7/TicketSatisfaction"):
            return httpx.Response(
                200,
                json=[{"id": 1, "tickets_id": 7, "satisfaction": 4, "comment": "ok"}],
            )
        if request.url.path.endswith("/apirest.php/killSession"):
            return httpx.Response(200, json={})
        return httpx.Response(404, json={"error": "missing"})

    client = HttpxGlpiClient(
        base_url="https://glpi.example",
        client_id="id",
        client_secret="super-secret",
        redirect_uri="https://centraldelpi.com.br/apps/helpdesk-api/auth/glpi/callback",
        legacy_upload_enabled=True,
        legacy_app_token="app-token-x",
        legacy_user_token="user-token-x",
        transport=httpx.MockTransport(handler),
    )
    client.accept_ticket_solution("oauth", 7, "aceito")
    client.reject_ticket_solution("oauth", 7, "recuso")
    client.submit_ticket_satisfaction("oauth", 7, satisfaction=4, comment="ok")
    assert client.get_ticket_satisfaction("oauth", 7) == (4, "ok")
    assert any("ITILFollowup" in item for item in calls)
    assert any("TicketSatisfaction" in item for item in calls)


def test_list_technician_user_ids_falls_back_to_search_user_when_profile_user_forbidden():
    """Prod GLPI: HLAPI Profile/User 404 + Profile_User 403; search/User field 20 works."""
    from helpdesk_app.infrastructure.glpi.mapping import parse_profile_user_ids

    assert parse_profile_user_ids(
        {
            "totalcount": 3,
            "data": [
                {"1": "tech", "2": 4, "20": "Technician"},
                {"1": "Michael", "2": 8, "20": "Technician"},
                {"1": "minha-delpi-upload", "2": 75, "20": "Technician"},
            ],
        }
    ) == {4, 8, 75}

    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        query = str(request.url)
        paths.append(f"{request.method} {path}")
        if "/Administration/Profile/6/User" in path:
            return httpx.Response(404, json={"error": "missing"})
        if path.endswith("/apirest.php/initSession"):
            return httpx.Response(200, json={"session_token": "sess-tech"})
        if path.endswith("/apirest.php/killSession"):
            return httpx.Response(200, json={})
        if "/Profile/6/Profile_User" in path:
            return httpx.Response(
                403,
                json=["ERROR_RIGHT_MISSING", "Você não tem permissão para executar essa ação."],
            )
        if "/search/Profile_User" in path:
            return httpx.Response(200, json={"totalcount": 0, "count": 0, "data": []})
        if "/search/User" in path:
            assert "criteria[0][field]=20" in query or "criteria%5B0%5D%5Bfield%5D=20" in query
            assert "value]=6" in query or "value%5D=6" in query
            return httpx.Response(
                200,
                json={
                    "totalcount": 3,
                    "count": 3,
                    "data": [
                        {"1": "tech", "2": 4, "20": "Technician"},
                        {"1": "Michael", "2": 8, "20": "Technician"},
                        {"1": "minha-delpi-upload", "2": 75, "20": "Technician"},
                    ],
                },
            )
        return httpx.Response(404, json={"error": "missing"})

    client = HttpxGlpiClient(
        base_url="https://glpi.example",
        client_id="id",
        client_secret="super-secret",
        redirect_uri="https://centraldelpi.com.br/apps/helpdesk-api/auth/glpi/callback",
        assignee_profile_ids=(6,),
        legacy_upload_enabled=True,
        legacy_app_token="app-token-x",
        legacy_user_token="user-token-x",
        transport=httpx.MockTransport(handler),
    )
    assert client.list_technician_user_ids("oauth") == {4, 8, 75}
    assert any("search/User" in item for item in paths)

