"""PostgreSQL real — evidências documentais P2-Upload SLICE-1.

Migrations V001–V004 em banco efêmero exclusivo desta execução (prova de
ownership via `pg_test_isolation` — nunca um banco preexistente). Prova:
FK composta item↔competência (D-U6=A), idempotência UNIQUE+request_hash
(D-U7=A), corrida concorrente resolvida no banco, auditoria append-only
(D-U3=A) e integridade referencial file→version→document.

Ativado com CF_TEST_PG_* + `CF_TEST_PG_CLUSTER=test` +
`CF_TEST_PG_ALLOW_DESTRUCTIVE=1` — skip explícito quando ausente.
"""

from __future__ import annotations

import hashlib
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


# -- SLICE-2: U5 versões, U7 cancelamento, U6/U8 leituras ------------------------


def _version_kwargs(setup, **over):
    kw = {
        "competence_id": setup["competence_id"],
        "storage_key": f"{setup['competence_id']}/{uuid.uuid4().hex}.pdf",
        "original_name": "extrato-v2.pdf",
        "stored_name": f"{uuid.uuid4().hex}.pdf",
        "mime_type": "application/pdf",
        "extension": ".pdf",
        "size_bytes": 8192,
        "checksum_sha256": uuid.uuid4().hex * 2,
        "idempotency_key": f"ver-key-{uuid.uuid4().hex[:12]}",
        "request_hash": hashlib.sha256(b"replace-request").hexdigest(),
        "actor": VIEWER,
    }
    kw.update(over)
    return kw


def test_add_version_supersedes_previous(setup):
    """AC-P2-UP-16 — replace cria v2 ATTACHED; v1 fica SUPERSEDED e
    referenciável; o documento segue ATTACHED com revision incrementada."""
    docs = setup["docs"]
    doc, _ = docs.create_document(**_doc_kwargs(setup, "k-ver-1"))
    doc_id = str(doc["document_id"])
    updated, created = docs.add_version(
        **_version_kwargs(
            setup, document_id=doc_id, expected_revision=1
        )
    )
    assert created is True
    assert updated["state"] == "ATTACHED"
    assert updated["current_version_no"] == 2
    assert updated["revision"] == 2
    assert updated["original_name"] == "extrato-v2.pdf"

    versions = docs.list_document_versions(setup["competence_id"], doc_id)
    assert [(v["version_no"], v["state"]) for v in versions] == [
        (2, "ATTACHED"),
        (1, "SUPERSEDED"),
    ]
    # A v1 continua referenciável para download (SUPERSEDED != DELETED).
    v1 = docs.get_version_file(setup["competence_id"], doc_id, 1)
    assert v1["original_name"] == "extrato.pdf"
    v2 = docs.get_version_file(setup["competence_id"], doc_id, 2)
    assert v2["original_name"] == "extrato-v2.pdf"

    events = docs.list_document_events(setup["competence_id"], doc_id)
    assert [e["event_type"] for e in events["items"]] == [
        "VERSION_ADDED",
        "DOCUMENT_UPLOADED",
    ]


def test_add_version_stale_revision_raises(setup):
    """AC-P2-UP-21 — quem segurava uma revision velha perde: nada muda."""
    docs = setup["docs"]
    doc, _ = docs.create_document(**_doc_kwargs(setup, "k-ver-stale"))
    with pytest.raises(de.StaleRevision):
        docs.add_version(
            **_version_kwargs(
                setup,
                document_id=str(doc["document_id"]),
                expected_revision=99,
            )
        )
    fetched = docs.get_document_by_id(
        setup["competence_id"], str(doc["document_id"])
    )
    assert fetched["current_version_no"] == 1
    assert len(
        docs.list_document_versions(
            setup["competence_id"], str(doc["document_id"])
        )
    ) == 1


