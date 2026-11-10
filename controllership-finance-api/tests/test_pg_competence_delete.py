"""CF-UX-054 — exclusão de competência em PostgreSQL efêmero.

Não publica checklist real nem altera competências de produção.
"""

from __future__ import annotations

import os
import uuid
from concurrent.futures import ThreadPoolExecutor

import psycopg
import pytest

from controllership_finance_app.application.clara.governed_writes import (
    ClaraGovernedWrites,
    OperationForbidden,
)
from controllership_finance_app.application.clara.step_up_consent import (
    ConsentRequired,
)
from controllership_finance_app.config import settings
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

PG_ENV = (
    "CF_TEST_PG_HOST",
    "CF_TEST_PG_NAME",
    "CF_TEST_PG_USER",
    "CF_TEST_PG_PASSWORD",
)
ACTOR = "11111111-1111-4111-8111-111111111111"

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
    assert applied[-1] == "V021__closing_audit_competence_set_null.sql"
    return True


def _open(period: str) -> str:
    row, _created = ClosingChecklistRepository().open_competence(
        period, actor=ACTOR
    )
    return str(row["competence_id"])


def _exists(period: str) -> bool:
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1 FROM controllership_finance.monthly_competence
             WHERE period = %s
            """,
            (period,),
        )
        return cur.fetchone() is not None


def _delete(
    period: str,
    competence_id: str,
    key: str,
    reason: str = "Competência de teste sem dependência operacional.",
):
    return delete_competence(
        period,
        actor=ACTOR,
        expected_competence_id=competence_id,
        reason=reason,
        idempotency_key=key,
        channel="portal",
    )


def test_invalid_period_does_not_touch_database():
    with pytest.raises(CompetenceDeleteInvalid):
        delete_competence(
            "2026-13",
            actor=ACTOR,
            expected_competence_id=str(uuid.uuid4()),
            reason="motivo válido",
            idempotency_key="invalid-period-key",
        )


def test_foreign_keys_keep_audit_and_block_cascade(migrated):
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT c.relname, con.confdeltype
              FROM pg_constraint con
              JOIN pg_class c ON c.oid = con.conrelid
             WHERE con.contype = 'f'
               AND con.confrelid = 'controllership_finance.monthly_competence'::regclass
            """
        )
        rules = {name: code for name, code in cur.fetchall()}
    assert rules["closing_audit_event"] == "n"
    assert "c" not in rules.values()
    assert "competence_checklist_item" in rules
    assert "closing_document" in rules


def test_blank_and_short_reasons_are_audited_as_given(migrated):
    cases = (("2020-08", "", "blank-reason-key"), ("2020-09", "ab", "short-reason-key"))
    for period, reason, key in cases:
        competence_id = _open(period)
        deleted = _delete(period, competence_id, key, reason=reason)
        assert deleted["deleted"] is True
        with plugins_db_connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT detail->>'reason'
                  FROM controllership_finance.closing_audit_event
                 WHERE event_type = 'COMPETENCE_DELETED'
                   AND detail->>'competence_id' = %s
                """,
                (competence_id,),
            )
            assert cur.fetchone()[0] == reason


def test_clara_prepare_without_reason(migrated, monkeypatch):
    monkeypatch.setattr(settings, "CLARA_CONSENT_CHANNEL", "conversational")
    period = "2020-07"
    competence_id = _open(period)
    writes = ClaraGovernedWrites(
        identity_provider=lambda: {
            "subject": ACTOR,
            "name": "Gestor",
            "is_manage": True,
            "is_dre": False,
        }
    )
    proposal = writes.prepare(
        capability="competence.delete",
        params={
            "period": period,
            "expected_competence_id": competence_id,
            "idempotency_key": "clara-delete-no-reason",
        },
        actor_sub=ACTOR,
    )
    assert proposal["presentation"]["displayable"] is True
    assert "Nenhuma justificativa foi informada." in (
        proposal["presentation"]["summary"]
    )
    assert _exists(period)


def test_empty_competence_is_deleted_and_audit_survives(migrated):
    period = "2020-01"
    competence_id = _open(period)
    result = _delete(period, competence_id, "empty-delete-key-01")
    assert result["deleted"] is True
    assert result["replayed"] is False
    assert not _exists(period)
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT event_type, competence_id::text, entity_id::text,
                   detail->>'period', detail->>'competence_id'
              FROM controllership_finance.closing_audit_event
             WHERE entity_id = %s
             ORDER BY created_at
            """,
            (competence_id,),
        )
        rows = cur.fetchall()
    kinds = [row[0] for row in rows]
    assert kinds == ["COMPETENCE_OPENED", "COMPETENCE_DELETED"]
    assert rows[0][1] is None
    assert rows[0][3] == period
    assert rows[1][4] == competence_id
    reopened, created = ClosingChecklistRepository().open_competence(
        period, actor=ACTOR
    )
    assert created is True
    assert str(reopened["competence_id"]) != competence_id


def test_document_dependency_blocks_and_rolls_back(migrated):
    period = "2020-02"
    competence_id = _open(period)
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO controllership_finance.closing_document
                (competence_id, link_kind, idempotency_key,
                 request_hash, uploaded_by)
            VALUES (%s, 'competence', %s, %s, %s)
            """,
            (competence_id, f"doc-{uuid.uuid4()}", "0" * 64, ACTOR),
        )
        conn.commit()
    with pytest.raises(CompetenceDeleteBlocked) as caught:
        _delete(period, competence_id, "blocked-document-key")
    assert caught.value.details["reasons"][0]["code"] == "closing_document"
    assert _exists(period)
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT count(*)
              FROM controllership_finance.closing_audit_event
             WHERE event_type = 'COMPETENCE_DELETED'
               AND detail->>'competence_id' = %s
            """,
            (competence_id,),
        )
        assert cur.fetchone()[0] == 0


