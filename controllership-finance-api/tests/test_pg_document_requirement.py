"""PostgreSQL real — DR-1/DR-2: operação documental transacional.

Prova atomicidade, rollback integral, replay idempotente, OCC
`base_version`, serialização contra writers legados e abertura de
competência, trilha REVIEW auditada, checklist publicado vazio e
snapshots congelados — mesma estratégia de banco efêmero de
`test_pg_closing_checklist.py` (CF_TEST_PG_* + cluster declarado).
"""

from __future__ import annotations

import os
import threading
import uuid
from datetime import date

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

ADMIN = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-dr1-admin"))
VIEWER = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-dr1-viewer"))

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
def migrated(_configure_db):
    applied = mr.run_migrations()
    assert applied[-1] == "V017__document_requirement_operations.sql"
    return True


@pytest.fixture(scope="module")
def repo():
    return ClosingChecklistRepository()


def _period(delta_months: int) -> str:
    base = date.today().replace(day=1)
    month = base.month + delta_months
    year = base.year + (month - 1) // 12
    month = (month - 1) % 12 + 1
    return f"{year}-{month:02d}"


def _item(key: str, name: str | None = None, **overrides) -> dict:
    item = {
        "item_key": key,
        "name": name or f"Documento {key}",
        "sheet": "ELETRONICO",
        "purpose": None,
        "origin_kind": "EXTERNAL",
        "recipient_area": "CONTABIL",
        "applicability": "REQUIRED",
        "branch_scope": "BOTH",
        "totvs_report_ref": None,
        "requirement_notes": None,
        "validation_scope": "PER_ATTACHMENT",
    }
    item.update(overrides)
    return item


def _new_template() -> str:
    with plugins_db.plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO controllership_finance.checklist_template"
            " (code, name, created_by)"
            " VALUES (%s, %s, %s) RETURNING template_id",
            (f"T-DR1-{uuid.uuid4().hex[:8]}", "Template DR1", ADMIN),
        )
        return str(cur.fetchone()[0])


def _apply(repo, template_id, item_key, *, period, **kwargs):
    base = {
        "item": None,
        "effective_from": period,
        "effective_until": None,
        "base_version": 0,
        "allow_empty": False,
        "idempotency_key": uuid.uuid4().hex,
        "actor": ADMIN,
    }
    base.update(kwargs)
    return repo.apply_document_requirement(
        template_id, item_key, **base
    )


def _count_versions(template_id: str) -> int:
    with plugins_db.plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) FROM"
            " controllership_finance.checklist_template_version"
            " WHERE template_id = %s",
            (template_id,),
        )
        return cur.fetchone()[0]


def _event_types(template_id: str) -> list[str]:
    with plugins_db.plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT e.event_type FROM"
            " controllership_finance.closing_audit_event e"
            " LEFT JOIN controllership_finance.checklist_template_version v"
            "   ON v.version_id = e.entity_id"
            " WHERE v.template_id = %s"
            "    OR e.entity_id = %s ORDER BY e.created_at",
            (template_id, template_id),
        )
        return [r[0] for r in cur.fetchall()]


