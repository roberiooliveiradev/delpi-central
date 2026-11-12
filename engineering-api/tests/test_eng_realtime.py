"""ENG-REALTIME-01 — WebSocket transversal da Engineering API (PRC).

Cobre handshake AuthN fail-closed, subscribe com AuthZ por objeto,
ACKs, ping, publicação pós-commit, ausência de evento em replay/
falha, revogação por objeto em conexão ativa e feature flag.
"""

from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from tests.conftest import rbac_payload
from tests.test_product_registration import (  # noqa: F401
    _create_body,
    _post,
    _token,
    prc_service_repo,
)

from engineering_app.application.services.engineering_realtime_hub import (
    engineering_realtime_hub,
)
from engineering_app.application.services.engineering_realtime_notify import (
    event_rooms,
    event_payload,
    queue_room,
    resource_room,
    user_room,
)
from engineering_app.application.ports.realtime import RealtimeEvent
from engineering_app.config import settings
from engineering_app.main import app

ENG_ACCESS = "engineering.access"
MR_PERMS = [
    "my-requests.access",
    "my-requests.raw-material-creation.create",
]
ANALYST_SUB = "analyst-1"
REQUESTER_SUB = "user-1"
THIRD_SUB = "third-1"

WS_URL = "/v1/realtime/ws"


def _set_rbac(core_rbac, permissions, sub):
    core_rbac["behavior"] = ("data", rbac_payload(permissions, id=sub))


def _ws_url(token: str, client_id: str = "c-1") -> str:
    return f"{WS_URL}?token={token}&client_id={client_id}"


@pytest.fixture
def prc_realtime_service(prc_service_repo):
    """Service do harness + publisher real (notifier → hub)."""
    from engineering_app.composition import prc_composer
    from engineering_app.application.services.engineering_realtime_notify import (  # noqa: E501
        engineering_realtime_notifier,
    )
    from engineering_app.application.use_cases.product_registration.service import (  # noqa: E501
        ProductRegistrationService,
    )
    from engineering_app.infrastructure.storage.prc_attachment_storage import (  # noqa: E501
        MemoryAttachmentStorage,
    )

    repo = prc_service_repo["repo"]
    prc_composer.set_prc_service_for_tests(
        ProductRegistrationService(
            repo,
            realtime_publisher=engineering_realtime_notifier,
            attachment_storage=MemoryAttachmentStorage(),
        )
    )
    yield prc_service_repo
    prc_composer.set_prc_service_for_tests(
        ProductRegistrationService(
            repo, attachment_storage=MemoryAttachmentStorage()
        )
    )


def _create_case(client, jwks_env, core_rbac, sub=REQUESTER_SUB) -> str:
    _set_rbac(core_rbac, MR_PERMS, sub)
    tok = _token(jwks_env, sub)
    resp = _post(
        client,
        "/v1/product-registration/intake/requests",
        tok,
        json=_create_body(source="my-requests"),
        headers={"Idempotency-Key": f"idem-{sub}-rt1"},
    )
    assert resp.status_code in (200, 201), resp.text
    return resp.json()["data"]["requestId"]


