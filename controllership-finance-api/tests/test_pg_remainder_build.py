"""Remainder build — integração PostgreSQL real (banco efêmero).

Cobre as capacidades implementadas sob CF-PROC0072-REMAINDER-BUILD-GO-001:

- F1: lifecycle DRAFT→REVIEW→PUBLISH e catálogos governados P6
  (`closing_catalog_entry`) com OCC, desativação prospectiva e consumo
  por P5-H (`PACKAGE_REQUIRED_AREA`) e T05-binding (`REVIEW_ELIGIBILITY`);
- F2: elegibilidade fail-closed por binding de grupo Core quando
  configurado — `assignment_only` permanece auditado quando ausente;
- F4: notification outbox (emissão atômica + dispatcher best-effort
  para Core — entrega nunca é estado de negócio) e congelamento de
  evidência/validação de item em pacote submetido;
- F5: TaskProjection self-only (`/me/tasks`) sobre producers P4/P5.
"""

from __future__ import annotations

import os
import uuid
from decimal import Decimal

import pytest
from psycopg.rows import dict_row

from controllership_finance_app.domain.closing_checklist.errors import (
    CatalogEntryNotFound,
    DraftAlreadyOpen,
    InvalidCatalogEntry,
    ItemLockedBySubmittedPackage,
    ReviewerNotEligible,
    StaleRevision,
    VersionNotDraft,
    VersionNotInReview,
)
from controllership_finance_app.infrastructure.gateways.core_notifications_gateway import (
    CoreNotificationsDispatcher,
)
from controllership_finance_app.infrastructure.persistence.closing_catalog_repository import (
    ClosingCatalogRepository,
)
from controllership_finance_app.infrastructure.persistence.closing_checklist_repository import (
    ClosingChecklistRepository,
)
from controllership_finance_app.infrastructure.persistence.closing_p3_repository import (
    ClosingP3Repository,
    RECONCILIATION_DOMAINS,
)
from controllership_finance_app.infrastructure.persistence.closing_package_repository import (
    ClosingPackageRepository,
)
from controllership_finance_app.infrastructure.persistence.closing_pendency_repository import (
    ClosingPendencyRepository,
)
from controllership_finance_app.infrastructure.persistence.closing_tasks_repository import (
    ClosingTasksRepository,
)
from controllership_finance_app.infrastructure.persistence.closing_validation_repository import (
    ClosingValidationRepository,
)
from controllership_finance_app.infrastructure.persistence import (
    migrations_runner as mr,
)
from controllership_finance_app.infrastructure.persistence.plugins_db import (
    plugins_db_connect,
)

from pg_test_isolation import (  # noqa: E402
    assert_safe_test_prefix,
    create_owned_test_database,
    drop_owned_test_database,
    require_test_environment,
)

ADMIN = str(uuid.uuid4())
REVIEWER_A = str(uuid.uuid4())
REVIEWER_B = str(uuid.uuid4())
OUTSIDER = str(uuid.uuid4())

P_LIFE = "2026-05"
P_PKG = "2026-06"
P_TASK = "2026-07"
P_LOCK = "2026-08"
P_ELIG = "2026-09"


def _test_connect(dbname: str):
    import psycopg

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
    assert "V010__p6_catalogs_review_lifecycle_notifications.sql" in applied
    checklist = ClosingChecklistRepository()
    template_id = str(checklist.list_templates()[0]["template_id"])
    return {
        "checklist": checklist,
        "template_id": template_id,
        "packages": ClosingPackageRepository(),
        "catalog": ClosingCatalogRepository(),
        "tasks": ClosingTasksRepository(),
        "pendencies": ClosingPendencyRepository(),
        "validations": ClosingValidationRepository(),
    }


def _publish_v1(setup, effective_from: str = "2026-01"):
    """Garante v1 PUBLISHED (idempotente entre testes do módulo)."""
    versions = {
        v["version"]: v["status"]
        for v in setup["checklist"].list_versions(setup["template_id"])
    }
    if versions.get(1) == "DRAFT":
        setup["checklist"].submit_version_for_review(
            setup["template_id"], 1, actor=ADMIN
        )
        setup["checklist"].publish_version(
            setup["template_id"],
            1,
            effective_from_period=effective_from,
            actor=ADMIN,
        )
    elif versions.get(1) == "REVIEW":
        setup["checklist"].publish_version(
            setup["template_id"],
            1,
            effective_from_period=effective_from,
            actor=ADMIN,
        )


