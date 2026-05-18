from app.application.services.admin_guideline_prompt_service import AdminGuidelinePromptService


class FakeGuidelineRepository:
    def list_active(self, environment=None, categories=None):
        return [
            {
                "id": "1",
                "title": "Regra",
                "category": "behavior",
                "status": "active",
                "description": "Desc",
                "content": "Conteúdo da regra.",
            }
        ]


def test_build_active_guidelines_prompt_uses_real_newlines():
    service = AdminGuidelinePromptService(FakeGuidelineRepository())

    prompt, guidelines = service.build_active_guidelines_prompt()

    assert guidelines
    assert "\n" in prompt
    assert "\\n" not in prompt
    assert "Conteúdo da regra." in prompt