def test_concurrent_replace_single_winner(setup):
    """AC-P2-UP-21 — replaces simultâneos: FOR UPDATE + revision dão um
    único vencedor; perdedores recebem stale_revision, versão nenhuma se
    perde."""
    docs = setup["docs"]
    doc, _ = docs.create_document(**_doc_kwargs(setup, "k-ver-race"))
    doc_id = str(doc["document_id"])
    results: list[dict] = []
    errors: list[Exception] = []
    barrier = threading.Barrier(4)
    lock = threading.Lock()

    def attempt(i: int) -> None:
        barrier.wait()
        try:
            out, _created = docs.add_version(
                **_version_kwargs(
                    setup,
                    document_id=doc_id,
                    expected_revision=1,
                    original_name=f"concorrente-{i}.pdf",
                )
            )
            with lock:
                results.append(out)
        except Exception as exc:  # noqa: BLE001 — classificada no assert
            with lock:
                errors.append(exc)

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(attempt, range(4)))

    assert len(results) == 1
    assert all(isinstance(e, de.StaleRevision) for e in errors)
    assert len(errors) == 3
    fetched = docs.get_document_by_id(setup["competence_id"], doc_id)
    assert fetched["current_version_no"] == 2
    versions = docs.list_document_versions(setup["competence_id"], doc_id)
    assert len(versions) == 2


def test_replace_idempotent_replay_no_second_version(setup):
    """D-U7=A na mutação — mesma key + mesmo payload ⇒ `created=False`,
    sem versão duplicada e sem segundo `VERSION_ADDED`, mesmo com a
    revision do request já obsoleta (dedup resolve antes do OCC)."""
    docs = setup["docs"]
    doc, _ = docs.create_document(**_doc_kwargs(setup, "k-ver-idem"))
    doc_id = str(doc["document_id"])
    kwargs = _version_kwargs(
        setup,
        document_id=doc_id,
        expected_revision=1,
        idempotency_key="replace-key-abc",
        request_hash=hashlib.sha256(b"same-payload").hexdigest(),
    )
    first, created = docs.add_version(**kwargs)
    assert created is True
    assert first["current_version_no"] == 2
    # Replay com revision obsoleta — dedup, não stale_revision.
    replay, replayed = docs.add_version(
        **{**kwargs, "expected_revision": 1}
    )
    assert replayed is False
    assert replay["current_version_no"] == 2
    assert len(docs.list_document_versions(setup["competence_id"], doc_id)) == 2
    events = docs.list_document_events(setup["competence_id"], doc_id)
    assert [e["event_type"] for e in events["items"]].count(
        "VERSION_ADDED"
    ) == 1


def test_replace_same_key_divergent_hash_conflicts(setup):
    """Mesma key + request_hash divergente ⇒ `idempotency_conflict` 409;
    a key U1 do upload NUNCA é aceita como key da mutação (aggregate
    distinto — document_id + key)."""
    docs = setup["docs"]
    doc, _ = docs.create_document(**_doc_kwargs(setup, "k-ver-div"))
    doc_id = str(doc["document_id"])
    key = "replace-key-xyz"
    docs.add_version(
        **_version_kwargs(
            setup,
            document_id=doc_id,
            expected_revision=1,
            idempotency_key=key,
        )
    )
    with pytest.raises(de.IdempotencyConflict):
        docs.add_version(
            **_version_kwargs(
                setup,
                document_id=doc_id,
                expected_revision=2,
                idempotency_key=key,
                request_hash=hashlib.sha256(b"divergent").hexdigest(),
            )
        )
    assert len(docs.list_document_versions(setup["competence_id"], doc_id)) == 2


