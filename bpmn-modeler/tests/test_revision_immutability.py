"""Revision append-only regression — DB-ISO-12 / T18.

With the shared ``plugins_user`` credential, append-only cannot rely on
DB-role denial. The invariant is an application/repository contract:

- no use case mutates or deletes a revision;
- ``ModelRepositoryPort`` exposes no revision update/delete operation;
- ``PostgresModelRepository`` never emits ``UPDATE``/``DELETE`` on
  ``bpmn_modeler.revisions``;
- ``Revision`` domain entity is immutable (frozen dataclass).

These tests run without a database (static contract) plus an integration
probe in ``test_repository_integration.py``.
"""
from __future__ import annotations

import inspect
import re
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_SRC = (
    BACKEND_ROOT / "bpmn_modeler" / "infrastructure" / "persistence" / "repository.py"
).read_text()
PORTS_SRC = (
    BACKEND_ROOT / "bpmn_modeler" / "application" / "ports.py"
).read_text()
MIGRATIONS_DIR = BACKEND_ROOT / "migrations"

MUTATING_REVISION_SQL = re.compile(
    r"\b(UPDATE|DELETE\s+FROM)\s+[\"`]?\w*\.?[\"`]?revisions\b",
    re.IGNORECASE,
)


def test_repository_never_mutates_revisions() -> None:
    """No UPDATE/DELETE against revisions in the repository layer."""
    assert not MUTATING_REVISION_SQL.search(REPO_SRC), (
        "PostgresModelRepository must never UPDATE/DELETE bpmn_modeler.revisions"
    )


def test_repository_inserts_revisions_with_schema_qualification() -> None:
    """Revision writes are schema-qualified INSERTs into bpmn_modeler.revisions."""
    inserts = re.findall(
        r"INSERT\s+INTO\s+[\"`]?bpmn_modeler[\"`]?\.[\"`]?revisions[\"`]?",
        REPO_SRC,
        re.IGNORECASE,
    )
    assert inserts, "expected schema-qualified INSERT INTO bpmn_modeler.revisions"


def test_port_has_no_revision_mutation_operation() -> None:
    """ModelRepositoryPort exposes no update/delete for revisions."""
    from bpmn_modeler.application.ports import ModelRepositoryPort

    names = [
        name
        for name, _ in inspect.getmembers(ModelRepositoryPort)
        if not name.startswith("_")
    ]
    forbidden = [
        n
        for n in names
        if re.search(r"(update|delete|remove|drop)", n, re.IGNORECASE)
        and re.search(r"revision", n, re.IGNORECASE)
    ]
    assert forbidden == [], f"port leaks revision mutation ops: {forbidden}"
    for name in names:
        assert not re.search(
            r"revision.*(update|delete)|(update|delete).*revision", name, re.I
        ), name


def test_revision_entity_is_immutable() -> None:
    """Domain Revision is a frozen dataclass — no in-place mutation."""
    from bpmn_modeler.domain.entities.revision import Revision

    params = getattr(Revision, "__dataclass_params__", None)
    assert params is not None and params.frozen, "Revision must be frozen"

    from bpmn_modeler.domain.entities.working_copy import WorkingCopy
    from bpmn_modeler.domain.value_objects.canonical_bpmn_artifact import (
        CanonicalBpmnArtifact,
    )
    from bpmn_modeler.domain.entities.revision import RevisionOrigin
    from datetime import datetime, timezone
    import uuid

    rev = Revision(
        revision_id=str(uuid.uuid4()),
        revision_number=1,
        artifact=WorkingCopy(
            CanonicalBpmnArtifact("<definitions/>")
        ).artifact,
        checksum="a" * 64,
        created_at=datetime.now(timezone.utc),
        created_by="test",
        origin=RevisionOrigin.EXPLICIT,
    )
    with pytest.raises(Exception):
        rev.revision_number = 2  # type: ignore[misc]


def test_no_migration_mutates_historical_revisions() -> None:
    """Migrations never rewrite or delete revision rows."""
    for migration in MIGRATIONS_DIR.glob("V*.sql"):
        src = migration.read_text()
        assert not MUTATING_REVISION_SQL.search(src), (
            f"{migration.name} mutates revisions"
        )


def test_service_has_no_revision_delete_use_case() -> None:
    """The application service exposes no revision update/delete use case."""
    from bpmn_modeler.application.use_cases import BpmnModelerService

    names = [n for n in dir(BpmnModelerService) if not n.startswith("_")]
    violations = [
        n
        for n in names
        if "revision" in n.lower()
        and re.search(r"(update|delete|remove|drop)", n, re.IGNORECASE)
    ]
    assert violations == [], f"use cases leak revision mutation: {violations}"
