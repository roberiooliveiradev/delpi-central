"""PostgreSQL real — workflow Central de Fechamento (CP02-DB/CP03-P2).

Executa migrations V001+V002 num schema `controllership_finance` real e
prova: seed 53 itens DRAFT (sem publish automático), publish governado,
abertura idempotente com snapshot EXPECTED, isolamento v1×v2, auditoria
append-only e falhas de concorrência/revisão.

Isolamento (R4): os testes NUNCA tocam um banco compartilhado. O destino é
um **banco dedicado e recriável** (`CF_TEST_PG_NAME`, obrigado a conter
"test" e fora da lista de bancos protegidos), dropado/criado via conexão
administrativa (`CF_TEST_PG_ADMIN_DB`, default `postgres`). Limpeza
destrutiva exige opt-in explícito `CF_TEST_PG_ALLOW_DESTRUCTIVE=1`.
Destino ambíguo falha antes de qualquer operação.

Ativado com CF_TEST_PG_HOST/CF_TEST_PG_NAME/CF_TEST_PG_USER/
CF_TEST_PG_PASSWORD (porta opcional CF_TEST_PG_PORT) +
CF_TEST_PG_ALLOW_DESTRUCTIVE=1. Skip explícito quando ausente — mock não
prova atomicidade.
"""

from __future__ import annotations

import os
import re
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

# Bancos que jamais podem ser alvo destrutivo, mesmo com opt-in.
FORBIDDEN_TEST_TARGETS = frozenset(
    {"postgres", "plugins_hub", "delpi_core", "template0", "template1"}
)
_TEST_DB_NAME = re.compile(r"^[a-z][a-z0-9_]*$")


def assert_safe_test_database(name: str) -> None:
    """Guarda do destino destrutivo — falha antes de qualquer DDL.

    Um banco de teste deve ser dedicado (nome contém ``test``), com nome
    SQL-safe e jamais um banco compartilhado/do sistema.
    """
    if not _TEST_DB_NAME.fullmatch(name):
        raise ValueError(f"CF_TEST_PG_NAME inválido: {name!r}")
    if name in FORBIDDEN_TEST_TARGETS:
        raise ValueError(
            f"CF_TEST_PG_NAME aponta para banco protegido: {name!r}"
        )
    if "test" not in name:
        raise ValueError(
            f"CF_TEST_PG_NAME deve ser um banco dedicado de teste "
            f"(nome contendo 'test'): {name!r}"
        )


def _admin_connection() -> psycopg.Connection:
    return psycopg.connect(
        host=os.environ["CF_TEST_PG_HOST"],
        port=int(os.getenv("CF_TEST_PG_PORT", "5432")),
        dbname=os.getenv("CF_TEST_PG_ADMIN_DB", "postgres"),
        user=os.environ["CF_TEST_PG_USER"],
        password=os.environ["CF_TEST_PG_PASSWORD"],
        autocommit=True,
    )


@pytest.fixture(scope="module", autouse=True)
def _configure_db():
    """Recria banco dedicado de teste e aponta plugins_db para ele."""
    import controllership_finance_app.config as cfg

    db_name = os.environ["CF_TEST_PG_NAME"]
    # Destino ambíguo/compartilhado: falha aqui, antes de qualquer DDL.
    assert_safe_test_database(db_name)
    if os.getenv("CF_TEST_PG_ALLOW_DESTRUCTIVE") != "1":
        pytest.skip(
            "CF_TEST_PG_ALLOW_DESTRUCTIVE=1 ausente — limpeza destrutiva "
            "do banco de teste não autorizada"
        )

    # Banco efêmero: DROP+CREATE no banco dedicado apenas; schemas vizinhos
    # de outros contextos vivem em outros bancos e não são tocados.
    with _admin_connection() as conn, conn.cursor() as cur:
        cur.execute(f'DROP DATABASE IF EXISTS "{db_name}" WITH (FORCE)')
        cur.execute(f'CREATE DATABASE "{db_name}"')

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
    cfg.settings.PLUGINS_DB_NAME = db_name
    cfg.settings.PLUGINS_DB_USER = os.environ["CF_TEST_PG_USER"]
    cfg.settings.PLUGINS_DB_PASSWORD = os.environ["CF_TEST_PG_PASSWORD"]
    cfg.settings.PLUGINS_DB_SSLMODE = os.getenv("CF_TEST_PG_SSLMODE", "prefer")
    cfg.settings.PLUGINS_DB_CONNECT_TIMEOUT = 10

    yield

    with _admin_connection() as conn, conn.cursor() as cur:
        cur.execute(f'DROP DATABASE IF EXISTS "{db_name}" WITH (FORCE)')
    for k, v in original.items():
        setattr(cfg.settings, k, v)


@pytest.fixture(scope="module")
def migrated(_configure_db):
    applied = mr.run_migrations()
    assert applied == [
        "V001__create_closing_checklist_schema.sql",
        "V002__seed_monthly_closing_checklist_v1.sql",
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
    with pytest.raises(de.VersionNotDraft):
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
