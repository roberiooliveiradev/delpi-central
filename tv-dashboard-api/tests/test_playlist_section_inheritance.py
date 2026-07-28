from __future__ import annotations

from tv_app.application.services.playlist_section_inheritance_service import (
    is_slide_visible_in_presentation,
    merge_master_configs,
    resolve_slide_duration_sec,
    resolve_slide_transition_style,
)


def test_merge_master_section_overrides_playlist_fields():
    playlist = {
        "enabled": True,
        "background": {"type": "color", "value": "#111"},
        "logo": {"opacity": 0.5},
    }
    section = {
        "enabled": True,
        "background": {"type": "color", "value": "#222"},
    }
    merged = merge_master_configs(playlist, section)
    assert merged is not None
    assert merged["enabled"] is True
    assert merged["background"]["value"] == "#222"
    assert merged["logo"]["opacity"] == 0.5


def test_merge_master_playlist_only_when_section_disabled():
    playlist = {"enabled": True, "background": {"type": "color", "value": "#111"}}
    section = {"enabled": False, "background": {"type": "color", "value": "#222"}}
    merged = merge_master_configs(playlist, section)
    assert merged is not None
    assert merged["background"]["value"] == "#111"


def test_resolve_duration_and_transition_cascade():
    assert resolve_slide_duration_sec(
        slide_duration=12,
        section_default=20,
        playlist_default=30,
    ) == 12
    assert resolve_slide_duration_sec(
        slide_duration=None,
        section_default=20,
        playlist_default=30,
    ) == 20
    assert resolve_slide_transition_style(
        slide_transition=None,
        section_transition="slide",
        playlist_transition="fade",
    ) == "slide"


def test_slide_hidden_when_section_inactive():
    assert is_slide_visible_in_presentation(slide_active=True, section=None) is True
    assert (
        is_slide_visible_in_presentation(
            slide_active=True,
            section={"isActive": False},
        )
        is False
    )
    assert (
        is_slide_visible_in_presentation(
            slide_active=False,
            section={"isActive": True},
        )
        is False
    )
