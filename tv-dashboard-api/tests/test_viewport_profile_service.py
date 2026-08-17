from tv_app.application.services.viewport_profile_service import (
    clamp_viewport_px,
    normalize_playlist_viewport_update,
)


def test_normalize_named_preset_clears_dims():
    profile, width, height, clear = normalize_playlist_viewport_update(
        viewport_profile="1080p",
        viewport_width=100,
        viewport_height=70,
        profile_provided=True,
        dims_provided=True,
    )
    assert profile == "1080p"
    assert width is None and height is None
    assert clear is True


def test_normalize_custom_requires_dims():
    try:
        normalize_playlist_viewport_update(
            viewport_profile="custom",
            viewport_width=None,
            viewport_height=None,
            profile_provided=True,
            dims_provided=False,
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "personalizada" in str(exc).lower() or "largura" in str(exc).lower()


def test_normalize_custom_clamps():
    profile, width, height, clear = normalize_playlist_viewport_update(
        viewport_profile="custom",
        viewport_width=10,
        viewport_height=9000,
        profile_provided=True,
        dims_provided=True,
    )
    assert profile == "custom"
    assert width == clamp_viewport_px(10)
    assert height == clamp_viewport_px(9000)
    assert clear is False
