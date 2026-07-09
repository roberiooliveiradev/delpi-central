"""Fixtures compartilhados — evita dependência de app context em testes de seleção."""

from __future__ import annotations

import pytest


def pytest_configure(config):
    from app.composition.content_composer import configure_domain_infrastructure_ports

    configure_domain_infrastructure_ports()


@pytest.fixture(autouse=True)
def _configure_domain_ports():
    from app.composition.content_composer import configure_domain_infrastructure_ports

    configure_domain_infrastructure_ports()


@pytest.fixture(autouse=True)
def _ensure_operational_fast_path_settings(monkeypatch):
    from app.infrastructure.config.settings import Settings

    monkeypatch.setattr(Settings, "CHAT_OPERATIONAL_FAST_PATH_ENABLED", True)


@pytest.fixture(autouse=True)
def _disable_web_search_blocks(monkeypatch):
    from app.domain.services.chat_web_search_intent_service import (
        ChatWebSearchIntentService,
    )

    monkeypatch.setattr(ChatWebSearchIntentService, "is_feature_enabled", lambda: False)


@pytest.fixture(autouse=True)
def _patch_chat_intelligence_runtime(monkeypatch):
    from tests.support.chat_intelligence_runtime import patch_resolve_chat_intelligence_runtime

    patch_resolve_chat_intelligence_runtime(monkeypatch)


@pytest.fixture
def presentation_only_shortcut_enabled(monkeypatch):
    """Restaura paridade 11.4.1 quando o default JSON é llm_prose_everywhere."""
    from app.domain.services.chat_presentation_prose_delivery_content_service import (
        ChatPresentationProseDeliveryContentService,
    )
    from app.domain.services.chat_response_mode_service import ChatResponseModeService

    monkeypatch.setattr(
        ChatPresentationProseDeliveryContentService,
        "llm_prose_everywhere",
        lambda: False,
    )
    monkeypatch.setattr(
        ChatPresentationProseDeliveryContentService,
        "allow_template_prose_fallback",
        lambda: True,
    )
    monkeypatch.setattr(
        ChatPresentationProseDeliveryContentService,
        "deprecate_humanized_linhas_as_prose",
        lambda: False,
    )
    monkeypatch.setattr(ChatResponseModeService, "is_enabled", lambda: False)
