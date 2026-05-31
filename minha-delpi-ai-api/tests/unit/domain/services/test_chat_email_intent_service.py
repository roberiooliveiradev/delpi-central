from app.domain.services.chat_email_intent_service import ChatEmailIntentService


def test_email_create_subtype():
    msg = "escreva um e-mail formal para Robério sobre criar uma IA para Minha DELPI"
    assert ChatEmailIntentService.classify_subtype(msg) == "email_create"
    assert ChatEmailIntentService.is_email_writing(msg) is True


def test_email_formalize_subtype():
    msg = "deixe o e-mail anterior mais formal"
    assert ChatEmailIntentService.classify_subtype(msg) == "email_formalize"


def test_email_subjects_subtype():
    msg = "crie 3 opções de assunto para o e-mail anterior"
    assert ChatEmailIntentService.classify_subtype(msg) == "email_subjects"


def test_extract_recipient_and_missing_sender():
    msg = "escreva um e-mail formal para Robério sobre a proposta de IA"
    ctx = ChatEmailIntentService.extract_context(msg)
    assert ctx["subtype"] == "email_create"
    assert ctx.get("recipient")
    assert "senderName" in (ctx.get("missingFields") or [])


def test_explicit_signature():
    msg = "escreva um e-mail para o cliente. Assine como João Silva, Engenharia."
    ctx = ChatEmailIntentService.extract_context(msg)
    assert "João Silva" in (ctx.get("senderSignature") or "")
    assert "senderName" not in (ctx.get("missingFields") or [])


def test_non_email_message():
    msg = "qual o estoque do produto 10080001?"
    assert ChatEmailIntentService.is_email_writing(msg) is False
