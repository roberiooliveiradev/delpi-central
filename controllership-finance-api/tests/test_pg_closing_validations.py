"""PostgreSQL real — validação humana P2 (RQ-P2-02..12).

Migrations V001–V005 em banco efêmero exclusivo desta execução (prova
de ownership via `pg_test_isolation`). Prova: decisão append-only,
aceite por anexo deriva item ACCEPTED, rejeição com motivo estruturado,
substituição reexige validação (RQ-P2-05), reversão pelo mesmo
validador bloqueada por versão posterior, N/A só em CONDITIONAL, item
excepcional só da competência, cancelamento pré-execução, correção
estrutural ACCESS→MANAGE com nova revision e stale check.

Ativado com CF_TEST_PG_* + `CF_TEST_PG_CLUSTER=test` +
`CF_TEST_PG_ALLOW_DESTRUCTIVE=1` — skip explícito quando ausente.
"""

from __future__ import annotations

import os
import uuid

import psycopg
import pytest

from controllership_finance_app.domain.closing_checklist import errors as de
from controllership_finance_app.infrastructure.persistence import (
    migrations_runner as mr,
)
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

ADMIN = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-admin-val-test"))
UPLOADER = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-up-loader-test"))
VALIDATOR = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-validator-test"))
OTHER = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-other-val-test"))
PERIOD = "2026-05"

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
    ]
    checklist = ClosingChecklistRepository()
    template_id = str(checklist.list_templates()[0]["template_id"])
    checklist.submit_version_for_review(
        template_id, 1, actor=ADMIN
    )
    checklist.publish_version(
        template_id, 1, effective_from_period="2026-01", actor=ADMIN
    )
    checklist.open_competence(PERIOD, actor=UPLOADER)
    docs = ClosingDocumentRepository()
    val = ClosingValidationRepository()
    competence_id = docs.get_competence_id(PERIOD)
    return {
        "docs": docs,
        "val": val,
        "checklist": checklist,
        "competence_id": competence_id,
    }


def _item(setup, item_key: str) -> dict:
    items = setup["checklist"].list_competence_items(PERIOD)
    return next(i for i in items if i["item_key"] == item_key)


def _doc_on_item(setup, item_key: str, key: str) -> dict:
    item = _item(setup, item_key)
    doc, _ = setup["docs"].create_document(
        competence_id=setup["competence_id"],
        snapshot_item_id=str(item["snapshot_item_id"]),
        link_kind="competence_item",
        title=f"Evidência {item_key}",
        attachment_role="generic",
        idempotency_key=key,
        request_hash=uuid.uuid4().hex * 2,
        storage_key=f"{setup['competence_id']}/{uuid.uuid4().hex}.pdf",
        original_name="evidencia.pdf",
        stored_name=f"{uuid.uuid4().hex}.pdf",
        mime_type="application/pdf",
        extension=".pdf",
        size_bytes=4096,
        checksum_sha256=uuid.uuid4().hex * 2,
        actor=UPLOADER,
    )
    return doc


def _replace(setup, document_id: str, revision: int) -> None:
    setup["docs"].add_version(
        competence_id=setup["competence_id"],
        document_id=str(document_id),
        expected_revision=revision,
        storage_key=f"{setup['competence_id']}/{uuid.uuid4().hex}.pdf",
        original_name="novo.pdf",
        stored_name=f"{uuid.uuid4().hex}.pdf",
        mime_type="application/pdf",
        extension=".pdf",
        size_bytes=2048,
        checksum_sha256=uuid.uuid4().hex * 2,
        idempotency_key=uuid.uuid4().hex,
        request_hash=uuid.uuid4().hex * 2,
        actor=UPLOADER,
    )


# -- PER_ATTACHMENT -----------------------------------------------------------


def test_accept_attachment_derives_item_accepted(setup):
    """RQ-P2-03/06 — aceite do único anexo ativo ⇒ item ACCEPTED."""
    doc = _doc_on_item(setup, "CK-E-01", "k-val-acc-1")
    result = setup["val"].decide_version(
        PERIOD, str(doc["document_id"]), VALIDATOR, decision="ACCEPTED"
    )
    assert result["decision"] == "ACCEPTED"
    assert result["item_state"] == "ACCEPTED"
    item = _item(setup, "CK-E-01")
    assert item["state"] == "ACCEPTED"


