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
def _disable_web_search_blocks(monkeypatch):
    from app.domain.services.chat_web_search_intent_service import (
        ChatWebSearchIntentService,
    )

    monkeypatch.setattr(ChatWebSearchIntentService, "is_feature_enabled", lambda: False)
