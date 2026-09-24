"""Normalização de viewportProfile + dimensões custom (px)."""

from __future__ import annotations

from typing import Any

NAMED_VIEWPORT_PROFILES = frozenset(
    {
        "720p",
        "1080p",
        "1366x768",
        "1920x1200",
        "2560x1440",
        "4k",
        "3840x1080",
        "1080p_portrait",
        "768x1366",
    }
)
CUSTOM_VIEWPORT_PROFILE = "custom"
VIEWPORT_PX_MIN = 64
VIEWPORT_PX_MAX = 7680

# Canonical pixel sizes for named profiles (PRESENTATION-001 screen authority).
# Clients must prefer materialized width/height from API/present payload.
NAMED_VIEWPORT_PIXEL_SIZES: dict[str, tuple[int, int]] = {
    "720p": (1280, 720),
    "1080p": (1920, 1080),
    "1366x768": (1366, 768),
    "1920x1200": (1920, 1200),
    "2560x1440": (2560, 1440),
    "4k": (3840, 2160),
    "3840x1080": (3840, 1080),
    "1080p_portrait": (1080, 1920),
    "768x1366": (768, 1366),
}
DEFAULT_VIEWPORT_PROFILE = "1080p"


def clamp_viewport_px(value: int | float) -> int:
    return max(VIEWPORT_PX_MIN, min(VIEWPORT_PX_MAX, int(round(value))))


def is_named_viewport_profile(profile: str | None) -> bool:
    return bool(profile and str(profile).strip() in NAMED_VIEWPORT_PROFILES)


def resolve_effective_viewport_px(
    *,
    viewport_profile: str | None,
    viewport_width: int | None = None,
    viewport_height: int | None = None,
) -> tuple[str, int, int]:
    """Return (profile, width, height) always materializado para paint/TV.

    Named profiles resolve from the canonical map; custom uses stored dims
    (fallback 1080p if invalid). Profile id remains the persisted setting;
    width/height are the materialized response fields.
    """
    profile = str(viewport_profile or "").strip() or DEFAULT_VIEWPORT_PROFILE
    if profile == CUSTOM_VIEWPORT_PROFILE:
        try:
            width = int(viewport_width) if viewport_width is not None else 0
            height = int(viewport_height) if viewport_height is not None else 0
        except (TypeError, ValueError):
            width, height = 0, 0
        if width > 0 and height > 0:
            return CUSTOM_VIEWPORT_PROFILE, clamp_viewport_px(width), clamp_viewport_px(height)
        w, h = NAMED_VIEWPORT_PIXEL_SIZES[DEFAULT_VIEWPORT_PROFILE]
        return DEFAULT_VIEWPORT_PROFILE, w, h
    if profile in NAMED_VIEWPORT_PIXEL_SIZES:
        w, h = NAMED_VIEWPORT_PIXEL_SIZES[profile]
        return profile, w, h
    w, h = NAMED_VIEWPORT_PIXEL_SIZES[DEFAULT_VIEWPORT_PROFILE]
    return DEFAULT_VIEWPORT_PROFILE, w, h


def normalize_playlist_viewport_update(
    *,
    viewport_profile: str | None,
    viewport_width: int | None,
    viewport_height: int | None,
    profile_provided: bool,
    dims_provided: bool,
) -> tuple[str | None, int | None, int | None, bool]:
    """Retorna (profile, width, height, clear_dims).

    clear_dims=True força NULL nas colunas (preset nomeado).
    """
    profile = viewport_profile.strip() if isinstance(viewport_profile, str) else viewport_profile

    if profile_provided and profile is not None:
        if profile == CUSTOM_VIEWPORT_PROFILE:
            if viewport_width is None or viewport_height is None:
                raise ValueError("Resolução personalizada exige largura e altura em pixels.")
            return (
                CUSTOM_VIEWPORT_PROFILE,
                clamp_viewport_px(viewport_width),
                clamp_viewport_px(viewport_height),
                False,
            )
        if is_named_viewport_profile(profile):
            return profile, None, None, True
        raise ValueError(f"Perfil de resolução inválido: {profile}")

    if dims_provided:
        if viewport_width is None or viewport_height is None:
            raise ValueError("Informe largura e altura juntas.")
        return None, clamp_viewport_px(viewport_width), clamp_viewport_px(viewport_height), False

    return None, None, None, False


def viewport_fields_from_playlist_row(row: dict[str, Any]) -> dict[str, Any]:
    """Materialize effective viewport px for API/present consumers.

    Named profiles: DB stores null dims; response always includes resolved px.
    Custom: DB stores dims; response echoes clamped stored values.
    """
    raw_profile = row.get("viewport_profile") or DEFAULT_VIEWPORT_PROFILE
    width = row.get("viewport_width")
    height = row.get("viewport_height")
    stored_w = int(width) if width is not None else None
    stored_h = int(height) if height is not None else None
    profile, effective_w, effective_h = resolve_effective_viewport_px(
        viewport_profile=str(raw_profile),
        viewport_width=stored_w,
        viewport_height=stored_h,
    )
    return {
        "viewportProfile": profile,
        "viewportWidth": effective_w,
        "viewportHeight": effective_h,
    }
