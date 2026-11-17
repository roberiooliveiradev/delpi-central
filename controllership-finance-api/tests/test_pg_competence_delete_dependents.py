"""Exclusão governada de competência com dependentes (CF-UX-054-R2).

Modo `delete_dependents` + `expected_dependents`: dados operacionais
exclusivos são removidos na mesma transação; artefatos oficiais,
referências compartilhadas e auditoria continuam protegidos.
"""

from __future__ import annotations

import hashlib
import os
import uuid

import psycopg
import pytest

from controllership_finance_app.domain.closing_checklist.errors import (
    CompetenceDeleteBlocked,
    CompetenceDeleteConflict,
    CompetenceDeleteInvalid,
    CompetenceNotFound,
)
from controllership_finance_app.infrastructure.persistence import (
    migrations_runner as mr,
)
from controllership_finance_app.infrastructure.persistence.closing_checklist_repository import (
    ClosingChecklistRepository,
)
from controllership_finance_app.infrastructure.persistence.competence_deletion import (
    delete_competence,
    diagnose_competence_deletion,
)
from controllership_finance_app.infrastructure.persistence.plugins_db import (
    plugins_db_connect,
)
from pg_test_isolation import (
    assert_safe_test_prefix,
    create_owned_test_database,
    drop_owned_test_database,
    require_test_environment,
)
from migration_head import latest_product_migration  # noqa: E402


PG_ENV = (
    "CF_TEST_PG_HOST",
    "CF_TEST_PG_NAME",
    "CF_TEST_PG_USER",
    "CF_TEST_PG_PASSWORD",
)
ACTOR = "11111111-1111-4111-8111-111111111111"
HASH = "0" * 64

pytestmark = pytest.mark.skipif(
    not all(os.getenv(name) for name in PG_ENV),
    reason="CF_TEST_PG_* ausente — integração PostgreSQL não configurada",
)


def _test_connect(dbname: str) -> psycopg.Connection:
    return psycopg.connect(
        host=os.environ["CF_TEST_PG_HOST"],
        port=int(os.getenv("CF_TEST_PG_PORT", "5432")),
        dbname=dbname,
        user=os.environ["CF_TEST_PG_USER"],
        password=os.environ["CF_TEST_PG_PASSWORD"],
        autocommit=True,
    )


@pytest.fixture(scope="module", autouse=True)
def _configure_db():
    import controllership_finance_app.config as cfg

    prefix = os.environ["CF_TEST_PG_NAME"]
    assert_safe_test_prefix(prefix)
    refusal = require_test_environment(os.environ)
    if refusal:
        pytest.skip(refusal)
    admin_db = os.getenv("CF_TEST_PG_ADMIN_DB", "postgres")
    owned = create_owned_test_database(
        _test_connect, admin_db, prefix=prefix
    )
    original = {
        name: getattr(cfg.settings, name)
        for name in (
            "PLUGINS_DB_HOST",
            "PLUGINS_DB_PORT",
            "PLUGINS_DB_NAME",
            "PLUGINS_DB_USER",
            "PLUGINS_DB_PASSWORD",
            "PLUGINS_DB_SSLMODE",
            "PLUGINS_DB_CONNECT_TIMEOUT",
        )
    }
    cfg.settings.PLUGINS_DB_HOST = os.environ["CF_TEST_PG_HOST"]
    cfg.settings.PLUGINS_DB_PORT = os.getenv("CF_TEST_PG_PORT", "5432")
    cfg.settings.PLUGINS_DB_NAME = owned.name
    cfg.settings.PLUGINS_DB_USER = os.environ["CF_TEST_PG_USER"]
    cfg.settings.PLUGINS_DB_PASSWORD = os.environ["CF_TEST_PG_PASSWORD"]
    cfg.settings.PLUGINS_DB_SSLMODE = os.getenv("CF_TEST_PG_SSLMODE", "prefer")
    cfg.settings.PLUGINS_DB_CONNECT_TIMEOUT = 10
    yield
    drop_owned_test_database(_test_connect, admin_db, owned)
    for key, value in original.items():
        setattr(cfg.settings, key, value)


