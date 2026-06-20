from app.domain.exceptions.vision_exceptions import VisionMemoryLimitedError
from app.domain.services.chat_drawing_intent_service import ChatDrawingIntentService
from app.domain.services.chat_vision_memory_guard_service import (
    ChatVisionMemoryGuardService,
)


def test_filter_engines_drops_easyocr_when_memory_low(monkeypatch):
    monkeypatch.setattr(
        ChatVisionMemoryGuardService,
        "available_memory_mb",
        staticmethod(lambda: 256),
    )
    monkeypatch.setattr(
        ChatVisionMemoryGuardService,
        "min_available_mb_for_easyocr",
        staticmethod(lambda: 1400),
    )

    filtered = ChatVisionMemoryGuardService.filter_engines_for_memory(
        ("tesseract", "easyocr")
    )

    assert filtered == ("tesseract",)


def test_filter_engines_keeps_easyocr_when_memory_ok(monkeypatch):
    monkeypatch.setattr(
        ChatVisionMemoryGuardService,
        "available_memory_mb",
        staticmethod(lambda: 4096),
    )

    filtered = ChatVisionMemoryGuardService.filter_engines_for_memory(
        ("tesseract", "easyocr")
    )

    assert filtered == ("tesseract", "easyocr")


def test_is_memory_related_error_detects_memory_error():
    assert ChatVisionMemoryGuardService.is_memory_related_error(MemoryError())
    assert ChatVisionMemoryGuardService.is_memory_related_error(
        VisionMemoryLimitedError()
    )
    assert not ChatVisionMemoryGuardService.is_memory_related_error(ValueError("x"))


def test_build_memory_limited_answer_has_guidance():
    answer = ChatDrawingIntentService.build_memory_limited_answer()

    assert "memória" in answer.lower()
    assert "wsl" in answer.lower() or "docker" in answer.lower()
