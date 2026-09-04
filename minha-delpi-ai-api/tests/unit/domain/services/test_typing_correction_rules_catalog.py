from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)


def test_static_rules_loaded_from_catalog():
    configure_domain_infrastructure_ports()

    assert ChatMessageNormalizationService.static_rule_count() >= 150


def test_normalize_estouque_from_catalog():
    configure_domain_infrastructure_ports()

    result = ChatMessageNormalizationService.normalize_for_matching(
        "estouque do produto 90262404"
    )

    assert "estoque" in result
    assert "90262404" in result.replace(" ", "")


def test_normalize_estrutra_static_rule_from_catalog():
    configure_domain_infrastructure_ports()

    result = ChatMessageNormalizationService.normalize_for_matching(
        "qual a estrutra do 90260148?"
    )

    assert "estrutura" in result
    assert "estrutra" not in result


def test_normalize_descriao_typo_from_catalog():
    """Regressão: descrião (falta ç) → descricao após strip + regra P14."""
    configure_domain_infrastructure_ports()

    for message in (
        "qual a descrião do 10050078?",
        "qual a descriao do 10050078?",
    ):
        result = ChatMessageNormalizationService.normalize_for_matching(message)
        assert "descricao" in result, message
        assert "descriao" not in result, message
        assert "10050078" in result.replace(" ", "")
