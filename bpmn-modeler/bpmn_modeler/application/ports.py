from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Protocol, Sequence, TypeVar

from bpmn_modeler.domain.entities.model import Model
from bpmn_modeler.domain.entities.revision import Revision
from bpmn_modeler.domain.value_objects.canonical_bpmn_artifact import (
    CanonicalBpmnArtifact,
)

T = TypeVar("T")


class ClockPort(Protocol):
    def now(self) -> datetime:
        """Server-side clock (timezone-aware)."""
        ...


class IdGeneratorPort(Protocol):
    def new_model_id(self) -> str: ...
    def new_revision_id(self) -> str: ...
    def new_bpmn_id(self, prefix: str) -> str: ...


class BlankArtifactFactoryPort(Protocol):
    def new_blank_artifact(self) -> CanonicalBpmnArtifact:
        """Generate the canonical blank BPMN document (template contract)."""
        ...


@dataclass(frozen=True, slots=True)
class ModelSummaryRecord:
    id: str
    display_name: str
    archived_at: datetime | None
    version: int
    created_at: datetime
    updated_at: datetime
    latest_revision_number: int | None


class RepositoryError(Exception):
    """Base for repository adapter failures (maps to INFRASTRUCTURE_FAILURE)."""


class AggregateNotFoundError(RepositoryError):
    pass


class ConcurrencyConflictError(RepositoryError):
    def __init__(self, model_id: str, current_version: int) -> None:
        super().__init__(f"aggregate {model_id} is at version {current_version}")
        self.model_id = model_id
        self.current_version = current_version


class ModelRepositoryPort(Protocol):
    """Aggregate-oriented persistence: Model + WorkingCopy + Revisions."""

    def create_aggregate(self, model: Model) -> None: ...

    def get_aggregate(self, model_id: str) -> Model | None: ...

    def list_summaries(
        self,
        *,
        owner_subject: str,
        query: str | None,
        archived: str,
        sort: str,
        direction: str,
        offset: int,
        limit: int,
    ) -> Sequence[ModelSummaryRecord]:
        """Return up to `limit` records owned by `owner_subject`
        (caller passes page_size + 1). Required scope — fail-closed by
        contract: there is no global-collection path."""
        ...

    def mutate(
        self,
        model_id: str,
        expected_version: int,
        mutation: Callable[[Model], T],
    ) -> tuple[Model, T]:
        """Load the aggregate under lock, check version (CAS), apply the
        mutation, persist the whole aggregate atomically, return (model, out).

        Raises AggregateNotFoundError / ConcurrencyConflictError.
        """
        ...
