from app.domain.services.chat_web_search_query_security_service import (
    ChatWebSearchQuerySecurityService,
)


def test_sanitize_removes_internal_price_and_rewrites_public_entity():
    result = ChatWebSearchQuerySecurityService.sanitize(
        "pesquise na web se o cliente ABC comprou pelo preco interno R$ 12,30",
        extracted_query="cliente ABC comprou pelo preco interno R$ 12,30",
    )

    assert result.redacted
    assert "12,30" not in result.query
    assert "preco interno" not in result.query
    assert "informacoes publicas" in result.query