def test_reject_requires_structured_reason_db(setup):
    """CHECK do banco: REJECTED sem reason_code viola a constraint."""
    doc = _doc_on_item(setup, "CK-E-02", "k-val-rej-1")
    with pytest.raises(psycopg.errors.CheckViolation):
        setup["val"].decide_version(
            PERIOD, str(doc["document_id"]), VALIDATOR,
            decision="REJECTED", reason_code=None,
        )


def test_reject_then_replace_requires_new_validation(setup):
    """RQ-P2-05 — nova versão invalida a decisão anterior: o item não
    fica aceito porque a versão corrente ainda não foi decidida."""
    doc = _doc_on_item(setup, "CK-E-03", "k-val-rej-2")
    setup["val"].decide_version(
        PERIOD, str(doc["document_id"]), VALIDATOR,
        decision="REJECTED", reason_code="ILLEGIBLE",
    )
    _replace(setup, doc["document_id"], doc["revision"])
    val = setup["val"].list_item_decisions(PERIOD, "CK-E-03")
    current = next(
        d for d in val["documents"]
        if str(d["document_id"]) == str(doc["document_id"])
    )
    assert current["current_version_no"] == 2
    assert current["current_version_decision"] is None
    assert _item(setup, "CK-E-03")["state"] == "EXPECTED"


def test_replace_on_accepted_item_reopens_validation(setup):
    """RQ-P2-05 — item ACCEPTED volta a EXPECTED quando a evidência é
    substituída (mesmo agregado, nova versão sem decisão)."""
    doc = _doc_on_item(setup, "CK-E-04", "k-val-acc-2")
    setup["val"].decide_version(
        PERIOD, str(doc["document_id"]), VALIDATOR, decision="ACCEPTED"
    )
    assert _item(setup, "CK-E-04")["state"] == "ACCEPTED"
    _replace(setup, doc["document_id"], doc["revision"])
    assert _item(setup, "CK-E-04")["state"] == "EXPECTED"


def test_reversal_same_validator_only(setup):
    """RQ-P2-10 — somente o validador que rejeitou pode reverter."""
    doc = _doc_on_item(setup, "CK-E-05", "k-val-rev-1")
    rejected = setup["val"].decide_version(
        PERIOD, str(doc["document_id"]), VALIDATOR,
        decision="REJECTED", reason_code="INCOMPLETE",
    )
    with pytest.raises(de.Forbidden):
        setup["val"].reverse_decision(
            PERIOD, str(rejected["decision_id"]), OTHER,
            result_state="UNDER_REVIEW", justification="outro ator",
        )
    reverted = setup["val"].reverse_decision(
        PERIOD, str(rejected["decision_id"]), VALIDATOR,
        result_state="ACCEPTED", justification="Análise refeita — ok.",
    )
    assert reverted["decision"] == "REVERSED"
    assert _item(setup, "CK-E-05")["state"] == "ACCEPTED"


def test_reversal_blocked_by_newer_version(setup):
    doc = _doc_on_item(setup, "CK-E-06", "k-val-rev-2")
    rejected = setup["val"].decide_version(
        PERIOD, str(doc["document_id"]), VALIDATOR,
        decision="REJECTED", reason_code="DIVERGENT",
    )
    _replace(setup, doc["document_id"], doc["revision"])
    with pytest.raises(de.InvalidStateTransition):
        setup["val"].reverse_decision(
            PERIOD, str(rejected["decision_id"]), VALIDATOR,
            result_state="ACCEPTED", justification="tarde demais",
        )


def test_decisions_are_append_only(setup):
    """Decisões nunca são UPDATE/DELETE — histórico completo preservado."""
    doc = _doc_on_item(setup, "CK-E-07", "k-val-hist-1")
    setup["val"].decide_version(
        PERIOD, str(doc["document_id"]), VALIDATOR,
        decision="REJECTED", reason_code="WRONG_DOCUMENT",
    )
    setup["val"].decide_version(
        PERIOD, str(doc["document_id"]), VALIDATOR,
        decision="ACCEPTED",
    )
    val = setup["val"].list_item_decisions(PERIOD, "CK-E-07")
    decisions = [
        d for d in val["decisions"]
        if str(d.get("document_id") or "") == str(doc["document_id"])
    ]
    assert len(decisions) == 2
    assert [d["decision"] for d in decisions] == ["REJECTED", "ACCEPTED"]


# -- WHOLE_SET ----------------------------------------------------------------