@pytest.fixture(scope="module")
def migrated(_configure_db):
    applied = mr.run_migrations()
    assert applied[-1] == latest_product_migration()
    return True


def _open(period: str) -> str:
    row, _created = ClosingChecklistRepository().open_competence(
        period, actor=ACTOR
    )
    return str(row["competence_id"])


def _exists(period: str) -> bool:
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM controllership_finance.monthly_competence"
            " WHERE period = %s",
            (period,),
        )
        return cur.fetchone() is not None


def _count(table: str, competence_id: str) -> int:
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT count(*) FROM controllership_finance.{table}"
            " WHERE competence_id = %s",
            (competence_id,),
        )
        return int(cur.fetchone()[0])


def _seed_document(competence_id: str, *, messages: int = 2) -> str:
    """Documento completo: arquivo, versão, mensagens e ajuste."""
    file_id = str(uuid.uuid4())
    document_id = str(uuid.uuid4())
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO controllership_finance.document_file
                (file_id, storage_key, original_name, stored_name,
                 mime_type, extension, size_bytes, checksum_sha256,
                 created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                file_id,
                f"{competence_id}/{file_id.replace('-', '')}.pdf",
                "evidencia.pdf",
                f"{file_id.replace('-', '')}.pdf",
                "application/pdf",
                ".pdf",
                128,
                hashlib.sha256(b"seed").hexdigest(),
                ACTOR,
            ),
        )
        cur.execute(
            """
            INSERT INTO controllership_finance.closing_document
                (document_id, competence_id, link_kind, idempotency_key,
                 request_hash, uploaded_by)
            VALUES (%s, %s, 'competence', %s, %s, %s)
            """,
            (document_id, competence_id, f"doc-{uuid.uuid4()}", HASH, ACTOR),
        )
        cur.execute(
            """
            INSERT INTO controllership_finance.document_version
                (document_id, version_no, file_id, uploaded_by,
                 idempotency_key, request_hash)
            VALUES (%s, 1, %s, %s, %s, %s)
            """,
            (document_id, file_id, ACTOR, f"ver-{uuid.uuid4()}", HASH),
        )
        for index in range(messages):
            cur.execute(
                """
                INSERT INTO controllership_finance.document_message
                    (document_id, competence_id, body, author_subject,
                     idempotency_key, request_hash)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    document_id,
                    competence_id,
                    f"mensagem {index}",
                    ACTOR,
                    f"msg-{uuid.uuid4()}",
                    HASH,
                ),
            )
        cur.execute(
            """
            INSERT INTO controllership_finance.document_adjustment_request
                (document_id, competence_id, body, requester_subject,
                 idempotency_key, request_hash)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                document_id,
                competence_id,
                "ajuste necessário",
                ACTOR,
                f"adj-{uuid.uuid4()}",
                HASH,
            ),
        )
        conn.commit()
    return document_id


def _seed_notification(competence_id: str) -> None:
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO controllership_finance.closing_notification_event
                (competence_id, event_type, recipient_subject, emitted_by)
            VALUES (%s, 'DOCUMENT_ATTACHED', %s, %s)
            """,
            (competence_id, ACTOR, ACTOR),
        )
        conn.commit()


def _seed_pendency(competence_id: str) -> None:
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO controllership_finance.closing_pendency
                (competence_id, kind, title, created_by)
            VALUES (%s, 'OTHER', 'pendência de teste', %s)
            """,
            (competence_id, ACTOR),
        )
        conn.commit()


