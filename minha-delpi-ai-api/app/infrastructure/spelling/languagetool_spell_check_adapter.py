from __future__ import annotations

from app.domain.ports.text_correction_spell_check_port import (
    TextCorrectionSpellCheckIssue,
    TextCorrectionSpellCheckPort,
)
from app.infrastructure.spelling.languagetool_http_gateway import LanguageToolHttpGateway


class InfrastructureLanguageToolSpellCheckAdapter(TextCorrectionSpellCheckPort):
    def check(self, text: str, *, language: str) -> list[TextCorrectionSpellCheckIssue]:
        gateway = LanguageToolHttpGateway()
        payload = gateway.check(text, language=language)

        return payload if isinstance(payload, list) else []
