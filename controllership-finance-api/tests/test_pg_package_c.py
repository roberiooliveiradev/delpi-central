"""Pacote C — integração PostgreSQL real (banco efêmero com ownership).

Cobre P5 (packages/PackageVersion/review/C2), controles pendentes do
Pacote B (ownership P4, proveniência oficial P3) e a derivação da
conclusão mensal — sem conclusão por vacuidade (D-FINAL-02).

Fixtures diretas em `competence_checklist_item.state` e
`closing_document` isolam o pacote sob teste — o ciclo documental P2
já está PROVEN na suíte do Pacote A.
"""

from __future__ import annotations

import os
import uuid
from decimal import Decimal

import pytest
from psycopg.rows import dict_row

from controllership_finance_app.domain.closing_checklist.errors import (
    AreaDecisionTerminal,
    CoordinatorRequired,
    InvalidPackageTransition,
    OfficialDocumentRequired,
    PendencyOwnershipRequired,
    ReviewerNotAssigned,
    StaleRevision,
    TerminalRejectionActive,
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
from controllership_finance_app.infrastructure.persistence.closing_checklist_repository import (
    ClosingChecklistRepository,
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

PERIOD = "2026-03"
ADMIN = str(uuid.uuid4())
REVIEWER_A = str(uuid.uuid4())
REVIEWER_B = str(uuid.uuid4())
REVIEWER_LATE = str(uuid.uuid4())
COORDINATOR = str(uuid.uuid4())
OUTSIDER = str(uuid.uuid4())


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
    assert "V008__p5_packages_review.sql" in applied
    checklist = ClosingChecklistRepository()
    template_id = str(checklist.list_templates()[0]["template_id"])
    checklist.submit_version_for_review(
        template_id, 1, actor=ADMIN
    )
    checklist.publish_version(
        template_id, 1, effective_from_period="2026-01", actor=ADMIN
    )
    checklist.open_competence(PERIOD, actor=ADMIN)
    repo = ClosingPackageRepository()
    return {"repo": repo}


def _accept_all_items(area: str | None = None):
    """Fixture: marca itens como ACCEPTED — P2 acceptance já é PROVEN
    na suíte do Pacote A; aqui isolamos P5."""
    where = "competence_id = (SELECT competence_id FROM controllership_finance.monthly_competence WHERE period = %s) AND state = 'EXPECTED'"
    params: list = [PERIOD]
    if area is not None:
        where += " AND recipient_area = %s"
        params.append(area)
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            f"UPDATE controllership_finance.competence_checklist_item"
            f" SET state = 'ACCEPTED' WHERE {where}",
            params,
        )


def _make_p3_ready(declared: bool = True, official_doc: bool = False):
    p3 = ClosingP3Repository()
    with plugins_db_connect() as conn, conn.cursor(
        row_factory=dict_row
    ) as cur:
        competence_id = p3._competence_id(cur, PERIOD)
    doc_id = None
    if official_doc:
        doc_id = _insert_official_document(competence_id)
    for domain in RECONCILIATION_DOMAINS:
        p3.upsert_reconciliation(
            PERIOD,
            domain,
            actor=ADMIN,
            source_state="AVAILABLE",
            expected_amount=Decimal("1000.00"),
            reported_amount=Decimal("1000.00"),
            provenance={"source": "test"},
            provenance_kind="OFFICIAL" if official_doc else "DECLARED",
            official_document_id=doc_id,
        )
    p3.confirm_cutoff(PERIOD, actor=ADMIN)
    p3.revalidate(PERIOD, actor=ADMIN)


def _insert_official_document(competence_id: str) -> str:
    doc_id = str(uuid.uuid4())
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO controllership_finance.closing_document
                (document_id, competence_id, link_kind,
                 idempotency_key, request_hash, uploaded_by)
            VALUES (%s, %s, 'competence', %s, %s, %s)
            """,
            (
                doc_id,
                competence_id,
                f"official-{uuid.uuid4()}",
                "0" * 64,
                ADMIN,
            ),
        )
    return doc_id


def _finalize(repo, area):
    return repo.finalize_package(PERIOD, area, actor=ADMIN)


def _latest_version_id(package_view):
    return str(package_view["current_version"]["package_version_id"])


# -- P4: controles de ownership (pendente Pacote B) -------------------------


def test_p4_claim_blocked_when_owned_by_other(setup):
    pend = ClosingPendencyRepository()
    created = pend.create_pendency(
        PERIOD,
        kind="OTHER",
        title="ownership check",
        actor=ADMIN,
    )
    pid = created["pendency_id"]
    pend.claim_pendency(
        PERIOD, pid, REVIEWER_A, expected_revision=1
    )
    # claim sobre pendência de terceiro = indevido
    with pytest.raises(PendencyOwnershipRequired):
        pend.claim_pendency(
            PERIOD, pid, OUTSIDER, expected_revision=2
        )
    # transição por não-owner e não-manage = bloqueada
    with pytest.raises(PendencyOwnershipRequired):
        pend.transition_pendency(
            PERIOD,
            pid,
            OUTSIDER,
            to_state="IN_ANALYSIS",
            expected_revision=2,
        )
    # owner transiciona
    row = pend.transition_pendency(
        PERIOD,
        pid,
        REVIEWER_A,
        to_state="IN_ANALYSIS",
        expected_revision=2,
    )
    assert row["state"] == "IN_ANALYSIS"
    # não-owner com manage transiciona (papel elegível)
    row = pend.transition_pendency(
        PERIOD,
        pid,
        ADMIN,
        to_state="WAITING_EXTERNAL",
        expected_revision=3,
        is_manage=True,
    )
    assert row["state"] == "WAITING_EXTERNAL"
    # manage resolve para liberar finalize
    pend.transition_pendency(
        PERIOD,
        pid,
        ADMIN,
        to_state="RESOLVED",
        expected_revision=4,
        is_manage=True,
    )


# -- P3: proveniência DECLARED vs OFFICIAL ----------------------------------


def test_p3_official_requires_attached_document(setup):
    p3 = ClosingP3Repository()
    with pytest.raises(OfficialDocumentRequired):
        p3.upsert_reconciliation(
            PERIOD,
            "ENTRADAS_SAIDAS",
            actor=ADMIN,
            source_state="AVAILABLE",
            expected_amount=Decimal("1.00"),
            reported_amount=Decimal("1.00"),
            provenance_kind="OFFICIAL",
        )
    with pytest.raises(OfficialDocumentRequired):
        p3.upsert_reconciliation(
            PERIOD,
            "ENTRADAS_SAIDAS",
            actor=ADMIN,
            source_state="AVAILABLE",
            expected_amount=Decimal("1.00"),
            reported_amount=Decimal("1.00"),
            provenance_kind="OFFICIAL",
            official_document_id=str(uuid.uuid4()),
        )


def test_p3_default_provenance_is_declared(setup):
    p3 = ClosingP3Repository()
    row = p3.upsert_reconciliation(
        PERIOD,
        "ENTRADAS_SAIDAS",
        actor=ADMIN,
        source_state="UNAVAILABLE",
        provenance={"note": "sem fonte"},
    )
    assert row["provenance_kind"] == "DECLARED"


# -- P5: visibilidade sibling -------------------------------------------------


def test_package_visibility_requires_assignment(setup):
    repo = setup["repo"]
    listed = repo.list_packages(
        PERIOD, viewer=ADMIN, is_manage=True
    )
    assert listed["applicable_areas"] == ["CONTABIL", "FISCAL"]
    # access sem assignment não vê pacote nenhum (sibling fail-closed)
    listed = repo.list_packages(
        PERIOD, viewer=REVIEWER_A, is_manage=False
    )
    assert listed["packages"] == []


def test_finalize_blocked_by_pending_checklist(setup):
    repo = setup["repo"]
    with pytest.raises(InvalidPackageTransition) as exc:
        _finalize(repo, "CONTABIL")
    assert "checklist_items_pending" in exc.value.message


# -- P5: lifecycle completo ----------------------------------------------------


@pytest.fixture(scope="module")
def submitted(setup):
    """Estado compartilhado: itens aceitos, P3 pronto (DECLARED),
    pacotes finalizados+submetidos, 2 reviewers em áreas distintas."""
    repo = setup["repo"]
    _accept_all_items()
    _make_p3_ready()
    repo.assign_actor(
        PERIOD,
        actor=ADMIN,
        role="REVIEWER",
        subject=REVIEWER_A,
        recipient_area="CONTABIL",
        area="CONTABIL",
    )
    repo.assign_actor(
        PERIOD,
        actor=ADMIN,
        role="REVIEWER",
        subject=REVIEWER_B,
        recipient_area="FISCAL",
        area="FISCAL",
    )
    pkg_c = _finalize(repo, "CONTABIL")
    pkg_f = _finalize(repo, "FISCAL")
    ver_c = _latest_version_id(pkg_c)
    ver_f = _latest_version_id(pkg_f)
    repo.submit_for_review(
        PERIOD, ver_c, actor=ADMIN, expected_revision=1
    )
    repo.submit_for_review(
        PERIOD, ver_f, actor=ADMIN, expected_revision=1
    )
    return {
        "repo": repo,
        "ver_c": ver_c,
        "ver_f": ver_f,
        "pkg_c": pkg_c["package_id"],
        "pkg_f": pkg_f["package_id"],
    }


def test_submit_creates_package_and_freezes_areas(submitted):
    repo = submitted["repo"]
    pkg = repo.get_package(
        PERIOD, submitted["pkg_c"], viewer=ADMIN, is_manage=True
    )
    assert pkg["state"] == "PACKAGE_SUBMITTED_FOR_REVIEW"
    assert pkg["current_version"]["status"] == "SUBMITTED"
    assert pkg["current_version"]["required_areas"] == ["CONTABIL"]
    assert pkg["review_state"] == "REVIEW_PENDING"


def test_submit_emits_notification_outbox(submitted):
    with plugins_db_connect() as conn, conn.cursor(
        row_factory=dict_row
    ) as cur:
        cur.execute(
            "SELECT recipient_subject, event_type, delivery_state"
            " FROM controllership_finance.closing_notification_event"
            " ORDER BY emitted_at"
        )
        rows = cur.fetchall()
    assert {str(r["recipient_subject"]) for r in rows} >= {
        REVIEWER_A,
        REVIEWER_B,
    }
    assert all(r["delivery_state"] == "EMITTED" for r in rows)


def test_reviewer_sees_only_assigned_package(submitted):
    repo = submitted["repo"]
    mine = repo.list_packages(
        PERIOD, viewer=REVIEWER_A, is_manage=False
    )["packages"]
    assert [p["recipient_area"] for p in mine] == ["CONTABIL"]
    other = repo.list_packages(
        PERIOD, viewer=REVIEWER_B, is_manage=False
    )["packages"]
    assert [p["recipient_area"] for p in other] == ["FISCAL"]


def test_decision_requires_assignment_and_area(submitted):
    repo = submitted["repo"]
    # ator sem assignment
    with pytest.raises(ReviewerNotAssigned):
        repo.record_decision(
            PERIOD,
            submitted["ver_c"],
            actor=OUTSIDER,
            area="CONTABIL",
            outcome="ACCEPTED",
        )
    # reviewer A não tem área FISCAL no pacote CONTABIL
    with pytest.raises(ReviewerNotAssigned):
        repo.record_decision(
            PERIOD,
            submitted["ver_c"],
            actor=REVIEWER_B,
            area="CONTABIL",
            outcome="ACCEPTED",
        )


def test_clarification_roundtrip_blocks_completion(submitted):
    repo = submitted["repo"]
    row = repo.open_clarification(
        PERIOD,
        submitted["ver_c"],
        actor=REVIEWER_A,
        question="Falta o anexo do extrato consolidado?",
        area="CONTABIL",
    )
    pkg = repo.get_package(
        PERIOD, submitted["pkg_c"], viewer=ADMIN, is_manage=True
    )
    assert pkg["review_state"] == "WAITING_FOR_CLARIFICATION"
    state = repo.derive_closing_state(PERIOD)
    assert "open_clarification:CONTABIL" in state["blocking_reasons"]
    repo.resolve_clarification(
        PERIOD,
        str(row["clarification_id"]),
        actor=ADMIN,
        response="Extrato anexado na versão vigente.",
    )
    pkg = repo.get_package(
        PERIOD, submitted["pkg_c"], viewer=ADMIN, is_manage=True
    )
    assert pkg["open_clarifications"] == 0


def test_area_decisions_and_completion_declared_blocker(submitted):
    repo = submitted["repo"]
    repo.record_decision(
        PERIOD,
        submitted["ver_c"],
        actor=REVIEWER_A,
        area="CONTABIL",
        outcome="ACCEPTED",
    )
    repo.record_decision(
        PERIOD,
        submitted["ver_f"],
        actor=REVIEWER_B,
        area="FISCAL",
        outcome="ACCEPTED",
    )
    pkg = repo.get_package(
        PERIOD, submitted["pkg_c"], viewer=ADMIN, is_manage=True
    )
    assert pkg["review_state"] == "REVIEW_ACCEPTED"
    # aceite por área é terminal — irreversível por UI e API (P5-B/G)
    with pytest.raises(AreaDecisionTerminal):
        repo.record_decision(
            PERIOD,
            submitted["ver_c"],
            actor=REVIEWER_A,
            area="CONTABIL",
            outcome="REJECTED",
            note="tentativa tardia",
        )
    # C2 satisfeito, mas P3 ainda DECLARED → PENDING (controle B/C:
    # conciliação registrada != resultado oficial comprovado)
    state = repo.derive_closing_state(PERIOD)
    assert state["state"] == "PENDING"
    assert any(
        r.startswith("p3_declared_only:")
        for r in state["blocking_reasons"]
    )


def test_official_provenance_unblocks_completion(submitted):
    repo = submitted["repo"]
    p3 = ClosingP3Repository()
    with plugins_db_connect() as conn, conn.cursor(
        row_factory=dict_row
    ) as cur:
        competence_id = p3._competence_id(cur, PERIOD)
    doc = _insert_official_document(competence_id)
    for domain in RECONCILIATION_DOMAINS:
        current = p3.get_p3_state(PERIOD)["reconciliations"]
        row = next(r for r in current if r["domain"] == domain)
        p3.upsert_reconciliation(
            PERIOD,
            domain,
            actor=ADMIN,
            source_state="AVAILABLE",
            expected_amount=Decimal("1000.00"),
            reported_amount=Decimal("1000.00"),
            provenance={"source": "official"},
            provenance_kind="OFFICIAL",
            official_document_id=doc,
            expected_revision=row["revision"],
        )
    # upsert muda input_fingerprint → precisa nova revalidação vigente
    p3.revalidate(PERIOD, actor=ADMIN)
    state = repo.derive_closing_state(PERIOD)
    assert state["state"] == "MONTHLY_CLOSING_COMPLETED"
    assert state["blocking_reasons"] == []


def test_new_version_resets_area_acceptances(submitted):
    """P5-E: nova PackageVersion não herda aceites — C2 volta a pendente."""
    repo = submitted["repo"]
    repo.create_complement(
        PERIOD, submitted["ver_c"], actor=ADMIN, reason="ajuste fiscal"
    )
    pkg = repo.get_package(
        PERIOD, submitted["pkg_c"], viewer=ADMIN, is_manage=True
    )
    assert pkg["current_version"]["status"] == "DRAFT"
    assert pkg["current_version"]["version_no"] == 2
    state = repo.derive_closing_state(PERIOD)
    assert "package_not_submitted:CONTABIL" in state["blocking_reasons"]
    # V1 permanece histórica e imutável
    versions = pkg["versions"]
    v1 = next(v for v in versions if v["version_no"] == 1)
    assert v1["status"] == "SUBMITTED"
    assert v1["area_decisions"]["CONTABIL"]["outcome"] == "ACCEPTED"
    # submit exige revision correta (OCC); upsert P3 oficial mudou o
    # fingerprint → revalidação antes de finalizar.
    ClosingP3Repository().revalidate(PERIOD, actor=ADMIN)
    _accept_all_items()
    repo.finalize_package(PERIOD, "CONTABIL", actor=ADMIN)
    pkg = repo.get_package(
        PERIOD, submitted["pkg_c"], viewer=ADMIN, is_manage=True
    )
    ver2 = _latest_version_id(pkg)
    with pytest.raises(StaleRevision):
        repo.submit_for_review(
            PERIOD, ver2, actor=ADMIN, expected_revision=99
        )
    # draft revision=1 → finalize incrementa para 2
    repo.submit_for_review(
        PERIOD, ver2, actor=ADMIN, expected_revision=2
    )
    pkg = repo.get_package(
        PERIOD, submitted["pkg_c"], viewer=ADMIN, is_manage=True
    )
    # aceites da V1 não valem para V2
    assert pkg["review_state"] == "REVIEW_PENDING"
    state = repo.derive_closing_state(PERIOD)
    assert "area_not_reviewed:CONTABIL:CONTABIL" in state[
        "blocking_reasons"
    ]
    repo.record_decision(
        PERIOD, ver2, actor=REVIEWER_A, area="CONTABIL",
        outcome="ACCEPTED",
    )
    state = repo.derive_closing_state(PERIOD)
    assert state["state"] == "MONTHLY_CLOSING_COMPLETED"


def test_terminal_rejection_requires_coordinator(submitted):
    repo = submitted["repo"]
    with pytest.raises(CoordinatorRequired):
        repo.confirm_terminal_rejection(
            PERIOD, actor=REVIEWER_A, reason="inconsistência material"
        )
    repo.assign_actor(
        PERIOD,
        actor=ADMIN,
        role="COORDINATOR",
        subject=COORDINATOR,
    )
    repo.confirm_terminal_rejection(
        PERIOD, actor=COORDINATOR, reason="inconsistência material"
    )
    state = repo.derive_closing_state(PERIOD)
    assert state["state"] == "TERMINALLY_REJECTED"
    # finalize bloqueado sob rejeição terminal
    with pytest.raises(TerminalRejectionActive):
        _finalize(repo, "FISCAL")
    repo.revert_terminal_rejection(
        PERIOD, actor=COORDINATOR, reason="correção autorizada"
    )
    state = repo.derive_closing_state(PERIOD)
    assert state["state"] == "MONTHLY_CLOSING_COMPLETED"


def test_reopen_preserves_finalized_version(submitted):
    """RQ-P5-03: complemento→finalize→reopen cria working copy; versões
    anteriores permanecem históricas e imutáveis."""
    repo = submitted["repo"]
    repo.create_complement(
        PERIOD, submitted["ver_f"], actor=ADMIN, reason="correção"
    )
    ClosingP3Repository().revalidate(PERIOD, actor=ADMIN)
    repo.finalize_package(PERIOD, "FISCAL", actor=ADMIN)
    pkg = repo.get_package(
        PERIOD, submitted["pkg_f"], viewer=ADMIN, is_manage=True
    )
    ver2 = _latest_version_id(pkg)
    assert pkg["current_version"]["version_no"] == 2
    assert pkg["current_version"]["status"] == "FINALIZED"
    repo.reopen_version(
        PERIOD, ver2, actor=ADMIN, reason="novo ajuste"
    )
    pkg = repo.get_package(
        PERIOD, submitted["pkg_f"], viewer=ADMIN, is_manage=True
    )
    assert pkg["current_version"]["status"] == "DRAFT"
    assert pkg["current_version"]["version_no"] == 3
    statuses = [v["status"] for v in pkg["versions"]]
    assert statuses == ["DRAFT", "FINALIZED", "SUBMITTED"]
    # volta ao verde: draft→finalize→submit→aceite do reviewer B
    repo.finalize_package(PERIOD, "FISCAL", actor=ADMIN)
    pkg = repo.get_package(
        PERIOD, submitted["pkg_f"], viewer=ADMIN, is_manage=True
    )
    ver3 = _latest_version_id(pkg)
    repo.submit_for_review(
        PERIOD,
        ver3,
        actor=ADMIN,
        expected_revision=pkg["current_version"]["revision"],
    )
    repo.record_decision(
        PERIOD, ver3, actor=REVIEWER_B, area="FISCAL",
        outcome="ACCEPTED",
    )
    state = repo.derive_closing_state(PERIOD)
    assert state["state"] == "MONTHLY_CLOSING_COMPLETED"


def test_reassignment_preserves_prior_acceptance(submitted):
    """P5-F: substituto age só futuramente; decisões passadas preservam
    autoria; assignment desativado não autoriza nova decisão."""
    repo = submitted["repo"]
    # v4 da FISCAL: complemento → finalize → submit
    repo.create_complement(
        PERIOD,
        str(
            repo.get_package(
                PERIOD, submitted["pkg_f"], viewer=ADMIN, is_manage=True
            )["current_version"]["package_version_id"]
        ),
        actor=ADMIN,
        reason="rodada complementar",
    )
    ClosingP3Repository().revalidate(PERIOD, actor=ADMIN)
    repo.finalize_package(PERIOD, "FISCAL", actor=ADMIN)
    pkg = repo.get_package(
        PERIOD, submitted["pkg_f"], viewer=ADMIN, is_manage=True
    )
    ver4 = _latest_version_id(pkg)
    assert pkg["current_version"]["version_no"] == 4
    repo.submit_for_review(
        PERIOD,
        ver4,
        actor=ADMIN,
        expected_revision=pkg["current_version"]["revision"],
    )
    # decisão passada na V3 preserva autoria original
    v3 = next(v for v in pkg["versions"] if v["version_no"] == 3)
    assert v3["area_decisions"]["FISCAL"]["actor_subject"] == uuid.UUID(
        REVIEWER_B
    )
    # desativa REVIEWER_B — sem vínculo na V4, não decide
    assignment = next(
        a for a in pkg["assignments"] if str(a["subject"]) == REVIEWER_B
    )
    repo.deactivate_assignment(
        PERIOD,
        str(assignment["assignment_id"]),
        actor=ADMIN,
        reason="substituição",
    )
    with pytest.raises(ReviewerNotAssigned):
        repo.record_decision(
            PERIOD, ver4, actor=REVIEWER_B, area="FISCAL",
            outcome="ACCEPTED",
        )
    # substituto recebe a área e age futuramente (nova versão exige
    # novos aceites — aceite da V3 não migra)
    repo.assign_actor(
        PERIOD,
        actor=ADMIN,
        role="REVIEWER",
        subject=OUTSIDER,
        recipient_area="FISCAL",
        area="FISCAL",
    )
    state = repo.derive_closing_state(PERIOD)
    assert "area_not_reviewed:FISCAL:FISCAL" in state[
        "blocking_reasons"
    ]
    repo.record_decision(
        PERIOD, ver4, actor=OUTSIDER, area="FISCAL",
        outcome="ACCEPTED",
    )
    state = repo.derive_closing_state(PERIOD)
    assert state["state"] == "MONTHLY_CLOSING_COMPLETED"


def test_no_vacuity_without_applicable_packages(setup):
    """D-FINAL-02/C2: zero pacotes aplicáveis nunca conclui — mesmo com
    reconciliações oficiais. Vacuidade não é conclusão."""
    repo = setup["repo"]
    period2 = "2026-04"
    ClosingChecklistRepository().open_competence(period2, actor=ADMIN)
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE controllership_finance.competence_checklist_item
               SET recipient_area = NULL
             WHERE competence_id = (
                 SELECT competence_id
                   FROM controllership_finance.monthly_competence
                  WHERE period = %s)
            """,
            (period2,),
        )
    state = repo.derive_closing_state(period2)
    assert state["state"] == "PENDING"
    assert "no_applicable_packages" in state["blocking_reasons"]
    # Mesmo com os 3 domínios oficiais, sem pacote aplicável: PENDING.
    p3 = ClosingP3Repository()
    with plugins_db_connect() as conn, conn.cursor(
        row_factory=dict_row
    ) as cur:
        competence_id = p3._competence_id(cur, period2)
    doc = _insert_official_document(competence_id)
    for domain in RECONCILIATION_DOMAINS:
        p3.upsert_reconciliation(
            period2,
            domain,
            actor=ADMIN,
            source_state="AVAILABLE",
            expected_amount=Decimal("1.00"),
            reported_amount=Decimal("1.00"),
            provenance={"source": "official"},
            provenance_kind="OFFICIAL",
            official_document_id=doc,
        )
    state = repo.derive_closing_state(period2)
    assert state["state"] == "PENDING"
    assert "no_applicable_packages" in state["blocking_reasons"]