def _whole_set_item(setup, name_suffix: str) -> dict:
    return setup["val"].create_exceptional_item(
        PERIOD, UPLOADER,
        sheet="ELETRONICO",
        name=f"Conjunto excepcional {name_suffix}",
        justification="Item exigido na conferência.",
        applicability="REQUIRED",
        validation_scope="WHOLE_SET",
    )


def _attach_to(setup, snapshot_item_id: str, key: str) -> dict:
    doc, _ = setup["docs"].create_document(
        competence_id=setup["competence_id"],
        snapshot_item_id=str(snapshot_item_id),
        link_kind="competence_item",
        title="Evidência do conjunto",
        attachment_role="generic",
        idempotency_key=key,
        request_hash=uuid.uuid4().hex * 2,
        storage_key=f"{setup['competence_id']}/{uuid.uuid4().hex}.pdf",
        original_name="conjunto.pdf",
        stored_name=f"{uuid.uuid4().hex}.pdf",
        mime_type="application/pdf",
        extension=".pdf",
        size_bytes=4096,
        checksum_sha256=uuid.uuid4().hex * 2,
        actor=UPLOADER,
    )
    return doc


def test_whole_set_accept_then_replace_reopens(setup):
    """RQ-P2-06 — conjunto aceito; qualquer substituição muda a
    composição e rebaixa o item para EXPECTED."""
    item = _whole_set_item(setup, "ws-1")
    d1 = _attach_to(setup, item["snapshot_item_id"], "k-ws-1a")
    _attach_to(setup, item["snapshot_item_id"], "k-ws-1b")
    result = setup["val"].decide_item_set(
        PERIOD, item["item_key"], VALIDATOR, decision="ACCEPTED"
    )
    assert result["item_state"] == "ACCEPTED"
    assert len(result["composition"]) == 2
    _replace(setup, d1["document_id"], d1["revision"])
    refreshed = _item(setup, item["item_key"])
    assert refreshed["state"] == "EXPECTED"


def test_whole_set_no_evidence_blocks(setup):
    item = _whole_set_item(setup, "ws-2")
    with pytest.raises(de.NoEvidence):
        setup["val"].decide_item_set(
            PERIOD, item["item_key"], VALIDATOR, decision="ACCEPTED"
        )


def test_whole_set_reject_with_reason(setup):
    item = _whole_set_item(setup, "ws-3")
    _attach_to(setup, item["snapshot_item_id"], "k-ws-3a")
    result = setup["val"].decide_item_set(
        PERIOD, item["item_key"], VALIDATOR,
        decision="REJECTED", reason_code="WRONG_COMPETENCE",
        comment="Refere-se a abril.",
    )
    assert result["item_state"] == "EXPECTED"


def test_per_attachment_route_on_whole_set_item_mismatch(setup):
    item = _whole_set_item(setup, "ws-4")
    doc = _attach_to(setup, item["snapshot_item_id"], "k-ws-4a")
    with pytest.raises(de.ValidationScopeMismatch):
        setup["val"].decide_version(
            PERIOD, str(doc["document_id"]), VALIDATOR,
            decision="ACCEPTED",
        )


# -- N/A ------------------------------------------------------------------------


def test_na_required_item_blocked(setup):
    with pytest.raises(de.InvalidStateTransition):
        setup["val"].mark_not_applicable(
            PERIOD, "CK-E-08", UPLOADER, "Sem uso."
        )


def test_na_conditional_and_revert(setup):
    item = setup["val"].create_exceptional_item(
        PERIOD, UPLOADER,
        sheet="ELETRONICO", name="Declaração condicional",
        justification="Criado para exceção do mês.",
        applicability="CONDITIONAL",
    )
    marked = setup["val"].mark_not_applicable(
        PERIOD, item["item_key"], UPLOADER,
        "Não se aplica à competência.",
    )
    assert marked["state"] == "NOT_APPLICABLE"
    reverted = setup["val"].revert_not_applicable(
        PERIOD, item["item_key"], UPLOADER, "Voltou a ser exigido."
    )
    assert reverted["state"] == "EXPECTED"


# -- item excepcional --------------------------------------------------------------


def test_exceptional_item_only_in_competence(setup):
    item = setup["val"].create_exceptional_item(
        PERIOD, UPLOADER,
        sheet="FISICO", name="Documento físico excepcional",
        justification="Exigência pontual da auditoria.",
        recipient_area="CONTABIL",
    )
    assert item["exceptional"] is True
    assert item["item_key"].startswith("EXC-")
    assert item["state"] == "EXPECTED"
    # não altera template mestre
    templates = setup["checklist"].list_templates()
    assert len(templates) == 1


