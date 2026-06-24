from app.domain.services.chat_presentation_text_mode_service import (
    ChatPresentationTextModeService,
)


def test_enforce_single_text_decision_for_explicit_session():
    metadata = {
        "explicitSessionFormat": "text",
        "availableFormats": ["text", "table", "tree", "dashboard"],
        "presentationDecision": {
            "selected": "text",
            "layoutMode": "stack",
            "visualOrder": ["text", "table", "tree", "dashboard"],
            "availableViews": ["text", "table", "tree", "dashboard"],
        },
        "tablePresentations": [{"type": "table", "rows": []}],
        "treePresentation": {"type": "tree", "root": {}},
    }

    ChatPresentationTextModeService.enforce_single_text_decision(metadata)

    decision = metadata["presentationDecision"]

    assert decision["layoutMode"] == "single"
    assert decision["visualOrder"] == ["text"]
    assert metadata.get("tablePresentations") is not None
    assert metadata.get("treePresentation") is not None


def test_should_embed_in_markdown_for_stack_with_text_selected():
    metadata = {
        "preferredFormat": "text",
        "presentationDecision": {"selected": "text", "layoutMode": "stack"},
    }

    assert ChatPresentationTextModeService.should_embed_in_markdown(metadata) is False


def test_finalize_explicit_text_mode_preserves_payload_after_embed():
    metadata = {
        "explicitSessionFormat": "text",
        "availableFormats": ["text", "table", "tree"],
        "textPresentation": {
            "type": "markdown",
            "markdown": "### Resumo\n\n| A | B |\n| --- | --- |\n| 1 | 2 |",
        },
        "tablePresentations": [{"type": "table", "rows": []}],
        "treePresentation": {"type": "tree", "root": {}},
        "kpiPresentation": {"type": "kpi", "cards": []},
        "presentationDecision": {
            "selected": "text",
            "layoutMode": "stack",
            "visualOrder": ["text", "table", "tree"],
            "availableViews": ["text", "table", "tree"],
        },
    }

    ChatPresentationTextModeService.finalize_explicit_text_mode(metadata)

    assert metadata.get("tablePresentations") is not None
    assert metadata.get("treePresentation") is not None
    assert metadata.get("kpiPresentation") is not None
    assert metadata["presentationDecision"]["layoutMode"] == "single"
    assert metadata["presentationDecision"]["selected"] == "text"


def test_should_embed_in_markdown_for_explicit_text():
    metadata = {
        "explicitSessionFormat": "text",
        "presentationDecision": {"selected": "text", "layoutMode": "stack"},
    }

    assert ChatPresentationTextModeService.should_embed_in_markdown(metadata) is True
