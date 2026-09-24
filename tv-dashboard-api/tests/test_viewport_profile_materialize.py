"""PRESENTATION-001 — viewport screen authority materialization."""

from __future__ import annotations

from tv_app.application.services.viewport_profile_service import (
    resolve_effective_viewport_px,
    viewport_fields_from_playlist_row,
)


def test_named_profile_materializes_px() -> None:
    profile, w, h = resolve_effective_viewport_px(viewport_profile="1080p")
    assert profile == "1080p"
    assert (w, h) == (1920, 1080)


def test_portrait_profile() -> None:
    profile, w, h = resolve_effective_viewport_px(viewport_profile="1080p_portrait")
    assert profile == "1080p_portrait"
    assert (w, h) == (1080, 1920)


def test_custom_uses_stored_dims() -> None:
    profile, w, h = resolve_effective_viewport_px(
        viewport_profile="custom",
        viewport_width=800,
        viewport_height=600,
    )
    assert profile == "custom"
    assert (w, h) == (800, 600)


def test_playlist_row_fields_named() -> None:
    fields = viewport_fields_from_playlist_row(
        {"viewport_profile": "720p", "viewport_width": None, "viewport_height": None}
    )
    assert fields == {
        "viewportProfile": "720p",
        "viewportWidth": 1280,
        "viewportHeight": 720,
    }
