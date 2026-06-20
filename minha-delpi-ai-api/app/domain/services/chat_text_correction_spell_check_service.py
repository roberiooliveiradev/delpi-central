"""Facade de domain para verificação ortográfica na correção textual."""

from __future__ import annotations

from typing import ClassVar

from app.domain.ports.text_correction_spell_check_port import (
    TextCorrectionSpellCheckIssue,
    TextCorrectionSpellCheckPort,
)
from app.domain.services.chat_domain_config_service import ChatDomainConfigService
from app.domain.services.chat_text_correction_spell_content_service import (
    ChatTextCorrectionSpellContentService,
)


class ChatTextCorrectionSpellCheckService:
    _port: ClassVar[TextCorrectionSpellCheckPort | None] = None

    @classmethod
    def configure(cls, port: TextCorrectionSpellCheckPort) -> None:
        cls._port = port

    @classmethod
    def is_enabled(cls) -> bool:
        return (
            ChatTextCorrectionSpellContentService.catalog_enabled()
            and ChatDomainConfigService.chat_text_correction_spell_check_enabled()
            and cls._port is not None
        )

    @classmethod
    def check(cls, text: str, *, language: str | None = None) -> list[TextCorrectionSpellCheckIssue]:
        if not cls.is_enabled():
            return []

        cleaned = str(text or "").strip()

        if not cleaned or cls._port is None:
            return []

        try:
            resolved_language = language or ChatDomainConfigService.chat_languagetool_language()
            issues = cls._port.check(cleaned, language=resolved_language)
        except Exception:
            return []

        return issues if isinstance(issues, list) else []
