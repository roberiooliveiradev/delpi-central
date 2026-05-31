"""Fixtures compartilhados — evita dependência de app context em testes de seleção."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _disable_web_search_blocks(monkeypatch):
    from app.domain.services.chat_web_search_intent_service import (
        ChatWebSearchIntentService,
    )

    monkeypatch.setattr(ChatWebSearchIntentService, "is_feature_enabled", lambda: False)
