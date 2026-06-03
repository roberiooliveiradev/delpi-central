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


def test_consulte_estoque_e_escreva_email_is_mixed():
    message = "consulte estoque do 10080001 e escreva um e-mail"

    assert ChatTextTaskIntentService.is_mixed_text_and_operational(message) is True
    assert ChatTextTaskIntentService.is_pure_text_task(message) is False


def test_sql_authoring_is_not_pure_text_task():
    message = (
        "Monte uma consulta para listar clientes ativos da tabela SA1, "
        "só código e nome, sem executar."
    )

    assert ChatTextTaskIntentService.classify(message) == "write"
    assert ChatTextTaskIntentService.is_pure_text_task(message) is False


def test_classify_letter_and_eli5():
    assert ChatTextTaskIntentService.classify("Crie uma carta formal solicitando autorização") == "letter"
    assert (
        ChatTextTaskIntentService.classify("Explique RBAC como se eu tivesse 5 anos")
        == "eli5"
    )


def test_classify_documentation_and_action_plan():
    assert (
        ChatTextTaskIntentService.classify("Transforme essa explicação em documentação técnica")
        == "documentation"
    )
    assert ChatTextTaskIntentService.classify("Extraia um plano de ação com responsáveis") == "action_plan"


def test_mixed_operational_and_text():
    message = (
        "Consulte o estoque do produto 10080001 e escreva um e-mail avisando compras"
    )

    assert ChatTextTaskIntentService.classify(message) in {"write", "email"}
    assert ChatTextTaskIntentService.is_pure_text_task(message) is False
    assert ChatTextTaskIntentService.is_mixed_text_and_operational(message) is True
