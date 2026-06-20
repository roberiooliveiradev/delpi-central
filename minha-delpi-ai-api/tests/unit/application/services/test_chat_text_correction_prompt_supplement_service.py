from app.application.services.chat_text_correction_prompt_supplement_service import (
    ChatTextCorrectionPromptSupplementService,
)
from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_domain_config_service import ChatDomainConfigService
from app.domain.services.chat_text_correction_spell_check_service import (
    ChatTextCorrectionSpellCheckService,
)
from app.domain.ports.text_correction_spell_check_port import TextCorrectionSpellCheckPort


class _FakeSpellCheckPort(TextCorrectionSpellCheckPort):
    def check(self, text: str, *, language: str) -> list[dict]:
        return [
            {
                "offset": 2,
                "length": 4,
                "message": "Possível erro de ortografia.",
                "replacements": ["está"],
                "ruleId": "MORFOLOGIK_RULE_PT_BR",
                "category": "TYPOS",
            }
        ]


def test_prompt_supplement_includes_spell_preflight(monkeypatch):
    configure_domain_infrastructure_ports()
    monkeypatch.setattr(
        ChatDomainConfigService,
        "chat_text_correction_spell_check_enabled",
        classmethod(lambda cls: True),
    )
    ChatTextCorrectionSpellCheckService.configure(_FakeSpellCheckPort())

    workspace_context: dict = {}
    block = ChatTextCorrectionPromptSupplementService.build(
        message="corrija: o estoque esta baixo",
        text_correction_subtype="text_correct_basic",
        workspace_context=workspace_context,
    )

    assert "Pré-análise ortográfica" in block
    assert "está" in block
    assert workspace_context.get("textCorrectionSpellPreflight", {}).get("used") is True
