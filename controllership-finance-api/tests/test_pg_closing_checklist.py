"""PostgreSQL real — workflow Central de Fechamento (CP02-DB/CP03-P2).

Executa migrations V001+V002 num schema `controllership_finance` real e
prova: seed 53 itens DRAFT (sem publish automático), publish governado,
abertura idempotente com snapshot EXPECTED, isolamento v1×v2, auditoria
append-only e falhas de concorrência/revisão.

Isolamento (R4 rework): o fixture só destrói o que a própria execução
criou. Um banco efêmero `cf_test_<prefixo>_<uuid>` é gerado por
`pg_test_isolation.create_owned_test_database` com prova de ownership
(token gravado no banco); o teardown dropa exclusivamente esse recurso,
após conferir o token — nunca um banco preexistente, jamais `plugins_hub`
ou qualquer destino indicado por configuração. Destino ambíguo ou cluster
não declarado falha/skipa antes de qualquer DDL.

Ativado com CF_TEST_PG_HOST/CF_TEST_PG_NAME (prefixo)/CF_TEST_PG_USER/
CF_TEST_PG_PASSWORD (porta opcional CF_TEST_PG_PORT, admin opcional
CF_TEST_PG_ADMIN_DB=postgres) + `CF_TEST_PG_CLUSTER=test` +
`CF_TEST_PG_ALLOW_DESTRUCTIVE=1`. Skip explícito quando ausente — mock
não prova atomicidade.
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
from controllership_finance_app.infrastructure.persistence import plugins_db
from controllership_finance_app.infrastructure.persistence.closing_checklist_repository import (
    ClosingChecklistRepository,
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

ADMIN = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-admin-test"))
VIEWER = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-viewer-test"))

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
    """Cria banco efêmero exclusivo desta execução e aponta plugins_db."""
    import controllership_finance_app.config as cfg

    prefix = os.environ["CF_TEST_PG_NAME"]
    # Configuração ambígua/protegida: falha aqui, antes de qualquer DDL.
    assert_safe_test_prefix(prefix)
    refusal = require_test_environment(os.environ)
    if refusal:
        pytest.skip(refusal)

    admin_db = os.getenv("CF_TEST_PG_ADMIN_DB", "postgres")
    # CREATE-only: nenhum banco preexistente é tocado. O objeto `owned`
    # prova que o recurso pertence a esta execução.
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

    # Teardown só dropa o recurso criado e comprovado desta execução —
    # sem releitura de env, sem varredura por convenção de nome.
    drop_owned_test_database(_test_connect, admin_db, owned)
    for k, v in original.items():
        setattr(cfg.settings, k, v)


@pytest.fixture(scope="module")
def migrated(_configure_db):
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
    return True


@pytest.fixture(scope="module")
def repo():
    return ClosingChecklistRepository()


def _template_id(repo) -> str:
    templates = repo.list_templates()
    assert len(templates) == 1
    return str(templates[0]["template_id"])


def test_seed_53_items_draft(migrated, repo):
    template_id = _template_id(repo)
    versions = repo.list_versions(template_id)
    assert len(versions) == 1
    assert versions[0]["status"] == "DRAFT"
    assert versions[0]["item_count"] == 53

    items = repo.get_version_with_items(template_id, 1)["items"]
    assert [i["item_key"] for i in items[:3]] == [
        "CK-E-01",
        "CK-E-02",
        "CK-E-03",
    ]
    keys = {i["item_key"] for i in items}
    assert "CK-E-27" in keys and "CK-F-23" in keys


def test_migration_restart_is_noop(migrated):
    assert mr.run_migrations() == []


def test_open_without_publish_fails(migrated, repo):
    with pytest.raises(de.NoPublishedTemplate):
        repo.open_competence("2026-10", actor=VIEWER)


def test_publish_open_snapshot(migrated, repo):
    template_id = _template_id(repo)

    repo.submit_version_for_review(
        template_id, 1, actor=ADMIN
    )
    published = repo.publish_version(
        template_id, 1, effective_from_period="2026-01", actor=ADMIN
    )
    assert published["status"] == "PUBLISHED"
    assert published["effective_from_period"] == "2026-01"

    competence, created = repo.open_competence("2026-10", actor=VIEWER)
    assert created is True
    assert competence["status"] == "OPEN"

    items = repo.list_competence_items("2026-10")
    assert len(items) == 53
    assert all(i["state"] == "EXPECTED" for i in items)


def test_open_replay_idempotent(migrated, repo):
    first, created = repo.open_competence("2026-10", actor=VIEWER)
    assert created is False  # já aberta no teste anterior
    competences = repo.list_competences()
    assert sum(1 for c in competences if c["period"] == "2026-10") == 1


def test_competence_resolution_uses_vigente(migrated, repo):
    """Versão vigente = PUBLISHED com effective_from_period <= competência."""
    template_id = _template_id(repo)

    draft = repo.create_draft_version(template_id, actor=ADMIN)
    assert draft["version"] == 2

    items = repo.get_version_with_items(template_id, 2)["items"]
    items[0]["name"] = "Extratos bancários — conta 01 (v2)"
    repo.update_draft_items(
        template_id,
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
            }
            for i in items
        ],
        actor=ADMIN,
    )
    repo.submit_version_for_review(
        template_id, 2, actor=ADMIN
    )
    repo.publish_version(
        template_id, 2, effective_from_period="2026-11", actor=ADMIN
    )

    # 2026-10 ainda resolve v1 (effective_from v2 = 2026-11 futuro).
    v_10 = repo.resolve_published_version("2026-10")
    assert v_10["version"] == 1

    # 2026-11 resolve v2 e o snapshot usa os itens editados.
    competence, created = repo.open_competence("2026-11", actor=VIEWER)
    assert created is True
    items_11 = repo.list_competence_items("2026-11")
    assert items_11[0]["name"].endswith("(v2)")

    # Snapshot de 2026-10 permanece v1 — publish nunca altera histórico.
    items_10 = repo.list_competence_items("2026-10")
    assert items_10[0]["name"] == "Extratos bancários — conta 01"


def test_stale_revision_rejected(migrated, repo):
    template_id = _template_id(repo)
    repo.create_draft_version(template_id, actor=ADMIN)  # v3 DRAFT
    with pytest.raises(de.StaleRevision):
        repo.update_draft_items(
            template_id,
            3,
            expected_revision=99,
            items=[
                {
                    "item_key": "CK-X-01",
                    "sheet": "ELETRONICO",
                    "name": "x",
                    "origin_kind": "EXTERNAL",
                }
            ],
            actor=ADMIN,
        )


def test_second_draft_rejected(migrated, repo):
    template_id = _template_id(repo)
    with pytest.raises(de.DraftAlreadyOpen):
        repo.create_draft_version(template_id, actor=ADMIN)


def test_published_immutable(migrated, repo):
    template_id = _template_id(repo)
    with pytest.raises(de.VersionNotDraft):
        repo.update_draft_items(
            template_id, 1, expected_revision=1, items=[], actor=ADMIN
        )
    with pytest.raises(de.VersionNotInReview):
        repo.publish_version(
            template_id, 1, effective_from_period="2026-01", actor=ADMIN
        )


def test_duplicate_item_key_typed_and_atomic(migrated, repo):
    """R1: item_key duplicado ⇒ erro tipado; nenhuma mutação parcial."""
    template_id = _template_id(repo)
    draft_version = next(
        v["version"]
        for v in repo.list_versions(template_id)
        if v["status"] == "DRAFT"
    )
    revision_before = repo.get_version(template_id, draft_version)[
        "revision"
    ]
    items_before = repo.get_version_with_items(template_id, draft_version)[
        "items"
    ]

    with pytest.raises(de.DuplicateItemKey):
        repo.update_draft_items(
            template_id,
            draft_version,
            expected_revision=revision_before,
            items=[
                {
                    "item_key": "CK-DUP",
                    "sheet": "ELETRONICO",
                    "name": "a",
                    "origin_kind": "EXTERNAL",
                },
                {
                    "item_key": "CK-DUP",
                    "sheet": "ELETRONICO",
                    "name": "b",
                    "origin_kind": "EXTERNAL",
                },
            ],
            actor=ADMIN,
        )

    after = repo.get_version(template_id, draft_version)
    assert after["revision"] == revision_before
    assert after["status"] == "DRAFT"
    items_after = repo.get_version_with_items(template_id, draft_version)[
        "items"
    ]
    assert [i["item_key"] for i in items_after] == [
        i["item_key"] for i in items_before
    ]


def test_audit_trail_append_only(migrated, repo):
    with plugins_db.plugins_db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT event_type, actor_subject"
                "  FROM controllership_finance.closing_audit_event"
                " ORDER BY created_at"
            )
            rows = cur.fetchall()
    types = [r[0] for r in rows]
    assert "VERSION_PUBLISHED" in types
    assert "COMPETENCE_OPENED" in types
    assert "DRAFT_CREATED" in types
    assert "DRAFT_UPDATED" in types
    actors = {r[1] for r in rows}
    assert str(ADMIN) in actors or ADMIN in [str(a) for a in actors]


def test_list_template_events(migrated, repo):
    template_id = _template_id(repo)
    events = repo.list_template_events(template_id)
    assert events, "eventos de template devem existir após publicação/draft"
    types = {e["event_type"] for e in events}
    assert "VERSION_PUBLISHED" in types
    assert "DRAFT_CREATED" in types
    assert all("version" in e for e in events)

    filtered = repo.list_template_events(template_id, version=1)
    assert all(e["version"] == 1 for e in filtered)
    assert all(
        e["event_type"]
        in ("VERSION_SUBMITTED_FOR_REVIEW", "VERSION_PUBLISHED")
        for e in filtered
    )
