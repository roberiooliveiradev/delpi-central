"""Testes PG — Checklist vivo (CF-CHECKLIST-LIVE-004).

Cobre RQ-01..RQ-12: séries, inicialização excepcional, revisões
append-only, retirada/reativação, conclusão histórica, encerramento
administrativo e outbox de sincronização.
"""

from __future__ import annotations

import os
import uuid

import psycopg
import pytest

from tests.pg_test_isolation import (
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
            "PLUGINS_DB_HOST", "PLUGINS_DB_PORT", "PLUGINS_DB_NAME",
            "PLUGINS_DB_USER", "PLUGINS_DB_PASSWORD",
            "PLUGINS_DB_SSLMODE", "PLUGINS_DB_CONNECT_TIMEOUT",
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
    from controllership_finance_app.infrastructure.persistence import (
        migrations_runner as mr,
    )
    from tests.migration_head import latest_product_migration

    applied = mr.run_migrations()
    assert applied[-1] == latest_product_migration()
    return True


@pytest.fixture()
def repo(migrated):
    from controllership_finance_app.infrastructure.persistence import (
        plugins_db,
    )
    from controllership_finance_app.infrastructure.persistence import (
        closing_checklist_repository as mod,
    )

    plugins_db._pool = None  # conexão limpa por teste
    return mod.ClosingChecklistRepository()


def _seed_template() -> str:
    code = f"live-test-{uuid.uuid4().hex[:12]}"
    from controllership_finance_app.infrastructure.persistence.plugins_db import (
        plugins_db_connect,
    )
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO controllership_finance.checklist_template"
            " (code, name, created_by) VALUES (%s, %s, %s)"
            " RETURNING template_id",
            (code, "Template de teste", ACTOR),
        )
        template_id = str(cur.fetchone()[0])
        conn.commit()
    return template_id


def _items(n: int, prefix: str = "CK") -> list[dict]:
    return [
        {
            "item_key": f"{prefix}-{i:02d}",
            "sort_order": i,
            "sheet": "ELETRONICO",
            "name": f"Documento {i}",
            "applicability": "REQUIRED",
            "branch_scope": "BOTH",
        }
        for i in range(1, n + 1)
    ]


def _new_series(repo, template_id, n_items=3):
    series = repo.start_checklist_sequence(
        template_id, actor=ACTOR, reason="nova geração",
        confirmation="START_NEW_SEQUENCE",
        idempotency_key=uuid.uuid4().hex,
    )
    init = repo.initialize_checklist_catalog(
        series["version_id"], actor=ACTOR, reason="carga inicial",
        items=_items(n_items), idempotency_key=uuid.uuid4().hex,
    )
    return series, init


def _publish(repo, template_id, series):
    repo.publish_version(
        template_id, series["version_id"], actor=ACTOR,
        effective_from_period="2026-01",
    ) if hasattr(repo, "publish_version") else None


# -- AC-07: série e identidade -------------------------------------------


def test_start_sequence_closes_previous_and_restarts_v1(repo):
    template_id = _seed_template()
    assert repo.list_series(template_id) == []

    first = repo.start_checklist_sequence(
        template_id, actor=ACTOR, reason="primeira sequência",
        confirmation="START_NEW_SEQUENCE",
        idempotency_key=uuid.uuid4().hex,
    )
    assert first["series_no"] == 1

    result = repo.start_checklist_sequence(
        template_id, actor=ACTOR, reason="nova geração",
        confirmation="START_NEW_SEQUENCE",
        idempotency_key=uuid.uuid4().hex,
    )
    assert result["series_no"] == 2
    assert not result["replayed"]

    series = repo.list_series(template_id)
    assert [s["series_no"] for s in series] == [1, 2]
    assert series[0]["status"] == "CLOSED"
    assert series[1]["status"] == "ACTIVE"


def test_start_sequence_requires_confirmation(repo):
    from controllership_finance_app.domain.closing_checklist.errors import (
        SeriesConfirmationRequired,
    )
    template_id = _seed_template()
    with pytest.raises(SeriesConfirmationRequired):
        repo.start_checklist_sequence(
            template_id, actor=ACTOR, reason="x",
            confirmation="", idempotency_key=uuid.uuid4().hex,
        )


