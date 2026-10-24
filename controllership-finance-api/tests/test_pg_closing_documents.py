"""PostgreSQL real — evidências documentais P2-Upload SLICE-1.

Migrations V001–V003 em banco efêmero exclusivo desta execução (prova de
ownership via `pg_test_isolation` — nunca um banco preexistente). Prova:
FK composta item↔competência (D-U6=A), idempotência UNIQUE+request_hash
(D-U7=A), corrida concorrente resolvida no banco, auditoria append-only
(D-U3=A) e integridade referencial file→version→document.

Ativado com CF_TEST_PG_* + `CF_TEST_PG_CLUSTER=test` +
`CF_TEST_PG_ALLOW_DESTRUCTIVE=1` — skip explícito quando ausente.
"""

from __future__ import annotations

import os
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor

import psycopg
import pytest

from controllership_finance_app.domain.closing_checklist import errors as de
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

ADMIN = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-admin-doc-test"))
VIEWER = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-viewer-doc-test"))
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
    ]
    checklist = ClosingChecklistRepository()
    template_id = str(checklist.list_templates()[0]["template_id"])
    checklist.publish_version(
        template_id, 1, effective_from_period="2026-01", actor=ADMIN
    )
    checklist.open_competence(PERIOD, actor=VIEWER)
    docs = ClosingDocumentRepository()
    competence_id = docs.get_competence_id(PERIOD)
    items = checklist.list_competence_items(PERIOD)
    return {
        "docs": docs,
        "competence_id": competence_id,
        "item": items[0],
    }


def _doc_kwargs(setup, key: str, request_hash: str | None = None, **over):
    kw = {
        "competence_id": setup["competence_id"],
        "snapshot_item_id": None,
        "link_kind": "competence",
        "title": "Extrato bancário",
        "attachment_role": "generic",
        "idempotency_key": key,
        "request_hash": request_hash or uuid.uuid4().hex * 2,
        "storage_key": f"{setup['competence_id']}/{uuid.uuid4().hex}.pdf",
        "original_name": "extrato.pdf",
        "stored_name": f"{uuid.uuid4().hex}.pdf",
        "mime_type": "application/pdf",
        "extension": ".pdf",
        "size_bytes": 4096,
        "checksum_sha256": uuid.uuid4().hex * 2,
        "actor": VIEWER,
    }
    kw.update(over)
    return kw


def test_create_competence_document(setup):
    docs = setup["docs"]
    doc, created = docs.create_document(**_doc_kwargs(setup, "k-comp-1"))
    assert created is True
    assert doc["state"] == "ATTACHED"
    assert doc["link_kind"] == "competence"
    assert doc["current_version_no"] == 1
    assert doc["attachment_role"] == "generic"


def test_create_item_document_membership_fk(setup):
    docs = setup["docs"]
    item_id = str(setup["item"]["snapshot_item_id"])
    resolved = docs.get_snapshot_item(setup["competence_id"], item_id)
    assert str(resolved["snapshot_item_id"]) == item_id
    assert resolved["branch_scope"] == setup["item"]["branch_scope"]
    doc, created = docs.create_document(
        **_doc_kwargs(
            setup,
            "k-item-1",
            snapshot_item_id=item_id,
            link_kind="competence_item",
        )
    )
    assert created is True
    assert str(doc["snapshot_item_id"]) == item_id
    assert doc["snapshot_item_key"] == setup["item"]["item_key"]


def test_cross_competence_item_rejected(setup):
    docs = setup["docs"]
    with pytest.raises(de.ItemNotFound):
        docs.get_snapshot_item(setup["competence_id"], str(uuid.uuid4()))


def test_idempotent_replay_same_hash(setup):
    docs = setup["docs"]
    rh = uuid.uuid4().hex * 2
    first, created1 = docs.create_document(
        **_doc_kwargs(setup, "k-replay", request_hash=rh)
    )
    second, created2 = docs.create_document(
        **_doc_kwargs(setup, "k-replay", request_hash=rh)
    )
    assert created1 is True and created2 is False
    assert second["document_id"] == first["document_id"]
    listed = docs.list_documents(setup["competence_id"])
    assert (
        sum(1 for i in listed["items"]
            if str(i["document_id"]) == str(first["document_id"]))
        == 1
    )


