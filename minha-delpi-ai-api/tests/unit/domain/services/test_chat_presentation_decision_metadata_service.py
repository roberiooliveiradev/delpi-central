from app.domain.services.chat_presentation_decision_metadata_service import (
    ChatPresentationDecisionMetadataService,
)


def test_rows_from_metadata_tables_prefers_table_presentation():
    metadata = {
        "tablePresentation": {
            "type": "table",
            "rows": [{"filial": "01", "saldo": 10}],
        },
        "presentation": {"type": "markdown", "markdown": "x"},
    }

    rows = ChatPresentationDecisionMetadataService.rows_from_metadata_tables(metadata)

    assert len(rows) == 1
    assert rows[0]["filial"] == "01"


def test_view_has_presentation_detects_primary_table():
    metadata = {
        "presentation": {"type": "table", "rows": [{"a": 1}]},
    }

    assert ChatPresentationDecisionMetadataService.view_has_presentation(metadata, "table")
