"""Exclusão definitiva de versão de checklist (CF-UX-054-R3).

A operação remove a configuração (versão + itens) sem tocar dados
operacionais — competências e snapshots bloqueiam; a trilha
append-only sobrevive e a numeração nunca é reutilizada.
"""

from __future__ import annotations

import os
import uuid

import psycopg
import pytest

from controllership_finance_app.domain.closing_checklist.errors import (
    VersionDeleteBlocked,
    VersionDeleteConflict,
)
from controllership_finance_app.infrastructure.persistence import (
    migrations_runner as mr,
)
from controllership_finance_app.infrastructure.persistence.closing_checklist_repository import (
    ClosingChecklistRepository,
)
from controllership_finance_app.infrastructure.persistence.checklist_version_deletion import (
    delete_template_version,
    diagnose_template_version_deletion,
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
TEMPLATE_CODE = "monthly-closing-checklist"

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
    cfg.settings.PLUGINS_DB_SSLMODE = os.getenv(
        "CF_TEST_PG_SSLMODE", "prefer"
    )
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


def _template_id(code: str = TEMPLATE_CODE) -> str:
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT template_id"
            " FROM controllership_finance.checklist_template"
            " WHERE code = %s",
            (code,),
        )
        return str(cur.fetchone()[0])


def _seed_template() -> str:
    """Template próprio por teste — isolamento entre cenários."""
    code = f"del-test-{uuid.uuid4().hex[:12]}"
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO controllership_finance.checklist_template"
            " (code, name, created_by) VALUES (%s, %s, %s)",
            (code, "Template de teste", ACTOR),
        )
        conn.commit()
    return _template_id(code)


def _seed_items(version_id: str, count: int = 2) -> None:
    with plugins_db_connect() as conn, conn.cursor() as cur:
        for index in range(count):
            cur.execute(
                "INSERT INTO controllership_finance"
                ".checklist_template_item"
                " (version_id, item_key, sort_order, sheet, name,"
                "  origin_kind)"
                " VALUES (%s, %s, %s, 'ELETRONICO', %s, 'EXTERNAL')",
                (
                    version_id,
                    f"CK-T-{index + 1:02d}",
                    index + 1,
                    f"Item {index + 1}",
                ),
            )
        conn.commit()


def _version_exists(template_id: str, version: int) -> bool:
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT 1"
            " FROM controllership_finance.checklist_template_version"
            " WHERE template_id = %s AND version = %s",
            (template_id, version),
        )
        return cur.fetchone() is not None


def _delete_kwargs(
    diagnosis: dict, *, key: str, reason: str = "saneamento"
) -> dict:
    return {
        "actor": ACTOR,
        "expected_version_id": diagnosis["version_id"],
        "expected_revision": diagnosis["revision"],
        "expected_item_count": diagnosis["item_count"],
        "reason": reason,
        "idempotency_key": key,
        "channel": "portal",
    }


def test_delete_draft_removes_items_and_preserves_audit(migrated):
    repo = ClosingChecklistRepository()
    template_id = _seed_template()
    draft = repo.create_draft_version(template_id, actor=ACTOR)
    version = int(draft["version"])
    _seed_items(str(draft["version_id"]))

    diagnosis = diagnose_template_version_deletion(template_id, version)
    assert diagnosis["outcome"] == "eligible"
    assert diagnosis["item_count"] == 2
    assert diagnosis["reasons"] == []
    exclusive = {
        item["code"]: item["count"]
        for item in diagnosis["dependents"]["exclusive"]
    }
    assert exclusive == {"checklist_template_item": 2}

    result = delete_template_version(
        template_id,
        version,
        **_delete_kwargs(diagnosis, key="pg-del-v-0001"),
    )
    assert result["deleted"] is True
    assert result["replayed"] is False
    assert result["audit_reference"]
    assert not _version_exists(template_id, version)
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) FROM controllership_finance"
            ".checklist_template_item WHERE version_id = %s",
            (diagnosis["version_id"],),
        )
        assert int(cur.fetchone()[0]) == 0

    events = repo.list_template_events(template_id)
    deleted_events = [
        row for row in events
        if row["event_type"] == "VERSION_DELETED"
    ]
    assert deleted_events
    assert deleted_events[0]["version"] == version
    detail = deleted_events[0]["detail"]
    assert detail["template_id"] == template_id
    assert detail["version"] == version
    assert detail["checklist_template_item"] == 2

    # Replay idempotente devolve a exclusão anterior, sem efeito novo.
    replay = delete_template_version(
        template_id,
        version,
        **_delete_kwargs(diagnosis, key="pg-del-v-0001"),
    )
    assert replay["replayed"] is True
    assert replay["version_id"] == result["version_id"]


def test_delete_blocked_by_competence_and_snapshot(migrated):
    repo = ClosingChecklistRepository()
    template_id = _template_id()
    repo.submit_version_for_review(template_id, 1, ACTOR)
    repo.publish_version(
        template_id, 1, "2099-01", ACTOR, allow_empty=True
    )
    row, _created = repo.open_competence("2099-01", actor=ACTOR)
    assert row["competence_id"]

    diagnosis = diagnose_template_version_deletion(template_id, 1)
    assert diagnosis["outcome"] == "blocked"
    codes = {reason["code"] for reason in diagnosis["reasons"]}
    assert "monthly_competence" in codes
    assert "snapshot_reference" in codes
    periods = [
        p
        for reason in diagnosis["reasons"]
        for p in reason.get("periods", [])
    ]
    assert "2099-01" in periods

    with pytest.raises(VersionDeleteBlocked):
        delete_template_version(
            template_id,
            1,
            **_delete_kwargs(diagnosis, key="pg-del-v-0002"),
        )
    assert _version_exists(template_id, 1)


def test_delete_manifest_conflict_deletes_nothing(migrated):
    repo = ClosingChecklistRepository()
    template_id = _seed_template()
    draft = repo.create_draft_version(template_id, actor=ACTOR)
    version = int(draft["version"])
    diagnosis = diagnose_template_version_deletion(template_id, version)

    wrong = _delete_kwargs(diagnosis, key="pg-del-v-0003")
    wrong["expected_item_count"] = diagnosis["item_count"] + 99
    with pytest.raises(VersionDeleteConflict):
        delete_template_version(template_id, version, **wrong)
    assert _version_exists(template_id, version)


def test_version_numbering_never_reuses_deleted_number(migrated):
    repo = ClosingChecklistRepository()
    template_id = _seed_template()
    draft = repo.create_draft_version(template_id, actor=ACTOR)
    version = int(draft["version"])
    diagnosis = diagnose_template_version_deletion(template_id, version)
    delete_template_version(
        template_id,
        version,
        **_delete_kwargs(diagnosis, key="pg-del-v-0004"),
    )
    assert not _version_exists(template_id, version)

    recreated = repo.create_draft_version(template_id, actor=ACTOR)
    assert int(recreated["version"]) > version
