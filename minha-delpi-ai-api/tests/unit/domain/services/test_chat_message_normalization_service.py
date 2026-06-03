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


def test_normalize_more_typos():
    assert "fornecedor" in ChatMessageNormalizationService.normalize_for_matching(
        "forncedor do 10080001"
    )
    assert "preco" in ChatMessageNormalizationService.normalize_for_matching("preço do prduto")
    assert "estrutura" in ChatMessageNormalizationService.normalize_for_matching("estrutur do 10080001")
    assert "quantidade" in ChatMessageNormalizationService.normalize_for_matching("qtd em estoque")


def test_normalize_filial_typos():
    assert ChatMessageNormalizationService.normalize_for_matching("filail 01") == "filial 01"
    assert ChatMessageNormalizationService.normalize_for_matching("filal 02") == "filial 02"


def test_expand_query_terms():
    terms = ChatMessageNormalizationService.expand_query_terms("Estoque do 10080001?")
    assert "estoque do 10080001" in terms
    assert any("?" not in t for t in terms)


def test_normalize_utility_time_typos():
    assert (
        ChatMessageNormalizationService.normalize_for_matching("que hors são?").rstrip("?")
        == "que horas sao"
    )
    assert ChatMessageNormalizationService.normalize_for_matching("q horas") == "que horas"
    assert ChatMessageNormalizationService.normalize_for_matching("q hrs") == "que horas"
    assert ChatMessageNormalizationService.normalize_for_matching("q dia") == "que dia e hoje"


def test_normalize_greeting_typos():
    assert ChatMessageNormalizationService.normalize_for_matching("bo dia") == "bom dia"
    assert ChatMessageNormalizationService.normalize_for_matching("bao dia") == "bom dia"


def test_normalize_identity_short_typos():
    norm = ChatMessageNormalizationService.normalize_for_matching
    assert norm("como vc s chama?").rstrip("?") == "como voce se chama"
    assert norm("como voce s chama").rstrip("?") == "como voce se chama"
    assert norm("qm e vc").rstrip("?") == "quem e voce"
    assert norm("oq vc faz") == "o que voce faz"
    assert norm("oq vc pode fazer") == "o que voce pode fazer"
    assert norm("cmo funciona") == "como funciona"
    assert norm("qual eh seu nome").startswith("qual e ")
    assert "seu nome" in norm("qual seu nom")


def test_normalize_nao_entendi_typos():
    norm = ChatMessageNormalizationService.normalize_for_matching
    assert norm("naum entendi") == "nao entendi"
    assert norm("num entendi") == "nao entendi"
    # `num entendi` não pode virar `numero entendi`
    assert "numero" not in norm("num entendi")
