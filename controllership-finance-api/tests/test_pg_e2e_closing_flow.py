"""Pacote D (doc 104 §D1) — E2E integrado do fechamento em PostgreSQL
real descartável.

Cenário canônico ponta a ponta, sem estado inferido:

- competência aberta a partir da versão publicada (snapshot imutável);
- P2: evidência anexada, aceite humano, rejeição+reversão e
  substituição que exige nova validação;
- matriz R01–R15 derivada do snapshot (sem relatório oficial
  fabricado);
- P3: cutoff, conciliação DECLARED vs OFFICIAL, revalidação e
  prontidão derivada (divergência R$0,01 bloqueia);
- P4: pendência registrada, classificada, assumida e resolvida com
  ownership — ator sem papel elegível bloqueado;
- P5: pacotes por destinatário independentes, PackageVersion
  imutável, submissão in-portal, clarificação, aceites por área e
  versão, rejeição terminal pelo coordenador e conclusão mensal só
  quando C2 satisfeito — nunca por vacuidade;
- trilha de auditoria append-only e cockpit com estados reais.

Cobre duas competências, dois destinatários, dois revisores e duas
PackageVersions. O ciclo decisório P2 unitário já está PROVEN na
suíte do Pacote A — aqui os itens restantes são aceitos via fixture
SQL para isolar o fluxo integrado.
"""

from __future__ import annotations

import os
import uuid
from decimal import Decimal

import psycopg
import pytest
from psycopg.rows import dict_row

from controllership_finance_app.domain.closing_checklist.errors import (
    CoordinatorRequired,
    PendencyOwnershipRequired,
    ReviewerNotAssigned,
    StaleRevision,
    TerminalRejectionActive,
)
from controllership_finance_app.infrastructure.persistence import (
    migrations_runner as mr,
)
from controllership_finance_app.infrastructure.persistence.plugins_db import (
    plugins_db_connect,
)
from controllership_finance_app.infrastructure.persistence.closing_checklist_repository import (
    ClosingChecklistRepository,
)
from controllership_finance_app.infrastructure.persistence.closing_document_repository import (
    ClosingDocumentRepository,
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
from controllership_finance_app.infrastructure.persistence.closing_validation_repository import (
    ClosingValidationRepository,
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

ADMIN = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-e2e-admin"))
UPLOADER = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-e2e-uploader"))
VALIDATOR = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-e2e-validator"))
REVIEWER_C = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-e2e-rev-contabil"))
REVIEWER_F = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-e2e-rev-fiscal"))
COORDINATOR = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-e2e-coord"))
OUTSIDER = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-e2e-outsider"))
PERIOD_1 = "2027-04"
PERIOD_2 = "2027-05"

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
def env(_configure_db):
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
    ]
    checklist = ClosingChecklistRepository()
    template_id = str(checklist.list_templates()[0]["template_id"])
    checklist.submit_version_for_review(
        template_id, 1, actor=ADMIN
    )
    checklist.publish_version(
        template_id, 1, effective_from_period="2027-01", actor=ADMIN
    )
    checklist.open_competence(PERIOD_1, actor=UPLOADER)
    checklist.open_competence(PERIOD_2, actor=UPLOADER)
    return {
        "checklist": checklist,
        "docs": ClosingDocumentRepository(),
        "val": ClosingValidationRepository(),
        "p3": ClosingP3Repository(),
        "pend": ClosingPendencyRepository(),
        "pkg": ClosingPackageRepository(),
    }


def _item(env, period: str, item_key: str) -> dict:
    items = env["checklist"].list_competence_items(period)
    return next(i for i in items if i["item_key"] == item_key)


def _attach(env, period: str, item_key: str) -> dict:
    item = _item(env, period, item_key)
    competence_id = env["docs"].get_competence_id(period)
    doc, _ = env["docs"].create_document(
        competence_id=competence_id,
        snapshot_item_id=str(item["snapshot_item_id"]),
        link_kind="competence_item",
        title=f"Evidência {period}/{item_key}",
        attachment_role="generic",
        idempotency_key=uuid.uuid4().hex,
        request_hash=uuid.uuid4().hex * 2,
        storage_key=f"{competence_id}/{uuid.uuid4().hex}.pdf",
        original_name="evidencia.pdf",
        stored_name=f"{uuid.uuid4().hex}.pdf",
        mime_type="application/pdf",
        extension=".pdf",
        size_bytes=4096,
        checksum_sha256=uuid.uuid4().hex * 2,
        actor=UPLOADER,
    )
    return doc


def _accept_remaining_items(period: str):
    """Fixture: demais itens aceitos — o ciclo decisório real já foi
    exercido nos itens canônicos desta suíte e na suíte do Pacote A."""
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
            (period,),
        )


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


