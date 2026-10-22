"""Leitura institucional do sumário: fail-closed, sem fallback de upload."""

from __future__ import annotations

import httpx
import pytest

from delpi_auth.service_identity import ServiceIdentity
from helpdesk_app.application.dashboard_reader_gate import (
    load_dashboard_reader_config,
    reader_is_ready,
)
from helpdesk_app.domain.models import TicketListQuery, TicketSummary
from helpdesk_app.infrastructure.glpi.dashboard_reader_mapping import (
    map_dashboard_reader_page,
    parse_sla_ttr_exceeded,
)
from helpdesk_app.infrastructure.glpi.http_client import HttpxGlpiClient
from tests.conftest import auth_headers, build_client, link


def _ready_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GLPI_DASHBOARD_READER_ENABLED", "true")
    monkeypatch.setenv("GLPI_DASHBOARD_READER_APP_TOKEN", "reader-app")
    monkeypatch.setenv("GLPI_DASHBOARD_READER_USER_TOKEN", "reader-user")
    monkeypatch.setenv("GLPI_DASHBOARD_READER_ENTITY_IDS", "1")
    monkeypatch.setenv("GLPI_DASHBOARD_READER_GROUP_IDS", "")
    monkeypatch.setenv("GLPI_DASHBOARD_READER_ALLOW_ROOT", "false")
    monkeypatch.setenv("GLPI_LEGACY_USER_TOKEN", "upload-user")
    monkeypatch.setenv("GLPI_PROFILE_SYNC_USER_TOKEN", "sync-user")


def test_reader_stays_unavailable_until_entity_allowlist_is_set(monkeypatch):
    monkeypatch.delenv("GLPI_DASHBOARD_READER_ENABLED", raising=False)
    monkeypatch.delenv("GLPI_DASHBOARD_READER_ENTITY_IDS", raising=False)
    assert reader_is_ready(load_dashboard_reader_config()) is False


def test_root_entity_is_refused_without_explicit_override(monkeypatch):
    _ready_env(monkeypatch)
    monkeypatch.setenv("GLPI_DASHBOARD_READER_ENTITY_IDS", "0")
    assert reader_is_ready(load_dashboard_reader_config()) is False
    monkeypatch.setenv("GLPI_DASHBOARD_READER_ALLOW_ROOT", "true")
    assert reader_is_ready(load_dashboard_reader_config()) is True


def test_upload_token_is_not_accepted_as_reader(monkeypatch):
    _ready_env(monkeypatch)
    monkeypatch.setenv("GLPI_DASHBOARD_READER_USER_TOKEN", "upload-user")
    assert reader_is_ready(load_dashboard_reader_config()) is False


def test_superadmin_service_without_scope_does_not_list(monkeypatch):
    client, glpi = build_client()
    identity = ServiceIdentity(
        client_id="tv-dashboard-api",
        subject="svc",
        scopes=frozenset(),
        audience=("api-delpi",),
        issuer="https://issuer",
    )
    monkeypatch.setattr(
        "helpdesk_app.application.dashboard_reader_gate.load_dashboard_service_identity",
        lambda request: identity,
    )
    response = client.get(
        "/tickets",
        headers={
            **auth_headers("internal-service"),
            "x-principal-type": "service",
            "x-superadmin": "1",
            "X-Delpi-Service-Authorization": "Bearer not-a-grant",
        },
    )
    assert response.status_code == 403
    assert response.json()["error"] == "institutional_read_denied"
    assert glpi.calls == 0
    assert glpi.reader_calls == 0


def test_authorized_service_without_allowlist_does_not_call_glpi(monkeypatch):
    client, glpi = build_client()
    identity = ServiceIdentity(
        client_id="tv-dashboard-api",
        subject="svc",
        scopes=frozenset({"helpdesk.dashboard.read"}),
        audience=("api-delpi",),
        issuer="https://issuer",
    )
    monkeypatch.setattr(
        "helpdesk_app.application.dashboard_reader_gate.load_dashboard_service_identity",
        lambda request: identity,
    )
    monkeypatch.delenv("GLPI_DASHBOARD_READER_ENABLED", raising=False)
    response = client.get(
        "/tickets",
        headers={
            **auth_headers("internal-service"),
            "x-principal-type": "service",
            "x-superadmin": "1",
            "X-Delpi-Service-Authorization": "Bearer scoped",
        },
    )
    assert response.status_code == 503
    assert response.json()["error"] == "institutional_reader_unavailable"
    assert glpi.calls == 0
    assert glpi.reader_calls == 0


def test_human_header_does_not_switch_to_the_reader():
    client, glpi = build_client()
    link(client)
    glpi.tickets = []
    response = client.get(
        "/tickets",
        headers={**auth_headers(), "X-Delpi-Service-Authorization": "Bearer scoped"},
    )
    assert response.status_code == 200
    assert glpi.reader_calls == 0
    assert glpi.calls == 1


def test_individual_ticket_ignores_the_reader_header():
    client, glpi = build_client()
    response = client.get(
        "/tickets/7",
        headers={
            **auth_headers("internal-service"),
            "x-principal-type": "service",
            "x-superadmin": "1",
            "X-Delpi-Service-Authorization": "Bearer scoped",
        },
    )
    assert response.status_code == 409
    assert response.json()["error"] == "glpi_link_required"
    assert glpi.reader_calls == 0