def test_recipient_packages_progress_independently(setup):
    """Submeter CONTABIL não avança FISCAL — pacotes são independentes."""
    repo = setup["repo"]
    period3 = "2026-05"
    ClosingChecklistRepository().open_competence(period3, actor=ADMIN)
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE controllership_finance.competence_checklist_item
               SET state = 'ACCEPTED'
             WHERE competence_id = (
                 SELECT competence_id
                   FROM controllership_finance.monthly_competence
                  WHERE period = %s)
               AND state = 'EXPECTED'
            """,
            (period3,),
        )
    p3 = ClosingP3Repository()
    for domain in RECONCILIATION_DOMAINS:
        p3.upsert_reconciliation(
            period3,
            domain,
            actor=ADMIN,
            source_state="AVAILABLE",
            expected_amount=Decimal("1.00"),
            reported_amount=Decimal("1.00"),
            provenance={"source": "test"},
        )
    p3.confirm_cutoff(period3, actor=ADMIN)
    p3.revalidate(period3, actor=ADMIN)
    pkg_c = repo.finalize_package(period3, "CONTABIL", actor=ADMIN)
    ver_c = _latest_version_id(pkg_c)
    repo.submit_for_review(
        period3, ver_c, actor=ADMIN, expected_revision=1
    )
    listed = repo.list_packages(
        period3, viewer=ADMIN, is_manage=True
    )["packages"]
    by_area = {p["recipient_area"]: p for p in listed}
    assert (
        by_area["CONTABIL"]["state"] == "PACKAGE_SUBMITTED_FOR_REVIEW"
    )
    assert by_area["FISCAL"]["state"] == "PACKAGE_INCOMPLETE"
    assert by_area["FISCAL"]["current_version"] is None
    state = repo.derive_closing_state(period3)
    assert state["state"] == "PENDING"
    assert "package_not_submitted:FISCAL" in state[
        "blocking_reasons"
    ]


def test_notification_failure_does_not_affect_completion(setup):
    """Notificação é outbox informativa: falha de entrega nunca reverte
    submissão nem vira critério de conclusão (P5-I)."""
    repo = setup["repo"]
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE controllership_finance.closing_notification_event
               SET delivery_state = 'UNAVAILABLE'
            """
        )
    state = repo.derive_closing_state(PERIOD)
    assert state["state"] == "MONTHLY_CLOSING_COMPLETED"
    assert not any(
        r.startswith("notification") for r in state["blocking_reasons"]
    )