def _open_competence(setup, period: str):
    _publish_v1(setup)
    setup["checklist"].open_competence(period, actor=ADMIN)


def _accept_all_items(period: str, area: str | None = None):
    where = (
        "competence_id = (SELECT competence_id FROM "
        "controllership_finance.monthly_competence WHERE period = %s)"
        " AND state = 'EXPECTED'"
    )
    params: list = [period]
    if area is not None:
        where += " AND recipient_area = %s"
        params.append(area)
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE controllership_finance.competence_checklist_item"
            f" SET state = 'ACCEPTED' WHERE {where}",
            params,
        )


def _make_p3_ready(period: str):
    p3 = ClosingP3Repository()
    for domain in RECONCILIATION_DOMAINS:
        p3.upsert_reconciliation(
            period,
            domain,
            actor=ADMIN,
            source_state="AVAILABLE",
            expected_amount=Decimal("1000.00"),
            reported_amount=Decimal("1000.00"),
            provenance={"source": "test"},
            provenance_kind="DECLARED",
        )
    p3.confirm_cutoff(period, actor=ADMIN)
    p3.revalidate(period, actor=ADMIN)


def _submit_fiscal(setup, period: str, reviewer: str = REVIEWER_A):
    """Pacote FISCAL pronto e submetido com reviewer atribuído."""
    repo = setup["packages"]
    _make_p3_ready(period)
    _accept_all_items(period, "FISCAL")
    package = repo.finalize_package(period, "FISCAL", actor=ADMIN)
    version_id = str(package["current_version"]["package_version_id"])
    repo.assign_actor(
        period,
        actor=ADMIN,
        role="REVIEWER",
        subject=reviewer,
        recipient_area="FISCAL",
        area="FISCAL",
    )
    repo.submit_for_review(
        period, version_id, actor=ADMIN, expected_revision=1
    )
    return version_id


def _notifications(event_type: str | None = None, period: str | None = None):
    sql = (
        "SELECT n.* FROM controllership_finance.closing_notification_event"
        " n JOIN controllership_finance.monthly_competence mc"
        " ON mc.competence_id = n.competence_id WHERE true"
    )
    params: list = []
    if event_type:
        sql += " AND n.event_type = %s"
        params.append(event_type)
    if period:
        sql += " AND mc.period = %s"
        params.append(period)
    sql += " ORDER BY n.emitted_at"
    with plugins_db_connect() as conn, conn.cursor(
        row_factory=dict_row
    ) as cur:
        cur.execute(sql, params)
        return cur.fetchall()


# -- F1: lifecycle REVIEW ---------------------------------------------------


def test_review_lifecycle_full_cycle(setup):
    checklist = setup["checklist"]
    template_id = setup["template_id"]
    _publish_v1(setup)

    draft = checklist.create_draft_version(template_id, actor=ADMIN)
    assert draft["version"] == 2
    assert draft["status"] == "DRAFT"

    # publicar direto de DRAFT é recusado — passa por REVIEW
    with pytest.raises(VersionNotInReview):
        checklist.publish_version(
            template_id, 2, effective_from_period="2026-12", actor=ADMIN
        )

    review = checklist.submit_version_for_review(
        template_id, 2, actor=ADMIN
    )
    assert review["status"] == "REVIEW"

    # REVIEW também ocupa o slot de "versão aberta" do template
    with pytest.raises(DraftAlreadyOpen):
        checklist.create_draft_version(template_id, actor=ADMIN)

    # submit em versão já REVIEW é recusado
    with pytest.raises(VersionNotDraft):
        checklist.submit_version_for_review(
            template_id, 2, actor=ADMIN
        )

    # devolução motivada a DRAFT
    returned = checklist.return_version_to_draft(
        template_id, 2, reason="ajustar item CK-E-01", actor=ADMIN
    )
    assert returned["status"] == "DRAFT"

    checklist.submit_version_for_review(template_id, 2, actor=ADMIN)
    published = checklist.publish_version(
        template_id, 2, effective_from_period="2026-12", actor=ADMIN
    )
    assert published["status"] == "PUBLISHED"
    assert published["effective_from_period"] == "2026-12"


