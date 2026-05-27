from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)


def test_normalize_fixes_common_typos():
    result = ChatMessageNormalizationService.normalize_for_matching(
        "forncedores do produto 10080001"
    )
    assert "fornecedor" in result
    assert "forncedores" not in result


def test_normalize_strips_accents():
    result = ChatMessageNormalizationService.normalize_for_matching("Preço do produto")
    assert result == "preco do produto"


def test_contains_any_with_typo():
    assert ChatMessageNormalizationService.contains_any(
        "quanto tem em estoq do 10080001",
        ("estoque",),
    )
