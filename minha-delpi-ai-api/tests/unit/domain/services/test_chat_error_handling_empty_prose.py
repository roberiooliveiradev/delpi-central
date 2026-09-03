"""Card de vazio / Recuperar consulta — não duplicar prosa nem resumo narrativo."""

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_error_handling_classifier import (
    ChatErrorHandlingClassifier,
)

configure_domain_infrastructure_ports()


def _empty_stock_tool_call() -> dict:
    return {
        "name": "execute_external_action",
        "metadata": {
            "ok": True,
            "path": "/products/202607/stock",
            "emptyResult": True,
            "humanizedSummary": {
                "titulo": "Estoque",
                "linhas": [
                    "Nenhum registro encontrado para o filtro informado.",
                ],
            },
        },
    }


def test_empty_card_suppressed_when_llm_prose_already_explains():
    answer = (
        "A consulta de estoque do produto **202607** não retornou nenhum registro "
        "— ou seja, não há saldo de estoque disponível para esse item no momento."
    )

    classification = ChatErrorHandlingClassifier.classify(
        message="e o estoque?",
        answer=answer,
        tool_calls=[_empty_stock_tool_call()],
    )

    assert classification is None


def test_empty_card_suppressed_on_summary_without_empty_tools():
    answer = (
        "Em resumo: há faturamento no período (ROL R$ 344.331,23), "
        "mas o produto 202607 está sem registros de estoque no momento."
    )

    classification = ChatErrorHandlingClassifier.classify(
        message="resuma isso",
        answer=answer,
        tool_calls=[],
    )

    assert classification is None


def test_empty_card_kept_for_cold_short_answer_with_empty_tool():
    classification = ChatErrorHandlingClassifier.classify(
        message="estoque do 10080001",
        answer="Não encontrei.",
        tool_calls=[_empty_stock_tool_call()],
    )

    assert classification is not None
    assert classification.error_type == "empty_result"