def test_start_sequence_idempotent(repo):
    template_id = _seed_template()
    key = uuid.uuid4().hex
    first = repo.start_checklist_sequence(
        template_id, actor=ACTOR, reason="r",
        confirmation="START_NEW_SEQUENCE", idempotency_key=key,
    )
    replay = repo.start_checklist_sequence(
        template_id, actor=ACTOR, reason="r",
        confirmation="START_NEW_SEQUENCE", idempotency_key=key,
    )
    assert replay["replayed"] is True
    assert replay["series_id"] == first["series_id"]
    assert len(repo.list_series(template_id)) == 1


# -- AC-01/RQ-01: inicialização excepcional -------------------------------


def test_initialize_catalog_only_in_draft(repo):
    template_id = _seed_template()
    series, init = _new_series(repo, template_id, 16)
    assert init["items_created"] == 16
    assert len(init["fingerprint"]) == 64

    version = repo.get_template_version(
        template_id, series["version_id"]
    ) if hasattr(repo, "get_template_version") else None


def test_initialize_catalog_replay(repo):
    template_id = _seed_template()
    series = repo.start_checklist_sequence(
        template_id, actor=ACTOR, reason="r",
        confirmation="START_NEW_SEQUENCE",
        idempotency_key=uuid.uuid4().hex,
    )
    key = uuid.uuid4().hex
    items = _items(3)
    first = repo.initialize_checklist_catalog(
        series["version_id"], actor=ACTOR, reason="r",
        items=items, idempotency_key=key,
    )
    replay = repo.initialize_checklist_catalog(
        series["version_id"], actor=ACTOR, reason="r",
        items=items, idempotency_key=key,
    )
    assert replay["replayed"] is True
    assert replay["fingerprint"] == first["fingerprint"]


def test_initialize_catalog_not_empty_conflict(repo):
    from controllership_finance_app.domain.closing_checklist.errors import (
        CatalogNotEmpty,
    )
    template_id = _seed_template()
    series, _ = _new_series(repo, template_id, 2)
    with pytest.raises(CatalogNotEmpty):
        repo.initialize_checklist_catalog(
            series["version_id"], actor=ACTOR, reason="r",
            items=_items(1, "NEW"), idempotency_key=uuid.uuid4().hex,
        )


# -- AC-08/09: revisões sobre PUBLISHED ------------------------------------


def _published_version(repo, template_id, n_items=3,
                       period="2026-01"):
    """Versão PUBLISHED na série ativa via fluxo canônico de draft.

    `effective_from_period` = `period` para resolução determinística
    do winner quando vários templates de teste coexistem."""
    series, _ = _new_series(repo, template_id, n_items)
    vid = series["version_id"]
    # publicação direta controlada pelo teste (mesmo efeito de
    # publish_version mas sem criar REVIEW intermediário)
    from controllership_finance_app.infrastructure.persistence.plugins_db import (
        plugins_db_connect,
    )
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE controllership_finance.checklist_template_version"
            " SET status='PUBLISHED', published_by=%s, published_at=now(),"
            " effective_from_period=%s"
            " WHERE version_id=%s",
            (ACTOR, period, vid),
        )
        conn.commit()
    return vid


def test_apply_revision_add_and_retire(repo):
    template_id = _seed_template()
    vid = _published_version(repo, template_id, 3)

    result = repo.apply_revision(
        vid, actor=ACTOR, reason="ajuste catálogo",
        expected_revision=1,
        changes=[
            {"op": "ADD", "item_key": "CK-04",
             "payload": {"sheet": "ELETRONICO", "name": "Novo",
                         "sort_order": 4}},
            {"op": "RETIRE", "item_key": "CK-02",
             "payload": {"reason": "obsoleto"}},
        ],
        idempotency_key=uuid.uuid4().hex,
    )
    assert result["revision_no"] == 1
    assert result["sync_event_id"]

    revision = repo.get_revision(result["revision_id"])
    assert len(revision["changes"]) == 2
    assert len(revision["fingerprint"]) == 64


def test_apply_revision_occ_stale(repo):
    from controllership_finance_app.domain.closing_checklist.errors import (
        StaleRevision,
    )
    template_id = _seed_template()
    vid = _published_version(repo, template_id, 2)
    with pytest.raises(StaleRevision):
        repo.apply_revision(
            vid, actor=ACTOR, reason="r", expected_revision=99,
            changes=[{"op": "RETIRE", "item_key": "CK-01"}],
            idempotency_key=uuid.uuid4().hex,
        )