class TestApplyDocumentRequirement:
    def test_upsert_atomic_governed_trail(self, migrated, repo):
        tid = _new_template()
        period = _period(50)
        result = _apply(
            repo, tid, "DOCX", period=period,
            item=_item("DOCX"),
        )
        assert result["replayed"] is False
        assert result["no_changes"] is False
        assert len(result["published_versions"]) == 1
        pv = result["published_versions"][0]
        assert pv["effective_from_period"] == period
        assert pv["item_count"] == 1

        events = _event_types(tid)
        for expected in (
            "DRAFT_CREATED",
            "DRAFT_UPDATED",
            "VERSION_SUBMITTED_FOR_REVIEW",
            "VERSION_PUBLISHED",
            "DOCUMENT_CONFIG_APPLIED",
        ):
            assert expected in events

        resolved = repo.resolve_published_version(period)
        assert resolved["version"] == pv["version"]

        competence, created = repo.open_competence(period, actor=VIEWER)
        assert created is True
        assert competence["template_version_id"] is not None
        items = repo.list_competence_items(period)
        assert [i["item_key"] for i in items] == ["DOCX"]

    def test_retry_same_key_replays_without_duplicates(
        self, migrated, repo
    ):
        tid = _new_template()
        key = uuid.uuid4().hex
        first = _apply(
            repo, tid, "DOCX", period=_period(51),
            item=_item("DOCX"), idempotency_key=key,
        )
        events_before = len(_event_types(tid))
        versions_before = _count_versions(tid)
        second = _apply(
            repo, tid, "DOCX", period=_period(51),
            item=_item("DOCX"), idempotency_key=key,
        )
        assert second["replayed"] is True
        assert (
            second["published_versions"]
            == first["published_versions"]
        )
        assert _count_versions(tid) == versions_before
        assert len(_event_types(tid)) == events_before

    def test_same_key_divergent_payload_conflicts(self, migrated, repo):
        tid = _new_template()
        key = uuid.uuid4().hex
        _apply(
            repo, tid, "DOCX", period=_period(51),
            item=_item("DOCX"), idempotency_key=key,
        )
        with pytest.raises(de.IdempotencyConflict):
            _apply(
                repo, tid, "DOCX", period=_period(52),
                item=_item("DOCX"), idempotency_key=key,
            )

    def test_replay_beats_stale_base_version(self, migrated, repo):
        """Idempotência resolve ANTES do OCC — retry legítimo com
        revisão já superada retorna o resultado persistido."""
        tid = _new_template()
        key = uuid.uuid4().hex
        first = _apply(
            repo, tid, "DOCX", period=_period(51),
            item=_item("DOCX"), idempotency_key=key,
        )
        # Outra operação avança a revisão do catálogo.
        _apply(
            repo, tid, "DOCY", period=_period(51),
            item=_item("DOCY"), base_version=1,
        )
        replay = _apply(
            repo, tid, "DOCX", period=_period(51),
            item=_item("DOCX"), idempotency_key=key,
        )
        assert replay["replayed"] is True
        assert (
            replay["published_versions"]
            == first["published_versions"]
        )

    def test_stale_base_version_rejected(self, migrated, repo):
        tid = _new_template()
        _apply(
            repo, tid, "DOCX", period=_period(51), item=_item("DOCX")
        )
        with pytest.raises(de.StaleRevision):
            _apply(
                repo, tid, "DOCY", period=_period(51),
                item=_item("DOCY"), base_version=0,
            )

    def test_mid_failure_rolls_back_integrally(
        self, migrated, repo, monkeypatch
    ):
        """Falha após a primeira versão publicada → zero versões novas
        e zero eventos persistidos (atomicidade real)."""
        tid = _new_template()
        # Janela com dois boundaries → plano de 2+ versões.
        _apply(
            repo, tid, "DOCA", period=_period(52), item=_item("DOCA")
        )
        _apply(
            repo, tid, "DOCB", period=_period(54),
            item=_item("DOCB"), base_version=1,
        )
        versions_before = _count_versions(tid)
        events_before = len(_event_types(tid))

        calls = {"n": 0}
        real_audit = ClosingChecklistRepository._audit

        def flaky_audit(self, cur, **kwargs):
            calls["n"] += 1
            if calls["n"] == 5:
                raise RuntimeError("injected mid-plan failure")
            return real_audit(self, cur, **kwargs)

        monkeypatch.setattr(
            ClosingChecklistRepository, "_audit", flaky_audit
        )
        with pytest.raises(RuntimeError):
            _apply(
                repo, tid, "DOCZ", period=_period(51),
                item=_item("DOCZ"), base_version=2,
            )
        assert _count_versions(tid) == versions_before
        assert len(_event_types(tid)) == events_before

    def test_window_covers_open_competence_rejected(
        self, migrated, repo
    ):
        tid = _new_template()
        period = _period(55)
        repo.open_competence(period, actor=VIEWER)
        with pytest.raises(de.WindowCoversOpenCompetence):
            _apply(
                repo, tid, "DOCX", period=period, item=_item("DOCX")
            )

    def test_open_after_config_resolves_new_version(
        self, migrated, repo
    ):
        """Teste D (ordem publicação→abertura): competência aberta após
        a configuração recebe o snapshot da versão nova."""
        tid = _new_template()
        period = _period(56)
        _apply(
            repo, tid, "DOCX", period=period, item=_item("DOCX")
        )
        competence, created = repo.open_competence(period, actor=VIEWER)
        assert created is True
        assert competence["template_version_id"] is not None
        assert [i["item_key"] for i in
                repo.list_competence_items(period)] == ["DOCX"]

    def test_last_item_requires_allow_empty(self, migrated, repo):
        tid = _new_template()
        _apply(
            repo, tid, "DOCX", period=_period(57), item=_item("DOCX")
        )
        # Encerrar a única exigência sem intenção explícita → 422.
        with pytest.raises(de.EmptyResultingChecklist):
            _apply(
                repo, tid, "DOCX", period=_period(58),
                base_version=1,
            )
        # Com allow_empty → versão publicada com zero itens.
        result = _apply(
            repo, tid, "DOCX", period=_period(58),
            base_version=1, allow_empty=True,
        )
        assert result["published_versions"][0]["item_count"] == 0

        # Competência posterior: versão vazia ≠ sem template.
        competence, created = repo.open_competence(
            _period(59), actor=VIEWER
        )
        assert created is True
        assert competence["template_version_id"] is not None
        assert repo.list_competence_items(_period(59)) == []

    def test_empty_publish_distinct_from_no_template(
        self, migrated, repo
    ):
        """Distinção DR-2: sem versão vigente → template_version_id
        NULL; versão vigente vazia → NOT NULL com snapshot vazio."""
        tid = _new_template()
        _apply(
            repo, tid, "DOCX", period=_period(60), item=_item("DOCX")
        )
        _apply(
            repo, tid, "DOCX", period=_period(61),
            base_version=1, allow_empty=True,
        )
        # Competência ANTES de qualquer versão efetiva → NULL.
        early, _ = repo.open_competence("2020-01", actor=VIEWER)
        assert early["template_version_id"] is None
        # Competência na vigência do checklist vazio → NOT NULL.
        late, _ = repo.open_competence(_period(62), actor=VIEWER)
        assert late["template_version_id"] is not None

    def test_open_draft_blocks_operation(self, migrated, repo):
        tid = _new_template()
        draft = repo.create_draft_version(tid, actor=ADMIN)
        assert draft["status"] == "DRAFT"
        with pytest.raises(de.CatalogDraftConflict):
            _apply(
                repo, tid, "DOCX", period=_period(63), item=_item("DOCX"),
                base_version=1,
            )

    def test_preserves_other_documents_and_reactivation(
        self, migrated, repo
    ):
        tid = _new_template()
        _apply(repo, tid, "DOCA", period=_period(64), item=_item("DOCA"))
        _apply(
            repo, tid, "DOCB", period=_period(64),
            item=_item("DOCB"), base_version=1,
        )
        # Janela temporária de DOCA: [15, 16] → remoção publicada em 17.
        _apply(
            repo, tid, "DOCA", period=_period(64),
            item=_item("DOCA"), effective_until=_period(65),
            base_version=2,
        )
        # Reativação: DOCA volta a partir de 18, DOCB preservado.
        _apply(
            repo, tid, "DOCA", period=_period(68),
            item=_item("DOCA"), base_version=3,
        )
        resolved = repo.resolve_published_version(_period(68))
        with plugins_db.plugins_db_connect() as conn, conn.cursor() as c:
            c.execute(
                "SELECT item_key FROM"
                " controllership_finance.checklist_template_item"
                " WHERE version_id = %s",
                (resolved["version_id"],),
            )
            keys = {r[0] for r in c.fetchall()}
        assert keys == {"DOCA", "DOCB"}

    def test_concurrent_admins_no_lost_update(self, migrated, repo):
        """Dois administradores com a mesma base_version: um vence, o
        outro recebe conflito — nunca perda silenciosa de exigência."""
        tid = _new_template()
        period = _period(70)
        results: dict[str, object] = {}
        errors: dict[str, Exception] = {}

        def run(name, key):
            try:
                results[name] = _apply(
                    repo, tid, key, period=period,
                    item=_item(key), base_version=0,
                )
            except de.ChecklistDomainError as exc:
                errors[name] = exc

        t1 = threading.Thread(
            target=run, args=("a", "DOCA"), daemon=True
        )
        t2 = threading.Thread(
            target=run, args=("b", "DOCB"), daemon=True
        )
        t1.start()
        t2.start()
        t1.join(timeout=30)
        t2.join(timeout=30)

        assert len(results) + len(errors) == 2
        if errors:
            loser_name = next(iter(errors))
            assert isinstance(
                errors[loser_name], (de.StaleRevision, de.OperationBusy)
            )
            # Retry do perdedor com a revisão fresca converge.
            loser_key = {"a": "DOCA", "b": "DOCB"}[loser_name]
            _apply(
                repo, tid, loser_key, period=period,
                item=_item(loser_key), base_version=1,
            )
        resolved = repo.resolve_published_version(period)
        with plugins_db.plugins_db_connect() as conn, conn.cursor() as c:
            c.execute(
                "SELECT item_key FROM"
                " controllership_finance.checklist_template_item"
                " WHERE version_id = %s",
                (resolved["version_id"],),
            )
            keys = {r[0] for r in c.fetchall()}
        assert {"DOCA", "DOCB"} <= keys


