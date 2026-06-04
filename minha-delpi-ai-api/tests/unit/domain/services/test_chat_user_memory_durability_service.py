from app.domain.services.chat_user_memory_durability_service import (
    ChatUserMemoryDurabilityService,
)


def test_detects_profile_name():
    result = ChatUserMemoryDurabilityService.detect("Pode me chamar de João Pedro")
    assert result is not None
    assert result["type"] == "profile"
    assert "joao pedro" in result["contentNorm"]
    assert result["scope"] == "user"


def test_detects_durable_preference():
    result = ChatUserMemoryDurabilityService.detect(
        "De agora em diante responda sempre de forma resumida"
    )
    assert result is not None
    assert result["type"] == "preference"
    assert result["confidence"] > 0


def test_detects_sempre_responda_preference():
    result = ChatUserMemoryDurabilityService.detect("Sempre responda em português")
    assert result is not None
    assert result["type"] == "preference"


def test_ignores_casual_message():
    assert ChatUserMemoryDurabilityService.detect("qual o faturamento de ontem?") is None
    assert ChatUserMemoryDurabilityService.detect("oi, tudo bem?") is None


def test_ignores_too_short_or_too_long():
    assert ChatUserMemoryDurabilityService.detect("oi") is None
    assert ChatUserMemoryDurabilityService.detect("prefiro " + "x" * 500) is None


def test_normalize_strips_accents_and_case():
    assert ChatUserMemoryDurabilityService.normalize("Ação Rápida") == "acao rapida"
