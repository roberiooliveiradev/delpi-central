"""P4 pendências — integração PostgreSQL real (doc 11 + RQ-P4-01..08).

Ativado com CF_TEST_PG_HOST/CF_TEST_PG_NAME/CF_TEST_PG_USER/
CF_TEST_PG_PASSWORD + CF_TEST_PG_CLUSTER=test +
CF_TEST_PG_ALLOW_DESTRUCTIVE=1 — banco efêmero com prova de ownership.
"""

from __future__ import annotations

import os
import uuid

import psycopg
import pytest

from controllership_finance_app.infrastructure.persistence import (
    migrations_runner as mr,
)
from controllership_finance_app.domain.closing_checklist.errors import (
    ClassificationAlreadyConfirmed,
    InvalidPendencyTransition,
    MissingDismissJustification,
    PendencyNotFound,
    PendencyOwnershipRequired,
    PendencyTerminal,
    StaleRevision,
)
from controllership_finance_app.infrastructure.persistence.closing_checklist_repository import (
    ClosingChecklistRepository,
)
from controllership_finance_app.infrastructure.persistence.closing_pendency_repository import (
    ClosingPendencyRepository,
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

ADMIN = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-admin-p4-test"))
ACTOR_A = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-actor-a-p4"))
ACTOR_B = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-actor-b-p4"))
PERIOD = "2026-06"

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
    assert applied == [
        "V001__create_closing_checklist_schema.sql",
        "V002__seed_monthly_closing_checklist_v1.sql",
        "V003__create_closing_documents.sql",
        "V004__document_version_idempotency.sql",
        "V005__p2_item_validation.sql",
        "V006__p4_pendencies.sql",
        "V007__p3_cutoff_reconciliation.sql",
        "V008__p5_packages_review.sql",
        "V009__p3_official_provenance.sql",
        "V010__p6_catalogs_review_lifecycle_notifications.sql",
        "V011__clara_knowledge_and_proposals.sql",
        "V012__clara_batch_orchestration.sql",
        "V013__clara_step_up_consent.sql",
        "V014__clara_consent_challenge.sql",
        "V015__monthly_competence_optional_template.sql",
        "V016__document_messages.sql",
        "V017__document_requirement_operations.sql",
        "V018__recipient_document_delivery.sql",
    ]
    checklist = ClosingChecklistRepository()
    template_id = str(checklist.list_templates()[0]["template_id"])
    checklist.submit_version_for_review(
        template_id, 1, actor=ADMIN
    )
    checklist.publish_version(
        template_id, 1, effective_from_period="2026-01", actor=ADMIN
    )
    checklist.open_competence(PERIOD, actor=ADMIN)
    return {
        "checklist": checklist,
        "pend": ClosingPendencyRepository(),
    }


def _create(setup, **overrides) -> dict:
    params = {
        "actor": ACTOR_A,
        "kind": "OTHER",
        "title": f"Pendência {uuid.uuid4().hex[:8]}",
        # ownership default do ator de teste — transições exigem
        # responsável atual ou papel elegível (controle B/C).
        "responsible_subject": ACTOR_A,
    }
    params.update(overrides)
    return setup["pend"].create_pendency(PERIOD, **params)


# -- criação/lista ---------------------------------------------------------


def test_create_and_get_pendency(setup):
    p = _create(
        setup,
        kind="MISSING_EVIDENCE",
        title="Nota fiscal pendente",
        queue="fiscal",
        responsible_subject=ACTOR_B,
    )
    assert p["state"] == "OPEN"
    assert p["responsible_subject"] == ACTOR_B

    fetched = setup["pend"].get_pendency(PERIOD, p["pendency_id"])
    assert fetched["kind"] == "MISSING_EVIDENCE"


def test_list_filters_by_state_and_kind(setup):
    open_p = _create(setup, kind="EXTERNAL_DEPENDENCY")
    resolved = _create(setup)
    setup["pend"].transition_pendency(
        PERIOD, resolved["pendency_id"], ACTOR_A,
        to_state="IN_ANALYSIS", expected_revision=1,
    )
    setup["pend"].transition_pendency(
        PERIOD, resolved["pendency_id"], ACTOR_A,
        to_state="RESOLVED", expected_revision=2,
    )
    opens = setup["pend"].list_pendencies(PERIOD, state="OPEN")
    ids = {i["pendency_id"] for i in opens["items"]}
    assert open_p["pendency_id"] in ids
    assert resolved["pendency_id"] not in ids

    ext = setup["pend"].list_pendencies(
        PERIOD, kind="EXTERNAL_DEPENDENCY"
    )
    assert any(
        i["pendency_id"] == open_p["pendency_id"]
        for i in ext["items"]
    )


def test_pendency_unknown_period_raises(setup):
    with pytest.raises(Exception) as exc:
        setup["pend"].list_pendencies("2026-12")
    assert "aberta" in str(exc.value).lower()


# -- claim / reassign ------------------------------------------------------


def test_claim_sets_responsible_and_history(setup):
    p = _create(setup)
    claimed = setup["pend"].claim_pendency(
        PERIOD, p["pendency_id"], ACTOR_A, expected_revision=1
    )
    assert claimed["responsible_subject"] == ACTOR_A
    # claim muda responsabilidade, não o estado — IN_ANALYSIS é
    # transição explícita separada (grafo fechado, RQ-P4-03).
    assert claimed["state"] == "OPEN"

    history = setup["pend"].list_pendency_history(
        PERIOD, p["pendency_id"]
    )
    event_types = [e["event_type"] for e in history["events"]]
    assert "PENDENCY_CREATED" in event_types
    assert "PENDENCY_CLAIMED" in event_types


def test_reassign_preserves_ownership_history(setup):
    p = _create(setup, responsible_subject=ACTOR_A)
    moved = setup["pend"].reassign_pendency(
        PERIOD, p["pendency_id"], ADMIN,
        new_responsible=ACTOR_B, expected_revision=1,
    )
    assert moved["responsible_subject"] == ACTOR_B
    events = [
        e["event_type"]
        for e in setup["pend"].list_pendency_history(
            PERIOD, p["pendency_id"]
        )["events"]
    ]
    assert "PENDENCY_REASSIGNED" in events


def test_stale_revision_rejected(setup):
    p = _create(setup, responsible_subject=None)
    setup["pend"].claim_pendency(
        PERIOD, p["pendency_id"], ACTOR_A, expected_revision=1
    )
    # revision desatualizada é rejeitada mesmo pelo próprio owner.
    with pytest.raises(StaleRevision):
        setup["pend"].claim_pendency(
            PERIOD, p["pendency_id"], ACTOR_A, expected_revision=1
        )
    # claim por terceiro é bloqueado por ownership antes do OCC.
    with pytest.raises(PendencyOwnershipRequired):
        setup["pend"].claim_pendency(
            PERIOD, p["pendency_id"], ACTOR_B, expected_revision=2
        )


# -- máquina de estados ----------------------------------------------------


def test_closed_transition_graph(setup):
    p = _create(setup)
    # OPEN → RESOLVED não é permitido direto pelo grafo fechado.
    with pytest.raises(InvalidPendencyTransition):
        setup["pend"].transition_pendency(
            PERIOD, p["pendency_id"], ACTOR_A,
            to_state="RESOLVED", expected_revision=1,
        )
    # OPEN → IN_ANALYSIS → WAITING_EXTERNAL → RESOLVED
    setup["pend"].transition_pendency(
        PERIOD, p["pendency_id"], ACTOR_A,
        to_state="IN_ANALYSIS", expected_revision=1,
    )
    setup["pend"].transition_pendency(
        PERIOD, p["pendency_id"], ACTOR_A,
        to_state="WAITING_EXTERNAL", expected_revision=2,
    )
    done = setup["pend"].transition_pendency(
        PERIOD, p["pendency_id"], ACTOR_A,
        to_state="RESOLVED", expected_revision=3,
        notes="regularizado no ERP pelo owner",
    )
    assert done["state"] == "RESOLVED"


def test_terminal_state_rejects_mutation(setup):
    p = _create(setup)
    setup["pend"].transition_pendency(
        PERIOD, p["pendency_id"], ACTOR_A,
        to_state="IN_ANALYSIS", expected_revision=1,
    )
    setup["pend"].transition_pendency(
        PERIOD, p["pendency_id"], ACTOR_A,
        to_state="RESOLVED", expected_revision=2,
    )
    with pytest.raises(PendencyTerminal):
        setup["pend"].transition_pendency(
            PERIOD, p["pendency_id"], ACTOR_A,
            to_state="OPEN", expected_revision=3,
        )
    with pytest.raises(PendencyTerminal):
        setup["pend"].claim_pendency(
            PERIOD, p["pendency_id"], ACTOR_B, expected_revision=3
        )


def test_dismissed_requires_justification(setup):
    p = _create(setup)
    with pytest.raises(MissingDismissJustification):
        setup["pend"].transition_pendency(
            PERIOD, p["pendency_id"], ACTOR_A,
            to_state="DISMISSED", expected_revision=1,
        )
    dismissed = setup["pend"].transition_pendency(
        PERIOD, p["pendency_id"], ACTOR_A,
        to_state="DISMISSED", expected_revision=1,
        justification="item não se aplica à filial",
    )
    assert dismissed["state"] == "DISMISSED"
    assert dismissed["dismiss_justification"]


# -- classificação ---------------------------------------------------------


def test_suggestion_does_not_decide(setup):
    """Sugestão determinística nunca preenche confirmed_classification."""
    p = _create(
        setup,
        kind="RECONCILIATION_DIVERGENCE",
        suggested_classification="RECONCILIATION",
        suggestion_source="DETERMINISTIC",
        suggestion_rationale="divergência recorrente",
    )
    assert p["suggested_classification"] == "RECONCILIATION"
    assert p["confirmed_classification"] is None


def test_confirm_classification_once(setup):
    p = _create(setup, suggested_classification="OTHER")
    confirmed = setup["pend"].confirm_classification(
        PERIOD, p["pendency_id"], ADMIN,
        classification="RECONCILIATION", reason="revisão humana",
        expected_revision=1,
    )
    assert confirmed["confirmed_classification"] == "RECONCILIATION"
    # Confirmação é uma vez — sugestão não pode ser re-confirmada.
    with pytest.raises(ClassificationAlreadyConfirmed):
        setup["pend"].confirm_classification(
            PERIOD, p["pendency_id"], ADMIN,
            classification="OTHER", reason=None,
            expected_revision=2,
        )


# -- escopo de recurso -----------------------------------------------------


def test_branch_scope_isolation(setup):
    """Recurso BRANCH invisível ao contexto MATRIX (e vice-versa)."""
    p = _create(setup, branch_scope="BRANCH")
    fetched = setup["pend"].get_pendency(
        PERIOD, p["pendency_id"], request_scope="BRANCH"
    )
    assert fetched["pendency_id"] == p["pendency_id"]
    with pytest.raises(PendencyNotFound):
        setup["pend"].get_pendency(
            PERIOD, p["pendency_id"], request_scope="MATRIX"
        )
    listed = setup["pend"].list_pendencies(
        PERIOD, request_scope="MATRIX"
    )
    assert all(
        i["pendency_id"] != p["pendency_id"] for i in listed["items"]
    )


def test_pendency_linked_to_checklist_item(setup):
    item = next(
        i
        for i in setup["checklist"].list_competence_items(PERIOD)
        if i["item_key"] == "CK-E-01"
    )
    p = _create(
        setup,
        kind="MISSING_EVIDENCE",
        snapshot_item_id=str(item["snapshot_item_id"]),
    )
    assert p["snapshot_item_id"] == item["snapshot_item_id"]
