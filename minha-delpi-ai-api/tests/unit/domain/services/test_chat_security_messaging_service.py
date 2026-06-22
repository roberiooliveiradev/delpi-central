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


def test_sql_invalid_object_failure_message():
    message = ChatSecurityMessagingService.resolve_api_failure(
        {
            "ok": False,
            "statusCode": 200,
            "error": "500: ('42S02', \"Invalid object name 'SA1010'.\")",
        },
        path="/data/sql",
    )

    assert "SA1010" in message
    assert "indispon" not in message.lower()


def test_internal_attribute_error_on_structure_uses_friendly_message():
    message = ChatSecurityMessagingService.resolve_api_failure(
        {
            "ok": False,
            "error": (
                "type object 'ChatApiDelpiResponseProfileService' "
                "has no attribute 'PRODUCT_LIST_PRESENT_ENTITIES'"
            ),
        },
        path="/products/9020115/structure",
    )

    assert "has no attribute" not in message
    assert "estrutura" in message.lower() or "bom" in message.lower()


def test_internal_attribute_error_uses_generic_presentation_message():
    message = ChatSecurityMessagingService.resolve_api_failure(
        {
            "ok": False,
            "error": "type object 'Foo' has no attribute 'bar'",
        },
        path="/products/10080001/suppliers",
    )

    assert "has no attribute" not in message
    assert "montar a resposta" in message.lower()


def test_system_metadata_db_failure_message():
    message = ChatSecurityMessagingService.resolve_api_failure(
        {
            "ok": False,
            "statusCode": 400,
            "error": "Erro de conexão com o banco de dados: login timeout",
        },
        path="/system/tables/search",
    )

    assert "protheus" in message.lower() or "dicionário" in message.lower()


def test_timeout_failure_uses_composite_timeout_message():
    message = ChatSecurityMessagingService.resolve_api_failure(
        {
            "ok": False,
            "statusCode": 504,
            "error": "read timed out",
        },
        path="/products/90260140/factory-status",
    )

    assert "demorou" in message.lower()
    assert "timeout" not in message.lower()
