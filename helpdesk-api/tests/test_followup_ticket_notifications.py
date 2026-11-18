"""#1618: notificações apenas para retornos públicos confirmados de terceiros."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from helpdesk_app.application.followup_ticket_notification_service import (
    FollowupTicketNotice, preview_from_html,
)
from helpdesk_app.application.solved_ticket_notification_service import CoreHelpdeskNotificationGateway
from helpdesk_app.domain.models import PersonIdentity
from tests.conftest import FakeGlpi, auth_headers, build_client, link

UUID_REQUESTER = "11111111-1111-4111-8111-111111111111"
UUID_OTHER = "22222222-2222-4222-8222-222222222222"


class Directory:
    def __init__(self, match=True):
        self.match = match

    def configured(self):
        return True

    def search_users(self, *, q, limit, browse):
        if self.match:
            return [{"id": UUID_REQUESTER, "email": q.lower()}]
        return [{"id": UUID_OTHER, "email": "other@example.invalid"}]


class Outbox:
    def __init__(self, raises=False):
        self.rows = {}
        self.raises = raises

    def enqueue(self, notice):
        if self.raises:
            raise RuntimeError("outbox offline")
        fresh = notice.event_key not in self.rows
        self.rows.setdefault(notice.event_key, notice)
        return fresh


class VerifiedGlpi(FakeGlpi):
    def __init__(self, *, author_verified=True, readback_visible=True):
        super().__init__()
        self.session_uid = 15
        self.author_verified = author_verified
        self.readback_visible = readback_visible

    def add_followup(self, access_token, ticket_id, content, *, request_type_id=None):
        followup_id = super().add_followup(
            access_token, ticket_id, content, request_type_id=request_type_id
        )
        if self.readback_visible:
            self.detail = replace(
                self.detail,
                timeline=tuple(
                    replace(
                        entry,
                        author_identity=PersonIdentity(
                            user_id=self.session_uid if self.author_verified else None
                        ),
                    ) if entry.kind == "followup" and entry.id == followup_id
                    else entry for entry in self.detail.timeline
                ),
            )
        else:
            self.detail = replace(
                self.detail,
                timeline=tuple(
                    row for row in self.detail.timeline
                    if not (row.kind == "followup" and row.id == followup_id)
                ),
            )
        return followup_id


def setup(*, glpi=None, match=True, outbox=None):
    glpi = glpi or VerifiedGlpi()
    glpi.detail = replace(
        glpi.detail, requester_identity=PersonIdentity(user_id=12),
        status_id=2, status="Em atendimento",
    )
    glpi.user_profiles[12] = SimpleNamespace(
        username="requester", firstname="Pessoa",
        realname="Solicitante", emails=("requester@example.invalid",),
    )
    client, _glpi = build_client(
        glpi=glpi, directory=Directory(match=match),
        followup_notifications=outbox,
    )
    link(client)
    return client, glpi


def post(client, key="fu-1", body="<p>Favor verificar a impressora.</p>"):
    return client.post(
        "/tickets/7/followups",
        json={"content": body},
        headers={
            **auth_headers(), "x-email": "ana.silva@delpi.com.br",
            "Idempotency-Key": key,
        },
    )


def test_new_followup_notifies_only_requester_and_replay_deduplicates():
    outbox = Outbox()
    client, glpi = setup(outbox=outbox)
    first = post(client)
    assert first.status_code == 201
    assert len(outbox.rows) == 1
    notice = next(iter(outbox.rows.values()))
    assert notice.ticket_id == 7 and notice.followup_id == first.json()["id"]
    assert notice.recipient_user_id == UUID_REQUESTER
    assert notice.preview == "Favor verificar a impressora."
    assert notice.event_key == "helpdesk:ticket-followup:7:8"
    payload = notice.payload()
    assert payload["userIds"] == [UUID_REQUESTER]
    assert payload["category"] == "helpdesk_ticket_followup"
    assert payload["sourceApp"] == "helpdesk"
    assert payload["action"] == {
        "type": "portal_route", "label": "Ver retorno",
        "target": "/apps/helpdesk/tickets/7",
    }
    assert "permissionCodes" not in payload and "broadcast" not in payload
    assert payload["metadata"]["dedupeKey"] == notice.event_key
    replay = post(client)
    assert replay.status_code == 201 and replay.json() == first.json()
    assert len(glpi.followups) == 1 and len(outbox.rows) == 1


def test_requester_own_followup_never_notifies():
    outbox = Outbox()
    glpi = VerifiedGlpi()
    glpi.session_uid = 12
    client, _glpi = setup(glpi=glpi, outbox=outbox)
    assert post(client).status_code == 201
    assert outbox.rows == {}


@pytest.mark.parametrize("glpi", [
    VerifiedGlpi(author_verified=False),
    VerifiedGlpi(readback_visible=False),
])
def test_no_notice_without_authoritative_public_readback(glpi):
    outbox = Outbox()
    client, _glpi = setup(glpi=glpi, outbox=outbox)
    assert post(client).status_code == 201
    assert outbox.rows == {}


def test_no_notification_for_unresolved_portal_user():
    outbox = Outbox()
    client, _glpi = setup(match=False, outbox=outbox)
    assert post(client).status_code == 201
    assert outbox.rows == {}


def test_outbox_failure_does_not_undo_glpi_followup():
    outbox = Outbox(raises=True)
    client, glpi = setup(outbox=outbox)
    assert post(client).status_code == 201
    assert len(glpi.followups) == 1


def test_followup_edit_does_not_generate_notification():
    outbox = Outbox()
    client, _glpi = setup(outbox=outbox)
    response = client.put(
        "/tickets/7/followups/8",
        json={"content": "<p>Corrigido</p>"},
        headers={
            **auth_headers(), "x-email": "ana.silva@delpi.com.br",
            "Idempotency-Key": "edit-8",
        },
    )
    assert response.status_code in (200, 201, 207)
    assert outbox.rows == {}


def test_preview_is_short_plain_text_not_html():
    html = "<p>Bom dia &amp; obrigado.</p><p>Verifique as informações</p>"
    assert preview_from_html(html) == "Bom dia & obrigado. Verifique as informações"
    sample = preview_from_html("<p>" + ("A" * 240) + "</p>")
    assert len(sample) == 160 and sample.endswith("…")
    assert "<" not in preview_from_html("<b>Olá</b>")
    assert preview_from_html("<p><img src='/app/img'/></p>") == ""


def test_invalid_glpi_user_is_not_a_core_recipient():
    with pytest.raises(ValueError):
        FollowupTicketNotice(7, 8, "12", "Título", "Retorno")


def test_reuses_core_notification_gateway():
    notice = FollowupTicketNotice(7, 8, UUID_REQUESTER, "Chamado", "Olá")
    calls = []

    def fake_post(url, **kwargs):
        calls.append({"url": url, **kwargs})
        return SimpleNamespace(status_code=201)

    gateway = CoreHelpdeskNotificationGateway(
        core_api_url="http://core-api:8000", service_token="token", http_post=fake_post,
    )
    assert gateway.send(notice) == "sent"
    assert calls[0]["json"]["category"] == "helpdesk_ticket_followup"
    assert calls[0]["json"]["userIds"] == [UUID_REQUESTER]
