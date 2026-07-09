"""Defaults legados para testes de use case que assertam prosa template / direct answer."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _legacy_presentation_template_mode(monkeypatch):
    from app.domain.services.chat_presentation_prose_delivery_content_service import (
        ChatPresentationProseDeliveryContentService,
    )

    monkeypatch.setattr(
        ChatPresentationProseDeliveryContentService,
        "llm_prose_everywhere",
        lambda: False,
    )
