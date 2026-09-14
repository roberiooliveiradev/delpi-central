"""Application-owned error contracts for TV Dashboard."""

from tv_app.application.errors.playlist_persistence import (
    MainSectionProtectedError,
    PlaylistNotFoundError,
    SectionNotFoundError,
    SlideNotFoundError,
)

__all__ = [
    "MainSectionProtectedError",
    "PlaylistNotFoundError",
    "SectionNotFoundError",
    "SlideNotFoundError",
]
