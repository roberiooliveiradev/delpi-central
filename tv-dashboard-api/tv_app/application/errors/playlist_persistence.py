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


class PlaylistRevisionConflictError(RuntimeError):
    """CAS de ``playlists.revision`` falhou dentro da transação de escrita."""

    def __init__(
        self,
        current_revision: int,
        *,
        expected_revision: int | None = None,
    ) -> None:
        self.current_revision = current_revision
        self.expected_revision = expected_revision
        super().__init__(f"Revisão atual: {current_revision}")
