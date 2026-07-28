"""Herança de defaults/master da seção → slide (contrato presentation payload)."""

from __future__ import annotations

from typing import Any


def merge_master_configs(
    playlist_master: dict[str, Any] | None,
    section_master: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """
    Empilha master da seção sob o da playlist.
    Campos preenchidos da seção (quando enabled) vencem; resto herda da playlist.
    """
    pl = playlist_master if isinstance(playlist_master, dict) else {}
    sec = section_master if isinstance(section_master, dict) else {}
    pl_on = bool(pl.get("enabled"))
    sec_on = bool(sec.get("enabled"))
    if not pl_on and not sec_on:
        return None

    base: dict[str, Any] = {}
    if pl_on:
        base = {**pl, "enabled": True}
    if sec_on:
        merged = {**base, **{k: v for k, v in sec.items() if v is not None}, "enabled": True}
        if isinstance(sec.get("background"), dict):
            merged["background"] = {
                **(base.get("background") if isinstance(base.get("background"), dict) else {}),
                **sec["background"],
            }
        if isinstance(sec.get("logo"), dict):
            merged["logo"] = {
                **(base.get("logo") if isinstance(base.get("logo"), dict) else {}),
                **sec["logo"],
            }
        return merged
    return base if pl_on else None


def resolve_slide_duration_sec(
    *,
    slide_duration: int | None,
    section_default: int | None,
    playlist_default: int | None,
    fallback: int = 30,
) -> int:
    if slide_duration is not None:
        return int(slide_duration)
    if section_default is not None:
        return int(section_default)
    if playlist_default is not None:
        return int(playlist_default)
    return fallback


def resolve_slide_transition_style(
    *,
    slide_transition: str | None,
    section_transition: str | None,
    playlist_transition: str | None,
    fallback: str = "fade",
) -> str | None:
    if slide_transition:
        return slide_transition
    if section_transition:
        return section_transition
    if playlist_transition:
        return playlist_transition
    return fallback


def is_slide_visible_in_presentation(
    *,
    slide_active: bool,
    section: dict[str, Any] | None,
) -> bool:
    if not slide_active:
        return False
    if section is not None and not section.get("isActive", True):
        return False
    return True