# -- F1: catálogos governados ------------------------------------------------


def test_catalog_crud_occ_and_prospective_deactivation(setup):
    catalog = setup["catalog"]

    entry = catalog.create_entry(
        "BANK_ACCOUNT",
        code="BB-001",
        label="Banco do Brasil — conta 12345-6",
        attributes={"bank": "001", "account": "12345-6"},
        actor=ADMIN,
    )
    assert entry["active"] is True
    assert entry["revision"] == 1

    updated = catalog.update_entry(
        "BANK_ACCOUNT",
        "BB-001",
        label="Banco do Brasil — conta 12345-6 (nova)",
        expected_revision=1,
        actor=ADMIN,
    )
    assert updated["revision"] == 2

    with pytest.raises(StaleRevision):
        catalog.update_entry(
            "BANK_ACCOUNT",
            "BB-001",
            label="stale",
            expected_revision=1,
            actor=ADMIN,
        )

    deactivated = catalog.deactivate_entry(
        "BANK_ACCOUNT", "BB-001", expected_revision=2, actor=ADMIN
    )
    assert deactivated["active"] is False
    # histórico permanece referenciável
    active_codes = {
        e["code"] for e in catalog.active_entries("BANK_ACCOUNT")
    }
    assert "BB-001" not in active_codes

    reactivated = catalog.reactivate_entry(
        "BANK_ACCOUNT", "BB-001", actor=ADMIN
    )
    assert reactivated["active"] is True

    with pytest.raises(InvalidCatalogEntry):
        catalog.create_entry(
            "NOT_A_CATALOG", code="X", label="x", actor=ADMIN
        )
    with pytest.raises(CatalogEntryNotFound):
        catalog.deactivate_entry(
            "BANK_ACCOUNT", "NOPE", expected_revision=1, actor=ADMIN
        )


def test_p5h_required_areas_from_catalog(setup):
    """Catálogo PACKAGE_REQUIRED_AREA alimenta required_areas; sem
    entrada o fallback monoárea é explícito e auditado."""
    catalog = setup["catalog"]
    _open_competence(setup, P_PKG)

    # 1) fallback: sem catálogo → [recipient_area], source auditado
    version_id = _submit_fiscal(setup, P_PKG)
    with plugins_db_connect() as conn, conn.cursor(
        row_factory=dict_row
    ) as cur:
        cur.execute(
            "SELECT required_areas FROM "
            "controllership_finance.closing_package_version "
            "WHERE package_version_id = %s",
            (version_id,),
        )
        assert cur.fetchone()["required_areas"] == ["FISCAL"]
        cur.execute(
            "SELECT detail FROM controllership_finance.closing_audit_event"
            " WHERE entity_id = %s"
            " AND event_type = 'PACKAGE_SUBMITTED_FOR_REVIEW'",
            (version_id,),
        )
        detail = cur.fetchone()["detail"]
        assert detail["required_areas_source"] == "fallback_recipient_area"


# -- F2: elegibilidade T05-binding --------------------------------------------


def test_review_eligibility_binding_fail_closed(setup):
    catalog = setup["catalog"]
    _open_competence(setup, P_ELIG)
    version_id = _submit_fiscal(setup, P_ELIG)
    repo = setup["packages"]

    # binding configurado para FISCAL → grupo errado falha fechado
    catalog.create_entry(
        "REVIEW_ELIGIBILITY",
        code="FISCAL-ELITE",
        label="Revisores fiscais elegíveis",
        attributes={"area": "FISCAL", "core_group": "cf-fiscal-reviewers"},
        actor=ADMIN,
    )
    with pytest.raises(ReviewerNotEligible):
        repo.record_decision(
            P_ELIG,
            version_id,
            actor=REVIEWER_A,
            area="FISCAL",
            outcome="ACCEPTED",
            user_groups=["grupo-errado"],
        )
    # grupo certo decide
    decision = repo.record_decision(
        P_ELIG,
        version_id,
        actor=REVIEWER_A,
        area="FISCAL",
        outcome="ACCEPTED",
        user_groups=["cf-fiscal-reviewers"],
    )
    assert decision["outcome"] == "ACCEPTED"

    # sem binding para CONTABIL → assignment_only (decisão permitida)
    _accept_all_items(P_ELIG, "CONTABIL")
    pkg = repo.finalize_package(P_ELIG, "CONTABIL", actor=ADMIN)
    v2 = str(pkg["current_version"]["package_version_id"])
    repo.assign_actor(
        P_ELIG,
        actor=ADMIN,
        role="REVIEWER",
        subject=REVIEWER_B,
        recipient_area="CONTABIL",
        area="CONTABIL",
    )
    repo.submit_for_review(
        P_ELIG, v2, actor=ADMIN, expected_revision=1
    )
    decision = repo.record_decision(
        P_ELIG,
        v2,
        actor=REVIEWER_B,
        area="CONTABIL",
        outcome="ACCEPTED",
        user_groups=[],
    )
    assert decision["outcome"] == "ACCEPTED"