# -- C2: P3 pré-condições revalidadas na conclusão -----------------------


def test_c2_blocked_when_reconciliation_inputs_change(setup):
    """C2 revalida P3 vigente: input alterado após submissão/aceite
    derruba a conclusão (revalidação obsoleta + divergência).
    Decisões humanas e versões permanecem intactas — só o estado
    derivado muda."""
    repo = setup["repo"]
    p3 = ClosingP3Repository()
    state = repo.derive_closing_state(PERIOD)
    assert state["state"] == "MONTHLY_CLOSING_COMPLETED"
    recons = p3.get_p3_state(PERIOD)["reconciliations"]
    row = next(
        r for r in recons if r["domain"] == "ENTRADAS_SAIDAS"
    )
    p3.upsert_reconciliation(
        PERIOD,
        "ENTRADAS_SAIDAS",
        actor=ADMIN,
        source_state="AVAILABLE",
        expected_amount=Decimal("1000.00"),
        reported_amount=Decimal("2000.00"),
        provenance_kind="OFFICIAL",
        official_document_id=row["official_document_id"],
        expected_revision=row["revision"],
    )
    state = repo.derive_closing_state(PERIOD)
    assert state["state"] == "PENDING"
    assert "p3_revalidation_required" in state["blocking_reasons"]
    assert (
        "p3_divergence:ENTRADAS_SAIDAS" in state["blocking_reasons"]
    )
    # Decisões/versão histórica preservadas — blocker é derivado.
    listed = repo.list_packages(
        PERIOD, viewer=ADMIN, is_manage=True
    )["packages"]
    pkg = next(
        p for p in listed if p["recipient_area"] == "CONTABIL"
    )
    assert pkg["state"] == "PACKAGE_SUBMITTED_FOR_REVIEW"
    # Restaura input e revalida → conclusão volta.
    row2 = next(
        r
        for r in p3.get_p3_state(PERIOD)["reconciliations"]
        if r["domain"] == "ENTRADAS_SAIDAS"
    )
    p3.upsert_reconciliation(
        PERIOD,
        "ENTRADAS_SAIDAS",
        actor=ADMIN,
        source_state="AVAILABLE",
        expected_amount=Decimal("1000.00"),
        reported_amount=Decimal("1000.00"),
        provenance_kind="OFFICIAL",
        official_document_id=row2["official_document_id"],
        expected_revision=row2["revision"],
    )
    p3.revalidate(PERIOD, actor=ADMIN)
    state = repo.derive_closing_state(PERIOD)
    assert state["state"] == "MONTHLY_CLOSING_COMPLETED"


