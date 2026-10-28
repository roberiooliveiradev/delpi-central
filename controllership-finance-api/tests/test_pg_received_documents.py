"""DRE-019 — projeção documental do destinatário externo em PG real.

Cadeia de autorização exercida de ponta a ponta (vínculo → release →
recurso), com casos positivos, irmãos (sibling/union) e negativos:

- entrega = vínculo `RECIPIENT` ativo + versão SUBMITTED mais alta do
  pacote da área destinataria;
- união de pacotes quando o mesmo ator é destinatário de duas áreas;
- documento fora do snapshot liberado é 404 — existência nunca vaza;
- conversa do destinatário é `SHARED`-only — INTERNAL nunca sai;
- solicitação OPEN → ANSWERED → CONFIRMED: resposta não encerra e
  confirmação é exclusiva do requerente;
- download revalida membership no conjunto liberado e audita
  AUTHORIZED/DENIED — versão não pinada é negada mesmo existindo.

Isolamento (R4): banco efêmero próprio por execução — ver
``pg_test_isolation``.
"""

from __future__ import annotations

import os
import uuid
from decimal import Decimal
from pathlib import Path

import psycopg
import pytest

from controllership_finance_app.application.services.received_documents_service import (
    ReceivedDocumentsService,
)
from controllership_finance_app.domain.closing_checklist.errors import (
    AdjustmentRequestNotFound,
    DocumentNotFound,
    IdempotencyConflict,
    InvalidAdjustmentRequestState,
)
from controllership_finance_app.infrastructure.persistence import (
    migrations_runner as mr,
)
from controllership_finance_app.infrastructure.persistence.closing_checklist_repository import (
    ClosingChecklistRepository,
)
from controllership_finance_app.infrastructure.persistence.closing_document_repository import (
    ClosingDocumentRepository,
)
from controllership_finance_app.infrastructure.persistence.closing_package_repository import (
    ClosingPackageRepository,
)
from controllership_finance_app.infrastructure.persistence.closing_p3_repository import (
    ClosingP3Repository,
    RECONCILIATION_DOMAINS,
)
from controllership_finance_app.infrastructure.persistence.closing_validation_repository import (
    ClosingValidationRepository,
)
from controllership_finance_app.infrastructure.persistence.plugins_db import (
    plugins_db_connect,
)
from controllership_finance_app.infrastructure.storage.closing_document_storage import (
    ClosingDocumentStorage,
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

ADMIN = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-dre-admin"))
UPLOADER = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-dre-uploader"))
VALIDATOR = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-dre-validator"))
INTERNAL = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-dre-internal"))
DRE_CONT = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-dre-recipient-cont"))
DRE_FISC = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-dre-recipient-fisc"))
DRE_BOTH = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-dre-recipient-both"))
DRE_UNSUB = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-dre-recipient-unsub"))
STRANGER = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-dre-stranger"))

PERIOD = "2027-05"
PERIOD_UNSUBMITTED = "2027-06"

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
    exercido nos itens canônicos (ver Pacote A / e2e)."""
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


def _make_p3(env, period: str):
    p3 = env["p3"]
    for domain in RECONCILIATION_DOMAINS:
        p3.upsert_reconciliation(
            period,
            domain,
            actor=ADMIN,
            source_state="AVAILABLE",
            expected_amount=Decimal("1000.00"),
            reported_amount=Decimal("1000.00"),
            provenance={"source": "declared"},
            provenance_kind="DECLARED",
            official_document_id=None,
        )
    p3.confirm_cutoff(period, actor=ADMIN)
    p3.revalidate(period, actor=ADMIN)


def _latest_version_id(pkg_view: dict) -> str:
    return str(pkg_view["current_version"]["package_version_id"])


@pytest.fixture(scope="module")
def env(_configure_db):
    applied = mr.run_migrations()
    assert applied[-1] == "V018__recipient_document_delivery.sql"

    checklist = ClosingChecklistRepository()
    template_id = str(checklist.list_templates()[0]["template_id"])
    checklist.submit_version_for_review(template_id, 1, actor=ADMIN)
    checklist.publish_version(
        template_id, 1, effective_from_period="2027-01", actor=ADMIN
    )

    docs = ClosingDocumentRepository()
    val = ClosingValidationRepository()
    pkg = ClosingPackageRepository()
    p3 = ClosingP3Repository()
    env = {
        "checklist": checklist,
        "docs": docs,
        "val": val,
        "pkg": pkg,
        "p3": p3,
        "service": ReceivedDocumentsService(
            storage=ClosingDocumentStorage("/tmp/cf-dre019-uploads")
        ),
        "storage": ClosingDocumentStorage("/tmp/cf-dre019-uploads"),
    }

    # -- Competência liberada: dois pacotes SUBMITTED -------------------
    checklist.open_competence(PERIOD, actor=UPLOADER)

    doc_cont = _attach(env, PERIOD, "CK-E-01")
    val.decide_version(
        PERIOD, str(doc_cont["document_id"]), VALIDATOR,
        decision="ACCEPTED",
    )
    doc_fisc = _attach(env, PERIOD, "CK-E-23")
    val.decide_version(
        PERIOD, str(doc_fisc["document_id"]), VALIDATOR,
        decision="ACCEPTED",
    )
    _accept_remaining_items(PERIOD)
    _make_p3(env, PERIOD)

    pkg_cont = pkg.finalize_package(PERIOD, "CONTABIL", actor=ADMIN)
    pkg.submit_for_review(
        PERIOD,
        _latest_version_id(pkg_cont),
        actor=ADMIN,
        expected_revision=1,
    )
    pkg_fisc = pkg.finalize_package(PERIOD, "FISCAL", actor=ADMIN)
    pkg.submit_for_review(
        PERIOD,
        _latest_version_id(pkg_fisc),
        actor=ADMIN,
        expected_revision=1,
    )

    # Vínculos RECIPIENT — consulta documental do destinatário.
    pkg.assign_actor(
        PERIOD, actor=ADMIN, role="RECIPIENT",
        subject=DRE_CONT, recipient_area="CONTABIL",
    )
    pkg.assign_actor(
        PERIOD, actor=ADMIN, role="RECIPIENT",
        subject=DRE_FISC, recipient_area="FISCAL",
    )
    pkg.assign_actor(
        PERIOD, actor=ADMIN, role="RECIPIENT",
        subject=DRE_BOTH, recipient_area="CONTABIL",
    )
    pkg.assign_actor(
        PERIOD, actor=ADMIN, role="RECIPIENT",
        subject=DRE_BOTH, recipient_area="FISCAL",
    )

    # -- Competência com pacote NÃO submetido ---------------------------
    checklist.open_competence(PERIOD_UNSUBMITTED, actor=UPLOADER)
    _accept_remaining_items(PERIOD_UNSUBMITTED)
    _make_p3(env, PERIOD_UNSUBMITTED)
    pkg.finalize_package(PERIOD_UNSUBMITTED, "CONTABIL", actor=ADMIN)
    pkg.assign_actor(
        PERIOD_UNSUBMITTED, actor=ADMIN, role="RECIPIENT",
        subject=DRE_UNSUB, recipient_area="CONTABIL",
    )

    env["doc_cont"] = doc_cont
    env["doc_fisc"] = doc_fisc
    env["ver_cont"] = _latest_version_id(pkg_cont)
    env["ver_fisc"] = _latest_version_id(pkg_fisc)
    return env


def _audit_results(document_id: str) -> list[str]:
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT detail ->> 'result'
              FROM controllership_finance.closing_audit_event
             WHERE event_type = 'DOCUMENT_DOWNLOADED'
               AND entity_id = %s
             ORDER BY created_at
            """,
            (document_id,),
        )
        return [r[0] for r in cur.fetchall()]


