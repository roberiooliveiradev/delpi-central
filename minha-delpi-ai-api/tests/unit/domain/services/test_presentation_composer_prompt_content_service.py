"""Contract: composer prompts live in assistant content JSON."""

from app.domain.services.presentation_composer_prompt_content_service import (
    PresentationComposerPromptContentService,
)


def test_prompt_content_keys_present():
    """Positive: bundle carrega system/repair/knobs."""
    system = PresentationComposerPromptContentService.system_prompt()
    assert "PresentationSpec" in system
    assert "hex" in system.lower() or "CSS" in system
    repair = PresentationComposerPromptContentService.repair_prompt(
        errors=["invalid_json"],
        previous="{",
    )
    assert "invalid_json" in repair
    assert "{" in repair
    assert "dashboard" in PresentationComposerPromptContentService.knobs_by_view()


def test_prompt_contract_snapshot_keys():
    """Sibling: keys canônicas do bundle."""
    keys = PresentationComposerPromptContentService.prompt_contract_keys()
    assert keys == {
        "systemPrompt",
        "repairPromptTemplate",
        "allowedPaletteFamilies",
        "rules",
        "knobsByView",
        "allowedViews",
    }


def test_prompt_forbids_css_request():
    """Negative: system não pede CSS ao modelo."""
    system = PresentationComposerPromptContentService.system_prompt().lower()
    assert "write css" not in system
    assert "background-color" not in system
    assert "never invent" in system or "never invent fields" in system