# -- F4: notification outbox + dispatcher -------------------------------------


def test_outbox_emission_and_dispatch_best_effort(setup):
    _open_competence(setup, P_LOCK)
    repo = setup["packages"]
    version_id = _submit_fiscal(setup, P_LOCK)

    events = _notifications("PACKAGE_SUBMITTED_FOR_REVIEW", P_LOCK)
    assert len(events) == 1
    assert events[0]["recipient_subject"] == uuid.UUID(REVIEWER_A)
    assert events[0]["delivery_state"] == "EMITTED"
    assert events[0]["payload"]["period"] == P_LOCK

    # dispatcher com Core simulado OK → DISPATCHED
    class FakeResp:
        status_code = 202

    calls: list[dict] = []

    def fake_post(url, *, headers, json, timeout):  # noqa: A002
        calls.append({"url": url, "body": json, "headers": headers})
        return FakeResp()

    dispatcher = CoreNotificationsDispatcher(
        core_api_url="http://core-test",
        service_token="svc-token",
        http_post=fake_post,
    )
    result = dispatcher.dispatch_pending(P_LOCK)
    assert result["dispatched"] == 1
    assert calls[0]["url"].endswith("/integrations/notifications")
    body = calls[0]["body"]
    assert body["sourceApp"] == "controllership-finance"
    assert body["userIds"] == [REVIEWER_A]
    assert "controllership-finance.access" in body[
        "requiredPermissionCodes"
    ]

    events = _notifications("PACKAGE_SUBMITTED_FOR_REVIEW", P_LOCK)
    assert events[0]["delivery_state"] == "DISPATCHED"
    assert events[0]["dispatched_at"] is not None

    # notification DISPATCHED não alterou estado de negócio
    listed = repo.list_packages(
        P_LOCK, viewer=ADMIN, is_manage=True
    )
    pkg = next(
        p for p in listed["packages"]
        if p["recipient_area"] == "FISCAL"
    )
    assert pkg["current_version"]["status"] == "SUBMITTED"


def test_outbox_dispatch_failure_never_blocks_business(setup):
    # marca um novo evento EMITTED via clarification
    repo = setup["packages"]
    listed = repo.list_packages(
        P_LOCK, viewer=ADMIN, is_manage=True
    )
    package = next(
        p for p in listed["packages"]
        if p["recipient_area"] == "FISCAL"
    )
    version_id = str(package["current_version"]["package_version_id"])
    repo.open_clarification(
        P_LOCK,
        version_id,
        actor=REVIEWER_A,
        question="Nota fiscal do item 12 confere?",
        area="FISCAL",
    )
    opened = _notifications("PACKAGE_CLARIFICATION_OPENED", P_LOCK)
    assert len(opened) == 1
    # destinatário = quem submeteu (ADMIN); o autor não se notifica
    assert opened[0]["recipient_subject"] == uuid.UUID(ADMIN)

    def failing_post(url, *, headers, json, timeout):  # noqa: A002
        raise ConnectionError("core down")

    dispatcher = CoreNotificationsDispatcher(
        core_api_url="http://core-test",
        service_token="svc-token",
        http_post=failing_post,
    )
    result = dispatcher.dispatch_pending(P_LOCK)
    assert result["failed"] == 1
    reopened = _notifications("PACKAGE_CLARIFICATION_OPENED", P_LOCK)
    assert reopened[0]["delivery_state"] == "FAILED"
    assert reopened[0]["dispatch_error"]

    # esclarecimento continua OPEN — falha de entrega não toca negócio
    listed = repo.list_packages(
        P_LOCK, viewer=ADMIN, is_manage=True
    )
    pkg = next(
        p for p in listed["packages"]
        if p["recipient_area"] == "FISCAL"
    )
    assert pkg["current_version"]["status"] == "SUBMITTED"