def test_c2_blocked_when_source_unavailable(setup):
    """Fonte indisponível após revisão bloqueia C2 — indisponível
    nunca equivale a zero nem a OK."""
    repo = setup["repo"]
    p3 = ClosingP3Repository()
    recons = p3.get_p3_state(PERIOD)["reconciliations"]
    row = next(r for r in recons if r["domain"] == "P7")
    p3.upsert_reconciliation(
        PERIOD,
        "P7",
        actor=ADMIN,
        source_state="UNAVAILABLE",
        expected_revision=row["revision"],
    )
    state = repo.derive_closing_state(PERIOD)
    assert state["state"] == "PENDING"
    assert "p3_source_unavailable:P7" in state["blocking_reasons"]
    # Restaura fonte + revalida → conclusão volta.
    with plugins_db_connect() as conn, conn.cursor(
        row_factory=dict_row
    ) as cur:
        competence_id = p3._competence_id(cur, PERIOD)
    doc = _insert_official_document(competence_id)
    row2 = next(
        r
        for r in p3.get_p3_state(PERIOD)["reconciliations"]
        if r["domain"] == "P7"
    )
    p3.upsert_reconciliation(
        PERIOD,
        "P7",
        actor=ADMIN,
        source_state="AVAILABLE",
        expected_amount=Decimal("1000.00"),
        reported_amount=Decimal("1000.00"),
        provenance_kind="OFFICIAL",
        official_document_id=doc,
        expected_revision=row2["revision"],
    )
    p3.revalidate(PERIOD, actor=ADMIN)
    state = repo.derive_closing_state(PERIOD)
    assert state["state"] == "MONTHLY_CLOSING_COMPLETED"


