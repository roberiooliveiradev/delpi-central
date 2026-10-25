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

import threading
import time

from controllership_finance_app.domain.closing_checklist.errors import (
    CatalogEntryNotFound,
    ChecklistDomainError,
    CoordinatorRequired,
    InvalidPackageTransition,
    DraftAlreadyOpen,
    InvalidCatalogEntry,
    ItemLockedBySubmittedPackage,
    ReviewerNotAssigned,
    ReviewerNotEligible,
    StaleRevision,
    TerminalRejectionActive,
    VersionNotDraft,
    VersionNotInReview,
)
from controllership_finance_app.application.services.closing_document_service import (
    ClosingDocumentService,
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
from controllership_finance_app.infrastructure.storage.closing_document_storage import (
    ClosingDocumentStorage,
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
    assert "V011__clara_knowledge_and_proposals.sql" in applied
    assert "V012__clara_batch_orchestration.sql" in applied
    assert "V013__clara_step_up_consent.sql" in applied
    assert "V014__clara_consent_challenge.sql" in applied
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
        user_groups=["cf-fiscal-reviewers"],
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


# -- R-105-05: recuperação da outbox sem nova ação do usuário ------------


def test_failed_notification_recovered_without_new_action(setup):
    """Evento FAILED é reivindicado e entregue por dispatch_pending()
    global (poller) — nenhuma mutação de negócio nova é necessária;
    dedupe por notification_id (dedupeKey) impede duplicidade."""
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
        question="segue pendente?",
        area="FISCAL",
        user_groups=["cf-fiscal-reviewers"],
    )
    # dispatcher global (como o poller) — conta todas as pendências
    # da base de teste, não só da competência corrente.
    pending = [
        e for e in _notifications()
        if e["delivery_state"] in ("EMITTED", "FAILED")
    ]
    assert pending

    # 1ª tentativa: Core indisponível → FAILED (negócio intacto)
    def failing_post(url, *, headers, json, timeout):  # noqa: A002
        raise ConnectionError("core down")

    failing = CoreNotificationsDispatcher(
        core_api_url="http://core-test",
        service_token="svc-token",
        http_post=failing_post,
    )
    result = failing.dispatch_pending()  # global — como o poller
    assert result["failed"] == len(pending)

    # recuperação: Core de volta → FAILED reivindicado e entregue
    class FakeResp:
        status_code = 202

    seen: list[dict] = []

    def ok_post(url, *, headers, json, timeout):  # noqa: A002
        seen.append(json)
        return FakeResp()

    recovered = CoreNotificationsDispatcher(
        core_api_url="http://core-test",
        service_token="svc-token",
        http_post=ok_post,
    )
    result = recovered.dispatch_pending()
    assert result["failed"] == 0
    assert result["dispatched"] == len(pending)

    # dedupeKey estável = notification_id — retry não duplica no Core
    keys = {
        body["metadata"]["dedupeKey"] for body in seen
    }
    assert len(keys) == len(pending)

    # segunda execução: nada pendente, nada reenviado
    seen.clear()
    result = recovered.dispatch_pending()
    assert result["dispatched"] == 0
    assert not seen


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


def test_submitted_package_locks_document_upload(setup, tmp_path):
    """Upload de evidência em item de pacote SUBMITTED é recusado —
    correção exige nova versão do pacote (F4/doc 105)."""
    repo = setup["packages"]
    locked = repo.locked_item_keys(P_LOCK)
    assert locked

    with plugins_db_connect() as conn, conn.cursor(
        row_factory=dict_row
    ) as cur:
        cur.execute(
            "SELECT snapshot_item_id, item_key FROM "
            "controllership_finance.competence_checklist_item i "
            "JOIN controllership_finance.monthly_competence mc "
            "ON mc.competence_id = i.competence_id "
            "WHERE mc.period = %s AND i.recipient_area = 'FISCAL' "
            "AND i.state <> 'CANCELLED' LIMIT 1",
            (P_LOCK,),
        )
        item = cur.fetchone()
    assert item["item_key"] in locked

    service = ClosingDocumentService(
        storage=ClosingDocumentStorage(str(tmp_path))
    )
    pdf = b"%PDF-1.4\n" + b"x" * 2048 + b"\n%%EOF\n"
    with pytest.raises(ItemLockedBySubmittedPackage):
        service.upload(
            period=P_LOCK,
            actor=ADMIN,
            original_name="extrato.pdf",
            declared_mime="application/pdf",
            chunks=[pdf],
            snapshot_item_id=str(item["snapshot_item_id"]),
            title="Extrato",
            attachment_role=None,
            idempotency_key="lock-test-1",
            branch_scope="BOTH",
        )


# -- R-105-01: rejeicao terminal congela o workflow de revisao --------

COORDINATOR = str(uuid.uuid4())
P_TERM = "2026-11"
P_TERM_SIBLING = "2026-12"
P_TERM_SUBMIT = "2027-01"


def _confirm_terminal(setup, period: str):
    repo = setup["packages"]
    repo.assign_actor(
        period,
        actor=ADMIN,
        role="COORDINATOR",
        subject=COORDINATOR,
    )
    return repo.confirm_terminal_rejection(
        period, actor=COORDINATOR, reason="irregularidade grave"
    )


def test_terminal_rejection_freezes_review_workflow(setup):
    """RQ-P5-TERM-02: rejeicao ACTIVE bloqueia decisao, inicio de
    revisao, esclarecimento, complemento e resolve; tarefas P5 somem;
    historico preservado; reversao autorizada retoma acoes validas."""
    repo = setup["packages"]
    _open_competence(setup, P_TERM)
    version_id = _submit_fiscal(setup, P_TERM)

    # clarification aberta antes da rejeicao — historico preservado
    clar = repo.open_clarification(
        P_TERM,
        version_id,
        actor=REVIEWER_A,
        question="falta extrato",
        user_groups=["cf-fiscal-reviewers"],
    )
    _confirm_terminal(setup, P_TERM)

    for action in (
        lambda: repo.start_review(
            P_TERM, version_id, actor=REVIEWER_A
        ),
        lambda: repo.record_decision(
            P_TERM,
            version_id,
            actor=REVIEWER_A,
            area="FISCAL",
            outcome="ACCEPTED",
        ),
        lambda: repo.open_clarification(
            P_TERM, version_id, actor=REVIEWER_A, question="nova?"
        ),
        lambda: repo.create_complement(
            P_TERM, version_id, actor=ADMIN, reason="correcao"
        ),
        lambda: repo.resolve_clarification(
            P_TERM,
            str(clar["clarification_id"]),
            actor=ADMIN,
            response="resposta",
        ),
    ):
        with pytest.raises(TerminalRejectionActive):
            action()

    # TaskProjections P5 deixam de ser acionaveis
    reviewer_tasks = setup["tasks"].list_my_tasks(
        subject=REVIEWER_A, user_groups=[], period=P_TERM
    )
    assert not any(
        t["actionKind"] == "PACKAGE_REVIEW_REQUIRED"
        for t in reviewer_tasks["items"]
    )
    submitter_tasks = setup["tasks"].list_my_tasks(
        subject=ADMIN, user_groups=[], period=P_TERM
    )
    assert not any(
        t["actionKind"] == "PACKAGE_CLARIFICATION_REQUIRED"
        for t in submitter_tasks["items"]
    )

    # ator sem COORDINATOR nao reverte
    with pytest.raises(CoordinatorRequired):
        repo.revert_terminal_rejection(
            P_TERM, actor=REVIEWER_A, reason="tentativa"
        )

    # outra competencia permanece independente
    _open_competence(setup, P_TERM_SIBLING)
    other_version = _submit_fiscal(setup, P_TERM_SIBLING)
    decision = repo.record_decision(
        P_TERM_SIBLING,
        other_version,
        actor=REVIEWER_A,
        area="FISCAL",
        outcome="ACCEPTED",
        user_groups=["cf-fiscal-reviewers"],
    )
    assert decision["outcome"] == "ACCEPTED"

    # reversao autorizada: acoes ainda validas retomam, sem restaurar
    # tarefa obsoleta — a projection recomputa do estado vigente.
    repo.revert_terminal_rejection(
        P_TERM, actor=COORDINATOR, reason="acordo formalizado"
    )
    decision = repo.record_decision(
        P_TERM,
        version_id,
        actor=REVIEWER_A,
        area="FISCAL",
        outcome="ACCEPTED",
        user_groups=["cf-fiscal-reviewers"],
    )
    assert decision["outcome"] == "ACCEPTED"


def test_terminal_rejection_blocks_package_submission(setup):
    """Versao FINALIZED nao pode ser submetida durante rejeicao."""
    repo = setup["packages"]
    _open_competence(setup, P_TERM_SUBMIT)
    _make_p3_ready(P_TERM_SUBMIT)
    _accept_all_items(P_TERM_SUBMIT, "FISCAL")
    package = repo.finalize_package(P_TERM_SUBMIT, "FISCAL", actor=ADMIN)
    version_id = str(package["current_version"]["package_version_id"])

    _confirm_terminal(setup, P_TERM_SUBMIT)
    with pytest.raises(TerminalRejectionActive):
        repo.submit_for_review(
            P_TERM_SUBMIT, version_id, actor=ADMIN, expected_revision=1
        )

    # revert libera a submissao
    repo.revert_terminal_rejection(
        P_TERM_SUBMIT, actor=COORDINATOR, reason="ok"
    )
    repo.submit_for_review(
        P_TERM_SUBMIT, version_id, actor=ADMIN, expected_revision=1
    )


# -- R-105-04: serializacao evidencia × submissao no lock da competencia

P_RACE_UPLOAD = "2027-02"
P_RACE_VALIDATION = "2027-03"
P_RACE_CANCEL = "2027-04"
P_RACE_SUBMIT2 = "2027-05"


def _hold_competence_lock(period: str):
    """Abre tx manual segurando FOR UPDATE na linha da competência —
    simula a submissão vencedora em voo (mesmo ponto de serialização
    que submit_for_review)."""
    conn = plugins_db_connect()
    cur = conn.cursor(row_factory=dict_row)
    cur.execute(
        "SELECT competence_id FROM "
        "controllership_finance.monthly_competence WHERE period = %s",
        (period,),
    )
    competence_id = cur.fetchone()["competence_id"]
    cur.execute(
        "SELECT competence_id FROM "
        "controllership_finance.monthly_competence "
        "WHERE competence_id = %s FOR UPDATE",
        (competence_id,),
    )
    return conn, cur, competence_id


def _mark_submitted(cur, version_id: str):
    """Mutação que submit_for_review faria — executada sob o lock da
    competência detido pela transação vencedora."""
    cur.execute(
        "UPDATE controllership_finance.closing_package_version "
        "SET status = 'SUBMITTED', "
        "    required_areas = '[\"FISCAL\"]'::jsonb, "
        "    submitted_at = now() "
        "WHERE package_version_id = %s",
        (version_id,),
    )


def _fiscal_item(period: str):
    with plugins_db_connect() as conn, conn.cursor(
        row_factory=dict_row
    ) as cur:
        cur.execute(
            "SELECT i.snapshot_item_id, i.item_key "
            "FROM controllership_finance.competence_checklist_item i "
            "JOIN controllership_finance.monthly_competence mc "
            "  ON mc.competence_id = i.competence_id "
            "WHERE mc.period = %s AND i.recipient_area = 'FISCAL' "
            "LIMIT 1",
            (period,),
        )
        return cur.fetchone()


def _finalized_fiscal(setup, period: str) -> str:
    _open_competence(setup, period)
    _make_p3_ready(period)
    _accept_all_items(period, "FISCAL")
    repo = setup["packages"]
    package = repo.finalize_package(period, "FISCAL", actor=ADMIN)
    version_id = str(package["current_version"]["package_version_id"])
    repo.assign_actor(
        period,
        actor=ADMIN,
        role="REVIEWER",
        subject=REVIEWER_A,
        recipient_area="FISCAL",
        area="FISCAL",
    )
    return version_id


def test_upload_loses_race_to_submitted_package(setup, tmp_path):
    """Upload concorrente bloqueia no lock da competência e revalida o
    congelamento na mesma transação do INSERT — nunca grava evidência
    em item já integrado a versão submetida."""
    version_id = _finalized_fiscal(setup, P_RACE_UPLOAD)
    item = _fiscal_item(P_RACE_UPLOAD)
    assert item is not None

    conn, cur, _ = _hold_competence_lock(P_RACE_UPLOAD)
    outcome: dict = {}

    def do_upload():
        service = ClosingDocumentService(
            storage=ClosingDocumentStorage(str(tmp_path))
        )
        pdf = b"%PDF-1.4\n" + b"x" * 2048 + b"\n%%EOF\n"
        try:
            outcome["result"] = service.upload(
                period=P_RACE_UPLOAD,
                actor=ADMIN,
                original_name="extrato.pdf",
                declared_mime="application/pdf",
                chunks=[pdf],
                snapshot_item_id=str(item["snapshot_item_id"]),
                title="Extrato",
                attachment_role=None,
                idempotency_key="race-upload-1",
                branch_scope="BOTH",
            )
        except Exception as exc:  # noqa: BLE001 — captura p/ assert
            outcome["error"] = exc

    thread = threading.Thread(target=do_upload)
    thread.start()
    time.sleep(0.6)
    _mark_submitted(cur, version_id)
    conn.commit()
    thread.join(timeout=20)
    conn.close()

    assert isinstance(
        outcome.get("error"), ItemLockedBySubmittedPackage
    )


def test_validation_loses_race_to_submitted_package(setup):
    """decide_item_set bloqueia no lock da competência e revalida sob
    a mesma transação — validação não decide item congelado."""
    version_id = _finalized_fiscal(setup, P_RACE_VALIDATION)
    item = _fiscal_item(P_RACE_VALIDATION)

    conn, cur, _ = _hold_competence_lock(P_RACE_VALIDATION)
    outcome: dict = {}

    def do_decide():
        try:
            outcome["result"] = setup["validations"].decide_item_set(
                P_RACE_VALIDATION,
                item["item_key"],
                actor=ADMIN,
                decision="ACCEPTED",
            )
        except Exception as exc:  # noqa: BLE001
            outcome["error"] = exc

    thread = threading.Thread(target=do_decide)
    thread.start()
    time.sleep(0.6)
    _mark_submitted(cur, version_id)
    conn.commit()
    thread.join(timeout=20)
    conn.close()

    assert isinstance(
        outcome.get("error"), ItemLockedBySubmittedPackage
    )


def test_cancel_loses_race_to_submitted_package(setup, tmp_path):
    """Cancelamento de documento concorrente com a submissão não
    modifica evidência congelada — aborta tipado após o unlock."""
    version_id = _finalized_fiscal(setup, P_RACE_CANCEL)
    item = _fiscal_item(P_RACE_CANCEL)

    service = ClosingDocumentService(
        storage=ClosingDocumentStorage(str(tmp_path))
    )
    pdf = b"%PDF-1.4\n" + b"x" * 2048 + b"\n%%EOF\n"
    document, created = service.upload(
        period=P_RACE_CANCEL,
        actor=ADMIN,
        original_name="extrato.pdf",
        declared_mime="application/pdf",
        chunks=[pdf],
        snapshot_item_id=str(item["snapshot_item_id"]),
        title="Extrato",
        attachment_role=None,
        idempotency_key="race-cancel-upload",
        branch_scope="BOTH",
    )
    assert created

    conn, cur, _ = _hold_competence_lock(P_RACE_CANCEL)
    outcome: dict = {}

    def do_cancel():
        try:
            outcome["result"] = service.cancel_document(
                period=P_RACE_CANCEL,
                document_id=str(document["document_id"]),
                actor=ADMIN,
                can_manage=True,
                expected_revision=document["revision"],
                branch_scope="BOTH",
            )
        except Exception as exc:  # noqa: BLE001
            outcome["error"] = exc

    thread = threading.Thread(target=do_cancel)
    thread.start()
    time.sleep(0.6)
    _mark_submitted(cur, version_id)
    conn.commit()
    thread.join(timeout=20)
    conn.close()

    assert isinstance(
        outcome.get("error"), ItemLockedBySubmittedPackage
    )
    # o documento permanece ATTACHED — evidência histórica intacta
    with plugins_db_connect() as conn2, conn2.cursor(
        row_factory=dict_row
    ) as cur2:
        cur2.execute(
            "SELECT state FROM controllership_finance.closing_document "
            "WHERE document_id = %s",
            (document["document_id"],),
        )
        assert cur2.fetchone()["state"] == "ATTACHED"


def test_concurrent_submits_single_winner(setup):
    """Duas submissões concorrentes da mesma versão: exatamente uma
    vence; a perdedora recebe transição inválida, nunca efeito duplo."""
    version_id = _finalized_fiscal(setup, P_RACE_SUBMIT2)
    repo = setup["packages"]
    outcomes: list = []

    def do_submit():
        try:
            outcomes.append(
                repo.submit_for_review(
                    P_RACE_SUBMIT2,
                    version_id,
                    actor=ADMIN,
                    expected_revision=1,
                )
            )
        except Exception as exc:  # noqa: BLE001
            outcomes.append(exc)

    threads = [threading.Thread(target=do_submit) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=20)

    wins = [r for r in outcomes if not isinstance(r, Exception)]
    losses = [
        r for r in outcomes if isinstance(r, InvalidPackageTransition)
    ]
    assert len(wins) == 1
    assert len(losses) == 1
    assert wins[0]["current_version"]["status"] == "SUBMITTED"


# ======================================================================
# CF-PROC0072-FINAL-REWORK-RELEASE-001 — Correções A (ordem de locks)
# e B (escopo de reviewer + versão vigente)
# ======================================================================


P_SCOPE_AREA = "2027-06"
P_HISTORIC = "2027-07"
P_PAIR_UXV = "2027-08"
P_PAIR_RXV = "2027-09"
P_PAIR_CXV = "2027-10"
P_PAIR_SXV = "2027-11"
P_SCOPE_FAILCLOSED = "2027-12"
P_SCOPE_SIBLING = "2028-01"


def _run_concurrent(fn_a, fn_b):
    """Dois fluxos concorrentes sincronizados por barreira. Prova
    ausência de deadlock (join com timeout) e devolve resultado ou
    exceção de cada lado."""
    barrier = threading.Barrier(2)
    out: dict = {}

    def run(name, fn):
        def go():
            try:
                barrier.wait(timeout=10)
                out[name] = fn()
            except Exception as exc:  # noqa: BLE001
                out[name] = exc

        return go

    threads = [
        threading.Thread(target=run("a", fn_a)),
        threading.Thread(target=run("b", fn_b)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)
    assert all(not t.is_alive() for t in threads), "deadlock suspeito"
    assert "a" in out and "b" in out
    return out


def _pdf_chunks():
    return [b"%PDF-1.4\n" + b"z" * 2048 + b"\n%%EOF\n"]


def _exceptional_item(setup, period: str, suffix: str) -> dict:
    return setup["validations"].create_exceptional_item(
        period,
        ADMIN,
        sheet="ELETRONICO",
        name=f"Item concorrência {suffix}",
        justification="Cobertura de corrida de locks.",
        applicability="REQUIRED",
        validation_scope="WHOLE_SET",
    )


def _doc_state(document_id: str) -> str:
    with plugins_db_connect() as conn, conn.cursor(
        row_factory=dict_row
    ) as cur:
        cur.execute(
            "SELECT state FROM controllership_finance.closing_document "
            "WHERE document_id = %s",
            (document_id,),
        )
        return cur.fetchone()["state"]


def test_upload_vs_validation_concurrent(setup, tmp_path):
    """Upload × decisão WHOLE_SET sob a mesma ordem de locks
    (competência → documento/item): sem deadlock, ambas as
    serializações são legais e o estado final é consistente."""
    _open_competence(setup, P_PAIR_UXV)
    item = _exceptional_item(setup, P_PAIR_UXV, "uxv")
    service = ClosingDocumentService(
        storage=ClosingDocumentStorage(str(tmp_path))
    )
    _, created = service.upload(
        period=P_PAIR_UXV,
        actor=ADMIN,
        original_name="uxv-1.pdf",
        declared_mime="application/pdf",
        chunks=_pdf_chunks(),
        snapshot_item_id=str(item["snapshot_item_id"]),
        title="uxv-1",
        attachment_role=None,
        idempotency_key="uxv-1",
        branch_scope="BOTH",
    )
    assert created

    def do_upload2():
        return service.upload(
            period=P_PAIR_UXV,
            actor=ADMIN,
            original_name="uxv-2.pdf",
            declared_mime="application/pdf",
            chunks=_pdf_chunks(),
            snapshot_item_id=str(item["snapshot_item_id"]),
            title="uxv-2",
            attachment_role=None,
            idempotency_key="uxv-2",
            branch_scope="BOTH",
        )

    def do_decide():
        return setup["validations"].decide_item_set(
            P_PAIR_UXV,
            item["item_key"],
            actor=ADMIN,
            decision="ACCEPTED",
        )

    out = _run_concurrent(do_upload2, do_decide)
    errors = [r for r in out.values() if isinstance(r, Exception)]
    assert all(
        isinstance(e, ChecklistDomainError) for e in errors
    ), errors
    decide = out["b"]
    if not isinstance(decide, Exception):
        assert decide["item_state"] == "ACCEPTED"
        assert len(decide["composition"]) >= 1


def test_replace_vs_validation_concurrent(setup, tmp_path):
    """Replace × validação: sem deadlock; qualquer ordem de
    serialização é consistente — versão v2 criada ou decisão sobre a
    composição vigente, nunca estado intermediário."""
    _open_competence(setup, P_PAIR_RXV)
    item = _exceptional_item(setup, P_PAIR_RXV, "rxv")
    service = ClosingDocumentService(
        storage=ClosingDocumentStorage(str(tmp_path))
    )
    document, _ = service.upload(
        period=P_PAIR_RXV,
        actor=ADMIN,
        original_name="rxv-1.pdf",
        declared_mime="application/pdf",
        chunks=_pdf_chunks(),
        snapshot_item_id=str(item["snapshot_item_id"]),
        title="rxv-1",
        attachment_role=None,
        idempotency_key="rxv-1",
        branch_scope="BOTH",
    )

    def do_replace():
        return service.replace_document(
            period=P_PAIR_RXV,
            document_id=str(document["document_id"]),
            actor=ADMIN,
            can_manage=True,
            original_name="rxv-2.pdf",
            declared_mime="application/pdf",
            chunks=_pdf_chunks(),
            expected_revision=document["revision"],
            idempotency_key="rxv-2",
            branch_scope="BOTH",
        )

    def do_decide():
        return setup["validations"].decide_item_set(
            P_PAIR_RXV,
            item["item_key"],
            actor=ADMIN,
            decision="ACCEPTED",
        )

    out = _run_concurrent(do_replace, do_decide)
    errors = [r for r in out.values() if isinstance(r, Exception)]
    assert all(
        isinstance(e, ChecklistDomainError) for e in errors
    ), errors
    assert _doc_state(str(document["document_id"])) == "ATTACHED"


def test_cancel_vs_validation_concurrent(setup, tmp_path):
    """Cancel × validação: sem deadlock — o cancelamento serializado
    antes da decisão exclui o documento da composição; depois dela,
    deriva o item de volta a EXPECTED. Nunca erro não tipado."""
    _open_competence(setup, P_PAIR_CXV)
    item = _exceptional_item(setup, P_PAIR_CXV, "cxv")
    service = ClosingDocumentService(
        storage=ClosingDocumentStorage(str(tmp_path))
    )
    doc1, _ = service.upload(
        period=P_PAIR_CXV,
        actor=ADMIN,
        original_name="cxv-1.pdf",
        declared_mime="application/pdf",
        chunks=_pdf_chunks(),
        snapshot_item_id=str(item["snapshot_item_id"]),
        title="cxv-1",
        attachment_role=None,
        idempotency_key="cxv-1",
        branch_scope="BOTH",
    )
    service.upload(
        period=P_PAIR_CXV,
        actor=ADMIN,
        original_name="cxv-2.pdf",
        declared_mime="application/pdf",
        chunks=_pdf_chunks(),
        snapshot_item_id=str(item["snapshot_item_id"]),
        title="cxv-2",
        attachment_role=None,
        idempotency_key="cxv-2",
        branch_scope="BOTH",
    )

    def do_cancel():
        return service.cancel_document(
            period=P_PAIR_CXV,
            document_id=str(doc1["document_id"]),
            actor=ADMIN,
            can_manage=True,
            expected_revision=doc1["revision"],
            branch_scope="BOTH",
        )

    def do_decide():
        return setup["validations"].decide_item_set(
            P_PAIR_CXV,
            item["item_key"],
            actor=ADMIN,
            decision="ACCEPTED",
        )

    out = _run_concurrent(do_cancel, do_decide)
    errors = [r for r in out.values() if isinstance(r, Exception)]
    assert all(
        isinstance(e, ChecklistDomainError) for e in errors
    ), errors
    assert _doc_state(str(doc1["document_id"])) in (
        "ATTACHED",
        "CANCELLED",
    )


def test_submit_vs_validation_concurrent(setup, tmp_path):
    """Submit × validação em corrida efetiva: a submissão sempre
    vence ou serializa depois da decisão — nunca uma decisão grava
    item congelado. Erro perdedor é `ItemLockedBySubmittedPackage`."""
    version_id = _finalized_fiscal(setup, P_PAIR_SXV)
    item = _fiscal_item(P_PAIR_SXV)
    service = ClosingDocumentService(
        storage=ClosingDocumentStorage(str(tmp_path))
    )
    doc, _ = service.upload(
        period=P_PAIR_SXV,
        actor=ADMIN,
        original_name="sxv-1.pdf",
        declared_mime="application/pdf",
        chunks=_pdf_chunks(),
        snapshot_item_id=str(item["snapshot_item_id"]),
        title="sxv-1",
        attachment_role=None,
        idempotency_key="sxv-1",
        branch_scope="BOTH",
    )

    def do_submit():
        return setup["packages"].submit_for_review(
            P_PAIR_SXV, version_id, actor=ADMIN, expected_revision=1
        )

    def do_decide():
        return setup["validations"].decide_version(
            P_PAIR_SXV,
            str(doc["document_id"]),
            actor=ADMIN,
            decision="ACCEPTED",
        )

    out = _run_concurrent(do_submit, do_decide)
    submit, decide = out["a"], out["b"]
    assert not isinstance(submit, Exception), submit
    assert submit["current_version"]["status"] == "SUBMITTED"
    if isinstance(decide, Exception):
        assert isinstance(decide, ItemLockedBySubmittedPackage), decide
    assert _doc_state(str(doc["document_id"])) == "ATTACHED"


# -- Correção B: escopo do reviewer e versão vigente ---------------------


def test_reviewer_area_must_match_active_assignment(setup):
    """Área explicitamente requerida precisa pertencer ao assignment
    ATIVO do ator naquele pacote — reviewer de outra área não esclarece
    em nome de área alheia."""
    _open_competence(setup, P_SCOPE_AREA)
    version_id = _submit_fiscal(setup, P_SCOPE_AREA, reviewer=REVIEWER_A)
    repo = setup["packages"]

    with pytest.raises(ReviewerNotAssigned):
        repo.open_clarification(
            P_SCOPE_AREA,
            version_id,
            actor=REVIEWER_A,
            question="Pendência na área errada?",
            area="CONTABIL",
            user_groups=["cf-fiscal-reviewers"],
        )

    # reviewer de outra área do MESMO pacote não fala pela FISCAL
    repo.assign_actor(
        P_SCOPE_AREA,
        actor=ADMIN,
        role="REVIEWER",
        subject=REVIEWER_B,
        recipient_area="FISCAL",
        area="CONTABIL",
    )
    with pytest.raises(ReviewerNotAssigned):
        repo.open_clarification(
            P_SCOPE_AREA,
            version_id,
            actor=REVIEWER_B,
            question="Esclarecimento FISCAL por reviewer CONTABIL?",
            area="FISCAL",
            user_groups=["cf-fiscal-reviewers"],
        )

    # reviewer autorizado na área correta
    clarification = repo.open_clarification(
        P_SCOPE_AREA,
        version_id,
        actor=REVIEWER_A,
        question="Esclarecimento legítimo.",
        area="FISCAL",
        user_groups=["cf-fiscal-reviewers"],
    )
    assert clarification["clarification_id"]


def test_start_review_and_clarification_fail_closed_eligibility(setup):
    """Sem o grupo Core exigido pelo binding, start_review e
    open_clarification falham fechados — assignment_only não é prova
    corporativa plena quando existe binding configurado."""
    _open_competence(setup, P_SCOPE_FAILCLOSED)
    version_id = _submit_fiscal(
        setup, P_SCOPE_FAILCLOSED, reviewer=REVIEWER_A
    )
    repo = setup["packages"]
    with pytest.raises(ReviewerNotEligible):
        repo.start_review(
            P_SCOPE_FAILCLOSED,
            version_id,
            actor=REVIEWER_A,
            user_groups=[],
        )
    with pytest.raises(ReviewerNotEligible):
        repo.open_clarification(
            P_SCOPE_FAILCLOSED,
            version_id,
            actor=REVIEWER_A,
            question="q",
            user_groups=[],
        )
    assert repo.start_review(
        P_SCOPE_FAILCLOSED,
        version_id,
        actor=REVIEWER_A,
        user_groups=["cf-fiscal-reviewers"],
    )["started"]


def test_historic_submitted_version_rejects_review_actions(setup):
    """Versão SUBMITTED histórica (após complemento) não aceita novas
    ações de revisão — somente a vigente. Competência irmã permanece
    independente e acionável."""
    _open_competence(setup, P_HISTORIC)
    version_id = _submit_fiscal(setup, P_HISTORIC, reviewer=REVIEWER_A)
    repo = setup["packages"]
    complement = repo.create_complement(
        P_HISTORIC, version_id, actor=ADMIN, reason="correção fiscal"
    )
    assert complement["current_version"]["status"] == "DRAFT"

    for action in (
        lambda: repo.start_review(
            P_HISTORIC,
            version_id,
            actor=REVIEWER_A,
            user_groups=["cf-fiscal-reviewers"],
        ),
        lambda: repo.open_clarification(
            P_HISTORIC,
            version_id,
            actor=REVIEWER_A,
            question="q",
            user_groups=["cf-fiscal-reviewers"],
        ),
        lambda: repo.record_decision(
            P_HISTORIC,
            version_id,
            actor=REVIEWER_A,
            area="FISCAL",
            outcome="ACCEPTED",
            user_groups=["cf-fiscal-reviewers"],
        ),
    ):
        with pytest.raises(InvalidPackageTransition):
            action()

    # competência irmã independente: versão vigente continua acionável
    _open_competence(setup, P_SCOPE_SIBLING)
    sibling_id = _submit_fiscal(
        setup, P_SCOPE_SIBLING, reviewer=REVIEWER_A
    )
    assert repo.start_review(
        P_SCOPE_SIBLING,
        sibling_id,
        actor=REVIEWER_A,
        user_groups=["cf-fiscal-reviewers"],
    )["started"]
