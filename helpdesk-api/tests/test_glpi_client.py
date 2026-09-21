from urllib.parse import unquote

import httpx
import pytest

from helpdesk_app.domain.errors import GlpiUnavailable
from helpdesk_app.infrastructure.glpi.http_client import HttpxGlpiClient
from helpdesk_app.infrastructure.glpi.mapping import (
    build_ticket_list_query,
    parse_categories,
    parse_ticket_detail,
    parse_ticket_list,
)
from helpdesk_app.domain.errors import GlpiValidation


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


def test_mapping_keeps_followups_and_hides_tasks():
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
    assert [entry.kind for entry in detail.timeline] == ["followup"]
    categories = parse_categories({"results": [{"id": 2, "completename": "TI > Rede"}]})
    assert categories[0].name == "TI > Rede"


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
    assert detail.timeline[0].content == "Máquina ligada"
    assert detail.category == ""


def test_mapping_keeps_text_that_is_already_utf8():
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


def test_mapping_keeps_followup_and_document_and_hides_task():
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
    assert [entry.content for entry in detail.timeline] == ["Cabo ok"]
    assert detail.attachments == (
        Attachment(2, "logo.png", "image/png"),
        Attachment(4, "foto.jpg", "image/jpeg"),
    )
    assert attachment_filename("../segredo.txt") == "segredo.txt"
    assert attachment_filename("   ") == "anexo"


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
    assert [entry.content for entry in detail.timeline] == ["Público"]


def test_list_query_uses_rsql_and_rejects_injection():
    query = build_ticket_list_query(
        q="Monitor;status==1",
        status="open",
        urgency_id=3,
        category_id=8,
        updated_from="2026-02-01",
        updated_to="2026-02-28",
        sort="created_at:asc",
        page=2,
        page_size=20,
    )
    assert "status==1" not in query.filter
    assert "name=like=*Monitorstatus1*" in query.filter
    assert "status.id=in=(1,10,2,3,4)" in query.filter
    assert "urgency==3" in query.filter
    assert "category.id==8" in query.filter
    assert query.sort == "date_creation:asc"
    assert query.start == 20
    assert query.limit == 21
    with pytest.raises(GlpiValidation):
        build_ticket_list_query(status="admin")
    with pytest.raises(GlpiValidation):
        build_ticket_list_query(sort="entity:desc")


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
                "team": [{"role": "assigned", "firstname": "Ana", "realname": "Silva"}],
            }
        ]
    )
    assert listed[0].created_at == "2026-02-19T10:00:00Z"
    assert listed[0].assigned_display_name == "Ana Silva"
    assert listed[0].category == ""


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