def test_same_binary_two_documents_no_collapse(setup):
    """AC-P2-UP-02 — hash de conteúdo não deduplica: o mesmo binário pode
    evidenciar itens diferentes; duas evidências legítimas nunca colapsam."""
    docs = setup["docs"]
    same_checksum = uuid.uuid4().hex * 2
    first, c1 = docs.create_document(
        **_doc_kwargs(setup, "k-binary-1", checksum_sha256=same_checksum)
    )
    second, c2 = docs.create_document(
        **_doc_kwargs(
            setup,
            "k-binary-2",
            checksum_sha256=same_checksum,
            snapshot_item_id=str(setup["item"]["snapshot_item_id"]),
            link_kind="competence_item",
        )
    )
    assert c1 is True and c2 is True
    assert str(first["document_id"]) != str(second["document_id"])


def test_same_key_divergent_hash_conflict(setup):
    docs = setup["docs"]
    docs.create_document(**_doc_kwargs(setup, "k-conflict"))
    with pytest.raises(de.IdempotencyConflict):
        docs.create_document(
            **_doc_kwargs(
                setup, "k-conflict", request_hash=uuid.uuid4().hex * 2
            )
        )


def test_concurrent_same_key_single_winner(setup):
    """Dois uploads simultâneos com a mesma chave: o banco garante um
    único vencedor — o perdedor recebe replay ou conflito, nunca uma
    segunda linha."""
    docs = setup["docs"]
    rh = uuid.uuid4().hex * 2
    results: list[tuple[bool, str]] = []
    errors: list[Exception] = []
    barrier = threading.Barrier(4)
    lock = threading.Lock()

    def attempt(i: int) -> None:
        barrier.wait()
        try:
            doc, created = docs.create_document(
                **_doc_kwargs(
                    setup,
                    "k-race",
                    request_hash=rh,
                    storage_key=(
                        f"{setup['competence_id']}/race-{i}-"
                        f"{uuid.uuid4().hex}.pdf"
                    ),
                )
            )
            with lock:
                results.append((created, str(doc["document_id"])))
        except Exception as exc:  # noqa: BLE001 — classificada no assert
            with lock:
                errors.append(exc)

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(attempt, range(4)))

    created_count = sum(1 for c, _ in results if c)
    replayed = [d for c, d in results if not c]
    assert created_count == 1
    assert all(d == results[0][1] or True for d in replayed)
    # Todos os replays apontam para o mesmo documento vencedor.
    doc_ids = {d for _, d in results}
    assert len(doc_ids) == 1
    assert errors == []


def test_audit_upload_and_download_append_only(setup):
    docs = setup["docs"]
    doc, _ = docs.create_document(**_doc_kwargs(setup, "k-audit"))
    docs.audit_download(
        competence_id=setup["competence_id"],
        document_id=str(doc["document_id"]),
        version_no=1,
        actor=VIEWER,
        result="AUTHORIZED",
    )
    with plugins_db.plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT event_type, actor_subject, detail"
            "  FROM controllership_finance.closing_audit_event"
            " WHERE entity_id = %s"
            " ORDER BY created_at",
            (str(doc["document_id"]),),
        )
        rows = cur.fetchall()
    types = [r[0] for r in rows]
    assert types == ["DOCUMENT_UPLOADED", "DOCUMENT_DOWNLOADED"]
    assert all(str(r[1]) == VIEWER for r in rows)
    assert rows[1][2]["result"] == "AUTHORIZED"
    assert rows[0][2]["checksum_sha256"]


def test_document_get_and_version_file(setup):
    docs = setup["docs"]
    doc, _ = docs.create_document(**_doc_kwargs(setup, "k-get"))
    fetched = docs.get_document_by_id(
        setup["competence_id"], str(doc["document_id"])
    )
    assert fetched["original_name"] == "extrato.pdf"
    vf = docs.get_version_file(
        setup["competence_id"], str(doc["document_id"]), 1
    )
    assert vf["version_no"] == 1
    assert vf["storage_key"].endswith(".pdf")
    with pytest.raises(de.DocumentNotFound):
        docs.get_version_file(
            setup["competence_id"], str(doc["document_id"]), 2
        )


def test_document_scoped_to_competence(setup):
    """Cross-competence nunca revela existência — 404 mesmo com id válido."""
    docs = setup["docs"]
    doc, _ = docs.create_document(**_doc_kwargs(setup, "k-scope"))
    with pytest.raises(de.DocumentNotFound):
        docs.get_document_by_id(
            str(uuid.uuid4()), str(doc["document_id"])
        )


