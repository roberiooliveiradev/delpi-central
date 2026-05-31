"""Regressão — escrita de e-mails (playbook E1–E15, subset automatizado)."""

from app.domain.services.chat_email_intent_service import ChatEmailIntentService
from app.domain.services.chat_email_quality_validator import ChatEmailQualityValidator
from app.domain.services.chat_text_task_intent_service import ChatTextTaskIntentService


def _assert_pure_email(msg: str) -> None:
    assert ChatTextTaskIntentService.classify(msg) == "email"
    assert ChatTextTaskIntentService.is_pure_text_task(msg) is True
    assert ChatEmailIntentService.is_email_writing(msg) is True


def test_e1_formal_email_create():
    _assert_pure_email("escreva um e-mail formal para a diretoria sobre o projeto")


def test_e2_placeholder_signature_expected():
    ctx = ChatEmailIntentService.extract_context("escreva um e-mail para o cliente")
    assert "senderName" in (ctx.get("missingFields") or [])


def test_e3_supplier_email():
    msg = "faça um e-mail para fornecedor confirmando prazo"
    assert ChatEmailIntentService.extract_context(msg).get("audience") == "supplier"


def test_e5_shorten_refinement():
    assert ChatEmailIntentService.classify_subtype("deixe o e-mail anterior mais curto") == "email_shorten"


def test_e6_firm_tone_refinement():
    assert ChatEmailIntentService.classify_subtype("tom mais firme no e-mail anterior") == "email_firm"


def test_e7_alternative_subjects():
    assert ChatEmailIntentService.classify_subtype("crie assunto alternativo para o e-mail") == "email_subjects"


def test_e8_translate_email():
    assert ChatEmailIntentService.classify_subtype("traduza o e-mail anterior para inglês") == "email_translate"


def test_e11_explicit_signature():
    ctx = ChatEmailIntentService.extract_context("escreva e-mail. Assine como Maria, Compras.")
    assert "Maria" in (ctx.get("senderSignature") or "")


def test_e12_no_invented_signature_in_validator():
    bad = "Atenciosamente,\nRoberto Silva\nSuperadministrador"
    assert ChatEmailQualityValidator.validate(bad)["passed"] is False
    good = (
        "Assunto: Proposta\n\n"
        "Gostaria de apresentar uma proposta para avaliação.\n\n"
        "Atenciosamente,\n\n[Seu nome]"
    )
    assert ChatEmailQualityValidator.validate(good)["passed"] is True


def test_e13_executive_tone_hint():
    msg = "escreva um e-mail executivo para a diretoria sobre IA"
    assert ChatEmailIntentService.extract_context(msg).get("tone") == "executive"


def test_e14_customer_audience():
    msg = "escreva um e-mail para cliente com atualização de entrega"
    assert ChatEmailIntentService.extract_context(msg).get("audience") == "customer"
