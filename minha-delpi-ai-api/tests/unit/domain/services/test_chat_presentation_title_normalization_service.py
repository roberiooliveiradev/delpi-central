"""Normalização declarativa de títulos — Playbook 12 A9/R24."""

from __future__ import annotations

from app.domain.services.chat_presentation_title_normalization_service import (
    ChatPresentationTitleNormalizationService,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)


def test_normalize_eficiencia_fabril_wrong_titles():
    metadata = {
        "tablePresentation": {"type": "table", "title": "Lista de LMPs"},
        "chartPresentation": {"type": "chart", "title": "Visualização dos dados"},
    }
    presenter = ExternalActionResultPresenter()

    ChatPresentationTitleNormalizationService.normalize_metadata(
        metadata,
        path="/production/eficiencia-fabril/dashboard",
        presenter=presenter,
    )

    assert metadata["tablePresentation"]["title"] == "Eficiência fabril"
    assert metadata["chartPresentation"]["title"] == "Eficiência fabril"


def test_normalize_skips_unrelated_paths():
    metadata = {
        "tablePresentation": {"type": "table", "title": "Lista de LMPs"},
    }
    presenter = ExternalActionResultPresenter()

    ChatPresentationTitleNormalizationService.normalize_metadata(
        metadata,
        path="/products/90269001/stock",
        presenter=presenter,
    )

    assert metadata["tablePresentation"]["title"] == "Lista de LMPs"