def test_stock_closed_does_not_mask_stale_inputs(setup):
    """STOCK_CLOSED canónico NÃO é conclusão mensal: se os inputs de
    conciliação mudam depois, C2 fica pendente mesmo com o estoque
    fechado — estado de estoque != conclusão mensal."""
    repo = setup["repo"]
    p3 = ClosingP3Repository()
    with plugins_db_connect() as conn, conn.cursor(
        row_factory=dict_row
    ) as cur:
        competence_id = p3._competence_id(cur, PERIOD)
        cur.execute(
            """
            INSERT INTO controllership_finance.closing_stock_state
                (competence_id, canonical_state, source, fetched_at)
            VALUES (%s, 'CLOSED', 'totvs_t03_sync', now())
            ON CONFLICT (competence_id)
            DO UPDATE SET canonical_state = 'CLOSED'
            """,
            (competence_id,),
        )
    # Inputs limpos + stock CLOSED → conclusão válida.
    state = repo.derive_closing_state(PERIOD)
    assert state["state"] == "MONTHLY_CLOSING_COMPLETED"
    # Input muda com estoque fechado → pendente (estoque != fechamento).
    row = next(
        r
        for r in p3.get_p3_state(PERIOD)["reconciliations"]
        if r["domain"] == "H02"
    )
    p3.upsert_reconciliation(
        PERIOD,
        "H02",
        actor=ADMIN,
        source_state="AVAILABLE",
        expected_amount=Decimal("9999.00"),
        reported_amount=Decimal("9999.00"),
        provenance_kind="OFFICIAL",
        official_document_id=row["official_document_id"],
        expected_revision=row["revision"],
    )
    assert p3.get_p3_state(PERIOD)["canonical_stock_state"] == "CLOSED"
    state = repo.derive_closing_state(PERIOD)
    assert state["state"] == "PENDING"
    assert "p3_revalidation_required" in state["blocking_reasons"]
    # Limpeza: stock row fora + restaura input + revalida.
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            DELETE FROM controllership_finance.closing_stock_state
             WHERE competence_id = %s
            """,
            (competence_id,),
        )
    row2 = next(
        r
        for r in p3.get_p3_state(PERIOD)["reconciliations"]
        if r["domain"] == "H02"
    )
    p3.upsert_reconciliation(
        PERIOD,
        "H02",
        actor=ADMIN,
        source_state="AVAILABLE",
        expected_amount=Decimal("1000.00"),
        reported_amount=Decimal("1000.00"),
        provenance_kind="OFFICIAL",
        official_document_id=row2["official_document_id"],
        expected_revision=row2["revision"],
    )
    p3.revalidate(PERIOD, actor=ADMIN)
    state = repo.derive_closing_state(PERIOD)
    assert state["state"] == "MONTHLY_CLOSING_COMPLETED"


# -- P5-H: required_areas por tipo de pacote, não por assignment ----------


def test_required_areas_from_package_type_not_assignments(setup):
    """P5-H: required_areas congela por tipo de pacote na submissão;
    reviewer assignment é vínculo operacional distinto. Sem reviewer
    a área obrigatória continua existindo → area_not_reviewed, nunca
    vacuidade. Revisor designado DEPOIS da submissão ainda consegue
    aceitar (vínculo avaliado na decisão, não na submissão)."""
    repo = setup["repo"]
    period3 = "2026-05"
    # FISCAL de period3 não tem versão nem reviewer assignment.
    pkg_f = repo.finalize_package(period3, "FISCAL", actor=ADMIN)
    ver_f = _latest_version_id(pkg_f)
    repo.submit_for_review(
        period3, ver_f, actor=ADMIN, expected_revision=1
    )
    listed = repo.list_packages(
        period3, viewer=ADMIN, is_manage=True
    )["packages"]
    pkg = next(
        p for p in listed if p["recipient_area"] == "FISCAL"
    )
    assert pkg["current_version"]["required_areas"] == ["FISCAL"]
    state = repo.derive_closing_state(period3)
    assert "area_not_reviewed:FISCAL:FISCAL" in state[
        "blocking_reasons"
    ]
    assert not any(
        r.startswith("no_required_areas")
        for r in state["blocking_reasons"]
    )
    # Reviewer designado após a submissão consegue aceitar a área.
    repo.assign_actor(
        period3,
        actor=ADMIN,
        role="REVIEWER",
        subject=REVIEWER_LATE,
        recipient_area="FISCAL",
        area="FISCAL",
    )
    repo.start_review(period3, ver_f, actor=REVIEWER_LATE)
    repo.record_decision(
        period3,
        ver_f,
        actor=REVIEWER_LATE,
        area="FISCAL",
        outcome="ACCEPTED",
    )
    state = repo.derive_closing_state(period3)
    assert "area_not_reviewed:FISCAL:FISCAL" not in state[
        "blocking_reasons"
    ]