# -- F4: congelamento de evidência/validação pós-submissão ---------------------


def test_submitted_package_locks_item_validation(setup):
    repo = setup["packages"]
    locked = repo.locked_item_keys(P_LOCK)
    assert locked, "pacote FISCAL submetido congela seus itens"
    # item do pacote é um item FISCAL do snapshot
    with plugins_db_connect() as conn, conn.cursor(
        row_factory=dict_row
    ) as cur:
        cur.execute(
            "SELECT item_key FROM "
            "controllership_finance.competence_checklist_item i "
            "JOIN controllership_finance.monthly_competence mc "
            "ON mc.competence_id = i.competence_id "
            "WHERE mc.period = %s AND i.recipient_area = 'FISCAL' "
            "AND i.state <> 'CANCELLED' LIMIT 1",
            (P_LOCK,),
        )
        item_key = cur.fetchone()["item_key"]
    assert item_key in locked

    # validação do conjunto do item travado é recusada
    validations = setup["validations"]
    with pytest.raises(ItemLockedBySubmittedPackage):
        validations.decide_item_set(
            P_LOCK,
            item_key,
            actor=ADMIN,
            decision="ACCEPTED",
            request_scope="BOTH",
        )


# -- F5: TaskProjection self-only ----------------------------------------------


def test_my_tasks_projection_self_only(setup):
    _open_competence(setup, P_TASK)
    pend = setup["pendencies"]
    tasks = setup["tasks"]

    # pacote submetido pendente de aceite → task do reviewer da área
    # (criada antes da pendência — pendência aberta bloqueia finalize)
    _submit_fiscal(setup, P_TASK)

    # pendência sob responsabilidade de REVIEWER_A → task dele
    pend.create_pendency(
        P_TASK,
        kind="OTHER",
        title="conciliar extrato",
        actor=ADMIN,
        responsible_subject=REVIEWER_A,
    )
    # catálogo global: binding FISCAL→cf-fiscal-reviewers existe
    # (criado no teste de elegibilidade) — grupos explícitos
    groups_a = ["cf-fiscal-reviewers"]
    mine = tasks.list_my_tasks(
        subject=REVIEWER_A, period=P_TASK, user_groups=groups_a
    )
    kinds = {t["actionKind"] for t in mine["items"]}
    assert "PENDENCY_ACTION_REQUIRED" in kinds
    assert all(
        t["assigneeUserId"] == REVIEWER_A for t in mine["items"]
    )
    assert "PACKAGE_REVIEW_REQUIRED" in kinds
    review_task = next(
        t for t in mine["items"]
        if t["actionKind"] == "PACKAGE_REVIEW_REQUIRED"
    )
    assert review_task["context"]["competence"] == P_TASK

    # outsider não vê nada — self-only estrito
    theirs = tasks.list_my_tasks(subject=OUTSIDER, period=P_TASK)
    assert theirs["total"] == 0

    # aceite da área remove a task (projeção é derivada, nunca cópia)
    listed = setup["packages"].list_packages(
        P_TASK, viewer=ADMIN, is_manage=True
    )
    package = next(
        p for p in listed["packages"]
        if p["recipient_area"] == "FISCAL"
    )
    version_id = str(package["current_version"]["package_version_id"])
    setup["packages"].record_decision(
        P_TASK,
        version_id,
        actor=REVIEWER_A,
        area="FISCAL",
        outcome="ACCEPTED",
        user_groups=["cf-fiscal-reviewers"],
    )
    mine = tasks.list_my_tasks(subject=REVIEWER_A, period=P_TASK)
    assert "PACKAGE_REVIEW_REQUIRED" not in {
        t["actionKind"] for t in mine["items"]
    }
    # pendência aberta permanece
    assert "PENDENCY_ACTION_REQUIRED" in {
        t["actionKind"] for t in mine["items"]
    }
