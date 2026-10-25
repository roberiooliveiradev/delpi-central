"""Pacote A (doc 104) — aceite integrado P6 + P2 em PostgreSQL real.

Cenário canônico de aceite do pacote:
- duas competências independentes abertas a partir da mesma versão vigente;
- evidência anexada e validada (aceite) em uma;
- rejeição com motivo estruturado e reversão na outra;
- substituição que exige nova validação (item rebaixado para EXPECTED);
- histórico de decisões/auditoria íntegro (append-only);
- publicação prospectiva não altera snapshot das competências abertas —
  a terceira competência resolve a nova versão.

Isolamento (R4): banco efêmero próprio por execução — ver
``pg_test_isolation``.
"""

from __future__ import annotations

import os
import uuid

import psycopg
import pytest

from controllership_finance_app.infrastructure.persistence import (
    migrations_runner as mr,
)
from controllership_finance_app.infrastructure.persistence import plugins_db
from controllership_finance_app.infrastructure.persistence.closing_checklist_repository import (
    ClosingChecklistRepository,
)
from controllership_finance_app.infrastructure.persistence.closing_document_repository import (
    ClosingDocumentRepository,
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

ADMIN = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-pka-admin"))
UPLOADER = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-pka-uploader"))
VALIDATOR = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-pka-validator"))
PERIOD_A = "2027-01"
PERIOD_B = "2027-02"
PERIOD_C = "2027-03"

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
    ]
    checklist = ClosingChecklistRepository()
    template_id = str(checklist.list_templates()[0]["template_id"])
    checklist.submit_version_for_review(
        template_id, 1, actor=ADMIN
    )
    checklist.publish_version(
        template_id, 1, effective_from_period="2026-06", actor=ADMIN
    )
    checklist.open_competence(PERIOD_A, actor=UPLOADER)
    checklist.open_competence(PERIOD_B, actor=UPLOADER)
    return {
        "checklist": checklist,
        "docs": ClosingDocumentRepository(),
        "val": ClosingValidationRepository(),
        "template_id": template_id,
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


def _decisions_seq(snapshot_item_id: str) -> list[tuple[str, str | None]]:
    with plugins_db.plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT decision, reason_code"
            "  FROM controllership_finance.evidence_decision"
            " WHERE snapshot_item_id = %s"
            " ORDER BY created_at, decision_id",
            (snapshot_item_id,),
        )
        return cur.fetchall()


def _audit_types() -> set[str]:
    with plugins_db.plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT event_type"
            "  FROM controllership_finance.closing_audit_event"
        )
        return {r[0] for r in cur.fetchall()}


