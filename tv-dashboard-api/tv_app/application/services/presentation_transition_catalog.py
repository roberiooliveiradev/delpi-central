"""Catálogo persistível de transições da programação."""

from __future__ import annotations

PRESENTATION_TRANSITION_STYLES = (
    "fade",
    "dissolve",
    "slide",
    "push",
    "wipe",
    "zoom",
    "none",
)

TRANSITION_STYLE_PATTERN = rf"^({'|'.join(PRESENTATION_TRANSITION_STYLES)})$"

