"""E2.S2 — generalização de ResultPresentationTitleResolver."""

from __future__ import annotations

from app.domain.services.result_presentation_title_resolver import (
    SOURCE_ACTION_DISPLAY_LABEL,
    SOURCE_PRESENTATION_TITLE,
    SOURCE_SLOT_TITLE,
    SOURCE_TECHNICAL_FALLBACK,
    ResultPresentationTitleResolver,
)


def test_title_slot_wins():
    resolved = ResultPresentationTitleResolver.resolve(
        path="/any/path",
        slot_title="Título do slot",
        legacy_title="Legado",
        summary="Summary",
    )
    assert resolved.title == "Título do slot"
    assert resolved.source == SOURCE_SLOT_TITLE


def test_title_presentation_metadata():
    resolved = ResultPresentationTitleResolver.resolve(
        path="/acme/widgets",
        metadata={"presentation": {"title": "Painel de widgets"}},
        legacy_title="Não usar",
    )
    assert resolved.title == "Painel de widgets"
    assert resolved.source == SOURCE_PRESENTATION_TITLE


def test_title_action_label_without_path_catalog():
    resolved = ResultPresentationTitleResolver.resolve(
        path="/acme/widgets/{id}/inventory",
        summary="Consultar inventário de widgets",
        legacy_title=None,
        fallback="Resultado",
    )
    assert resolved.source == SOURCE_ACTION_DISPLAY_LABEL
    assert "inventário" in resolved.title.casefold()


def test_title_metamorphic_path_rename_same_summary():
    summary = "Consultar disponibilidade de item"
    a = ResultPresentationTitleResolver.resolve(path="/v1/a", summary=summary)
    b = ResultPresentationTitleResolver.resolve(path="/v2/b", summary=summary)
    assert a.title == b.title == summary


def test_title_unknown_api_fallback():
    resolved = ResultPresentationTitleResolver.resolve(
        path="/fleet/vehicles/telemetry",
        summary="",
        action_id="",
        fallback="Resultado",
    )
    assert resolved.title
    assert resolved.source in {
        SOURCE_ACTION_DISPLAY_LABEL,
        SOURCE_TECHNICAL_FALLBACK,
    }


def test_title_default_ignores_legacy_title_argument():
    resolved = ResultPresentationTitleResolver.resolve(
        path="/products/x/stock",
        summary="Consultar estoque do produto",
        legacy_title="Título legado path-based",
        fallback="Resultado",
    )
    assert resolved.title == "Consultar estoque do produto"
    assert resolved.source == SOURCE_ACTION_DISPLAY_LABEL
