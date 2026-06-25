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
    runtime.multi_action_enabled = False
    runtime.rag_identity_question_min_score = 0.0
    for key, value in overrides.items():
        setattr(runtime, key, value)
    return runtime


def patch_resolve_chat_intelligence_runtime(monkeypatch, runtime: Any | None = None) -> Any:
    resolved = runtime or build_chat_intelligence_runtime_mock()
    for target in _RUNTIME_PATCH_TARGETS:
        monkeypatch.setattr(target, lambda _runtime=resolved: _runtime)
    monkeypatch.setattr(
        "app.application.services.chat_platform_runtime_access.learning_pipeline_settings",
        lambda: {"enabled": False},
    )
    return resolved