# -- cancelamento de item -------------------------------------------------------------


def test_cancel_item_without_evidence(setup):
    item = setup["val"].create_exceptional_item(
        PERIOD, UPLOADER,
        sheet="ELETRONICO", name="Item a cancelar",
        justification="Criado por engano.",
    )
    cancelled = setup["val"].cancel_item(
        PERIOD, item["item_key"], UPLOADER, "Cancelado por engano."
    )
    assert cancelled["state"] == "CANCELLED"
    with pytest.raises(de.InvalidStateTransition):
        setup["val"].cancel_item(
            PERIOD, item["item_key"], UPLOADER, "de novo"
        )


def test_cancel_item_with_evidence_blocked(setup):
    item = setup["val"].create_exceptional_item(
        PERIOD, UPLOADER,
        sheet="ELETRONICO", name="Item com evidência",
        justification="Requisito pontual.",
    )
    _attach_to(setup, item["snapshot_item_id"], "k-cancel-ev")
    with pytest.raises(de.ItemLocked):
        setup["val"].cancel_item(
            PERIOD, item["item_key"], UPLOADER, "tentativa"
        )


# -- correção estrutural -----------------------------------------------------------------


def test_correction_request_approve_new_revision(setup):
    correction = setup["val"].request_correction(
        PERIOD, "CK-E-09", UPLOADER,
        changes={"validation_scope": "WHOLE_SET",
                 "requirement_notes": "Avaliar o conjunto inteiro."},
        justification="Escopo errado na abertura.",
    )
    assert correction["status"] == "PENDING"
    reviewed = setup["val"].review_correction(
        PERIOD, str(correction["correction_id"]), VALIDATOR,
        approve=True,
    )
    assert reviewed["status"] == "APPROVED"
    assert reviewed["new_revision"] == 2
    item = _item(setup, "CK-E-09")
    assert item["revision"] == 2
    assert item["validation_scope"] == "WHOLE_SET"
    with pytest.raises(de.CorrectionNotPending):
        setup["val"].review_correction(
            PERIOD, str(correction["correction_id"]), VALIDATOR,
            approve=True,
        )


def test_correction_reject_requires_reason(setup):
    correction = setup["val"].request_correction(
        PERIOD, "CK-E-10", UPLOADER,
        changes={"requirement_notes": "nova nota"},
        justification="Nota desatualizada.",
    )
    reviewed = setup["val"].review_correction(
        PERIOD, str(correction["correction_id"]), VALIDATOR,
        approve=False, review_reason="Nota correta como está.",
    )
    assert reviewed["status"] == "REJECTED"


def test_correction_stale_after_another_approval(setup):
    """OCC da correção: aprovar outra correção antes torna esta stale."""
    c1 = setup["val"].request_correction(
        PERIOD, "CK-E-11", UPLOADER,
        changes={"requirement_notes": "n1"},
        justification="primeira",
    )
    c2 = setup["val"].request_correction(
        PERIOD, "CK-E-11", UPLOADER,
        changes={"requirement_notes": "n2"},
        justification="segunda",
    )
    setup["val"].review_correction(
        PERIOD, str(c1["correction_id"]), VALIDATOR, approve=True,
    )
    with pytest.raises(de.StaleRevision):
        setup["val"].review_correction(
            PERIOD, str(c2["correction_id"]), VALIDATOR, approve=True,
        )


# -- resource scope ---------------------------------------------------------------------


def test_item_out_of_declared_scope_404(setup):
    """Item BRANCH não existe no contexto MATRIX declarado."""
    with pytest.raises(de.ItemNotFound):
        setup["val"].decide_item_set(
            PERIOD, "CK-E-27", VALIDATOR, decision="ACCEPTED",
            request_scope="MATRIX",
        )


# -- auditoria ---------------------------------------------------------------------------


def test_validation_events_in_audit(setup):
    """EVIDENCE_ACCEPTED / ITEM_NOT_APPLICABLE / CORRECTION_* trilhados."""
    doc = _doc_on_item(setup, "CK-E-12", "k-audit-1")
    setup["val"].decide_version(
        PERIOD, str(doc["document_id"]), VALIDATOR, decision="ACCEPTED"
    )
    events = setup["docs"].list_document_events(
        setup["competence_id"], str(doc["document_id"])
    )
    types = [e["event_type"] for e in events["items"]]
    assert "EVIDENCE_ACCEPTED" in types
