import httpx

from helpdesk_app.domain.errors import GlpiUnavailable
from helpdesk_app.infrastructure.glpi.http_client import HttpxGlpiClient
from helpdesk_app.infrastructure.glpi.mapping import parse_categories, parse_ticket_detail


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
    listed = client.list_tickets("token")
    assert listed == []
    assert calls["get"] == 3


def test_authorization_url_keeps_state_across_glpi_login():
    client = HttpxGlpiClient(
        base_url="https://helpdesk.example",
        client_id="client",
        client_secret="super-secret",
        redirect_uri="https://centraldelpi.com.br/apps/helpdesk-api/auth/glpi/callback",
    )
    url = client.authorization_url(state="abc_DEF-123", code_challenge="challenge")
    assert url.startswith("https://helpdesk.example/?redirect=")
    inner = url.split("redirect=", 1)[1]
    assert "api.php%2Fauthorize" in inner
    assert "state%3Dabc_DEF-123" in inner
    assert "code_challenge%3Dchallenge" in inner
    assert "code_challenge_method%3DS256" in inner
    assert inner.startswith("https%3A%2F%2Fhelpdesk.example%2Fapi.php%2Fauthorize")


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
    assert [entry.kind for entry in detail.timeline] == ["followup"]
    categories = parse_categories({"results": [{"id": 2, "completename": "TI > Rede"}]})
    assert categories[0].name == "TI > Rede"
