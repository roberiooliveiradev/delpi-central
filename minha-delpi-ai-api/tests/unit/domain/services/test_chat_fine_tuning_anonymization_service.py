from app.domain.services.chat_fine_tuning_anonymization_service import (
    ChatFineTuningAnonymizationService,
)


def test_anonymize_redacts_email():
    text = "contato joao@empresa.com.br sobre o modulo"
    result = ChatFineTuningAnonymizationService.anonymize(text)
    assert "joao@empresa.com.br" not in result
    assert "[REDACTED]" in result


def test_anonymize_messages_preserves_roles():
    messages = ChatFineTuningAnonymizationService.anonymize_messages(
        [
            {"role": "user", "content": "ola"},
            {"role": "assistant", "content": "oi, tudo bem?"},
        ]
    )
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
