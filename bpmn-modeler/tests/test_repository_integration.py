"""Integration test — real PostgreSQL.

Runs only when PLUGINS_DB_* env vars point at a reachable, migrated
plugins_hub database with the bpmn_modeler schema. Verifies the
PostgresModelRepository CAS/list/append contract end-to-end.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("PLUGINS_DB_HOST"),
    reason="PLUGINS_DB_* not set — requires migrated plugins_hub DB",
)

from bpmn_modeler.application.ports import (
    AggregateNotFoundError,
    ConcurrencyConflictError,
)
from bpmn_modeler.domain.entities.model import Model
from bpmn_modeler.domain.entities.revision import Revision, RevisionOrigin
from bpmn_modeler.domain.entities.working_copy import WorkingCopy
from bpmn_modeler.domain.value_objects.canonical_bpmn_artifact import (
    CanonicalBpmnArtifact,
)
from bpmn_modeler.infrastructure.persistence.repository import (
    PostgresModelRepository,
)

XML_A = '<?xml version="1.0" encoding="UTF-8"?><definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" id="d1" targetNamespace="urn:x"/>'
XML_B = '<?xml version="1.0" encoding="UTF-8"?><definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" id="d1" targetNamespace="urn:x" name="b"/>'


@pytest.fixture()
def repo():
    return PostgresModelRepository()


def _model() -> Model:
    now = datetime.now(timezone.utc)
    return Model(
        id=str(uuid.uuid4()),
        working_copy=WorkingCopy(CanonicalBpmnArtifact(XML_A)),
        display_name=f"IT Model {uuid.uuid4().hex[:8]}",
        version=1,
        created_at=now,
        updated_at=now,
        created_by="it-test",
        updated_by="it-test",
    )


def test_create_and_read_roundtrip(repo):
    model = _model()
    repo.create_aggregate(model)
    loaded = repo.get_aggregate(model.id)
    assert loaded is not None
    assert loaded.display_name == model.display_name
    assert loaded.working_copy.artifact.content == XML_A
    assert loaded.version == 1


def test_mutate_cas_conflict(repo):
    model = _model()
    repo.create_aggregate(model)

    def replace(model_: Model) -> str:
        model_.working_copy.replace_artifact(CanonicalBpmnArtifact(XML_B))
        model_.version = model_.version + 1
        model_.updated_at = datetime.now(timezone.utc)
        return "ok"

    _, outcome = repo.mutate(model.id, 1, replace)
    assert outcome == "ok"
    assert repo.get_aggregate(model.id).working_copy.artifact.content == XML_B

    with pytest.raises(ConcurrencyConflictError):
        repo.mutate(model.id, 1, replace)


def test_mutate_not_found(repo):
    with pytest.raises(AggregateNotFoundError):
        repo.mutate(str(uuid.uuid4()), 1, lambda m: None)


def test_revision_append_and_lookup(repo):
    model = _model()
    repo.create_aggregate(model)

    def add_revision(model_: Model) -> int:
        model_.append_revision(
            Revision(
                revision_id=str(uuid.uuid4()),
                revision_number=1,
                artifact=model_.working_copy.artifact,
                checksum="a" * 64,
                created_at=datetime.now(timezone.utc),
                created_by="it-test",
                origin=RevisionOrigin.EXPLICIT,
            )
        )
        return 1

    repo.mutate(model.id, 1, add_revision)
    loaded = repo.get_aggregate(model.id)
    assert len(loaded.revisions) == 1
    assert loaded.revisions[0].artifact.content == XML_A


def test_revision_rows_survive_working_copy_mutations(repo):
    """DB-ISO-12: appended revision bytes are never rewritten by later mutations."""
    from bpmn_modeler.infrastructure.persistence.connection import db_connection

    model = _model()
    repo.create_aggregate(model)

    def add_revision(model_: Model) -> None:
        model_.append_revision(
            Revision(
                revision_id=str(uuid.uuid4()),
                revision_number=1,
                artifact=model_.working_copy.artifact,
                checksum="a" * 64,
                created_at=datetime.now(timezone.utc),
                created_by="it-test",
                origin=RevisionOrigin.EXPLICIT,
            )
        )
        model_.version += 1

    repo.mutate(model.id, 1, add_revision)

    def mutate_wc(model_: Model) -> None:
        model_.working_copy.replace_artifact(CanonicalBpmnArtifact(XML_B))
        model_.version += 1
        model_.updated_at = datetime.now(timezone.utc)

    repo.mutate(model.id, 2, mutate_wc)

    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT artifact_xml, revision_number FROM bpmn_modeler.revisions "
                "WHERE model_id = %(id)s ORDER BY revision_number",
                {"id": model.id},
            )
            rows = cur.fetchall()
    assert len(rows) == 1
    assert rows[0]["artifact_xml"] == XML_A  # snapshot intacto — WC virou XML_B


def test_list_summaries_filters(repo):
    active = _model()
    repo.create_aggregate(active)
    archived = _model()
    repo.create_aggregate(archived)

    def archive(model_: Model) -> None:
        model_.archived_at = datetime.now(timezone.utc)
        model_.version += 1

    repo.mutate(archived.id, 1, archive)

    actives = repo.list_summaries(
        query=None, archived="active", sort="updated_at",
        direction="desc", offset=0, limit=200,
    )
    assert any(m.id == active.id for m in actives)
    assert not any(m.id == archived.id for m in actives)

    all_rows = repo.list_summaries(
        query=None, archived="all", sort="updated_at",
        direction="desc", offset=0, limit=500,
    )
    assert any(m.id == archived.id for m in all_rows)

    by_name = repo.list_summaries(
        query=active.display_name, archived="active", sort="updated_at",
        direction="desc", offset=0, limit=10,
    )
    assert [m.id for m in by_name] == [active.id]


def test_schema_isolation(repo):
    """Contexto isolado no schema bpmn_modeler do plugins_hub compartilhado."""
    from bpmn_modeler.infrastructure.persistence.connection import db_connection

    model = _model()
    repo.create_aggregate(model)

    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'bpmn_modeler' ORDER BY table_name"
            )
            tables = {row["table_name"] for row in cur.fetchall()}
            assert {"models", "revisions", "schema_migrations"} <= tables

            # nada do contexto pode vazar para o schema public
            cur.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' "
                "AND table_name IN ('models', 'revisions', 'schema_migrations')"
            )
            assert cur.fetchall() == []

            # dado persiste no schema correto
            cur.execute(
                "SELECT display_name FROM bpmn_modeler.models WHERE id = %(id)s",
                {"id": model.id},
            )
            assert cur.fetchone()["display_name"] == model.display_name
