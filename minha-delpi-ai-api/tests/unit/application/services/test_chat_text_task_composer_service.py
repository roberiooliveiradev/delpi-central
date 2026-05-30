from app.application.services.chat_text_task_composer_service import (
    ChatTextTaskComposerService,
)
from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService


def test_mixed_turn_email_supplement_from_stock_tool():
    supplement = ChatTextTaskComposerService.build_supplement_for_mixed_turn(
        message="consulte estoque do 10080001 e escreva um e-mail",
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": True,
                    "path": "/products/10080001/stock",
                    "humanizedSummary": {
                        "titulo": "Estoque do produto",
                        "linhas": [
                            "Filial 01: quantidade disponível 100 un.",
                            "Filial 02: quantidade disponível 50 un.",
                        ],
                    },
                },
            }
        ],
    )

    assert supplement is not None
    assert "Assunto sugerido" in supplement
    assert "10080001" in supplement
    assert "Filial 01" in supplement


def test_email_from_conversation_after_stock():
    previous = [
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/10080001/stock",
                            "humanizedSummary": {
                                "titulo": "Estoque do produto",
                                "linhas": ["Filial 01: 100 un. disponíveis."],
                            },
                        },
                    }
                ]
            },
        }
    ]
    message = "escreva um email com os dados da tabela"

    assert ChatAnalysisIntentService.is_email_from_operational_data_request(
        message,
        previous,
    )

    draft = ChatTextTaskComposerService.build_email_from_conversation(message, previous)

    assert draft is not None
    assert "Assunto sugerido" in draft
    assert "Estoque" in draft


def test_pure_text_not_when_email_from_data_follow_up():
    from app.domain.services.chat_text_task_intent_service import ChatTextTaskIntentService

    previous = [
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {"ok": True, "path": "/products/10080001/stock"},
                    }
                ]
            },
        }
    ]

    assert (
        ChatTextTaskIntentService.is_pure_text_task(
            "escreva um email com os dados da tabela",
            previous_messages=previous,
        )
        is False
    )