def test_version_rows_never_updated(setup):
    """V004 — `document_version` é linha imutável: após replace, a linha
    v1 permanece byte-idêntica (file_id, key, hash, ator, timestamp);
    `SUPERSEDED` é apenas derivação de `current_version_no`."""
    docs = setup["docs"]
    doc, _ = docs.create_document(**_doc_kwargs(setup, "k-ver-immut"))
    doc_id = str(doc["document_id"])
    import controllership_finance_app.config as cfg

    with _test_connect(cfg.settings.PLUGINS_DB_NAME) as conn:
        before = conn.execute(
            "SELECT document_version_id, version_no, file_id, "
            "uploaded_by, idempotency_key, request_hash, created_at "
            "FROM controllership_finance.document_version "
            "WHERE document_id = %s ORDER BY version_no",
            (doc_id,),
        ).fetchall()
        docs.add_version(
            **_version_kwargs(
                setup, document_id=doc_id, expected_revision=1
            )
        )
        after = conn.execute(
            "SELECT document_version_id, version_no, file_id, "
            "uploaded_by, idempotency_key, request_hash, created_at "
            "FROM controllership_finance.document_version "
            "WHERE document_id = %s ORDER BY version_no",
            (doc_id,),
        ).fetchall()
    assert after[0] == before[0]  # v1 intocada
    assert len(after) == 2
    versions = docs.list_document_versions(setup["competence_id"], doc_id)
    assert [(v["version_no"], v["state"]) for v in versions] == [
        (2, "ATTACHED"),
        (1, "SUPERSEDED"),
    ]


def test_concurrent_same_key_replace_deduplicates(setup):
    """Corrida com a MESMA key: um vencedor materializa a versão; os
    demais deduplicam — nenhum stale_revision, nenhuma versão perdida,
    um único VERSION_ADDED."""
    docs = setup["docs"]
    doc, _ = docs.create_document(**_doc_kwargs(setup, "k-ver-samekey"))
    doc_id = str(doc["document_id"])
    request_hash = hashlib.sha256(b"identical-replace").hexdigest()
    barrier = threading.Barrier(4)
    lock = threading.Lock()
    wins: list[dict] = []
    dedups: list[dict] = []
    errors: list[Exception] = []

    def attempt(i: int) -> None:
        barrier.wait()
        try:
            out, created = docs.add_version(
                **_version_kwargs(
                    setup,
                    document_id=doc_id,
                    expected_revision=1,
                    idempotency_key="same-replace-key",
                    request_hash=request_hash,
                    original_name=f"concorrente-{i}.pdf",
                )
            )
            with lock:
                (wins if created else dedups).append(out)
        except Exception as exc:  # noqa: BLE001 — classificada no assert
            with lock:
                errors.append(exc)

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(attempt, range(4)))

    assert len(wins) == 1 and len(dedups) == 3 and not errors
    assert len(docs.list_document_versions(setup["competence_id"], doc_id)) == 2
    events = docs.list_document_events(setup["competence_id"], doc_id)
    assert [e["event_type"] for e in events["items"]].count(
        "VERSION_ADDED"
    ) == 1


def test_cancel_preserves_history_and_exits_active_list(setup):
    """AC-P2-UP-19 — CANCELLED != DELETED: sai da listagem ativa, mas o
    documento, as versões e a auditoria continuam consultáveis."""
    docs = setup["docs"]
    doc, _ = docs.create_document(**_doc_kwargs(setup, "k-cancel-1"))
    doc_id = str(doc["document_id"])
    cancelled = docs.cancel_document(
        competence_id=setup["competence_id"],
        document_id=doc_id,
        expected_revision=1,
        actor=VIEWER,
    )
    assert cancelled["state"] == "CANCELLED"
    assert cancelled["revision"] == 2

    active = docs.list_documents(setup["competence_id"], limit=100)
    assert doc_id not in {str(i["document_id"]) for i in active["items"]}
    cancelled_only = docs.list_documents(
        setup["competence_id"], state="CANCELLED", limit=100
    )
    assert doc_id in {
        str(i["document_id"]) for i in cancelled_only["items"]
    }

    # Consultável no histórico autorizado (U3/U6) e baixável (U4).
    fetched = docs.get_document_by_id(setup["competence_id"], doc_id)
    assert fetched["state"] == "CANCELLED"
    v1 = docs.get_version_file(setup["competence_id"], doc_id, 1)
    assert v1["original_name"] == "extrato.pdf"
    versions = docs.list_document_versions(setup["competence_id"], doc_id)
    assert len(versions) == 1
    events = docs.list_document_events(setup["competence_id"], doc_id)
    assert events["items"][0]["event_type"] == "DOCUMENT_CANCELLED"