def test_ready_reader_filters_entities_and_does_not_use_upload_token():
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST" and request.url.path.endswith("/changeActiveEntities"):
            assert "entities_id" not in (request.content.decode() if request.content else "")
            return httpx.Response(200, json=[])
        if request.method != "GET":
            return httpx.Response(405)
        if request.url.path.endswith("/getFullSession"):
            return httpx.Response(200, json={"session": {"glpiactiveentities": [1]}})
        if request.url.path.endswith("/initSession"):
            assert request.headers.get("App-Token") == "reader-app"
            assert request.headers.get("Authorization") == "user_token reader-user"
            return httpx.Response(200, json={"session_token": "sess"})
        if request.url.path.endswith("/killSession"):
            return httpx.Response(200, json={})
        if request.url.path.endswith("/search/Ticket"):
            assert request.url.params["criteria[0][field]"] == "2"
            assert request.url.params["criteria[0][value]"] == "10"
            assert request.url.params["forcedisplay[1]"] == "82"
            return httpx.Response(200, json={"data": [{"2": 10, "82": 1, "159": 0}]})
        seen["app"] = request.headers.get("App-Token") or ""
        seen["session"] = request.headers.get("Session-Token") or ""
        return httpx.Response(
            206,
            json=[
                {
                    "id": 10,
                    "name": "na filial",
                    "status": 1,
                    "date": "2026-10-02 10:00:00",
                    "solvedate": None,
                    "closedate": None,
                    "date_mod": "2026-10-03 10:00:00",
                    "time_to_own": "2026-10-04 10:00:00",
                    "time_to_resolve": None,
                    "entities_id": 1,
                },
                {
                    "id": 11,
                    "name": "outra filial",
                    "status": 2,
                    "date": "2026-10-02 11:00:00",
                    "entities_id": 2,
                },
            ],
            headers={"Content-Range": "0-1/2"},
        )

    transport = httpx.MockTransport(handler)
    client = HttpxGlpiClient(
        base_url="http://glpi.test",
        client_id="minha-delpi-helpdesk",
        client_secret="secret",
        redirect_uri="https://centraldelpi.com.br/callback",
        legacy_app_token="upload-app",
        legacy_user_token="upload-user",
        transport=transport,
    )
    page = client.list_tickets_as_dashboard_reader(
        TicketListQuery(page=1, page_size=50),
        app_token="reader-app",
        user_token="reader-user",
        entity_ids=(1,),
        group_ids=(),
    )
    assert seen["app"] == "reader-app"
    assert seen["session"] == "sess"
    assert [item.id for item in page.items] == [10]
    assert page.items[0].status_id == 1
    assert page.items[0].created_at == "2026-10-02 10:00:00"
    assert page.items[0].sla_tto == "2026-10-04 10:00:00"
    assert page.items[0].sla_ttr_exceeded is True
    assert page.has_more is False


def test_ready_route_uses_reader_page_not_personal_oauth(monkeypatch):
    _ready_env(monkeypatch)
    client, glpi = build_client()
    glpi.tickets = [
        TicketSummary(id=10, title="t", status="new", category="", urgency="", updated_at="", status_id=1)
    ]
    identity = ServiceIdentity(
        client_id="tv-dashboard-api",
        subject="svc",
        scopes=frozenset({"helpdesk.dashboard.read"}),
        audience=("api-delpi",),
        issuer="https://issuer",
    )
    monkeypatch.setattr(
        "helpdesk_app.application.dashboard_reader_gate.load_dashboard_service_identity",
        lambda request: identity,
    )
    response = client.get(
        "/tickets",
        headers={
            **auth_headers("internal-service"),
            "x-principal-type": "service",
            "X-Delpi-Service-Authorization": "Bearer scoped",
        },
    )
    assert response.status_code == 200
    assert response.json()["items"][0]["id"] == 10
    assert response.json()["items"][0]["status_id"] == 1
    assert glpi.calls == 0
    assert glpi.reader_calls == 1
    assert glpi.last_reader_kwargs["user_token"] == "reader-user"
    assert glpi.last_reader_kwargs["entity_ids"] == (1,)


def test_allowed_entities_alias_keeps_exact_ids(monkeypatch):
    _ready_env(monkeypatch)
    monkeypatch.delenv("GLPI_DASHBOARD_READER_ENTITY_IDS", raising=False)
    monkeypatch.setenv("GLPI_DASHBOARD_READER_ALLOWED_ENTITIES", "0,1,2")
    monkeypatch.setenv("GLPI_DASHBOARD_READER_ALLOW_ROOT", "true")
    config = load_dashboard_reader_config()
    assert config.entity_ids == (0, 1, 2)
    assert reader_is_ready(config) is True


def test_reader_page_keeps_only_allowlisted_entities_without_group_filter():
    kept, has_more = map_dashboard_reader_page(
        [
            {"id": 1, "entities_id": 0, "status": 1, "groups_id": 2, "date": "2026-10-01 00:00:00"},
            {"id": 1, "entities_id": 0, "status": 1},
            {"id": 2, "entities_id": 1, "status": 2, "groups_id": 9},
            {"id": 3, "entities_id": 2, "status": 4},
            {"id": 4, "entities_id": 3, "status": 1},
        ],
        content_range="0-4/9",
        entity_ids=(0, 1, 2),
        group_ids=(),
        page_size=5,
    )
    assert [item["id"] for item in kept] == [1, 2, 3]
    assert has_more is True


def test_personal_unlink_stays_409():
    client, glpi = build_client()
    response = client.get("/tickets", headers=auth_headers("user-b"))
    assert response.status_code == 409
    assert response.json()["error"] == "glpi_link_required"
    assert glpi.reader_calls == 0


def test_parse_sla_ttr_exceeded_uses_only_field_82():
    flags = parse_sla_ttr_exceeded(
        {"data": [{"2": "10", "82": 1, "159": 0}, {"2": 11, "82": 0}, {"2": 12, "159": 1}]},
        (10, 11, 12),
    )
    assert flags == {10: True, 11: False}
    assert parse_sla_ttr_exceeded([], (10,)) == {}
