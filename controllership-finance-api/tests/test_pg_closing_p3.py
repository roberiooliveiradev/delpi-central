"""P3 cutoff/conciliação — integração PostgreSQL real (doc 10/15.1).

Ativado com CF_TEST_PG_* + CF_TEST_PG_CLUSTER=test +
CF_TEST_PG_ALLOW_DESTRUCTIVE=1 — banco efêmero com prova de ownership.

Cobre: cutoff humano único, revalidação append-only invalidada por
mudança de input, paridade monetária exata R$ 0,00, bloqueio por source
indisponível e `STOCK_CLOSED` exclusivamente via estado canônico.
"""

from __future__ import annotations

import os
import uuid
from decimal import Decimal

import psycopg
import pytest
from psycopg.rows import dict_row

from controllership_finance_app.infrastructure.persistence import (
    migrations_runner as mr,
)
from controllership_finance_app.domain.closing_checklist.errors import (
    CutoffAlreadyConfirmed,
    CutoffNotConfirmed,
    InvalidReconciliationDomain,
    InvalidSourceState,
    StaleRevision,
)
from controllership_finance_app.infrastructure.persistence.closing_checklist_repository import (
    ClosingChecklistRepository,
)
from controllership_finance_app.infrastructure.persistence.closing_p3_repository import (
    RECONCILIATION_DOMAINS,
    ClosingP3Repository,
)
from controllership_finance_app.infrastructure.persistence.plugins_db import (
    SCHEMA_NAME,
    plugins_db_connect,
)

PG_ENV = (
    "CF_TEST_PG_HOST",
    "CF_TEST_PG_NAME",
    "CF_TEST_PG_USER",
    "CF_TEST_PG_PASSWORD",
)

pytestmark = pytest.mark.skipif(
    not all(os.getenv(k) for k in PG_ENV),
    reason="CF_TEST_PG_* ausente — integração PostgreSQL não configurada",
)

ADMIN = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-admin-p3-test"))
ACTOR = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-actor-p3"))
PERIOD = "2026-07"

