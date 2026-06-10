from app.domain.services.chat_presentation_text_mode_service import (
    ChatPresentationTextModeService,
)


def test_enforce_single_text_decision_for_explicit_session():
    metadata = {
        "explicitSessionFormat": "text",
        "presentationDecision": {
            "selected": "text",
            "layoutMode": "stack",
            "visualOrder": ["text", "table", "tree"],
            "availableViews": ["text", "table", "tree"],
        },
    }

    ChatPresentationTextModeService.enforce_single_text_decision(metadata)

    decision = metadata["presentationDecision"]

    assert decision["layoutMode"] == "single"
    assert decision["visualOrder"] == ["text"]


def test_strip_native_visual_slots_on_explicit_text():
    metadata = {
        "explicitSessionFormat": "text",
        "textPresentation": {"type": "markdown", "markdown": "### Resumo\n\n| A | B |"},
        "tablePresentations": [{"type": "table", "rows": []}],
        "treePresentation": {"type": "tree", "root": {}},
        "kpiPresentation": {"type": "kpi", "cards": []},
        "presentationDecision": {"selected": "text", "layoutMode": "stack"},
    }

    ChatPresentationTextModeService.strip_native_visual_slots(metadata)

    assert metadata.get("tablePresentations") is None
    assert metadata.get("treePresentation") is None
    assert metadata.get("kpiPresentation") is None
    assert metadata["presentationDecision"]["layoutMode"] == "single"


def test_should_embed_in_markdown_for_stack_with_text_selected():
    metadata = {
        "preferredFormat": "text",
        "presentationDecision": {"selected": "text", "layoutMode": "stack"},
    }

    assert ChatPresentationTextModeService.should_embed_in_markdown(metadata) is False


def test_should_embed_in_markdown_for_explicit_text_even_in_stack():
    metadata = {
        "explicitSessionFormat": "text",
        "presentationDecision": {"selected": "text", "layoutMode": "stack"},
    }

    assert ChatPresentationTextModeService.should_embed_in_markdown(metadata) is True
