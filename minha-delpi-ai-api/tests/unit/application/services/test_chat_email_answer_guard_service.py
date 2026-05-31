from app.application.services.chat_email_answer_guard_service import ChatEmailAnswerGuardService


def test_guard_sanitizes_invented_signature():
    answer = """Assunto: Proposta

Gostaria de apresentar uma proposta.

Atenciosamente,
Roberto Silva
Superadministrador"""
    sanitized, meta = ChatEmailAnswerGuardService.apply(
        answer,
        message="escreva um e-mail formal para Robério",
        workspace_context={"emailWritingMode": True},
    )
    assert "[Seu nome]" in sanitized
    assert meta is not None
    assert meta.get("emailGuard", {}).get("sanitized") is True
