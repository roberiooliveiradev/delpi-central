from app.application.services.admin_guideline_prompt_service import (
    AdminGuidelinePromptService,
)


class FakeGuidelineRepository:
    def __init__(self, guidelines):
        self.guidelines = guidelines

    def list_active(self, *, environment=None):
        return self.guidelines


def test_build_active_guidelines_prompt_returns_empty_without_guidelines():
    prompt, guidelines = AdminGuidelinePromptService(
        FakeGuidelineRepository([])
    ).build_active_guidelines_prompt()

    assert prompt == ""
    assert guidelines == []


def test_build_active_guidelines_prompt_formats_active_guidelines():
    prompt, guidelines = AdminGuidelinePromptService(
        FakeGuidelineRepository(
            [
                {
                    "id": "1",
                    "title": "Não inventar",
                    "description": "Evitar alucinação",
                    "content": "Se não houver fonte suficiente, diga que não sabe.",
                    "category": "behavior",
                    "status": "active",
                }
            ]
        )
    ).build_active_guidelines_prompt()

    assert "Diretrizes administrativas globais ativas" in prompt
    assert "Não inventar" in prompt
    assert "Se não houver fonte suficiente" in prompt
    assert guidelines[0]["id"] == "1"