class TestLegacyWritersD3:
    """CP1.1 GATE-016 — writers legados respeitam a mesma regra D3:
    nenhuma publicação/inativação cobre competência já aberta."""

    def test_legacy_publish_rejects_window_over_open_competence(
        self, migrated, repo
    ):
        tid = _new_template()
        open_p = _period(70)
        repo.open_competence(open_p, actor=VIEWER)
        draft = repo.create_draft_version(tid, actor=ADMIN)
        repo.update_draft_items(
            tid,
            draft["version"],
            expected_revision=draft["revision"],
            items=[_item("DOCX")],
            actor=ADMIN,
        )
        repo.submit_version_for_review(
            tid, draft["version"], actor=ADMIN
        )
        with pytest.raises(de.WindowCoversOpenCompetence):
            repo.publish_version(
                tid,
                draft["version"],
                effective_from_period=_period(69),
                actor=ADMIN,
            )

    def test_legacy_publish_after_open_competence_allowed(
        self, migrated, repo
    ):
        """Irmão: vigência posterior à última competência aberta segue
        permitida — a guarda não é um bloqueio cego de retroatividade."""
        tid = _new_template()
        repo.open_competence(_period(71), actor=VIEWER)
        draft = repo.create_draft_version(tid, actor=ADMIN)
        repo.update_draft_items(
            tid,
            draft["version"],
            expected_revision=draft["revision"],
            items=[_item("DOCX")],
            actor=ADMIN,
        )
        repo.submit_version_for_review(
            tid, draft["version"], actor=ADMIN
        )
        published = repo.publish_version(
            tid,
            draft["version"],
            effective_from_period=_period(72),
            actor=ADMIN,
        )
        assert published["status"] == "PUBLISHED"

    def test_legacy_inactivate_rejects_window_over_open_competence(
        self, migrated, repo
    ):
        tid = _new_template()
        open_p = _period(73)
        _apply(
            repo, tid, "DOCX", period=open_p, item=_item("DOCX")
        )
        repo.open_competence(open_p, actor=VIEWER)
        with pytest.raises(de.WindowCoversOpenCompetence):
            repo.inactivate_version(tid, 1, actor=ADMIN)


