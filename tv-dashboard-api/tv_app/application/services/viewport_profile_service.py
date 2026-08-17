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


def clamp_viewport_px(value: int | float) -> int:
    return max(VIEWPORT_PX_MIN, min(VIEWPORT_PX_MAX, int(round(value))))


def is_named_viewport_profile(profile: str | None) -> bool:
    return bool(profile and str(profile).strip() in NAMED_VIEWPORT_PROFILES)


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
    width = row.get("viewport_width")
    height = row.get("viewport_height")
    return {
        "viewportWidth": int(width) if width is not None else None,
        "viewportHeight": int(height) if height is not None else None,
    }
