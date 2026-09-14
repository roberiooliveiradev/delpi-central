"""Semantic playlist persistence errors — application-owned contract.

Infrastructure adapters raise these types; they must not be defined under
``tv_app.infrastructure``.
"""

from __future__ import annotations


class PlaylistNotFoundError(LookupError):
    pass


class SlideNotFoundError(LookupError):
    pass


class SectionNotFoundError(LookupError):
    pass


class MainSectionProtectedError(ValueError):
    """Seção principal não pode ser excluída."""

    pass
