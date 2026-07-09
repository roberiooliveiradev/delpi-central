"""Mock de resolve_chat_intelligence_runtime para testes de stream/send."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

_RUNTIME_PATCH_TARGETS = (
    "app.application.services.chat_intelligence_runtime_access.resolve_chat_intelligence_runtime",
    "app.application.services.chat_turn.chat_stream_turn_prepare_service.resolve_chat_intelligence_runtime",
    "app.application.use_cases.send_chat_message_use_case.resolve_chat_intelligence_runtime",
)


def build_chat_intelligence_runtime_mock(**overrides: Any) -> MagicMock | SimpleNamespace:
    runtime = MagicMock()
    runtime.fast_path_enabled = False
    runtime.assistant_identity_direct_enabled = True
    runtime.multi_action_enabled = True
    runtime.rag_identity_question_min_score = 0.0
    for key, value in overrides.items():
        setattr(runtime, key, value)
    return runtime


def build_vision_settings_mock(**overrides: Any) -> dict[str, Any]:
    from app.infrastructure.config.settings import Settings

    base = {
        "documentVisionEnabled": bool(Settings.CHAT_DOCUMENT_VISION_ENABLED),
        "documentVisionAutoWithDrawing": bool(Settings.CHAT_DOCUMENT_VISION_AUTO_WITH_DRAWING),
        "documentVisionAutoVlmFallback": bool(Settings.CHAT_DOCUMENT_VISION_AUTO_VLM_FALLBACK),
        "attachmentImageOcrEnabled": bool(Settings.CHAT_ATTACHMENT_IMAGE_OCR_ENABLED),
        "documentVisionStampCropEnabled": bool(Settings.CHAT_DOCUMENT_VISION_STAMP_CROP_ENABLED),
        "documentVisionImageDescribeEnabled": bool(
            Settings.CHAT_DOCUMENT_VISION_IMAGE_DESCRIBE_ENABLED
        ),
    }
    base.update(overrides)
    return base


def patch_platform_runtime_access(monkeypatch, *, vision: dict[str, Any] | None = None) -> dict[str, Any]:
    resolved_vision = vision or build_vision_settings_mock()
    monkeypatch.setattr(
        "app.application.services.chat_platform_runtime_access.vision_settings",
        lambda: resolved_vision,
    )
    return resolved_vision


def patch_resolve_chat_intelligence_runtime(monkeypatch, runtime: Any | None = None) -> Any:
    resolved = runtime or build_chat_intelligence_runtime_mock()
    for target in _RUNTIME_PATCH_TARGETS:
        monkeypatch.setattr(target, lambda _runtime=resolved: _runtime)
    patch_platform_runtime_access(monkeypatch)
    monkeypatch.setattr(
        "app.application.services.chat_platform_runtime_access.learning_pipeline_settings",
        lambda: {"enabled": False},
    )
    return resolved