class TestDiscardDraftVersion:
    """GATE-017 — descarte governado de DRAFT (sem mecanismo anterior)."""

    def _draft(self, repo, tid, items=None):
        draft = repo.create_draft_version(tid, actor=ADMIN)
        if items is not None:
            repo.update_draft_items(
                tid,
                draft["version"],
                expected_revision=draft["revision"],
                items=items,
                actor=ADMIN,
            )
            draft["revision"] += 1
        return draft

    def test_discard_removes_version_items_and_audits(
        self, migrated, repo
    ):
        tid = _new_template()
        draft = self._draft(repo, tid, items=[_item("DOCX")])
        result = repo.discard_draft_version(
            tid, draft["version"], expected_revision=2, actor=ADMIN
        )
        assert result["status"] == "DISCARDED"
        versions = repo.list_versions(tid)
        assert versions == []
        with plugins_db.plugins_db_connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT count(*) FROM"
                " controllership_finance.checklist_template_item i"
                " JOIN controllership_finance.checklist_template_version v"
                "   ON v.version_id = i.version_id"
                " WHERE v.template_id = %s",
                (tid,),
            )
            assert cur.fetchone()[0] == 0
            cur.execute(
                "SELECT event_type FROM"
                " controllership_finance.closing_audit_event"
                " WHERE entity_id = %s ORDER BY created_at",
                (result["version_id"],),
            )
            types = [r[0] for r in cur.fetchall()]
        assert "VERSION_DISCARDED" in types

    def test_discard_unblocks_document_operation(
        self, migrated, repo
    ):
        """Após o descarte, o comando documental opera com
        base_version=0 — fluxo do PO desbloqueado."""
        tid = _new_template()
        draft = self._draft(repo, tid)
        repo.discard_draft_version(
            tid, draft["version"], expected_revision=1, actor=ADMIN
        )
        result = _apply(
            repo, tid, "DOCX", period=_period(80), item=_item("DOCX")
        )
        assert result["replayed"] is False
        assert [v["version"]
                for v in result["published_versions"]] == [1]

    def test_discard_published_rejected(self, migrated, repo):
        tid = _new_template()
        _apply(
            repo, tid, "DOCX", period=_period(81), item=_item("DOCX")
        )
        with pytest.raises(de.VersionNotDraft):
            repo.discard_draft_version(
                tid, 1, expected_revision=1, actor=ADMIN
            )
        assert len(repo.list_versions(tid)) == 1

    def test_discard_review_rejected(self, migrated, repo):
        tid = _new_template()
        draft = self._draft(repo, tid, items=[_item("DOCX")])
        repo.submit_version_for_review(
            tid, draft["version"], actor=ADMIN
        )
        with pytest.raises(de.VersionNotDraft):
            repo.discard_draft_version(
                tid, draft["version"], expected_revision=2, actor=ADMIN
            )

    def test_discard_stale_revision(self, migrated, repo):
        tid = _new_template()
        draft = self._draft(repo, tid, items=[_item("DOCX")])
        with pytest.raises(de.StaleRevision):
            repo.discard_draft_version(
                tid,
                draft["version"],
                expected_revision=99,
                actor=ADMIN,
            )
        assert len(repo.list_versions(tid)) == 1

    def test_discard_missing_version(self, migrated, repo):
        tid = _new_template()
        with pytest.raises(de.VersionNotFound):
            repo.discard_draft_version(
                tid, 9, expected_revision=1, actor=ADMIN
            )