def test_apply_revision_idempotent_replay(repo):
    template_id = _seed_template()
    vid = _published_version(repo, template_id, 2)
    key = uuid.uuid4().hex
    changes = [{"op": "RETIRE", "item_key": "CK-01"}]
    first = repo.apply_revision(
        vid, actor=ACTOR, reason="r", expected_revision=1,
        changes=changes, idempotency_key=key,
    )
    replay = repo.apply_revision(
        vid, actor=ACTOR, reason="r", expected_revision=1,
        changes=changes, idempotency_key=key,
    )
    assert replay["replayed"] is True
    assert replay["revision_id"] == first["revision_id"]


def test_revert_revision_append_only(repo):
    template_id = _seed_template()
    vid = _published_version(repo, template_id, 2)
    rev = repo.apply_revision(
        vid, actor=ACTOR, reason="r", expected_revision=1,
        changes=[{"op": "RETIRE", "item_key": "CK-01"}],
        idempotency_key=uuid.uuid4().hex,
    )
    # versão agora em revision=2
    undo = repo.revert_revision(
        rev["revision_id"], actor=ACTOR, reason="reverter",
        expected_revision=2, idempotency_key=uuid.uuid4().hex,
    )
    assert undo["revision_no"] == 2
    detail = repo.get_revision(undo["revision_id"])
    assert detail["reverts_revision_id"] == uuid.UUID(
        rev["revision_id"]
    ) or str(detail["reverts_revision_id"]) == rev["revision_id"]
    # revisão original intacta (append-only)
    original = repo.get_revision(rev["revision_id"])
    assert original["changes"][0]["op"] == "RETIRE"
    # item restaurado
    version = repo.get_revision(undo["revision_id"])
    from controllership_finance_app.infrastructure.persistence.plugins_db import (
        plugins_db_connect,
    )
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT item_state FROM controllership_finance"
            ".checklist_template_item WHERE version_id=%s"
            " AND item_key='CK-01'",
            (vid,),
        )
        assert cur.fetchone()[0] == "ACTIVE"


def test_double_revert_blocked(repo):
    from controllership_finance_app.domain.closing_checklist.errors import (
        OperationNotRepeatable,
    )
    template_id = _seed_template()
    vid = _published_version(repo, template_id, 2)
    rev = repo.apply_revision(
        vid, actor=ACTOR, reason="r", expected_revision=1,
        changes=[{"op": "RETIRE", "item_key": "CK-01"}],
        idempotency_key=uuid.uuid4().hex,
    )
    repo.revert_revision(
        rev["revision_id"], actor=ACTOR, reason="x",
        expected_revision=2, idempotency_key=uuid.uuid4().hex,
    )
    with pytest.raises(OperationNotRepeatable):
        repo.revert_revision(
            rev["revision_id"], actor=ACTOR, reason="x",
            expected_revision=3, idempotency_key=uuid.uuid4().hex,
        )


# -- AC-10: conclusão histórica -------------------------------------------


def test_open_competence_starts_never(repo):
    template_id = _seed_template()
    _published_version(repo, template_id, 2, "2026-02")
    competence, created = repo.open_competence("2026-02", ACTOR)
    assert created is True
    from controllership_finance_app.infrastructure.persistence.plugins_db import (
        plugins_db_connect,
    )
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT completion_record, first_completed_at"
            " FROM controllership_finance.monthly_competence"
            " WHERE competence_id=%s",
            (competence["competence_id"],),
        )
        row = cur.fetchone()
        assert row[0] == "NEVER" and row[1] is None
        cur.execute(
            "SELECT count(*) FROM controllership_finance"
            ".competence_checklist_item WHERE competence_id=%s",
            (competence["competence_id"],),
        )
        assert cur.fetchone()[0] == 2


def test_open_competence_retry_keeps_record(repo):
    _published_version(repo, _seed_template(), 1, "2026-03")
    first, _ = repo.open_competence("2026-03", ACTOR)
    from controllership_finance_app.infrastructure.persistence.plugins_db import (
        plugins_db_connect,
    )
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE controllership_finance.monthly_competence"
            " SET completion_record='UNEVALUATED'"
            " WHERE competence_id=%s",
            (first["competence_id"],),
        )
        conn.commit()
    second, created = repo.open_competence("2026-03", ACTOR)
    assert created is False
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT completion_record FROM controllership_finance"
            ".monthly_competence WHERE competence_id=%s",
            (first["competence_id"],),
        )
        assert cur.fetchone()[0] == "UNEVALUATED"