from pg_test_isolation import (  # noqa: E402
    assert_safe_test_prefix,
    create_owned_test_database,
    drop_owned_test_database,
    require_test_environment,
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
    owned = create_owned_test_database(_test_connect, admin_db, prefix)

    original = {
        k: getattr(cfg.settings, k)
        for k in (
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
    for k, v in original.items():
        setattr(cfg.settings, k, v)


@pytest.fixture(scope="module")
def setup(_configure_db):
    applied = mr.run_migrations()
    assert applied[-2:] == [
        "V006__p4_pendencies.sql",
        "V007__p3_cutoff_reconciliation.sql",
    ]
    checklist = ClosingChecklistRepository()
    template_id = str(checklist.list_templates()[0]["template_id"])
    checklist.publish_version(
        template_id, 1, effective_from_period="2026-01", actor=ADMIN
    )
    checklist.open_competence(PERIOD, actor=ADMIN)
    p3 = ClosingP3Repository()
    with plugins_db_connect() as conn, conn.cursor(
        row_factory=dict_row
    ) as cur:
        competence_id = p3._competence_id(cur, PERIOD)
    return {"p3": p3, "competence_id": competence_id}


def _set_all_available(setup, amount: str = "1000.00"):
    for domain in RECONCILIATION_DOMAINS:
        setup["p3"].upsert_reconciliation(
            PERIOD, domain, actor=ACTOR,
            source_state="AVAILABLE",
            expected_amount=Decimal(amount),
            reported_amount=Decimal(amount),
            provenance={"source": "test_fixture"},
        )


# -- estado inicial --------------------------------------------------------


def test_initial_state_waiting_for_cutoff(setup):
    state = setup["p3"].get_p3_state(PERIOD)
    assert state["state"] == "WAITING_FOR_CUTOFF"
    assert "cutoff_not_confirmed" in state["blockers"]
    # sources nunca nascem zeradas: indisponibilidade honesta.
    for domain in RECONCILIATION_DOMAINS:
        assert f"source_unavailable:{domain}" in state["blockers"]
    assert state["canonical_stock_state"] == "UNAVAILABLE"


# -- cutoff ----------------------------------------------------------------


def test_revalidation_before_cutoff_fails(setup):
    with pytest.raises(CutoffNotConfirmed):
        setup["p3"].revalidate(PERIOD, actor=ACTOR)


def test_cutoff_unique_per_competence(setup):
    cutoff = setup["p3"].confirm_cutoff(PERIOD, actor=ACTOR)
    assert cutoff["confirmed_by"] == ACTOR
    with pytest.raises(CutoffAlreadyConfirmed):
        setup["p3"].confirm_cutoff(PERIOD, actor=ACTOR)


# -- conciliação e paridade ------------------------------------------------


def test_unavailable_source_blocks_ready(setup):
    """Mesmo com cutoff e revalidação, source ausente bloqueia."""
    setup["p3"].revalidate(PERIOD, actor=ACTOR)
    state = setup["p3"].get_p3_state(PERIOD)
    assert state["state"] == "REVALIDATION_REQUIRED"
    assert not state["revalidation_valid"]


def test_zero_parity_ready_to_close(setup):
    _set_all_available(setup, "1000.00")
    rev = setup["p3"].revalidate(PERIOD, actor=ACTOR)
    assert rev["result"] == "VALID"
    state = setup["p3"].get_p3_state(PERIOD)
    assert state["state"] == "READY_TO_CLOSE"
    assert state["blockers"] == []


def test_nonzero_divergence_blocks(setup):
    """R$ 0,01 de divergência bloqueia — tolerância é exatamente zero."""
    setup["p3"].upsert_reconciliation(
        PERIOD, "P7", actor=ACTOR,
        source_state="AVAILABLE",
        expected_amount=Decimal("1000.00"),
        reported_amount=Decimal("1000.01"),
        provenance={"source": "test_fixture"},
    )
    setup["p3"].revalidate(PERIOD, actor=ACTOR)
    state = setup["p3"].get_p3_state(PERIOD)
    assert state["state"] != "READY_TO_CLOSE"
    assert "divergence:P7" in state["blockers"]
    # -R$ 0,01 também bloqueia.
    setup["p3"].upsert_reconciliation(
        PERIOD, "P7", actor=ACTOR,
        source_state="AVAILABLE",
        expected_amount=Decimal("1000.00"),
        reported_amount=Decimal("999.99"),
        provenance={"source": "test_fixture"},
    )
    state = setup["p3"].get_p3_state(PERIOD)
    assert "divergence:P7" in state["blockers"]


def test_input_change_invalidates_revalidation(setup):
    """Mudança de input após VALID exige nova revalidação."""
    _set_all_available(setup, "1000.00")
    rev = setup["p3"].revalidate(PERIOD, actor=ACTOR)
    assert rev["result"] == "VALID"
    assert setup["p3"].get_p3_state(PERIOD)["state"] == "READY_TO_CLOSE"
    # input muda (source passa a divergir) → fingerprint diverge →
    # REVALIDATION_REQUIRED
    setup["p3"].upsert_reconciliation(
        PERIOD, "H02", actor=ACTOR,
        source_state="AVAILABLE",
        expected_amount=Decimal("1000.00"),
        reported_amount=Decimal("5000.00"),
        provenance={"source": "test_fixture", "retried": True},
    )
    state = setup["p3"].get_p3_state(PERIOD)
    assert state["state"] == "REVALIDATION_REQUIRED"
    # input corrigido + nova revalidação sobre o input vigente volta
    # a valer
    setup["p3"].upsert_reconciliation(
        PERIOD, "H02", actor=ACTOR,
        source_state="AVAILABLE",
        expected_amount=Decimal("1000.00"),
        reported_amount=Decimal("1000.00"),
        provenance={"source": "test_fixture"},
    )
    setup["p3"].revalidate(PERIOD, actor=ACTOR)
    assert setup["p3"].get_p3_state(PERIOD)["state"] == "READY_TO_CLOSE"


def test_zero_before_cutoff_is_only_preliminary(setup):
    """R$ 0,00 registrado não basta — sem cutoff/revalidação válida,
    readiness não é alcançada (coberto pelo caminho WAITING → REVAL)."""
    state = setup["p3"].get_p3_state(PERIOD)
    # cutoff já confirmado neste módulo — verifica-se que inputs zerados
    # sem revalidação válida não liberam readiness.
    _set_all_available(setup, "0.00")
    # fingerprint mudou → revalidação anterior expira
    state = setup["p3"].get_p3_state(PERIOD)
    assert state["state"] == "REVALIDATION_REQUIRED"


def test_reconciliation_domain_and_state_catalog(setup):
    with pytest.raises(InvalidReconciliationDomain):
        setup["p3"].upsert_reconciliation(
            PERIOD, "BOGUS", actor=ACTOR, source_state="AVAILABLE"
        )
    with pytest.raises(InvalidSourceState):
        setup["p3"].upsert_reconciliation(
            PERIOD, "P7", actor=ACTOR, source_state="MAGICAL"
        )


def test_reconciliation_optimistic_revision(setup):
    row = setup["p3"].upsert_reconciliation(
        PERIOD, "ENTRADAS_SAIDAS", actor=ACTOR,
        source_state="PARTIAL",
    )
    with pytest.raises(StaleRevision):
        setup["p3"].upsert_reconciliation(
            PERIOD, "ENTRADAS_SAIDAS", actor=ACTOR,
            source_state="AVAILABLE",
            expected_revision=row["revision"] + 9,
        )


# -- estado canônico do estoque --------------------------------------------


def test_stock_closed_only_from_canonical_row(setup):
    """Sem linha em closing_stock_state → UNAVAILABLE; com CLOSED →
    STOCK_CLOSED. O Portal nunca escreve esse estado por rota."""
    competence_id = setup["competence_id"]
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            f"DELETE FROM {SCHEMA_NAME}.closing_stock_state"
            " WHERE competence_id = %s",
            (competence_id,),
        )
        cur.execute(
            f"""
            INSERT INTO {SCHEMA_NAME}.closing_stock_state
                (competence_id, canonical_state, source, fetched_at)
            VALUES (%s, 'CLOSED', 'totvs_t03_sync', now())
            """,
            (competence_id,),
        )
        conn.commit()
    state = setup["p3"].get_p3_state(PERIOD)
    assert state["state"] == "STOCK_CLOSED"
    assert state["canonical_stock_state"] == "CLOSED"


def test_p3_audit_events_recorded(setup):
    events = setup["p3"].list_p3_events(PERIOD)
    types = [e["event_type"] for e in events["items"]]
    assert "CUTOFF_CONFIRMED" in types
    assert "P3_REVALIDATED" in types
    assert "RECONCILIATION_UPDATED" in types
