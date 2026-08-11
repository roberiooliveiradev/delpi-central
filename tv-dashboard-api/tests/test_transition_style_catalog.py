from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from tv_app.application.services.presentation_transition_catalog import (
    PRESENTATION_TRANSITION_STYLES,
    TRANSITION_STYLE_PATTERN,
)
from tv_app.interface.http.routes.section_routes import CreateSectionBody, UpdateSectionBody
from tv_app.interface.http.routes.slide_routes import CreateSlideBody, UpdateSlideBody


def test_catalog_accepts_wipe_across_http_contracts():
    assert "wipe" in PRESENTATION_TRANSITION_STYLES
    assert TRANSITION_STYLE_PATTERN.startswith("^(")
    assert (
        CreateSectionBody.model_validate({"name": "Seção", "transitionStyle": "wipe"}).transitionStyle
        == "wipe"
    )
    assert UpdateSectionBody.model_validate({"transitionStyle": "wipe"}).transitionStyle == "wipe"
    assert (
        CreateSlideBody.model_validate(
            {
                "slideType": "native",
                "title": "Tela",
                "nativeScreenKey": "custom_message",
                "transitionStyle": "wipe",
            }
        ).transitionStyle
        == "wipe"
    )
    assert UpdateSlideBody.model_validate({"transitionStyle": "wipe"}).transitionStyle == "wipe"


@pytest.mark.parametrize(
    ("model", "payload"),
    [
        (CreateSectionBody, {"name": "Seção", "transitionStyle": "origami"}),
        (UpdateSectionBody, {"transitionStyle": "origami"}),
        (
            CreateSlideBody,
            {
                "slideType": "native",
                "title": "Tela",
                "nativeScreenKey": "custom_message",
                "transitionStyle": "origami",
            },
        ),
        (UpdateSlideBody, {"transitionStyle": "origami"}),
    ],
)
def test_catalog_rejects_unknown_transition(model, payload):
    with pytest.raises(ValidationError):
        model.model_validate(payload)


def test_v014_updates_all_persisted_transition_constraints():
    sql = (
        Path(__file__).resolve().parents[1]
        / "migrations"
        / "V014__transition_styles_catalog.sql"
    ).read_text(encoding="utf-8")

    assert "ALTER TABLE tv_dashboard.playlists" in sql
    assert "ALTER TABLE tv_dashboard.slides" in sql
    assert "ALTER TABLE tv_dashboard.playlist_sections" in sql
    for style in PRESENTATION_TRANSITION_STYLES:
        assert f"'{style}'" in sql


def test_playlist_http_contract_uses_the_same_catalog_pattern():
    source = (
        Path(__file__).resolve().parents[1]
        / "tv_app"
        / "interface"
        / "http"
        / "routes"
        / "playlist_routes.py"
    ).read_text(encoding="utf-8")

    assert "transitionStyle: str | None = Field(default=None, pattern=TRANSITION_STYLE_PATTERN)" in source