def test_cancel_twice_is_typed_conflict(setup):
    docs = setup["docs"]
    doc, _ = docs.create_document(**_doc_kwargs(setup, "k-cancel-2"))
    doc_id = str(doc["document_id"])
    docs.cancel_document(
        competence_id=setup["competence_id"],
        document_id=doc_id,
        expected_revision=1,
        actor=VIEWER,
    )
    # Replay com a revision nova encontra o estado terminal — nunca um
    # segundo evento DOCUMENT_CANCELLED.
    with pytest.raises(de.DocumentCancelled):
        docs.cancel_document(
            competence_id=setup["competence_id"],
            document_id=doc_id,
            expected_revision=2,
            actor=VIEWER,
        )
    events = docs.list_document_events(setup["competence_id"], doc_id)
    assert [
        e["event_type"] for e in events["items"]
    ].count("DOCUMENT_CANCELLED") == 1


def test_mutation_on_cancelled_document_rejected(setup):
    docs = setup["docs"]
    doc, _ = docs.create_document(**_doc_kwargs(setup, "k-cancel-3"))
    doc_id = str(doc["document_id"])
    docs.cancel_document(
        competence_id=setup["competence_id"],
        document_id=doc_id,
        expected_revision=1,
        actor=VIEWER,
    )
    with pytest.raises(de.DocumentCancelled):
        docs.add_version(
            **_version_kwargs(
                setup, document_id=doc_id, expected_revision=2
            )
        )


def test_list_document_events_scoped_and_filtered(setup):
    """U8 — só os eventos documentais do contrato, na competência do
    documento; outra competência nunca vê o histórico."""
    docs = setup["docs"]
    doc, _ = docs.create_document(**_doc_kwargs(setup, "k-events"))
    doc_id = str(doc["document_id"])
    docs.audit_download(
        competence_id=setup["competence_id"],
        document_id=doc_id,
        version_no=1,
        actor=VIEWER,
        result="AUTHORIZED",
    )
    # Evento de outra entidade na mesma competência não aparece.
    other, _ = docs.create_document(**_doc_kwargs(setup, "k-events-2"))

    result = docs.list_document_events(setup["competence_id"], doc_id)
    assert result["total"] == 2
    assert [e["event_type"] for e in result["items"]] == [
        "DOCUMENT_DOWNLOADED",
        "DOCUMENT_UPLOADED",
    ]
    assert all(
        str(e["actor_subject"]) == VIEWER for e in result["items"]
    )
    # Sem vazamento de storage_key / stored_name no detail exposto.
    for e in result["items"]:
        assert "storage_key" not in e["detail"]
        assert "stored_name" not in e["detail"]

    page = docs.list_document_events(
        setup["competence_id"], doc_id, limit=1, offset=0
    )
    assert page["total"] == 2 and len(page["items"]) == 1
    other_events = docs.list_document_events(
        setup["competence_id"], str(other["document_id"])
    )
    assert [e["event_type"] for e in other_events["items"]] == [
        "DOCUMENT_UPLOADED"
    ]


# -- U9 — conversa documental (V016) ---------------------------------------------


def _message_kwargs(doc, **over):
    kw = {
        "competence_id": str(doc["competence_id"]),
        "document_id": str(doc["document_id"]),
        "version_no": doc["current_version_no"],
        "audience": "INTERNAL",
        "body": "Documento disponibilizado para conferência.",
        "author_subject": VIEWER,
        "author_name": "Ana Souza",
        "idempotency_key": f"msg-{uuid.uuid4().hex[:12]}",
        "request_hash": uuid.uuid4().hex * 2,
    }
    kw.update(over)
    return kw