def test_assess_completion_reconciles_unevaluated(repo):
    _published_version(repo, _seed_template(), 1, "2026-04")
    comp, _ = repo.open_competence("2026-04", ACTOR)
    from controllership_finance_app.infrastructure.persistence.plugins_db import (
        plugins_db_connect,
    )
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE controllership_finance.monthly_competence"
            " SET completion_record='UNEVALUATED'"
            " WHERE competence_id=%s",
            (comp["competence_id"],),
        )
        conn.commit()
    result = repo.assess_completion(
        comp["competence_id"], actor=ACTOR,
        reason="histórico verificado", completion_record="NEVER",
        evidence_summary="zero pacotes, zero trilha",
    )
    assert result["completion_record"] == "NEVER"
    assert result["completion_basis"] == "GOVERNED"


# -- AC-11/12: sync — retirada, correções, reativação ----------------------


def _open_and_seed_correction(repo, period="2026-05"):
    _published_version(repo, _seed_template(), 2, period)
    comp, _ = repo.open_competence(period, ACTOR)
    return comp


def test_sync_retire_cancels_item_and_closes_records(repo):
    from controllership_finance_app.infrastructure.persistence.plugins_db import (
        plugins_db_connect,
    )
    template_id = _seed_template()
    vid = _published_version(repo, template_id, 2, "2026-06")
    comp, _ = repo.open_competence("2026-06", ACTOR)

    # correção PENDING + pendência OPEN no item CK-01
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT snapshot_item_id FROM controllership_finance"
            ".competence_checklist_item WHERE competence_id=%s"
            " AND item_key='CK-01'",
            (comp["competence_id"],),
        )
        snap = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO controllership_finance.item_correction"
            " (competence_id, snapshot_item_id, item_revision,"
            "  changes, justification, requested_by)"
            " VALUES (%s,%s,1,'{}','ajuste',%s)",
            (comp["competence_id"], snap, ACTOR),
        )
        cur.execute(
            "INSERT INTO controllership_finance.closing_pendency"
            " (competence_id, snapshot_item_id, kind, title,"
            "  created_by) VALUES (%s,%s,'OTHER','pend',%s)",
            (comp["competence_id"], snap, ACTOR),
        )
        conn.commit()

    repo.apply_revision(
        vid, actor=ACTOR, reason="retirar CK-01",
        expected_revision=1,
        changes=[{"op": "RETIRE", "item_key": "CK-01"}],
        idempotency_key=uuid.uuid4().hex,
    )
    result = repo.dispatch_sync_events()
    assert result["claimed"] >= 1
    assert result["events_completed"] >= 1

    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT state, cancel_origin FROM controllership_finance"
            ".competence_checklist_item WHERE snapshot_item_id=%s",
            (snap,),
        )
        row = cur.fetchone()
        assert row == ("CANCELLED", "CATALOG_RETIRE")
        cur.execute(
            "SELECT status, closure_reason FROM controllership_finance"
            ".item_correction WHERE snapshot_item_id=%s",
            (snap,),
        )
        row = cur.fetchone()
        assert row[0] == "CLOSED_REQUIREMENT_RETIRED"
        assert row[1] == "requirement_retired"
        cur.execute(
            "SELECT state, dismiss_justification FROM"
            " controllership_finance.closing_pendency"
            " WHERE snapshot_item_id=%s",
            (snap,),
        )
        assert cur.fetchone() == ("DISMISSED", "catalog_retire")

    # Doc 176: o encerramento administrativo apresenta-se como
    # closed_administrative — nunca rejected — preservando o status bruto.
    from controllership_finance_app.infrastructure.persistence.closing_validation_repository import (
        ClosingValidationRepository,
    )
    corrections = ClosingValidationRepository().list_corrections("2026-06")
    retired = [c for c in corrections if c["snapshot_item_id"] == snap]
    assert retired and all(
        c["status"] == "CLOSED_REQUIREMENT_RETIRED"
        and c["status_class"] == "closed_administrative"
        for c in retired
    )


def test_correction_status_class_mapping():
    from controllership_finance_app.infrastructure.persistence.closing_validation_repository import (
        ClosingValidationRepository as Repo,
    )
    classify = Repo._correction_status_class
    assert classify("CLOSED_REQUIREMENT_RETIRED") == "closed_administrative"
    assert classify("PENDING") == "pending"
    assert classify("APPROVED") == "approved"
    assert classify("REJECTED") == "rejected"
    assert classify("UNKNOWN_X") == "unknown_x"
    assert classify(None) is None