def test_checklist_snapshot_blocks_without_cascade(migrated):
    repo = ClosingChecklistRepository()
    template_id = str(repo.list_templates()[0]["template_id"])
    repo.submit_version_for_review(template_id, 1, actor=ACTOR)
    repo.publish_version(
        template_id, 1, effective_from_period="2099-01", actor=ACTOR
    )
    period = "2099-01"
    competence_id = _open(period)
    with pytest.raises(CompetenceDeleteBlocked) as caught:
        _delete(period, competence_id, "blocked-checklist-key")
    codes = {item["code"] for item in caught.value.details["reasons"]}
    assert "competence_checklist_item" in codes
    assert _exists(period)
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT count(*)
              FROM controllership_finance.competence_checklist_item
             WHERE competence_id = %s
            """,
            (competence_id,),
        )
        assert cur.fetchone()[0] > 0


def test_replay_does_not_delete_another_competence(migrated):
    first = _open("2020-03")
    second = _open("2020-04")
    original = _delete("2020-03", first, "replay-same-competence")
    replay = _delete("2020-03", first, "replay-same-competence")
    assert replay["replayed"] is True
    assert replay["audit_reference"] == original["audit_reference"]
    assert _exists("2020-04")
    with pytest.raises(CompetenceDeleteConflict):
        _delete("2020-04", second, "replay-same-competence")
    assert _exists("2020-04")
    with pytest.raises(CompetenceDeleteConflict):
        _delete("2020-04", str(uuid.uuid4()), "other-competence-key")
    assert _exists("2020-04")


def test_concurrent_deletes_remove_the_competence_once(migrated):
    period = "2020-05"
    competence_id = _open(period)

    def attempt(key: str):
        try:
            return _delete(period, competence_id, key)
        except CompetenceNotFound:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(attempt, ("race-key-a", "race-key-b")))
    assert sum(item is not None for item in outcomes) == 1
    assert not _exists(period)
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT count(*)
              FROM controllership_finance.closing_audit_event
             WHERE event_type = 'COMPETENCE_DELETED'
               AND detail->>'competence_id' = %s
            """,
            (competence_id,),
        )
        assert cur.fetchone()[0] == 1


def test_clara_prepare_confirmation_and_readback(migrated, monkeypatch):
    monkeypatch.setattr(settings, "CLARA_CONSENT_CHANNEL", "conversational")
    period = "2020-06"
    competence_id = _open(period)
    identity = {
        "subject": ACTOR,
        "name": "Gestor",
        "is_manage": True,
        "is_dre": False,
    }
    writes = ClaraGovernedWrites(identity_provider=lambda: identity)
    params = {
        "period": period,
        "expected_competence_id": competence_id,
        "reason": "Exclusão de teste autorizada.",
        "idempotency_key": "clara-delete-key-01",
    }
    proposal = writes.prepare(
        capability="competence.delete", params=params, actor_sub=ACTOR
    )
    assert _exists(period)
    assert proposal["presentation"]["displayable"] is True
    with pytest.raises(ConsentRequired):
        writes.commit(
            handle=proposal["proposal_handle"],
            actor_sub=ACTOR,
            confirmation=False,
        )
    assert _exists(period)
    identity["is_manage"] = False
    with pytest.raises(OperationForbidden):
        writes.commit(
            handle=proposal["proposal_handle"],
            actor_sub=ACTOR,
            confirmation=True,
        )
    identity["is_manage"] = True
    executed = writes.commit(
        handle=proposal["proposal_handle"],
        actor_sub=ACTOR,
        confirmation=True,
    )
    assert executed["executed"] is True
    assert executed["result"]["deleted"] is True
    assert not _exists(period)
    with pytest.raises(Exception):
        writes.commit(
            handle=proposal["proposal_handle"],
            actor_sub=ACTOR,
            confirmation=True,
        )
    assert not _exists(period)


def test_dependency_added_after_prepare_is_rejected(migrated, monkeypatch):
    monkeypatch.setattr(settings, "CLARA_CONSENT_CHANNEL", "conversational")
    period = "2020-07"
    competence_id = _open(period)
    writes = ClaraGovernedWrites(
        identity_provider=lambda: {
            "subject": ACTOR,
            "name": "Gestor",
            "is_manage": True,
            "is_dre": False,
        }
    )
    proposal = writes.prepare(
        capability="competence.delete",
        params={
            "period": period,
            "expected_competence_id": competence_id,
            "reason": "Exclusão de teste autorizada.",
            "idempotency_key": "clara-delete-key-02",
        },
        actor_sub=ACTOR,
    )
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO controllership_finance.closing_document
                (competence_id, link_kind, idempotency_key,
                 request_hash, uploaded_by)
            VALUES (%s, 'competence', %s, %s, %s)
            """,
            (competence_id, f"late-{uuid.uuid4()}", "0" * 64, ACTOR),
        )
        conn.commit()
    with pytest.raises(CompetenceDeleteBlocked):
        writes.commit(
            handle=proposal["proposal_handle"],
            actor_sub=ACTOR,
            confirmation=True,
        )
    assert _exists(period)
