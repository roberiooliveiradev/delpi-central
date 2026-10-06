from __future__ import annotations

import copy
import hashlib

import pytest

from bpmn_modeler.application.ports import (
    AggregateNotFoundError,
    ConcurrencyConflictError,
    ModelSummaryRecord,
)
from bpmn_modeler.application.use_cases import (
    BpmnModelerService,
    CallerIdentity,
)
from bpmn_modeler.application.validation import InputSafetyEvidence
from bpmn_modeler.infrastructure.runtime import SystemClock, UuidGenerator
from bpmn_modeler.infrastructure.validation.blank import (
    TemplateBlankArtifactFactory,
)
from bpmn_modeler.infrastructure.validation.engine import LxmlBpmnValidator
from bpmn_modeler.infrastructure.validation.intake import intake_bytes

ALL_PERMISSIONS = frozenset(
    {"bpmn-modeler.view", "bpmn-modeler.edit", "bpmn-modeler.manage"}
)


def clean_evidence(content: bytes | str) -> InputSafetyEvidence:
    raw = content.encode("utf-8") if isinstance(content, str) else content
    return intake_bytes(raw).evidence


def clean_input(content: bytes | str):
    from bpmn_modeler.application.use_cases import ArtifactInput

    raw = content.encode("utf-8") if isinstance(content, str) else content
    intake = intake_bytes(raw)
    return ArtifactInput(artifact=intake.artifact, evidence=intake.evidence)


class InMemoryRepository:
    def __init__(self) -> None:
        self.store: dict[str, object] = {}

    def create_aggregate(self, model) -> None:
        self.store[model.id] = copy.deepcopy(model)

    def get_aggregate(self, model_id: str):
        return copy.deepcopy(self.store.get(model_id))

    def list_summaries(
        self, *, owner_subject, query, archived, sort, direction, offset, limit
    ):
        rows = [
            m
            for m in self.store.values()
            if m.created_by == owner_subject
            if (archived == "all")
            or (archived == "active" and m.archived_at is None)
            or (archived == "archived" and m.archived_at is not None)
        ]
        if query:
            q = query.lower()
            rows = [r for r in rows if q in r.display_name.lower() or r.id == query]
        key = {
            "updated_at": lambda m: m.updated_at,
            "created_at": lambda m: m.created_at,
            "display_name": lambda m: m.display_name.lower(),
        }[sort]
        rows.sort(key=key, reverse=(direction == "desc"))
        return [
            ModelSummaryRecord(
                id=m.id,
                display_name=m.display_name,
                archived_at=m.archived_at,
                version=m.version,
                created_at=m.created_at,
                updated_at=m.updated_at,
                latest_revision_number=(
                    m.latest_revision.revision_number if m.latest_revision else None
                ),
            )
            for m in rows[offset : offset + limit]
        ]

    def mutate(self, model_id: str, expected_version: int, mutation):
        if model_id not in self.store:
            raise AggregateNotFoundError(model_id)
        model = self.store[model_id]
        if model.version != expected_version:
            raise ConcurrencyConflictError(model_id, model.version)
        outcome = mutation(model)
        return copy.deepcopy(model), outcome


@pytest.fixture(scope="session")
def validator():
    return LxmlBpmnValidator()


@pytest.fixture()
def repository():
    return InMemoryRepository()


@pytest.fixture()
def service(repository, validator):
    return BpmnModelerService(
        repository=repository,
        validator=validator,
        input_safety=validator,
        blank_artifacts=TemplateBlankArtifactFactory(UuidGenerator()),
        clock=SystemClock(),
        ids=UuidGenerator(),
    )


@pytest.fixture()
def caller():
    return CallerIdentity(subject="user-1", permissions=ALL_PERMISSIONS)


@pytest.fixture()
def model_id(service, caller):
    return service.create_model("Fixture Model", caller).model_id
