from __future__ import annotations

import pytest

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.ports.text_correction_spell_check_port import TextCorrectionSpellCheckPort
from app.domain.services.chat_domain_config_service import ChatDomainConfigService
from app.domain.services.chat_text_correction_spell_check_service import (
    ChatTextCorrectionSpellCheckService,
)
from app.domain.services.chat_text_correction_spell_preflight_service import (
    ChatTextCorrectionSpellPreflightService,
)


class _FakeSpellCheckPort(TextCorrectionSpellCheckPort):
    def __init__(self, issues: list[dict] | None = None) -> None:
        self._issues = issues or []
        self.calls: list[tuple[str, str]] = []

    def check(self, text: str, *, language: str) -> list[dict]:
        self.calls.append((text, language))
        return list(self._issues)


@pytest.fixture(autouse=True)
def _configure_ports(monkeypatch):
    configure_domain_infrastructure_ports()
    monkeypatch.setattr(
        ChatDomainConfigService,
        "chat_text_correction_spell_check_enabled",
        classmethod(lambda cls: True),
    )
    yield


def test_preflight_filters_ignored_rules_and_protected_codes():
    port = _FakeSpellCheckPort(
        [
            {
                "offset": 2,
                "length": 4,
                "message": "Possível erro de ortografia.",
                "replacements": ["está"],
                "ruleId": "MORFOLOGIK_RULE_PT_BR",
                "category": "TYPOS",
            },
            {
                "offset": 24,
                "length": 8,
                "message": "Erro no código.",
                "replacements": ["10080002"],
                "ruleId": "MORFOLOGIK_RULE_PT_BR",
                "category": "TYPOS",
            },
            {
                "offset": 0,
                "length": 3,
                "message": "Estilo.",
                "replacements": [],
                "ruleId": "UPPERCASE_SENTENCE_START",
                "category": "TYPOGRAPHY",
            },
        ]
    )
    ChatTextCorrectionSpellCheckService.configure(port)

    result = ChatTextCorrectionSpellPreflightService.run(
        source_text="o estoque esta baixo produto 10080001",
        preserved_codes=["10080001"],
    )

    assert result is not None
    assert result["used"] is True
    assert result["issueCount"] == 3
    assert result["filteredIssueCount"] == 1
    assert "está" in result["promptBlock"]
    assert "10080001" not in result["promptBlock"]


def test_preflight_skips_when_disabled(monkeypatch):
    monkeypatch.setattr(
        ChatDomainConfigService,
        "chat_text_correction_spell_check_enabled",
        classmethod(lambda cls: False),
    )
    port = _FakeSpellCheckPort([{"offset": 0, "length": 1, "message": "x", "replacements": []}])
    ChatTextCorrectionSpellCheckService.configure(port)

    assert ChatTextCorrectionSpellPreflightService.run(source_text="texto curto demais?") is None


def test_preflight_respects_source_length_limits():
    port = _FakeSpellCheckPort()
    ChatTextCorrectionSpellCheckService.configure(port)

    assert ChatTextCorrectionSpellPreflightService.run(source_text="curto") is None