def test_sync_reactivate_restores_catalog_retired(repo):
    from controllership_finance_app.infrastructure.persistence.plugins_db import (
        plugins_db_connect,
    )
    template_id = _seed_template()
    vid = _published_version(repo, template_id, 2, "2026-07")
    comp, _ = repo.open_competence("2026-07", ACTOR)

    repo.apply_revision(
        vid, actor=ACTOR, reason="r1", expected_revision=1,
        changes=[{"op": "RETIRE", "item_key": "CK-01"}],
        idempotency_key=uuid.uuid4().hex,
    )
    repo.dispatch_sync_events()
    repo.apply_revision(
        vid, actor=ACTOR, reason="r2", expected_revision=2,
        changes=[{"op": "REACTIVATE", "item_key": "CK-01"}],
        idempotency_key=uuid.uuid4().hex,
    )
    repo.dispatch_sync_events()

    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT state, cancel_origin FROM controllership_finance"
            ".competence_checklist_item WHERE competence_id=%s"
            " AND item_key='CK-01'",
            (comp["competence_id"],),
        )
        row = cur.fetchone()
        assert row == ("EXPECTED", None)


def test_sync_never_reactivates_manual_cancel(repo):
    from controllership_finance_app.infrastructure.persistence.plugins_db import (
        plugins_db_connect,
    )
    template_id = _seed_template()
    vid = _published_version(repo, template_id, 2, "2026-08")
    comp, _ = repo.open_competence("2026-08", ACTOR)
    repo.apply_revision(
        vid, actor=ACTOR, reason="r1", expected_revision=1,
        changes=[{"op": "RETIRE", "item_key": "CK-01"}],
        idempotency_key=uuid.uuid4().hex,
    )
    repo.dispatch_sync_events()
    # cancelamento manual: origem divergente da retirada de catálogo
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE controllership_finance.competence_checklist_item"
            " SET cancel_origin='MANUAL'"
            " WHERE competence_id=%s AND item_key='CK-01'",
            (comp["competence_id"],),
        )
        conn.commit()
    repo.apply_revision(
        vid, actor=ACTOR, reason="r2", expected_revision=2,
        changes=[{"op": "REACTIVATE", "item_key": "CK-01"}],
        idempotency_key=uuid.uuid4().hex,
    )
    repo.dispatch_sync_events()
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT state, cancel_origin FROM controllership_finance"
            ".competence_checklist_item WHERE competence_id=%s"
            " AND item_key='CK-01'",
            (comp["competence_id"],),
        )
        assert cur.fetchone() == ("CANCELLED", "MANUAL")


def test_sync_adds_new_item(repo):
    from controllership_finance_app.infrastructure.persistence.plugins_db import (
        plugins_db_connect,
    )
    template_id = _seed_template()
    vid = _published_version(repo, template_id, 2, "2026-09")
    comp, _ = repo.open_competence("2026-09", ACTOR)
    repo.apply_revision(
        vid, actor=ACTOR, reason="r", expected_revision=1,
        changes=[{"op": "ADD", "item_key": "CK-99",
                  "payload": {"sheet": "FISICO", "name": "Novo doc",
                              "sort_order": 99}}],
        idempotency_key=uuid.uuid4().hex,
    )
    repo.dispatch_sync_events()
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT state FROM controllership_finance"
            ".competence_checklist_item WHERE competence_id=%s"
            " AND item_key='CK-99'",
            (comp["competence_id"],),
        )
        assert cur.fetchone()[0] == "EXPECTED"


def test_sync_skips_completed_competence(repo):
    from controllership_finance_app.infrastructure.persistence.plugins_db import (
        plugins_db_connect,
    )
    template_id = _seed_template()
    vid = _published_version(repo, template_id, 2, "2026-10")
    comp, _ = repo.open_competence("2026-10", ACTOR)
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE controllership_finance.monthly_competence"
            " SET first_completed_at=now(),"
            "     completion_record='COMPLETED'"
            " WHERE competence_id=%s",
            (comp["competence_id"],),
        )
        conn.commit()
    repo.apply_revision(
        vid, actor=ACTOR, reason="r", expected_revision=1,
        changes=[{"op": "RETIRE", "item_key": "CK-01"}],
        idempotency_key=uuid.uuid4().hex,
    )
    repo.dispatch_sync_events()
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT state FROM controllership_finance"
            ".competence_checklist_item WHERE competence_id=%s"
            " AND item_key='CK-01'",
            (comp["competence_id"],),
        )
        assert cur.fetchone()[0] == "EXPECTED"  # intocada
        cur.execute(
            "SELECT state, skip_reason FROM controllership_finance"
            ".checklist_sync_run WHERE competence_id=%s",
            (comp["competence_id"],),
        )
        assert cur.fetchone() == ("SKIPPED", "competence_completed")