def _seed_package(competence_id: str) -> None:
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO controllership_finance.closing_package
                (competence_id, recipient_area, created_by)
            VALUES (%s, 'CONTABIL', %s)
            """,
            (competence_id, ACTOR),
        )
        conn.commit()


def _manifest_of(diagnosis: dict) -> dict[str, int]:
    return {
        item["code"]: item["count"]
        for item in diagnosis["dependents"]["exclusive"]
    }


def _delete_governed(
    period: str,
    competence_id: str,
    key: str,
    manifest: dict[str, int],
    reason: str = "Saneamento autorizado de competência de teste.",
):
    return delete_competence(
        period,
        actor=ACTOR,
        expected_competence_id=competence_id,
        reason=reason,
        idempotency_key=key,
        channel="portal",
        delete_dependents=True,
        expected_dependents=manifest,
    )


def test_diagnose_classifies_exclusive_dependents(migrated):
    period = "2021-01"
    competence_id = _open(period)
    _seed_document(competence_id, messages=3)
    _seed_notification(competence_id)
    _seed_pendency(competence_id)
    diagnosis = diagnose_competence_deletion(period)
    assert diagnosis["outcome"] == "eligible_with_dependents"
    manifest = _manifest_of(diagnosis)
    assert manifest == {
        "closing_document": 1,
        "document_version": 1,
        "document_file": 1,
        "document_message": 3,
        "document_adjustment_request": 1,
        "closing_notification_event": 1,
        "closing_pendency": 1,
    }
    assert diagnosis["reasons"] == []


def test_governed_delete_removes_document_tree_and_audits(migrated):
    period = "2021-02"
    competence_id = _open(period)
    document_id = _seed_document(competence_id, messages=2)
    _seed_notification(competence_id)
    _seed_pendency(competence_id)
    manifest = _manifest_of(diagnose_competence_deletion(period))
    result = _delete_governed(period, competence_id, "gov-del-key-01", manifest)
    assert result["deleted"] is True
    assert result["dependents"] == manifest
    assert not _exists(period)
    for table in (
        "closing_document",
        "document_message",
        "document_adjustment_request",
        "closing_notification_event",
        "closing_pendency",
    ):
        assert _count(table, competence_id) == 0, table
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) FROM controllership_finance.document_version"
            " WHERE document_id = %s",
            (document_id,),
        )
        assert cur.fetchone()[0] == 0
        cur.execute(
            "SELECT count(*) FROM controllership_finance.document_file f"
            " WHERE NOT EXISTS ("
            "  SELECT 1 FROM controllership_finance.document_version dv"
            "   WHERE dv.file_id = f.file_id)"
        )
        assert cur.fetchone()[0] == 0
        cur.execute(
            """
            SELECT detail->'dependents'
              FROM controllership_finance.closing_audit_event
             WHERE event_type = 'COMPETENCE_DELETED'
               AND detail->>'competence_id' = %s
            """,
            (competence_id,),
        )
        stored = cur.fetchone()[0]
    assert stored == manifest


def test_dependents_present_without_flag_stays_blocked(migrated):
    period = "2021-03"
    competence_id = _open(period)
    _seed_document(competence_id)
    with pytest.raises(CompetenceDeleteBlocked) as caught:
        delete_competence(
            period,
            actor=ACTOR,
            expected_competence_id=competence_id,
            reason="sem confirmação",
            idempotency_key="blocked-dep-key-01",
        )
    assert caught.value.details["confirmation"] == (
        "delete_dependents+expected_dependents"
    )
    assert _exists(period)
    assert _count("closing_document", competence_id) == 1


def test_flag_without_manifest_is_invalid(migrated):
    period = "2021-04"
    competence_id = _open(period)
    _seed_document(competence_id)
    with pytest.raises(CompetenceDeleteInvalid):
        delete_competence(
            period,
            actor=ACTOR,
            expected_competence_id=competence_id,
            reason="falta manifesto",
            idempotency_key="missing-manifest-key",
            delete_dependents=True,
        )
    assert _exists(period)


def test_divergent_manifest_conflicts_and_deletes_nothing(migrated):
    period = "2021-05"
    competence_id = _open(period)
    _seed_document(competence_id, messages=2)
    manifest = _manifest_of(diagnose_competence_deletion(period))
    _seed_notification(competence_id)
    with pytest.raises(CompetenceDeleteConflict) as caught:
        _delete_governed(period, competence_id, "divergent-key-01", manifest)
    assert caught.value.details["expected"] == manifest
    assert _exists(period)
    assert _count("closing_document", competence_id) == 1
    assert _count("document_message", competence_id) == 2
    assert _count("closing_notification_event", competence_id) == 1


def test_package_blocks_even_with_governed_flag(migrated):
    period = "2021-06"
    competence_id = _open(period)
    _seed_package(competence_id)
    _seed_document(competence_id)
    manifest = _manifest_of(diagnose_competence_deletion(period))
    with pytest.raises(CompetenceDeleteBlocked) as caught:
        _delete_governed(period, competence_id, "package-block-key", manifest)
    codes = {item["code"] for item in caught.value.details["reasons"]}
    assert "closing_package" in codes
    assert _exists(period)
    assert _count("closing_document", competence_id) == 1


def test_shared_document_reference_blocks_governed_delete(migrated):
    period, other_period = "2021-07", "2021-08"
    competence_id = _open(period)
    other_id = _open(other_period)
    document_id = _seed_document(competence_id)
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO controllership_finance.closing_reconciliation
                (competence_id, domain, official_document_id)
            VALUES (%s, 'ENTRADAS_SAIDAS', %s)
            """,
            (other_id, document_id),
        )
        conn.commit()
    diagnosis = diagnose_competence_deletion(period)
    assert diagnosis["outcome"] == "blocked"
    codes = {item["code"] for item in diagnosis["reasons"]}
    assert "shared_reference" in codes
    with pytest.raises(CompetenceDeleteBlocked):
        _delete_governed(
            period,
            competence_id,
            "shared-block-key",
            _manifest_of(diagnosis) or {"closing_document": 1},
        )
    assert _exists(period)
    assert _count("closing_document", competence_id) == 1


