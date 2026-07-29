from __future__ import annotations

from unittest.mock import patch

from app.application.services.lnf_portal_notification_service import (
    block_reason_label,
    build_block_assigned_copy,
    build_block_resolved_copy,
    lnf_portal_notifications_enabled,
    notify_block_assignee,
    notify_block_resolved,
    request_portal_route,
    resolve_block_requester_user_id,
    send_lnf_portal_notification,
    should_notify_block_assignee,
    should_notify_block_requester,
)


def test_lnf_portal_notifications_enabled_requires_core_api() -> None:
    with patch("app.application.services.lnf_portal_notification_service.settings") as settings:
        settings.LNF_NOTIFICATIONS_ENABLED = True
        settings.CORE_API_BASE_URL = "http://core-api:8000"
        settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN = "token"
        assert lnf_portal_notifications_enabled() is True


def test_lnf_portal_notifications_disabled_without_token() -> None:
    with patch("app.application.services.lnf_portal_notification_service.settings") as settings:
        settings.LNF_NOTIFICATIONS_ENABLED = True
        settings.CORE_API_BASE_URL = "http://core-api:8000"
        settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN = ""
        assert lnf_portal_notifications_enabled() is False


def test_should_notify_block_assignee_skips_self() -> None:
    assert (
        should_notify_block_assignee(
            assignee_user_id="u1",
            actor_user_id="u1",
        )
        is False
    )
    assert (
        should_notify_block_assignee(
            assignee_user_id="u2",
            actor_user_id="u1",
        )
        is True
    )
    assert should_notify_block_assignee(assignee_user_id="") is False


def test_request_portal_route_includes_request_id() -> None:
    assert (
        request_portal_route(branch_code="01", request_id="req-1")
        == "/apps/lancamento-notas-fiscais/filial-01?requestId=req-1"
    )
    assert (
        request_portal_route(branch_code="02", request_id="req-2")
        == "/apps/lancamento-notas-fiscais/filial-02?requestId=req-2"
    )


def test_build_block_assigned_copy_includes_request_and_pendency() -> None:
    title, message, html_content = build_block_assigned_copy(
        actor_name="Fiscal Delpi",
        block_reason="purchase_order",
        block_description="Falta o PC",
        document_number="123456",
        series="1",
        supplier_name="Fornecedor Alpha",
        branch_code="01",
        amount="1500.5",
        issue_date="2026-07-20",
    )
    assert "Aguardando pedido de compra" in title
    assert "Falta o PC" in message
    assert "000123456 / 1" in message
    assert "Fornecedor Alpha" in message
    assert "Filial 01 (SC)" in message
    assert "R$ 1.500,50" in message
    assert "Falta o PC" in html_content
    assert "notification-note-bubble" in html_content
    assert block_reason_label("other") == "Outra pendência"


def test_send_lnf_portal_notification_posts_to_core_api() -> None:
    with patch("app.application.services.lnf_portal_notification_service.settings") as settings:
        settings.LNF_NOTIFICATIONS_ENABLED = True
        settings.CORE_API_BASE_URL = "http://core-api:8000"
        settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN = "token"

        with patch("httpx.Client") as client_cls:
            client = client_cls.return_value.__enter__.return_value
            client.post.return_value.status_code = 201
            client.post.return_value.text = "ok"

            sent = send_lnf_portal_notification(
                recipient_user_id="user-42",
                title="Pendência",
                message="Detalhe",
                action_target="/apps/lancamento-notas-fiscais/filial-01?requestId=req-1",
                dedupe_key="lnf:block_assigned:req-1:user-42",
                event_type="lnf_request_blocked_assigned",
                html_content="<p>Detalhe</p>",
            )
            assert sent is True
            payload = client.post.call_args.kwargs["json"]
            assert payload["userIds"] == ["user-42"]
            assert payload["category"] == "lancamento_notas_fiscais"
            assert payload["sourceApp"] == "lancamento-notas-fiscais"
            assert payload["presentation"] == "html"
            assert payload["action"]["target"].endswith("requestId=req-1")