def test_two_independent_competences_full_cycle(env):
    """Aceite do pacote: attach→validate, reject+reason, replace→revalidate."""
    # -- Competência A: anexa e aceita --------------------------------------
    doc_a = _attach(env, PERIOD_A, "CK-E-01")
    result = env["val"].decide_version(
        PERIOD_A, str(doc_a["document_id"]), VALIDATOR, decision="ACCEPTED"
    )
    assert result["item_state"] == "ACCEPTED"
    assert _item(env, PERIOD_A, "CK-E-01")["state"] == "ACCEPTED"

    # -- Competência B: rejeita com motivo, reverte, aceita ------------------
    doc_b = _attach(env, PERIOD_B, "CK-E-01")
    rejected = env["val"].decide_version(
        PERIOD_B,
        str(doc_b["document_id"]),
        VALIDATOR,
        decision="REJECTED",
        reason_code="WRONG_DOCUMENT",
        comment="Extrato de outra conta.",
    )
    assert _item(env, PERIOD_B, "CK-E-01")["state"] == "EXPECTED"

    env["val"].reverse_decision(
        PERIOD_B,
        str(rejected["decision_id"]),
        VALIDATOR,
        result_state="UNDER_REVIEW",
        justification="Documento correto — erro de leitura.",
    )
    env["val"].decide_version(
        PERIOD_B, str(doc_b["document_id"]), VALIDATOR, decision="ACCEPTED"
    )
    assert _item(env, PERIOD_B, "CK-E-01")["state"] == "ACCEPTED"

    # -- Substituição em A exige nova validação ------------------------------
    env["docs"].add_version(
        competence_id=env["docs"].get_competence_id(PERIOD_A),
        document_id=str(doc_a["document_id"]),
        expected_revision=doc_a["revision"],
        storage_key=(
            f"{env['docs'].get_competence_id(PERIOD_A)}/{uuid.uuid4().hex}"
            ".pdf"
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
    assert _item(env, PERIOD_A, "CK-E-01")["state"] == "EXPECTED"

    # Revalidação após substituição — a nova versão é decidida.
    env["val"].decide_version(
        PERIOD_A, str(doc_a["document_id"]), VALIDATOR, decision="ACCEPTED"
    )
    assert _item(env, PERIOD_A, "CK-E-01")["state"] == "ACCEPTED"

    # -- Histórico append-only íntegro ---------------------------------------
    item_a = _item(env, PERIOD_A, "CK-E-01")
    seq_a = _decisions_seq(str(item_a["snapshot_item_id"]))
    assert [d[0] for d in seq_a] == ["ACCEPTED", "ACCEPTED"]

    item_b = _item(env, PERIOD_B, "CK-E-01")
    seq_b = _decisions_seq(str(item_b["snapshot_item_id"]))
    assert [d[0] for d in seq_b] == ["REJECTED", "REVERSED", "ACCEPTED"]
    assert seq_b[0][1] == "WRONG_DOCUMENT"

    # Eventos do documento B preservam o ciclo decisório.
    events = env["docs"].list_document_events(
        env["docs"].get_competence_id(PERIOD_B),
        str(doc_b["document_id"]),
    )["items"]
    types = [e["event_type"] for e in events]
    assert "EVIDENCE_REJECTED" in types
    assert "EVIDENCE_ACCEPTED" in types
    assert "DOCUMENT_UPLOADED" in types


def test_publish_does_not_rewrite_open_snapshots(env):
    """Publicação prospectiva: competências abertas mantêm a v1; a nova
    competência resolve v2."""
    checklist = env["checklist"]
    draft = checklist.create_draft_version(env["template_id"], actor=ADMIN)
    assert draft["version"] == 2
    items = checklist.get_version_with_items(env["template_id"], 2)["items"]
    items[0]["name"] = items[0]["name"] + " — v2"
    checklist.update_draft_items(
        env["template_id"],
        2,
        expected_revision=1,
        items=[
            {
                "item_key": i["item_key"],
                "sort_order": i["sort_order"],
                "sheet": i["sheet"],
                "name": i["name"],
                "origin_kind": i["origin_kind"],
                "recipient_area": i["recipient_area"],
                "applicability": i["applicability"],
                "branch_scope": i["branch_scope"],
                "totvs_report_ref": i["totvs_report_ref"],
                "validation_scope": i.get("validation_scope", "PER_ATTACHMENT"),
            }
            for i in items
        ],
        actor=ADMIN,
    )
    checklist.submit_version_for_review(
        env["template_id"], 2, actor=ADMIN
    )
    checklist.publish_version(
        env["template_id"], 2, effective_from_period=PERIOD_C, actor=ADMIN
    )

    # Competências abertas permanecem na v1.
    assert not _item(env, PERIOD_A, "CK-E-01")["name"].endswith("— v2")
    assert not _item(env, PERIOD_B, "CK-E-01")["name"].endswith("— v2")

    # Nova competência resolve a versão vigente (v2).
    checklist.open_competence(PERIOD_C, actor=UPLOADER)
    assert _item(env, PERIOD_C, "CK-E-01")["name"].endswith("— v2")

    # Estados validados anteriores intactos.
    assert _item(env, PERIOD_A, "CK-E-01")["state"] == "ACCEPTED"
    assert _item(env, PERIOD_B, "CK-E-01")["state"] == "ACCEPTED"


def test_audit_trail_covers_full_cycle(env):
    """Eventos administrativos, documentais e de validação append-only."""
    types = _audit_types()
    assert "VERSION_PUBLISHED" in types
    assert "COMPETENCE_OPENED" in types
    assert "DRAFT_CREATED" in types
    assert "DRAFT_UPDATED" in types
    assert "DOCUMENT_UPLOADED" in types
    assert "VERSION_ADDED" in types
    assert "EVIDENCE_ACCEPTED" in types
    assert "EVIDENCE_REJECTED" in types
    assert "REJECTION_REVERSED" in types