def test_governed_delete_is_idempotent_and_scoped(migrated):
    first = _open("2021-09")
    second = _open("2021-10")
    _seed_document(first)
    _seed_document(second)
    manifest = _manifest_of(diagnose_competence_deletion("2021-09"))
    original = _delete_governed("2021-09", first, "gov-replay-key", manifest)
    replay = _delete_governed("2021-09", first, "gov-replay-key", manifest)
    assert replay["replayed"] is True
    assert replay["audit_reference"] == original["audit_reference"]
    assert replay["dependents"] == manifest
    assert _exists("2021-10")
    assert _count("closing_document", second) == 1
    with pytest.raises(CompetenceNotFound):
        _delete_governed(
            "2021-09",
            first,
            "gov-after-delete-key",
            manifest,
        )
    assert _exists("2021-10")


def test_governed_delete_rolls_back_on_late_shared_reference(migrated):
    """Injeção de referência cruzada entre inventário e delete simulada
    via violação de FK: nada é removido parcialmente."""
    period, other_period = "2021-11", "2021-12"
    competence_id = _open(period)
    other_id = _open(other_period)
    document_id = _seed_document(competence_id)
    manifest = _manifest_of(diagnose_competence_deletion(period))
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO controllership_finance.closing_reconciliation
                (competence_id, domain, official_document_id)
            VALUES (%s, 'ENTRADAS_SAIDAS', %s)
            """,
            (other_id, document_id),
        )
        conn.commit()
    with pytest.raises(CompetenceDeleteBlocked):
        delete_competence(
            period,
            actor=ACTOR,
            expected_competence_id=competence_id,
            reason="tentativa",
            idempotency_key="late-shared-key",
            delete_dependents=True,
            expected_dependents=manifest,
        )
    assert _exists(period)
    assert _count("closing_document", competence_id) == 1
    assert _count("document_message", competence_id) == 2


def test_exclusive_delete_preserves_audit_and_siblings(migrated):
    """Apenas a competência alvo e seus dados exclusivos saem; auditoria
    e a competência irmã permanecem íntegras."""
    period = "2022-01"
    competence_id = _open(period)
    other_id = _open("2022-02")
    _seed_document(competence_id)
    _seed_notification(other_id)
    manifest = _manifest_of(diagnose_competence_deletion(period))
    _delete_governed(period, competence_id, "scoped-key-01", manifest)
    assert _exists("2022-02")
    assert _count("closing_notification_event", other_id) == 1
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT event_type FROM controllership_finance.closing_audit_event
             WHERE entity_id = %s ORDER BY created_at
            """,
            (competence_id,),
        )
        kinds = [row[0] for row in cur.fetchall()]
    assert kinds == ["COMPETENCE_OPENED", "COMPETENCE_DELETED"]
