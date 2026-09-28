from __future__ import annotations

from abc import ABC, abstractmethod

from tm_app.domain.diagnostic.diagnostic import Diagnostic


class DiagnosticRepositoryPort(ABC):
    """Persistence boundary of the Diagnostic aggregate.

    The port speaks only in aggregates — never rows, dicts or sub-entity
    repositories. Findings, hypotheses, links and conclusions are persisted
    exclusively through their owning ``Diagnostic``.
    """

    @abstractmethod
    def get(self, diagnostic_id: str) -> Diagnostic | None:
        """Authoritative rehydration of a persisted aggregate."""
        raise NotImplementedError

    @abstractmethod
    def list_by_revision(self, revision_id: str) -> list[Diagnostic]:
        """All diagnostics anchored to a revision."""
        raise NotImplementedError

    @abstractmethod
    def create(self, diagnostic: Diagnostic) -> Diagnostic:
        """Persist a new aggregate in a single transaction."""
        raise NotImplementedError

    @abstractmethod
    def save(self, diagnostic: Diagnostic, *, expected_version: int) -> int:
        """Atomically persist mutations guarded by ``expected_version``.

        Returns the new aggregate version. Raises a concurrency error with
        code ``diagnostic.concurrent_modification`` when the stored version
        no longer equals ``expected_version``.
        """
        raise NotImplementedError