def _seeded_item(item_key: str) -> dict:
    items = ClosingChecklistRepository().list_competence_items(PERIOD)
    return next(i for i in items if i["item_key"] == item_key)


def test_document_inherits_item_branch_scope(setup):
    """Documento vinculado herda `branch_scope` do item (MATRIX/BRANCH);
    documento de competência reporta BOTH — escopo vem do join, não de
    metadado duplicado."""
    docs = setup["docs"]
    matrix_item = _seeded_item("CK-E-01")
    branch_item = _seeded_item("CK-E-27")
    assert matrix_item["branch_scope"] == "MATRIX"
    assert branch_item["branch_scope"] == "BRANCH"

    matrix_doc, _ = docs.create_document(
        **_doc_kwargs(
            setup,
            "k-scope-matrix",
            snapshot_item_id=str(matrix_item["snapshot_item_id"]),
            link_kind="competence_item",
        )
    )
    branch_doc, _ = docs.create_document(
        **_doc_kwargs(
            setup,
            "k-scope-branch",
            snapshot_item_id=str(branch_item["snapshot_item_id"]),
            link_kind="competence_item",
        )
    )
    comp_doc, _ = docs.create_document(
        **_doc_kwargs(setup, "k-scope-comp")
    )

    assert matrix_doc["branch_scope"] == "MATRIX"
    assert branch_doc["branch_scope"] == "BRANCH"
    assert comp_doc["branch_scope"] == "BOTH"

    vf = docs.get_version_file(
        setup["competence_id"], str(branch_doc["document_id"]), 1
    )
    assert vf["branch_scope"] == "BRANCH"


def test_list_documents_filters_by_request_scope(setup):
    """U2 — filial-contexto do request: MATRIX lista escopo MATRIX+BOTH;
    BRANCH lista BRANCH+BOTH; BOTH é irrestrito (dataset compartilhado)."""
    docs = setup["docs"]
    matrix_item = _seeded_item("CK-E-01")
    branch_item = _seeded_item("CK-E-27")
    matrix_doc, _ = docs.create_document(
        **_doc_kwargs(
            setup,
            "k-list-matrix",
            snapshot_item_id=str(matrix_item["snapshot_item_id"]),
            link_kind="competence_item",
        )
    )
    branch_doc, _ = docs.create_document(
        **_doc_kwargs(
            setup,
            "k-list-branch",
            snapshot_item_id=str(branch_item["snapshot_item_id"]),
            link_kind="competence_item",
        )
    )
    comp_doc, _ = docs.create_document(
        **_doc_kwargs(setup, "k-list-comp")
    )
    ids = {str(d["document_id"]) for d in (matrix_doc, branch_doc, comp_doc)}

    def scoped_ids(scope: str) -> set[str]:
        result = docs.list_documents(
            setup["competence_id"], branch_scope=scope, limit=100
        )
        return {
            str(i["document_id"]) for i in result["items"]
        } & ids

    matrix_id = str(matrix_doc["document_id"])
    branch_id = str(branch_doc["document_id"])
    comp_id = str(comp_doc["document_id"])

    assert scoped_ids("MATRIX") == {matrix_id, comp_id}
    assert scoped_ids("BRANCH") == {branch_id, comp_id}
    assert scoped_ids("BOTH") == ids


def test_audit_download_denied_phase_classification(setup):
    """D-U3=A — `phase` classifica a etapa: decisão de autorização
    (AUTHORIZED/DENIED) versus falha de entrega (FAILED); nenhuma linha
    afirma transferência concluída."""
    docs = setup["docs"]
    doc, _ = docs.create_document(**_doc_kwargs(setup, "k-audit-phase"))
    for result in ("DENIED", "FAILED", "AUTHORIZED"):
        docs.audit_download(
            competence_id=setup["competence_id"],
            document_id=str(doc["document_id"]),
            version_no=1,
            actor=VIEWER,
            result=result,
        )
    with plugins_db.plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT detail->>'result', detail->>'phase'"
            "  FROM controllership_finance.closing_audit_event"
            " WHERE entity_id = %s AND event_type = 'DOCUMENT_DOWNLOADED'"
            " ORDER BY created_at",
            (str(doc["document_id"]),),
        )
        rows = cur.fetchall()
    assert rows == [
        ("DENIED", "authorization"),
        ("FAILED", "delivery"),
        ("AUTHORIZED", "authorization"),
    ]
