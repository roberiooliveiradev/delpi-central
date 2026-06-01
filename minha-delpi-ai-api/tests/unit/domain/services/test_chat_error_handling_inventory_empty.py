from app.domain.services.chat_error_handling_classifier import (
    ChatErrorHandlingClassifier,
)


def test_empty_inventory_minimum_for_stock_list_message():
    classification = ChatErrorHandlingClassifier.classify(
        message="Liste os produtos com estoque abaixo do mínimo",
        answer="Nenhum produto com estoque abaixo do mínimo cadastrado.",
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": True,
                    "path": "/data/sql",
                    "humanizedSummary": {
                        "titulo": "Produtos com estoque abaixo do mínimo",
                        "linhas": [
                            "Nenhum produto com estoque abaixo do mínimo cadastrado."
                        ],
                    },
                },
            }
        ],
    )

    assert classification is not None
    assert classification.error_type == "empty_inventory_minimum"
    assert classification.affirms_non_existence is True