def _start_case(client, jwks_env, core_rbac, rid: str) -> None:
    _set_rbac(core_rbac, [ENG_ACCESS], ANALYST_SUB)
    tok = _token(jwks_env, ANALYST_SUB)
    detail = client.get(
        f"/v1/product-registration/requests/{rid}",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert detail.status_code == 200, detail.text
    version = detail.json()["data"]["caseVersion"]
    resp = _post(
        client,
        f"/v1/product-registration/requests/{rid}/actions/start",
        tok,
        json={"expectedVersion": version},
        headers={"Idempotency-Key": "idem-start-rt1"},
    )
    assert resp.status_code == 200, resp.text


class _WsSession:
    def __init__(self, client: TestClient):
        self._client = client

    def connect(self, token: str, client_id: str = "c-1"):
        return self._client.websocket_connect(_ws_url(token, client_id))


class TestHandshakeAuthN:
    def test_no_token_rejected(self, client):
        with pytest.raises(Exception):
            with client.websocket_connect(WS_URL):
                pass

    def test_invalid_token_rejected(
        self, client, jwks_env, core_rbac
    ):
        bad = jwks_env["make_wrong_key_token"](sub="x")
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(_ws_url(bad)):
                pass

    def test_no_permission_rejected(
        self, client, jwks_env, core_rbac
    ):
        _set_rbac(core_rbac, [], "noperm-1")
        tok = _token(jwks_env, "noperm-1")
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(_ws_url(tok)):
                pass

    def test_analyst_connects_and_pings(
        self, client, jwks_env, core_rbac
    ):
        _set_rbac(core_rbac, [ENG_ACCESS], ANALYST_SUB)
        tok = _token(jwks_env, ANALYST_SUB)
        with client.websocket_connect(_ws_url(tok)) as ws:
            hello = ws.receive_json()
            assert hello["type"] == "connected"
            assert user_room(ANALYST_SUB) in hello["roomKeys"]
            assert queue_room("product-registration") in hello["roomKeys"]
            ws.send_text("ping")
            assert ws.receive_json()["type"] == "pong"

    def test_requester_has_no_queue_room(
        self, client, jwks_env, core_rbac
    ):
        _set_rbac(core_rbac, MR_PERMS, REQUESTER_SUB)
        tok = _token(jwks_env, REQUESTER_SUB)
        with client.websocket_connect(_ws_url(tok)) as ws:
            hello = ws.receive_json()
            assert hello["type"] == "connected"
            assert user_room(REQUESTER_SUB) in hello["roomKeys"]
            assert (
                queue_room("product-registration")
                not in hello["roomKeys"]
            )


class TestSubscriptionAuthZ:
    def test_subscribe_own_case(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _create_case(client, jwks_env, core_rbac)
        _set_rbac(core_rbac, MR_PERMS, REQUESTER_SUB)
        tok = _token(jwks_env, REQUESTER_SUB)
        with client.websocket_connect(_ws_url(tok)) as ws:
            ws.receive_json()  # connected
            ws.send_json(
                {
                    "type": "subscribe",
                    "domain": "product-registration",
                    "resourceType": "request",
                    "resourceId": rid,
                }
            )
            ack = ws.receive_json()
            assert ack["type"] == "subscribed"
            assert ack["resourceId"] == rid
            assert ack["roomKey"] == resource_room(
                "product-registration", rid
            )

    def test_third_party_denied(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _create_case(client, jwks_env, core_rbac)
        _set_rbac(core_rbac, MR_PERMS, THIRD_SUB)
        tok = _token(jwks_env, THIRD_SUB)
        with client.websocket_connect(_ws_url(tok)) as ws:
            ws.receive_json()
            ws.send_json(
                {
                    "type": "subscribe",
                    "domain": "product-registration",
                    "resourceType": "request",
                    "resourceId": rid,
                }
            )
            ack = ws.receive_json()
            assert ack["type"] == "error"
            assert ack["code"] == "accessDenied"

    def test_invalid_resource_id(
        self, client, jwks_env, core_rbac
    ):
        _set_rbac(core_rbac, MR_PERMS, REQUESTER_SUB)
        tok = _token(jwks_env, REQUESTER_SUB)
        with client.websocket_connect(_ws_url(tok)) as ws:
            ws.receive_json()
            ws.send_json(
                {
                    "type": "subscribe",
                    "domain": "product-registration",
                    "resourceId": "not-a-uuid",
                }
            )
            ack = ws.receive_json()
            assert ack["type"] == "error"
            assert ack["code"] == "resourceIdInvalid"

    def test_unsupported_domain(self, client, jwks_env, core_rbac):
        _set_rbac(core_rbac, MR_PERMS, REQUESTER_SUB)
        tok = _token(jwks_env, REQUESTER_SUB)
        with client.websocket_connect(_ws_url(tok)) as ws:
            ws.receive_json()
            ws.send_json(
                {
                    "type": "subscribe",
                    "domain": "nonconformity",
                    "resourceId":
                        "123e4567-e89b-12d3-a456-426614174000",
                }
            )
            ack = ws.receive_json()
            assert ack["type"] == "error"
            assert ack["code"] == "domainUnsupported"

    def test_feature_flag_disabled(
        self, client, jwks_env, core_rbac, monkeypatch
    ):
        monkeypatch.setattr(settings, "ENG_REALTIME_ENABLED", False)
        _set_rbac(core_rbac, [ENG_ACCESS], ANALYST_SUB)
        tok = _token(jwks_env, ANALYST_SUB)
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(_ws_url(tok)):
                pass


class TestPostCommitPublish:
    """Eventos fluem pelo hub com lifespan real (TestClient ctx)."""

    def test_requester_receives_start_event_and_revocation(
        self, client, jwks_env, core_rbac, prc_realtime_service
    ):
        """Recepção de evento pós-commit + revogação por objeto em
        conexão ativa: o authorizer por-entrega barra o evento quando o
        escopo do caso deixa de incluir o assinante."""
        rid = _create_case(client, jwks_env, core_rbac)
        _set_rbac(core_rbac, MR_PERMS, REQUESTER_SUB)
        tok = _token(jwks_env, REQUESTER_SUB)
        with client.websocket_connect(_ws_url(tok)) as ws:
            hello = ws.receive_json()
            assert hello["type"] == "connected"
            ws.send_json(
                {
                    "type": "subscribe",
                    "domain": "product-registration",
                    "resourceType": "request",
                    "resourceId": rid,
                }
            )
            assert ws.receive_json()["type"] == "subscribed"

            _start_case(client, jwks_env, core_rbac, rid)

            event = ws.receive_json()
            assert event["type"] == "engineering.resource.changed"
            assert event["domain"] == "product-registration"
            assert event["resourceType"] == "request"
            assert event["resourceId"] == rid
            assert event["reason"] == "start"
            assert event["status"] == "in_progress"
            assert event["eventId"]
            assert event["occurredAt"]
            # Payload leve: sem dados de ficha/fornecedores
            assert "suppliers" not in event
            assert "technicalData" not in event

            # --- Revogação por objeto em conexão ativa -----------------
            repo = prc_realtime_service["repo"]
            # get_request devolve deepcopy — a revogação simulada muda
            # o store interno (harness in-memory).
            request = repo._requests[rid]
            request["requester_subject"] = "someone-else"
            request["assigned_to_subject"] = None

            # Broadcast direto na sala do caso — o authorizer deve
            # barrar a entrega e remover a assinatura.
            revoked_event = RealtimeEvent(
                domain="product-registration",
                resource_type="request",
                resource_id=rid,
                reason="resume",
                occurred_at="2026-11-12T00:00:00Z",
                event_id="evt-rev-1",
                queue_impact=False,
            )
            engineering_realtime_hub.schedule_broadcast_rooms(
                [resource_room("product-registration", rid)],
                event_payload(revoked_event),
            )
            time.sleep(0.5)
            ws.send_text("ping")
            assert ws.receive_json()["type"] == "pong"

            # Assinatura removida: mesmo revertendo o escopo, a sala já
            # não contém o socket — nada novo deve chegar.
            request["requester_subject"] = REQUESTER_SUB
            engineering_realtime_hub.schedule_broadcast_rooms(
                [resource_room("product-registration", rid)],
                event_payload(revoked_event),
            )
            time.sleep(0.5)
            ws.send_text("ping")
            assert ws.receive_json()["type"] == "pong"


class TestEmitContract:
    def test_no_event_on_replay(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        """Replay idempotente não reemite (a mutação não ocorreu de
        novo — o store retorna antes)."""
        events: list[RealtimeEvent] = []

        class _Capture:
            def publish(self, event: RealtimeEvent) -> None:
                events.append(event)

        # Reconstroi service com publisher capturador.
        from engineering_app.composition import prc_composer
        from engineering_app.application.use_cases.product_registration.service import (  # noqa: E501
            ProductRegistrationService,
        )

        repo = prc_service_repo["repo"]
        prc_composer.set_prc_service_for_tests(
            ProductRegistrationService(repo, realtime_publisher=_Capture())
        )
        try:
            _set_rbac(core_rbac, MR_PERMS, REQUESTER_SUB)
            tok = _token(jwks_env, REQUESTER_SUB)
            body = _create_body(source="my-requests")
            headers = {"Idempotency-Key": "idem-replay-1"}
            r1 = _post(
                client,
                "/v1/product-registration/intake/requests",
                tok,
                json=body,
                headers=headers,
            )
            assert r1.status_code in (200, 201), r1.text
            r2 = _post(
                client,
                "/v1/product-registration/intake/requests",
                tok,
                json=body,
                headers=headers,
            )
            assert r2.status_code == 200, r2.text
            assert (
                r2.json()["data"]["requestId"]
                == r1.json()["data"]["requestId"]
            )
        finally:
            prc_composer.set_prc_service_for_tests(
                ProductRegistrationService(repo)
            )

        # Somente a primeira mutação emitiu.
        intake_events = [e for e in events if e.reason == "intake"]
        assert len(intake_events) == 1
        assert intake_events[0].resource_type == "request"
        assert REQUESTER_SUB in intake_events[0].recipient_user_ids

    def test_no_event_on_validation_failure(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        events: list[RealtimeEvent] = []

        class _Capture:
            def publish(self, event: RealtimeEvent) -> None:
                events.append(event)

        from engineering_app.composition import prc_composer
        from engineering_app.application.use_cases.product_registration.service import (  # noqa: E501
            ProductRegistrationService,
        )

        repo = prc_service_repo["repo"]
        prc_composer.set_prc_service_for_tests(
            ProductRegistrationService(repo, realtime_publisher=_Capture())
        )
        try:
            _set_rbac(core_rbac, MR_PERMS, REQUESTER_SUB)
            tok = _token(jwks_env, REQUESTER_SUB)
            body = _create_body(source="my-requests")
            # CREATE exige ao menos um vínculo de fornecedor (CORRECTION-10).
            body["requestedData"]["suppliers"] = []
            resp = _post(
                client,
                "/v1/product-registration/intake/requests",
                tok,
                json=body,
                headers={"Idempotency-Key": "idem-fail-1"},
            )
            assert resp.status_code in (400, 422), resp.text
        finally:
            prc_composer.set_prc_service_for_tests(
                ProductRegistrationService(repo)
            )

        assert [e for e in events if e.reason == "intake"] == []


class TestNeutralContract:
    """Transversalidade (AC-13): um segundo domínio adere sem reescrever
    hub/handshake — basta prover rooms + authorizer."""

    def test_rooms_and_envelope_are_domain_neutral(self):
        event = RealtimeEvent(
            domain="nonconformity",
            resource_type="case",
            resource_id="abc",
            reason="triaged",
            occurred_at="2026-11-12T00:00:00Z",
            event_id="e-1",
            recipient_user_ids=("u-9",),
        )
        rooms = event_rooms(event)
        assert resource_room("nonconformity", "abc") in rooms
        assert user_room("u-9") in rooms
        assert queue_room("nonconformity") in rooms
        payload = event_payload(event)
        assert payload["type"] == "engineering.resource.changed"
        assert payload["domain"] == "nonconformity"
