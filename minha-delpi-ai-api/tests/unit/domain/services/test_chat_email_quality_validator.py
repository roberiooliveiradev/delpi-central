from app.domain.services.chat_email_quality_validator import ChatEmailQualityValidator


def test_detects_artificial_phrase():
    answer = """Assunto: Teste

Prezado João,

Estou em consideração, gostaria de solicitar seu feedback.

Atenciosamente,
[Seu nome]"""
    result = ChatEmailQualityValidator.validate(answer)
    assert result["passed"] is False
    assert any("artificial" in (w or "").lower() for w in result.get("warnings") or [])


def test_detects_invented_signature():
    answer = """Assunto: IA

Corpo.

Atenciosamente,
Roberto Silva
Superadministrador
Minha DELPI Chat"""
    result = ChatEmailQualityValidator.validate(answer)
    assert result["passed"] is False


def test_accepts_placeholder_signature():
    answer = """Assunto: Proposta

Gostaria de apresentar uma proposta para avaliação.

Atenciosamente,

[Seu nome]"""
    result = ChatEmailQualityValidator.validate(answer)
    assert result["passed"] is True


def test_invented_deadline_without_user_input():
    answer = "Precisamos receber o retorno até sexta-feira."
    result = ChatEmailQualityValidator.validate(
        answer,
        user_message="escreva um e-mail de cobrança cordial",
    )
    assert result["passed"] is False
