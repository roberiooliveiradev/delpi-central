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


def test_sanitize_replaces_invented_signature():
    answer = """Assunto: Teste

Gostaria de informar.

Atenciosamente,
Roberto Silva
Superadministrador"""
    sanitized, fixes = ChatEmailQualityValidator.sanitize(answer)
    assert "signature_placeholder" in fixes
    assert "[Seu nome]" in sanitized
    assert "Roberto Silva" not in sanitized


def test_weak_subject_flagged():
    answer = "Assunto: Solicitação de Criação de IA para Minha DELPI\n\nGostaria de apresentar uma proposta."
    result = ChatEmailQualityValidator.validate(answer)
    assert any(c["criterion"] == "subject_quality" and not c["ok"] for c in result["checks"])
