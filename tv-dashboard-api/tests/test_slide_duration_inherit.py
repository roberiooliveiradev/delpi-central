"""Contrato de limpeza de durationSec (herança) no update de slide."""

from __future__ import annotations

from tv_app.application.services.playlist_section_inheritance_service import (
    resolve_slide_duration_sec,
)
from tv_app.interface.http.routes.slide_routes import UpdateSlideBody


def test_update_slide_body_accepts_null_duration():
    body = UpdateSlideBody.model_validate({"durationSec": None})
    assert "durationSec" in body.model_fields_set
    assert body.durationSec is None
    dumped = body.model_dump(exclude_unset=True)
    assert dumped == {"durationSec": None}


def test_update_slide_body_rejects_out_of_range_duration():
    try:
        UpdateSlideBody.model_validate({"durationSec": 3})
        assert False, "expected validation error"
    except Exception:
        pass


def test_update_slide_body_accepts_duration_override():
    body = UpdateSlideBody.model_validate({"durationSec": 20})
    assert body.durationSec == 20


def test_null_duration_resolves_to_playlist_or_section_default():
    assert (
        resolve_slide_duration_sec(
            slide_duration=None,
            section_default=None,
            playlist_default=30,
        )
        == 30
    )
    assert (
        resolve_slide_duration_sec(
            slide_duration=None,
            section_default=15,
            playlist_default=30,
        )
        == 15
    )
    assert (
        resolve_slide_duration_sec(
            slide_duration=10,
            section_default=15,
            playlist_default=30,
        )
        == 10
    )
