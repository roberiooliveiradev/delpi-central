"""Playbook 08 — mensagens de falha de API."""

from app.domain.services.chat_security_messaging_service import (
    ChatSecurityMessagingService,
)


def test_stock_failure_message():
    message = ChatSecurityMessagingService.resolve_api_failure(
        {"ok": False, "statusCode": 502},
        path="/products/10080001/stock",
    )

    assert "estoque" in message.lower()


def test_permission_failure_uses_no_access():
    message = ChatSecurityMessagingService.resolve_api_failure(
        {"ok": False, "statusCode": 403, "detail": "forbidden"},
        path="/products/10080001/suppliers",
    )

    assert "permiss" in message.lower()
