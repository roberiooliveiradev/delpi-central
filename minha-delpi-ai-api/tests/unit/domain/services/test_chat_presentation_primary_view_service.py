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


def test_finalize_decision_alignment_recovers_stale_text_explicit_for_table():
    table = {
        "type": "table",
        "title": "Posições",
        "rows": [{"branch": "01", "current_quantity": 10}],
    }
    metadata = {
        "explicitSessionFormat": "text",
        "preferredFormat": "table",
        "presentation": table,
        "presentationDecision": {
            "selected": "table",
            "layoutMode": "single",
            "visualOrder": ["table"],
        },
    }

    ChatPresentationPrimaryViewService.finalize_decision_alignment(metadata)

    assert metadata["explicitSessionFormat"] == "table"
    assert metadata["presentation"] == table
    assert metadata["presentationDecision"]["visualOrder"] == ["table"]


def test_finalize_explicit_dashboard_preserves_full_bundle_for_toolbar():
    dashboard = {
        "type": "dashboard",
        "title": "Painel fabril — 90269002",
        "panels": [
            {
                "id": "kpi",
                "title": "Indicadores fabris — 90269002",
                "presentation": {
                    "type": "kpi",
                    "title": "Indicadores fabris — 90269002",
                    "cards": [{"label": "OPs", "value": "1"}],
                },
            },
        ],
    }
    metadata = {
        "explicitSessionFormat": "dashboard",
        "preferredFormat": "dashboard",
        "presentation": dashboard,
        "treePresentation": {"type": "tree", "title": "Estrutura", "root": {}},
        "chartPresentation": {"type": "chart", "data": []},
        "textPresentation": {
            "type": "markdown",
            "title": "Status fabril",
            "markdown": "### Status\n\nNarrativa longa que não deve ir junto ao painel.",
        },
        "presentationDecision": {
            "selected": "dashboard",
            "layoutMode": "stack",
            "availableViews": ["text", "tree", "chart", "dashboard"],
            "visualOrder": ["text", "tree", "chart", "dashboard"],
        },
    }

    ChatPresentationPrimaryViewService.finalize_explicit_native_single_view(metadata)

    assert metadata.get("presentation", {}).get("type") == "dashboard"
    assert metadata.get("treePresentation") is not None
    assert metadata.get("chartPresentation") is not None
    assert "Narrativa longa" in metadata["textPresentation"]["markdown"]
    assert metadata["presentationDecision"]["layoutMode"] == "stack"