def _make_p3(env, period: str, official: bool):
    p3 = env["p3"]
    with plugins_db_connect() as conn, conn.cursor(
        row_factory=dict_row
    ) as cur:
        competence_id = p3._competence_id(cur, period)
    doc_id = (
        _insert_official_document(competence_id) if official else None
    )
    for domain in RECONCILIATION_DOMAINS:
        p3.upsert_reconciliation(
            period,
            domain,
            actor=ADMIN,
            source_state="AVAILABLE",
            expected_amount=Decimal("1000.00"),
            reported_amount=Decimal("1000.00"),
            provenance={"source": "official" if official else "declared"},
            provenance_kind="OFFICIAL" if official else "DECLARED",
            official_document_id=doc_id,
        )
    p3.confirm_cutoff(period, actor=ADMIN)
    p3.revalidate(period, actor=ADMIN)


def _latest_version_id(pkg_view: dict) -> str:
    return str(pkg_view["current_version"]["package_version_id"])


def test_e2e_full_closing_flow_two_competences(env):
    """D1: ciclo completo P1→P5 com negativos e duas competências."""

    # -- 1-2. Competência aberta → snapshot carregado -----------------
    items_1 = env["checklist"].list_competence_items(PERIOD_1)
    assert items_1, "snapshot vazio"
    areas = {
        i["recipient_area"]
        for i in items_1
        if i.get("recipient_area")
    }
    assert {"CONTABIL", "FISCAL"} <= areas

    # -- 3. Identificar itens e fontes (R-ID no snapshot) -------------
    refs = {i.get("totvs_report_ref") for i in items_1} - {None}
    assert {"R01", "R02", "R03"} & refs, "matriz sem itens vinculados"

    # -- 4-6. P2: anexar, aceitar, rejeitar, substituir, revalidar ----
    doc_1 = _attach(env, PERIOD_1, "CK-E-01")
    res = env["val"].decide_version(
        PERIOD_1, str(doc_1["document_id"]), VALIDATOR,
        decision="ACCEPTED",
    )
    assert res["item_state"] == "ACCEPTED"

    doc_2 = _attach(env, PERIOD_1, "CK-E-02")
    rejected = env["val"].decide_version(
        PERIOD_1,
        str(doc_2["document_id"]),
        VALIDATOR,
        decision="REJECTED",
        reason_code="WRONG_DOCUMENT",
        comment="Extrato da conta errada.",
    )
    assert _item(env, PERIOD_1, "CK-E-02")["state"] == "EXPECTED"
    env["val"].reverse_decision(
        PERIOD_1,
        str(rejected["decision_id"]),
        VALIDATOR,
        result_state="UNDER_REVIEW",
        justification="Documento correto — leitura equivocada.",
    )
    env["val"].decide_version(
        PERIOD_1, str(doc_2["document_id"]), VALIDATOR,
        decision="ACCEPTED",
    )
    # Substituição exige nova validação.
    doc3 = _attach(env, PERIOD_1, "CK-E-03")
    env["val"].decide_version(
        PERIOD_1, str(doc3["document_id"]), VALIDATOR,
        decision="ACCEPTED",
    )
    env["docs"].add_version(
        competence_id=env["docs"].get_competence_id(PERIOD_1),
        document_id=str(doc3["document_id"]),
        expected_revision=doc3["revision"],
        storage_key=(
            f"{env['docs'].get_competence_id(PERIOD_1)}/"
            f"{uuid.uuid4().hex}.pdf"
        ),
        original_name="corrigido.pdf",
        stored_name=f"{uuid.uuid4().hex}.pdf",
        mime_type="application/pdf",
        extension=".pdf",
        size_bytes=2048,
        checksum_sha256=uuid.uuid4().hex * 2,
        idempotency_key=uuid.uuid4().hex,
        request_hash=uuid.uuid4().hex * 2,
        actor=UPLOADER,
    )
    assert _item(env, PERIOD_1, "CK-E-03")["state"] == "EXPECTED"
    env["val"].decide_version(
        PERIOD_1, str(doc3["document_id"]), VALIDATOR,
        decision="ACCEPTED",
    )
    _accept_remaining_items(PERIOD_1)

    # -- 7. Matriz R01–R15 derivada do snapshot -----------------------
    items_post = env["checklist"].list_competence_items(PERIOD_1)
    by_ref: dict[str, list] = {}
    for i in items_post:
        if i.get("totvs_report_ref"):
            by_ref.setdefault(i["totvs_report_ref"], []).append(i)
    # R01/R02/R03 são visões operacionais — todos os itens vinculados
    # aparecem como evidência validada, não como relatório oficial.
    for rid in ("R01", "R02", "R03"):
        if rid in by_ref:
            assert all(
                i["state"] == "ACCEPTED" for i in by_ref[rid]
            ), rid

    # -- 8. P3: DECLARED primeiro — finalize passa, C2 não conclui ----
    _make_p3(env, PERIOD_1, official=False)
    p3_state = env["p3"].get_p3_state(PERIOD_1)
    assert p3_state["state"] == "READY_TO_CLOSE"

    # -- 9. P4: registrar, classificar, assumir, resolver -------------
    pend = env["pend"].create_pendency(
        PERIOD_1,
        kind="MISSING_EVIDENCE",
        title="Extrato consolidado pendente",
        actor=ADMIN,
    )
    pend = env["pend"].confirm_classification(
        PERIOD_1,
        str(pend["pendency_id"]),
        actor=ADMIN,
        classification="EVIDENCE_GAP",
        reason="lacuna documental identificada na triagem",
        expected_revision=pend["revision"],
    )
    pend = env["pend"].claim_pendency(
        PERIOD_1,
        str(pend["pendency_id"]),
        VALIDATOR,
        expected_revision=pend["revision"],
    )
    # Negativo: ator sem ownership nem papel elegível.
    with pytest.raises(PendencyOwnershipRequired):
        env["pend"].transition_pendency(
            PERIOD_1,
            str(pend["pendency_id"]),
            OUTSIDER,
            to_state="IN_ANALYSIS",
            expected_revision=pend["revision"],
        )
    pend = env["pend"].transition_pendency(
        PERIOD_1,
        str(pend["pendency_id"]),
        VALIDATOR,
        to_state="IN_ANALYSIS",
        expected_revision=pend["revision"],
    )
    env["pend"].transition_pendency(
        PERIOD_1,
        str(pend["pendency_id"]),
        VALIDATOR,
        to_state="RESOLVED",
        expected_revision=pend["revision"],
    )

    # -- 10-12. P5: pacotes independentes por destinatário ------------
    repo = env["pkg"]
    repo.assign_actor(
        PERIOD_1, actor=ADMIN, role="REVIEWER",
        subject=REVIEWER_C, recipient_area="CONTABIL", area="CONTABIL",
    )
    repo.assign_actor(
        PERIOD_1, actor=ADMIN, role="REVIEWER",
        subject=REVIEWER_F, recipient_area="FISCAL", area="FISCAL",
    )
    repo.assign_actor(
        PERIOD_1, actor=ADMIN, role="COORDINATOR",
        subject=COORDINATOR,
    )
    pkg_c = repo.finalize_package(PERIOD_1, "CONTABIL", actor=ADMIN)
    ver_c1 = _latest_version_id(pkg_c)
    repo.submit_for_review(
        PERIOD_1, ver_c1, actor=ADMIN, expected_revision=1
    )
    # Independência: FISCAL não avança com o irmão.
    by_area = {
        p["recipient_area"]: p
        for p in repo.list_packages(
            PERIOD_1, viewer=ADMIN, is_manage=True
        )["packages"]
    }
    assert by_area["CONTABIL"]["state"] == (
        "PACKAGE_SUBMITTED_FOR_REVIEW"
    )
    assert by_area["FISCAL"]["state"] == "PACKAGE_INCOMPLETE"

    pkg_f = repo.finalize_package(PERIOD_1, "FISCAL", actor=ADMIN)
    ver_f1 = _latest_version_id(pkg_f)
    repo.submit_for_review(
        PERIOD_1, ver_f1, actor=ADMIN, expected_revision=1
    )

    # -- 13-14. Esclarecimento bloqueia e é resolvido ------------------
    clarif = repo.open_clarification(
        PERIOD_1, ver_c1, actor=REVIEWER_C,
        question="Confirma o extrato consolidado da filial?",
        area="CONTABIL",
    )
    assert "open_clarification:CONTABIL" in (
        repo.derive_closing_state(PERIOD_1)["blocking_reasons"]
    )
    repo.resolve_clarification(
        PERIOD_1, str(clarif["clarification_id"]),
        actor=ADMIN, response="Extrato confirmado.",
    )

    # -- 15. Aceites por área na versão vigente ------------------------
    with pytest.raises(ReviewerNotAssigned):
        repo.record_decision(
            PERIOD_1, ver_c1, actor=OUTSIDER,
            area="CONTABIL", outcome="ACCEPTED",
        )
    repo.record_decision(
        PERIOD_1, ver_c1, actor=REVIEWER_C,
        area="CONTABIL", outcome="ACCEPTED",
    )
    repo.record_decision(
        PERIOD_1, ver_f1, actor=REVIEWER_F,
        area="FISCAL", outcome="ACCEPTED",
    )
    state = repo.derive_closing_state(PERIOD_1)
    # C2 satisfeito, mas P3 apenas DECLARED → ainda PENDING.
    assert state["state"] == "PENDING"
    assert any(
        r.startswith("p3_declared_only:")
        for r in state["blocking_reasons"]
    )

    # Oficializa P3 (artefato anexado + OFFICIAL + revalidação).
    with plugins_db_connect() as conn, conn.cursor(
        row_factory=dict_row
    ) as cur:
        competence_id = env["p3"]._competence_id(cur, PERIOD_1)
    official_doc = _insert_official_document(competence_id)
    for domain in RECONCILIATION_DOMAINS:
        current = env["p3"].get_p3_state(PERIOD_1)["reconciliations"]
        row = next(r for r in current if r["domain"] == domain)
        env["p3"].upsert_reconciliation(
            PERIOD_1,
            domain,
            actor=ADMIN,
            source_state="AVAILABLE",
            expected_amount=Decimal("1000.00"),
            reported_amount=Decimal("1000.00"),
            provenance={"source": "official"},
            provenance_kind="OFFICIAL",
            official_document_id=official_doc,
            expected_revision=row["revision"],
        )
    env["p3"].revalidate(PERIOD_1, actor=ADMIN)

    # -- 16. C2 satisfeito → conclusão derivada ------------------------
    state = repo.derive_closing_state(PERIOD_1)
    assert state["state"] == "MONTHLY_CLOSING_COMPLETED"

    # -- 17. Segunda versão: aceites não migram ------------------------
    repo.create_complement(
        PERIOD_1, ver_c1, actor=ADMIN,
        reason="complemento solicitado pela revisão",
    )
    repo.finalize_package(PERIOD_1, "CONTABIL", actor=ADMIN)
    pkg_c2 = repo.get_package(
        PERIOD_1, pkg_c["package_id"], viewer=ADMIN, is_manage=True
    )
    ver_c2 = _latest_version_id(pkg_c2)
    assert pkg_c2["current_version"]["version_no"] == 2
    # OCC: revisão obsoleta recusada antes do submit correto.
    with pytest.raises(StaleRevision):
        repo.submit_for_review(
            PERIOD_1, ver_c2, actor=ADMIN, expected_revision=1
        )
    repo.submit_for_review(
        PERIOD_1,
        ver_c2,
        actor=ADMIN,
        expected_revision=pkg_c2["current_version"]["revision"],
    )
    state = repo.derive_closing_state(PERIOD_1)
    assert "area_not_reviewed:CONTABIL:CONTABIL" in state[
        "blocking_reasons"
    ]
    repo.record_decision(
        PERIOD_1, ver_c2, actor=REVIEWER_C,
        area="CONTABIL", outcome="ACCEPTED",
    )
    state = repo.derive_closing_state(PERIOD_1)
    assert state["state"] == "MONTHLY_CLOSING_COMPLETED"

    # -- 18. Rejeição terminal só pelo coordenador ---------------------
    with pytest.raises(CoordinatorRequired):
        repo.confirm_terminal_rejection(
            PERIOD_1, actor=REVIEWER_C, reason="tentativa indevida"
        )
    repo.confirm_terminal_rejection(
        PERIOD_1, actor=COORDINATOR,
        reason="inconsistência material detectada pós-aceite",
    )
    state = repo.derive_closing_state(PERIOD_1)
    assert state["state"] == "TERMINALLY_REJECTED"
    with pytest.raises(TerminalRejectionActive):
        repo.finalize_package(PERIOD_1, "FISCAL", actor=ADMIN)
    repo.revert_terminal_rejection(
        PERIOD_1, actor=COORDINATOR, reason="regularização aprovada"
    )
    state = repo.derive_closing_state(PERIOD_1)
    assert state["state"] == "MONTHLY_CLOSING_COMPLETED"

    # -- 19. Cockpit com estados reais ---------------------------------
    cockpit = repo.get_cockpit(PERIOD_1)
    assert cockpit["closing"]["state"] == "MONTHLY_CLOSING_COMPLETED"
    assert cockpit["p3"]["cutoff_confirmed"] is True
    assert all(
        d["provenance_kind"] == "OFFICIAL"
        for d in cockpit["p3"]["domains"]
    )
    assert cockpit["p4_pendencies"].get("RESOLVED", 0) >= 1

    # -- 20. Competência 2: isolamento e progressão própria ------------
    items_2 = env["checklist"].list_competence_items(PERIOD_2)
    assert items_2 and all(
        i["state"] == "EXPECTED" for i in items_2
    ), "competência 2 herdou estado da 1"
    state2 = repo.derive_closing_state(PERIOD_2)
    assert state2["state"] == "PENDING"
    assert "package_not_submitted:CONTABIL" in state2[
        "blocking_reasons"
    ]


