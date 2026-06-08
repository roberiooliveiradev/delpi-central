from app.application.use_cases.execute_external_action_use_case import (
    ExecuteExternalActionUseCase,
)


def test_align_presentation_prefers_kpi_cards_over_duplicate_text():
    metadata = {
        "presentationDecision": {"selected": "kpi"},
        "presentation": {"type": "kpi", "title": "Snapshot de RH", "cards": []},
        "textPresentation": {
            "type": "markdown",
            "title": "Snapshot de RH",
            "markdown": "### Snapshot de RH\n\n**PDIs ativos:** 334",
        },
    }
    kpi = {"type": "kpi", "title": "Snapshot de RH", "cards": [{"label": "PDIs ativos", "value": 334}]}

    ExecuteExternalActionUseCase._align_presentation_with_decision(
        metadata,
        kpi_presentation=kpi,
    )

    assert metadata["presentation"] == kpi
    assert metadata["textPresentation"]["markdown"] == "### Snapshot de RH"


def test_align_presentation_text_mode_hides_kpi_primary():
    kpi = {"type": "kpi", "title": "Snapshot de RH", "cards": []}
    metadata = {
        "presentationDecision": {"selected": "text"},
        "presentation": kpi,
        "textPresentation": {
            "type": "markdown",
            "title": "Snapshot de RH",
            "markdown": "### Snapshot de RH\n\n**PDIs ativos:** 334",
        },
    }

    ExecuteExternalActionUseCase._align_presentation_with_decision(
        metadata,
        kpi_presentation=kpi,
    )

    assert metadata["presentation"] is None
    assert metadata["kpiPresentation"] == kpi
