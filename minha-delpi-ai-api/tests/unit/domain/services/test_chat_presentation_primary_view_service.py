from app.domain.services.chat_presentation_primary_view_service import (
    ChatPresentationPrimaryViewService,
)


def test_apply_session_preference_noop_for_auto():
    metadata = {"presentation": {"type": "table", "rows": []}}

    applied = ChatPresentationPrimaryViewService.apply_session_preference(metadata, "auto")

    assert applied is False
    assert "explicitSessionFormat" not in metadata


def test_apply_text_primary_moves_kpi_to_secondary():
    kpi = {"type": "kpi", "title": "RH", "cards": []}
    metadata = {"presentation": kpi, "textPresentation": {"type": "markdown", "markdown": "x"}}

    ChatPresentationPrimaryViewService.apply_session_preference(metadata, "text")

    assert metadata["presentation"] is None
    assert metadata["kpiPresentation"] == kpi


def test_apply_session_table_promotes_list_from_table_presentations():
    table = {
        "type": "table",
        "role": "list",
        "title": "Estoque",
        "rows": [{"branch": "01", "current_quantity": 10}],
    }
    metadata = {
        "presentation": None,
        "textPresentation": {"type": "markdown", "markdown": "Resumo"},
        "tablePresentations": [table],
    }

    ChatPresentationPrimaryViewService.apply_session_preference(metadata, "table")

    assert metadata["presentation"] == table
    assert metadata["preferredFormat"] == "table"