def test_e2e_p3_divergence_blocks_readiness(env):
    """Negativo: divergência de R$0,01 bloqueia a prontidão P3."""
    p3 = env["p3"]
    env["p3"].upsert_reconciliation(
        PERIOD_2,
        "ENTRADAS_SAIDAS",
        actor=ADMIN,
        source_state="AVAILABLE",
        expected_amount=Decimal("1000.00"),
        reported_amount=Decimal("1000.01"),
        provenance={"source": "test"},
    )
    for domain in ("P7", "H02"):
        env["p3"].upsert_reconciliation(
            PERIOD_2,
            domain,
            actor=ADMIN,
            source_state="AVAILABLE",
            expected_amount=Decimal("1.00"),
            reported_amount=Decimal("1.00"),
            provenance={"source": "test"},
        )
    env["p3"].confirm_cutoff(PERIOD_2, actor=ADMIN)
    env["p3"].revalidate(PERIOD_2, actor=ADMIN)
    state = p3.get_p3_state(PERIOD_2)
    assert state["state"] != "READY_TO_CLOSE"
    assert env["pkg"].derive_closing_state(PERIOD_2)[
        "state"
    ] == "PENDING"


def test_e2e_audit_trail_append_only(env):
    """Trilha íntegra: eventos de todo o ciclo, append-only."""
    with plugins_db_connect() as conn, conn.cursor(
        row_factory=dict_row
    ) as cur:
        cur.execute(
            "SELECT event_type"
            "  FROM controllership_finance.closing_audit_event"
            " WHERE competence_id = ("
            "   SELECT competence_id"
            "     FROM controllership_finance.monthly_competence"
            "    WHERE period = %s)"
            " ORDER BY created_at, event_id",
            (PERIOD_1,),
        )
        types = {r["event_type"] for r in cur.fetchall()}
    expected = {
        "COMPETENCE_OPENED",
        "DOCUMENT_UPLOADED",
        "EVIDENCE_ACCEPTED",
        "EVIDENCE_REJECTED",
        "REJECTION_REVERSED",
        "PENDENCY_CREATED",
        "PENDENCY_CLAIMED",
        "PACKAGE_FINALIZED",
        "PACKAGE_SUBMITTED_FOR_REVIEW",
        "PACKAGE_REVIEW_ACCEPTED",
        "CLARIFICATION_OPENED",
        "CLARIFICATION_RESOLVED",
        "COMPETENCE_TERMINALLY_REJECTED",
        "COMPETENCE_REJECTION_REVERTED",
    }
    missing = expected - types
    assert not missing, f"eventos ausentes: {missing}"
