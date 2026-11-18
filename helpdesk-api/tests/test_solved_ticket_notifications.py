"""GLPI #1616: envio individual e pós-confirmação de solução."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from helpdesk_app.application.solved_ticket_notification_service import (
    CoreHelpdeskNotificationGateway,
    SolvedTicketNotice,
)
from helpdesk_app.domain.models import PersonIdentity
from tests.conftest import auth_headers, build_client, link

REQUESTER_UUID = "11111111-1111-4111-8111-111111111111"
OTHER_UUID = "22222222-2222-4222-8222-222222222222"


class FakeDirectory:
    def __init__(self, *, match=True):
        self.match = match

    def configured(self):
        return True

    def search_users(self, *, q, limit, browse):
        if self.match:
            return [{"id": REQUESTER_UUID, "email": q.lower(), "name": "Solicitante"}]
        return [{"id": OTHER_UUID, "email": "outra.pessoa@example.invalid", "name": "Outra"}]


class MemoryNoticeOutbox:
    def __init__(self, *, raises=False):
        self.rows = {}
        self.raises = raises

    def enqueue(self, notice):
        if self.raises:
            raise RuntimeError("outbox unavailable")
        is_new = notice.event_key not in self.rows
        self.rows.setdefault(notice.event_key, notice)
        return is_new


def configured_client(*, match=True, outbox=None):
    client, glpi = build_client(
        directory=FakeDirectory(match=match),
        solved_notifications=outbox,
    )
    glpi.detail = replace(
        glpi.detail,
        requester_identity=PersonIdentity(user_id=12),
        status_id=2,
        status="Em atendimento",
    )
    glpi.user_profiles[12] = SimpleNamespace(
        username="solicitante", firstname="Pessoa",
        realname="Solicitante", emails=("solicitante@example.invalid",),
    )
    link(client)
    return client, glpi


def test_solution_transition_enqueues_only_requester_and_replays_without_duplicate():
    outbox = MemoryNoticeOutbox()
    client, glpi = configured_client(outbox=outbox)
    headers = {**auth_headers(), "x-email": "ana.silva@delpi.com.br",
               "Idempotency-Key": "solve-1616"}
    res = client.post("/tickets/7/solutions", json={"content": "<p>Resolvido</p>"},
                      headers=headers)
    assert res.status_code == 201
    assert res.json()["status_id"] == 5
    assert len(outbox.rows) == 1
    notice = next(iter(outbox.rows.values()))
    assert notice.recipient_user_id == REQUESTER_UUID
    assert notice.ticket_id == 7
    assert notice.solution_id == res.json()["id"]
    assert notice.ticket_title == glpi.detail.title

    replay = client.post("/tickets/7/solutions",
                         json={"content": "<p>Resolvido</p>"}, headers=headers)
    assert replay.status_code == 201
    assert replay.json() == res.json()
    assert len(outbox.rows) == 1
    assert len(glpi.solutions) == 1


def test_unresolved_requester_never_notifies_an_unrelated_person():
    outbox = MemoryNoticeOutbox()
    client, _glpi = configured_client(match=False, outbox=outbox)
    headers = {**auth_headers(), "x-email": "ana.silva@delpi.com.br",
               "Idempotency-Key": "solve-unresolved"}
    res = client.post("/tickets/7/solutions",
                      json={"content": "Resolvido"}, headers=headers)
    assert res.status_code == 201
    assert outbox.rows == {}


def test_notification_storage_failure_does_not_undo_confirmed_glpi_solution():
    outbox = MemoryNoticeOutbox(raises=True)
    client, glpi = configured_client(outbox=outbox)
    headers = {**auth_headers(), "x-email": "ana.silva@delpi.com.br",
               "Idempotency-Key": "solve-storage-failed"}
    res = client.post("/tickets/7/solutions",
                      json={"content": "Resolvido"}, headers=headers)
    assert res.status_code == 201
    assert glpi.detail.status_id == 5


def test_payload_is_private_and_links_to_real_helpdesk_ticket():
    notice = SolvedTicketNotice(
        ticket_id=1616, solution_id=50,
        recipient_user_id=REQUESTER_UUID,
        ticket_title="Problema no Outlook",
    )
    payload = notice.payload()
    assert payload["sourceApp"] == "helpdesk"
    assert payload["category"] == "helpdesk_ticket_solved"
    assert payload["userIds"] == [REQUESTER_UUID]
    assert "permissionCodes" not in payload and "broadcast" not in payload
    assert payload["action"] == {
        "type": "portal_route", "label": "Ver solução",
        "target": "/apps/helpdesk/tickets/1616",
    }
    assert payload["metadata"]["dedupeKey"] == "helpdesk:ticket-solved:1616:50"


def test_gateway_reuses_core_api_and_retries_transient_failures():
    posts = []
    status = {"code": 201}

    def fake_post(url, **kwargs):
        posts.append((url, kwargs))
        return SimpleNamespace(status_code=status["code"])
    notice = SolvedTicketNotice(7, 50, REQUESTER_UUID, "Chamado")
    gateway = CoreHelpdeskNotificationGateway(
        core_api_url="http://core-api:8000", service_token="fake-token",
        http_post=fake_post,
    )
    assert gateway.send(notice) == "sent"
    url, request = posts[-1]
    assert url == "http://core-api:8000/integrations/notifications"
    assert request["headers"]["Authorization"] == "Bearer fake-token"
    assert request["json"]["userIds"] == [REQUESTER_UUID]
    status["code"] = 503
    assert gateway.send(notice) == "retry"
    status["code"] = 422
    assert gateway.send(notice) == "ignored"
    assert CoreHelpdeskNotificationGateway(service_token="").send(notice) == "retry"


def test_invalid_glpi_recipient_cannot_be_used_as_portal_user():
    with pytest.raises(ValueError):
        SolvedTicketNotice(7, 50, "12", "Chamado")


def test_new_solution_can_be_notified_only_after_status_transition():
    outbox = MemoryNoticeOutbox()
    client, glpi = configured_client(outbox=outbox)
    glpi.detail = replace(glpi.detail, status_id=5, status="Solucionado")
    headers = {**auth_headers(), "x-email": "ana.silva@delpi.com.br",
               "Idempotency-Key": "solved-earlier"}
    res = client.post("/tickets/7/solutions",
                      json={"content": "Complemento"}, headers=headers)
    assert res.status_code in (201, 403, 422)
    assert outbox.rows == {}