def test_notify_block_assignee_sends_for_other_user() -> None:
    with patch(
        "app.application.services.lnf_portal_notification_service.send_lnf_portal_notification",
        return_value=True,
    ) as send:
        ok = notify_block_assignee(
            request={
                "id": "req-1",
                "branch_code": "01",
                "document_number": "000012078",
                "series": "",
                "supplier_name": "Alpha",
                "amount": 10,
                "issue_date": "2026-07-01",
                "block_reason": "other",
                "block_description": "Pendência X",
                "assignee_user_id": "u-compras",
                "assignee_name": "Compras",
            },
            actor_user_id="u-fiscal",
            actor_name="Fiscal",
        )
        assert ok is True
        assert send.called
        kwargs = send.call_args.kwargs
        assert kwargs["recipient_user_id"] == "u-compras"
        assert "Pendência X" in kwargs["message"]


def test_notify_block_assignee_skips_self() -> None:
    with patch(
        "app.application.services.lnf_portal_notification_service.send_lnf_portal_notification"
    ) as send:
        ok = notify_block_assignee(
            request={
                "id": "req-1",
                "assignee_user_id": "u-fiscal",
                "block_reason": "other",
                "block_description": "x",
            },
            actor_user_id="u-fiscal",
            actor_name="Fiscal",
        )
        assert ok is False
        assert not send.called


def test_resolve_block_requester_user_id_uses_last_block_actor() -> None:
    history = [
        {
            "event_type": "status_changed",
            "to_status": "in_progress",
            "actor_user_id": "u-process",
        },
        {
            "event_type": "status_changed",
            "to_status": "blocked",
            "actor_user_id": "u-fiscal",
        },
        {
            "event_type": "comment_added",
            "actor_user_id": "u-compras",
        },
    ]
    assert resolve_block_requester_user_id(history) == "u-fiscal"
    assert resolve_block_requester_user_id([]) is None


def test_build_block_resolved_copy() -> None:
    title, message, html_content = build_block_resolved_copy(
        actor_name="Compras Delpi",
        block_reason="purchase_order",
        block_description="Falta o PC",
        document_number="4041160",
        series="1",
        supplier_name="Alpha",
        branch_code="01",
    )
    assert "Pendência de NF resolvida" in title
    assert "Aguardando pedido de compra" in title
    assert "marcou a pendência como resolvida" in message
    assert "Falta o PC" in message
    assert "004041160 / 1" in message
    assert "notification-note-bubble" in html_content


def test_notify_block_resolved_sends_to_requester() -> None:
    with patch(
        "app.application.services.lnf_portal_notification_service.send_lnf_portal_notification",
        return_value=True,
    ) as send:
        ok = notify_block_resolved(
            request={
                "id": "req-1",
                "branch_code": "01",
                "document_number": "000012078",
                "series": "",
                "supplier_name": "Alpha",
                "amount": 10,
                "issue_date": "2026-07-01",
            },
            recipient_user_id="u-fiscal",
            block_reason="other",
            block_description="Pendência X",
            actor_user_id="u-compras",
            actor_name="Compras",
        )
        assert ok is True
        kwargs = send.call_args.kwargs
        assert kwargs["recipient_user_id"] == "u-fiscal"
        assert kwargs["notification_type"] == "success"
        assert kwargs["event_type"] == "lnf_request_block_resolved"
        assert "Pendência X" in kwargs["message"]


def test_notify_block_resolved_skips_self() -> None:
    with patch(
        "app.application.services.lnf_portal_notification_service.send_lnf_portal_notification"
    ) as send:
        ok = notify_block_resolved(
            request={"id": "req-1"},
            recipient_user_id="u-fiscal",
            block_reason="other",
            block_description="x",
            actor_user_id="u-fiscal",
            actor_name="Fiscal",
        )
        assert ok is False
        assert not send.called
    assert should_notify_block_requester(
        requester_user_id="u-fiscal",
        actor_user_id="u-compras",
    )