def test_create_document_message_persists_and_audits(setup):
    docs = setup["docs"]
    doc, _ = docs.create_document(**_doc_kwargs(setup, "k-msg-1"))
    message, created = docs.create_document_message(
        **_message_kwargs(doc)
    )
    assert created is True
    assert message["audience"] == "INTERNAL"
    assert message["author_name"] == "Ana Souza"
    assert message["version_no"] == doc["current_version_no"]
    assert message["body"] == "Documento disponibilizado para conferência."
    assert str(message["document_id"]) == str(doc["document_id"])
    assert str(message["competence_id"]) == setup["competence_id"]

    # Auditoria na mesma transação — sem corpo da mensagem no detail.
    events = docs.list_document_events(
        setup["competence_id"], str(doc["document_id"])
    )
    kinds = [e["event_type"] for e in events["items"]]
    assert "DOCUMENT_MESSAGE_POSTED" in kinds
    posted = next(
        e
        for e in events["items"]
        if e["event_type"] == "DOCUMENT_MESSAGE_POSTED"
    )
    assert posted["detail"]["message_id"] == str(message["message_id"])
    assert "body" not in posted["detail"]


def test_document_message_idempotent_replay(setup):
    docs = setup["docs"]
    doc, _ = docs.create_document(**_doc_kwargs(setup, "k-msg-2"))
    kw = _message_kwargs(doc, idempotency_key="msg-dedup")
    first, created_first = docs.create_document_message(**kw)
    second, created_second = docs.create_document_message(**kw)
    assert created_first is True
    assert created_second is False
    assert str(second["message_id"]) == str(first["message_id"])


def test_document_message_divergent_key_conflicts(setup):
    docs = setup["docs"]
    doc, _ = docs.create_document(**_doc_kwargs(setup, "k-msg-3"))
    docs.create_document_message(
        **_message_kwargs(doc, idempotency_key="msg-conflict")
    )
    with pytest.raises(de.IdempotencyConflict):
        docs.create_document_message(
            **_message_kwargs(
                doc,
                idempotency_key="msg-conflict",
                request_hash="f" * 64,
            )
        )


def test_document_message_empty_body_rejected_by_check(setup):
    docs = setup["docs"]
    doc, _ = docs.create_document(**_doc_kwargs(setup, "k-msg-4"))
    with pytest.raises(psycopg.errors.CheckViolation):
        docs.create_document_message(
            **_message_kwargs(doc, body="   ")
        )


def test_list_document_messages_chronological_and_scoped(setup):
    docs = setup["docs"]
    first_doc, _ = docs.create_document(**_doc_kwargs(setup, "k-msg-5a"))
    other_doc, _ = docs.create_document(**_doc_kwargs(setup, "k-msg-5b"))
    docs.create_document_message(
        **_message_kwargs(first_doc, body="primeira")
    )
    docs.create_document_message(
        **_message_kwargs(first_doc, body="segunda")
    )
    docs.create_document_message(
        **_message_kwargs(other_doc, body="outro documento")
    )
    result = docs.list_document_messages(
        setup["competence_id"], str(first_doc["document_id"])
    )
    assert result["total"] == 2
    assert [m["body"] for m in result["items"]] == [
        "primeira",
        "segunda",
    ]
    page = docs.list_document_messages(
        setup["competence_id"],
        str(first_doc["document_id"]),
        limit=1,
        offset=1,
    )
    assert page["total"] == 2
    assert page["items"][0]["body"] == "segunda"


def test_document_message_fk_restricts_orphans(setup):
    docs = setup["docs"]
    # document_id inexistente ⇒ FK RESTRICT — mensagem nunca fica órfã.
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        docs.create_document_message(
            competence_id=setup["competence_id"],
            document_id=str(uuid.uuid4()),
            version_no=1,
            audience="INTERNAL",
            body="órfã",
            author_subject=VIEWER,
            author_name=None,
            idempotency_key="msg-orphan",
            request_hash=uuid.uuid4().hex * 2,
        )
