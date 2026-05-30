from app.domain.services.chat_text_task_intent_service import ChatTextTaskIntentService


def test_classify_correction():
    assert ChatTextTaskIntentService.classify("Corrija: nos vai enviar o pedido amanhã") == "correct"


def test_classify_email():
    assert (
        ChatTextTaskIntentService.classify(
            "Escreva um e-mail cobrando retorno do fornecedor sobre prazo",
        )
        == "email"
    )


def test_pure_text_task_correction_with_stock_word():
    message = "Corrija este texto: o estoque esta baixo"

    assert ChatTextTaskIntentService.is_pure_text_task(message) is True


def test_not_pure_when_operational_stock_query():
    assert ChatTextTaskIntentService.is_pure_text_task("qual o estoque do produto 10080001?") is False


def test_mixed_operational_and_text():
    message = (
        "Consulte o estoque do produto 10080001 e escreva um e-mail avisando compras"
    )

    assert ChatTextTaskIntentService.classify(message) in {"write", "email"}
    assert ChatTextTaskIntentService.is_pure_text_task(message) is False
    assert ChatTextTaskIntentService.is_mixed_text_and_operational(message) is True