def _storage_key(document_id: str, version_no: int) -> str:
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT f.storage_key
              FROM controllership_finance.document_version dv
              JOIN controllership_finance.document_file f
                ON f.file_id = dv.file_id
             WHERE dv.document_id = %s
               AND dv.version_no = %s
            """,
            (document_id, version_no),
        )
        return cur.fetchone()[0]


def _materialize_file(storage: ClosingDocumentStorage, key: str) -> Path:
    path = storage.base_dir / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"%PDF-1.4 dre019")
    return path


# -- N1: lista de entregas -----------------------------------------------


def test_deliveries_union_isolation_and_projection(env):
    svc = env["service"]

    cont = svc.list_deliveries(actor=DRE_CONT)
    assert len(cont) == 1
    assert cont[0]["period"] == PERIOD
    assert cont[0]["recipient_area"] == "CONTABIL"
    assert cont[0]["document_count"] == 1

    both = svc.list_deliveries(actor=DRE_BOTH)
    assert {d["recipient_area"] for d in both} == {"CONTABIL", "FISCAL"}

    assert svc.list_deliveries(actor=STRANGER) == []
    # Vínculo existe, mas nada foi submetido ainda — lista vazia, sem
    # vazamento de que o pacote/pacote-versão existe.
    assert svc.list_deliveries(actor=DRE_UNSUB) == []

    for row in cont + both:
        assert "content" not in row
        assert "p3_reconciliation" not in row
        assert "package_version_id" not in row


# -- N2: entrega da competência ------------------------------------------


def test_get_delivery_released_only(env):
    svc = env["service"]

    delivery = svc.get_delivery(period=PERIOD, actor=DRE_CONT)
    assert [d["recipient_area"] for d in delivery["deliveries"]] == [
        "CONTABIL"
    ]
    ids = {d["document_id"] for d in delivery["documents"]}
    assert ids == {str(env["doc_cont"]["document_id"])}
    doc = delivery["documents"][0]
    assert "storage_key" not in doc
    assert "idempotency_key" not in doc

    # União: destinatário das duas áreas vê os dois documentos.
    both = svc.get_delivery(period=PERIOD, actor=DRE_BOTH)
    assert {d["document_id"] for d in both["documents"]} == {
        str(env["doc_cont"]["document_id"]),
        str(env["doc_fisc"]["document_id"]),
    }


def test_get_delivery_fail_closed(env):
    svc = env["service"]

    with pytest.raises(DocumentNotFound):
        svc.get_delivery(period=PERIOD, actor=STRANGER)
    with pytest.raises(DocumentNotFound):
        svc.get_delivery(period=PERIOD_UNSUBMITTED, actor=DRE_UNSUB)
    # Competência inexistente — mesmo 404, sem confirmar existência.
    with pytest.raises(DocumentNotFound):
        svc.get_delivery(period="2027-09", actor=DRE_CONT)


# -- N3: detalhe + versões autorizadas ------------------------------------


def test_get_document_detail_and_sibling_denied(env):
    svc = env["service"]
    doc_cont = env["doc_cont"]

    detail = svc.get_document(
        period=PERIOD,
        document_id=str(doc_cont["document_id"]),
        actor=DRE_CONT,
    )
    assert detail["document"]["document_id"] == str(
        doc_cont["document_id"]
    )
    assert [v["version_no"] for v in detail["versions"]] == [1]

    # Sibling: documento liberado para outra área é 404 para este ator.
    with pytest.raises(DocumentNotFound):
        svc.get_document(
            period=PERIOD,
            document_id=str(env["doc_fisc"]["document_id"]),
            actor=DRE_CONT,
        )
    # Documento inexistente — mesmo 404.
    with pytest.raises(DocumentNotFound):
        svc.get_document(
            period=PERIOD,
            document_id=str(uuid.uuid4()),
            actor=DRE_CONT,
        )


def test_new_version_not_released_until_resubmitted(env):
    """Substituição interna após o SUBMITTED: a versão nova não entra
    na entrega corrente nem é baixável — a pinada permanece."""
    svc = env["service"]
    doc_cont = env["doc_cont"]
    competence_id = env["docs"].get_competence_id(PERIOD)

    # Correção pós-submissão: v1 SUBMITTED permanece imutável (entrega
    # corrente); o DRAFT encadeado destrava a evidência para correção.
    env["pkg"].create_complement(
        PERIOD,
        env["ver_cont"],
        actor=ADMIN,
        reason="Correção documental.",
    )
    env["docs"].add_version(
        competence_id=competence_id,
        document_id=str(doc_cont["document_id"]),
        expected_revision=doc_cont["revision"],
        storage_key=f"{competence_id}/{uuid.uuid4().hex}.pdf",
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

    detail = svc.get_document(
        period=PERIOD,
        document_id=str(doc_cont["document_id"]),
        actor=DRE_CONT,
    )
    assert [v["version_no"] for v in detail["versions"]] == [1]


# -- conversa compartilhada -------------------------------------------------


def test_shared_conversation_never_leaks_internal(env):
    svc = env["service"]
    docs = env["docs"]
    doc_cont = env["doc_cont"]
    competence_id = env["docs"].get_competence_id(PERIOD)

    msg, created = svc.post_message(
        period=PERIOD,
        document_id=str(doc_cont["document_id"]),
        actor=DRE_CONT,
        author_name="Dre Contábil",
        body="Poderiam confirmar o extrato da conta 01?",
        idempotency_key="dre-msg-1",
    )
    assert created is True
    assert msg["audience"] == "SHARED"

    # Internal posts INTERNAL (default) e SHARED explícito — via
    # repositório, sem rota (a superfície interna é exercida na suíte
    # de rotas documentais).
    docs.create_document_message(
        competence_id=competence_id,
        document_id=str(doc_cont["document_id"]),
        version_no=1,
        audience="INTERNAL",
        body="nota interna — nunca visível ao destinatário",
        author_subject=INTERNAL,
        author_name="Controladoria",
        idempotency_key="int-msg-1",
        request_hash=uuid.uuid4().hex * 2,
    )
    docs.create_document_message(
        competence_id=competence_id,
        document_id=str(doc_cont["document_id"]),
        version_no=1,
        audience="SHARED",
        body="Confirmado — extrato correto.",
        author_subject=INTERNAL,
        author_name="Controladoria",
        idempotency_key="int-msg-2",
        request_hash=uuid.uuid4().hex * 2,
    )

    shared = svc.list_messages(
        period=PERIOD,
        document_id=str(doc_cont["document_id"]),
        actor=DRE_CONT,
        limit=100,
        offset=0,
    )
    bodies = [m["body"] for m in shared["items"]]
    assert all(m["audience"] == "SHARED" for m in shared["items"])
    assert len(shared["items"]) == 2
    assert "nota interna" not in " ".join(bodies)
    mine = [m for m in shared["items"] if m.get("mine")]
    assert len(mine) == 1 and mine[0]["author_name"] == "Dre Contábil"

    # Visão interna sem filtro enxerga as três — boundary preservado.
    internal = docs.list_document_messages(
        competence_id,
        str(doc_cont["document_id"]),
        audience=None,
        limit=100,
        offset=0,
    )
    assert len(internal["items"]) == 3


# -- solicitação de ajuste ---------------------------------------------------


def test_adjustment_request_lifecycle_and_idempotency(env):
    svc = env["service"]
    docs = env["docs"]
    doc_cont = env["doc_cont"]
    competence_id = env["docs"].get_competence_id(PERIOD)

    request, created = svc.create_request(
        period=PERIOD,
        document_id=str(doc_cont["document_id"]),
        actor=DRE_CONT,
        author_name="Dre Contábil",
        body="Favor revisar a competência do extrato — parece 04/2027.",
        idempotency_key="dre-req-1",
    )
    assert created is True
    assert request["state"] == "OPEN"
    assert request["requester_subject"] == DRE_CONT
    assert request["version_no"] == 1

    # Replay idempotente: mesma chave + corpo deduplica.
    replay, replay_created = svc.create_request(
        period=PERIOD,
        document_id=str(doc_cont["document_id"]),
        actor=DRE_CONT,
        author_name="Dre Contábil",
        body="Favor revisar a competência do extrato — parece 04/2027.",
        idempotency_key="dre-req-1",
    )
    assert replay_created is False
    assert replay["request_id"] == request["request_id"]

    # Mesma chave com corpo divergente é conflito.
    with pytest.raises(IdempotencyConflict):
        svc.create_request(
            period=PERIOD,
            document_id=str(doc_cont["document_id"]),
            actor=DRE_CONT,
            author_name="Dre Contábil",
            body="corpo diferente",
            idempotency_key="dre-req-1",
        )

    # Confirmar antes da resposta é transição inválida (409).
    with pytest.raises(InvalidAdjustmentRequestState):
        svc.confirm_request(
            period=PERIOD,
            document_id=str(doc_cont["document_id"]),
            request_id=request["request_id"],
            actor=DRE_CONT,
        )

    # Resposta da Controladoria não encerra a solicitação.
    answered = docs.answer_adjustment_request(
        competence_id,
        request["request_id"],
        answer_body="Competência correta — extrato reflete 05/2027.",
        answered_by=INTERNAL,
        answered_name="Controladoria",
    )
    assert answered["state"] == "ANSWERED"

    # Outro ator vinculado não confirma pedido alheio.
    with pytest.raises(AdjustmentRequestNotFound):
        svc.confirm_request(
            period=PERIOD,
            document_id=str(doc_cont["document_id"]),
            request_id=request["request_id"],
            actor=DRE_BOTH,
        )

    confirmed = svc.confirm_request(
        period=PERIOD,
        document_id=str(doc_cont["document_id"]),
        request_id=request["request_id"],
        actor=DRE_CONT,
    )
    assert confirmed["state"] == "CONFIRMED"
    assert confirmed["answer_body"] is not None

    # Listagem do ator só traz os próprios pedidos.
    mine = svc.list_requests(
        period=PERIOD,
        document_id=str(doc_cont["document_id"]),
        actor=DRE_CONT,
    )
    assert [r["request_id"] for r in mine] == [request["request_id"]]
    assert (
        svc.list_requests(
            period=PERIOD,
            document_id=str(doc_cont["document_id"]),
            actor=DRE_BOTH,
        )
        == []
    )


# -- download autorizado + auditoria -----------------------------------------


def test_download_only_released_versions_with_audit(env):
    svc = env["service"]
    docs = env["docs"]
    doc_cont = env["doc_cont"]
    key = _storage_key(str(doc_cont["document_id"]), 1)
    _materialize_file(env["storage"], key)

    path, meta = svc.resolve_download(
        period=PERIOD,
        document_id=str(doc_cont["document_id"]),
        version_no=1,
        actor=DRE_CONT,
    )
    assert path.is_file()
    assert meta["storage_key"] == key

    # Versão v2 existe na competência mas não está pinada na entrega —
    # 404 com DENIED auditado (o recurso existe; a autorização falhou).
    with pytest.raises(DocumentNotFound):
        svc.resolve_download(
            period=PERIOD,
            document_id=str(doc_cont["document_id"]),
            version_no=2,
            actor=DRE_CONT,
        )
    # Sibling: documento existe na competência, fora do vínculo.
    with pytest.raises(DocumentNotFound):
        svc.resolve_download(
            period=PERIOD,
            document_id=str(env["doc_fisc"]["document_id"]),
            version_no=1,
            actor=DRE_CONT,
        )

    results = _audit_results(str(doc_cont["document_id"]))
    assert "AUTHORIZED" in results
    assert "DENIED" in results