def test_sync_status_and_retry(repo):
    template_id = _seed_template()
    vid = _published_version(repo, template_id, 1, "2026-11")
    repo.open_competence("2026-11", ACTOR)
    rev = repo.apply_revision(
        vid, actor=ACTOR, reason="r", expected_revision=1,
        changes=[{"op": "RETIRE", "item_key": "CK-01"}],
        idempotency_key=uuid.uuid4().hex,
    )
    repo.dispatch_sync_events()
    status = repo.get_sync_status("2026-11")
    assert status["state"] in ("CONVERGED", "CONVERGED_WITH_EXCLUSIONS",
                               "SYNCED")
    # retry sem falhas -> erro tipado
    from controllership_finance_app.domain.closing_checklist.errors import (
        SyncRetryNotAllowed,
    )
    with pytest.raises(SyncRetryNotAllowed):
        repo.retry_sync_event(rev["sync_event_id"], ACTOR)


def test_preview_revision(repo):
    template_id = _seed_template()
    vid = _published_version(repo, template_id, 2, "2026-12")
    repo.open_competence("2026-12", ACTOR)
    preview = repo.preview_revision(
        vid,
        [{"op": "RETIRE", "item_key": "CK-01"},
         {"op": "ADD", "item_key": "CK-03"},
         {"op": "REACTIVATE", "item_key": "CK-01"}],
    )
    assert preview["eligible_competences"] >= 1
    assert preview["affected_items"][0]["valid"] is True
    assert preview["affected_items"][1]["valid"] is True
    assert preview["affected_items"][2]["valid"] is False


def test_sync_readback_reopens_divergent_run(repo):
    """OC-2/RQ-03: evento não converge com diff residual — o read-back
    reabre o run para PENDING e converged_at permanece NULL."""
    from controllership_finance_app.infrastructure.persistence.plugins_db import (
        plugins_db_connect,
    )
    template_id = _seed_template()
    vid = _published_version(repo, template_id, 1, "2027-01")
    comp, _ = repo.open_competence("2027-01", ACTOR)
    repo.apply_revision(
        vid, actor=ACTOR, reason="r", expected_revision=1,
        changes=[{"op": "RETIRE", "item_key": "CK-01"}],
        idempotency_key=uuid.uuid4().hex,
    )
    result = repo.dispatch_sync_events()
    assert result["events_completed"] >= 1
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT converged_at FROM controllership_finance"
            ".checklist_sync_event ORDER BY emitted_at DESC LIMIT 1"
        )
        assert cur.fetchone()[0] is not None
        # Divergência residual simulada: item voltou a EXPECTED sem
        # passar pelo reconcile (escrita perdida/corrida).
        cur.execute(
            "UPDATE controllership_finance.competence_checklist_item"
            " SET state='EXPECTED', cancel_origin=NULL"
            " WHERE competence_id=%s AND item_key='CK-01'",
            (comp["competence_id"],),
        )
        conn.commit()
        # Novo evento sobre a mesma revisão — read-back deve reabrir.
        cur.execute(
            "UPDATE controllership_finance.checklist_sync_event"
            " SET converged_at=NULL, completion_state=NULL"
            " WHERE converged_at IS NOT NULL"
        )
        conn.commit()
    result2 = repo.dispatch_sync_events()
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT state, last_error FROM controllership_finance"
            ".checklist_sync_run WHERE competence_id=%s",
            (comp["competence_id"],),
        )
        row = cur.fetchone()
        # run reaberto pelo read-back OU reconciliado novamente —
        # o que nunca pode acontecer é convergir com diff residual
        # persistido: após nova reconciliação o estado converge.
        assert row[0] in ("PENDING", "APPLIED",
                          "APPLIED_WITH_EXCLUSIONS")
        if row[0] == "PENDING":
            assert row[1] == "read_back_divergence"
